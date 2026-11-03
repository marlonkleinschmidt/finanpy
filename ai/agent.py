"""Only module that builds the chat model and the agent."""

import time
from dataclasses import dataclass

import langsmith
from django.conf import settings
from langchain.agents import create_agent
from langchain.agents.middleware import (
    ModelCallLimitMiddleware,
    PIIMiddleware,
    ToolCallLimitMiddleware,
    before_model,
)
from langchain.agents.structured_output import ToolStrategy
from langchain_core.callbacks import UsageMetadataCallbackHandler
from langchain_openai import ChatOpenAI

from ai.context import AnalysisContext
from ai.prompts import SYSTEM_PROMPT, build_request_text
from ai.schemas import AnalysisOutput
from ai.tools import FINANCIAL_TOOLS

# Safety net only, since the limit middlewares control the cost. A run needs
# 10 steps per model call plus 7 (docs/ia.md), so 100 allows up to 9 calls.
AGENT_RECURSION_LIMIT = 100

# The built-in detector misses local parts with accents (joão@b.com).
EMAIL_PATTERN = r'[\w.%+-]+@[\w-]+(?:\.[\w-]+)+'

# Shapes of 13 to 19 digits. The built-in detector misses 15 and 19 digits,
# dots and numbers right after a letter. Money always ends in .NN, so the
# last lookahead and the fixed groups keep it intact, even for large totals.
# There is no Luhn check: a false positive only hides part of a description.
CREDIT_CARD_PATTERN = (
    r'(?<!\d)(?:'
    r'\d{13,19}'
    r'|\d{4}[ .-]\d{6}[ .-]\d{4,5}'
    r'|\d{4}(?:[ .-]\d{4}){3}(?:[ .-]\d{3})?'
    r')(?!\d)(?!\.\d)'
)


class ToolResultPIIMiddleware(PIIMiddleware):
    """Also redact the tool results that no later model call would read.

    A data tool called along with the output tool ends the run right after
    executing, and so its result never goes through before_model.
    """

    def after_agent(self, state, runtime):
        return self.before_model(state, runtime)


@before_model(can_jump_to=['end'])
def enforce_run_deadline(state, runtime):
    """End the run, without calling the model, once the deadline has passed.

    AnalysisContext.deadline is a value of time.monotonic().
    """
    if time.monotonic() >= runtime.context.deadline:
        return {'jump_to': 'end'}
    return None


@dataclass(frozen=True)
class AgentRunResult:
    structured_response: AnalysisOutput | None
    messages: list
    input_tokens: int
    output_tokens: int
    total_tokens: int


class RunTracker(UsageMetadataCallbackHandler):
    """Keep the tokens and the model messages, even if the run fails.

    The result of agent.invoke is lost when an exception leaves it. The call
    that raised the exception returned no usage, so it is not counted. Use
    one instance per run.
    """

    def __init__(self):
        super().__init__()
        self.ai_messages = []

    def on_llm_end(self, response, **kwargs):
        super().on_llm_end(response, **kwargs)
        for generations in response.generations:
            for generation in generations:
                message = getattr(generation, 'message', None)
                if message is not None:
                    self.ai_messages.append(message)

    def token_totals(self):
        usage = self.usage_metadata.values()
        return {
            'input_tokens': sum(item['input_tokens'] for item in usage),
            'output_tokens': sum(item['output_tokens'] for item in usage),
            'total_tokens': sum(item['total_tokens'] for item in usage),
        }


def build_chat_model():
    """Return a new chat model configured from the settings."""
    return ChatOpenAI(
        model=settings.AI_MODEL_NAME,
        api_key=settings.OPENAI_API_KEY,
        timeout=settings.AI_MODEL_TIMEOUT_SECONDS,
        max_retries=settings.AI_MODEL_MAX_RETRIES,
        max_completion_tokens=settings.AI_MAX_OUTPUT_TOKENS,
        reasoning_effort=settings.AI_REASONING_EFFORT,
    )


def build_agent():
    """Return a new agent, with no memory shared between runs."""
    return create_agent(
        model=build_chat_model(),
        tools=FINANCIAL_TOOLS,
        system_prompt=SYSTEM_PROMPT,
        context_schema=AnalysisContext,
        response_format=ToolStrategy(AnalysisOutput),
        # before_model hooks run in this order. Redaction comes first because
        # the other two hooks may end the run, which would leave the last
        # tool results without redaction.
        middleware=[
            ToolResultPIIMiddleware(
                'email',
                strategy='redact',
                detector=EMAIL_PATTERN,
                apply_to_tool_results=True,
            ),
            ToolResultPIIMiddleware(
                'credit_card',
                strategy='redact',
                detector=CREDIT_CARD_PATTERN,
                apply_to_tool_results=True,
            ),
            enforce_run_deadline,
            ModelCallLimitMiddleware(
                run_limit=settings.AI_MAX_MODEL_CALLS,
                exit_behavior='end',
            ),
            ToolCallLimitMiddleware(
                run_limit=settings.AI_MAX_TOOL_CALLS,
                exit_behavior='continue',
            ),
        ],
    )


def run_agent(context, tracker=None):
    """Run the agent once and return its output, messages and token usage.

    structured_response is None when the run ended without a valid output.
    Exceptions are not handled here: mapping them is up to the service, which
    passes a RunTracker to read the tokens of a run that failed.
    """
    usage_handler = tracker or RunTracker()
    agent = build_agent()
    # Tracing would send prompts and descriptions to LangSmith if a variable
    # in the environment turned it on (RNF26).
    with langsmith.tracing_context(enabled=False):
        result = agent.invoke(
            {
                'messages': [
                    {'role': 'user', 'content': build_request_text(context)},
                ],
            },
            context=context,
            config={
                'callbacks': [usage_handler],
                'recursion_limit': AGENT_RECURSION_LIMIT,
            },
        )
    return AgentRunResult(
        structured_response=result.get('structured_response'),
        messages=result['messages'],
        **usage_handler.token_totals(),
    )

"""Validation of output evidence against the actual tool results.

Messages are identified by their type attribute, so that this module can be
imported without loading LangChain (RNF23).
"""

import json
import re
from dataclasses import dataclass, field
from decimal import Decimal

OUTPUT_TOOL_NAME = 'AnalysisOutput'
REFUSED_OUTPUT_PREFIX = 'Error:'

# Text written by the user. A description such as '999.99' is not an amount,
# so it must not support an evidence about money.
FREE_TEXT_KEYS = frozenset({'description', 'category_name', 'account_name'})

# Only plain digits with an optional dot are numbers. The prompt asks for the
# value as the tool returned it, so '1.200,00', 'R$ 1200' and '12%' are not.
NUMBER_PATTERN = re.compile(r'-?[0-9]+(?:\.[0-9]+)?')
INTEGER_PATTERN = re.compile(r'-?[0-9]+')

DISCARDED_ITEM_NOTES = {
    'insights': (
        'Um insight foi descartado porque suas evidências não conferem com '
        'os dados.'
    ),
    'recommendations': (
        'Uma recomendação foi descartada porque suas evidências não conferem '
        'com os dados.'
    ),
    'alerts': (
        'Um alerta foi descartado porque suas evidências não conferem com os '
        'dados.'
    ),
}


@dataclass
class ToolValues:
    """Values of one tool, kept apart so that kinds never match by accident.

    A count only matches an integer evidence, and a boolean only its own
    text: neither of them may support '1.00' or '1200.00'.
    """

    numbers: set = field(default_factory=set)
    counts: set = field(default_factory=set)
    texts: set = field(default_factory=set)


@dataclass(frozen=True)
class EvidenceCheck:
    is_verified: bool
    content: dict


def _normalize_text(text):
    return ' '.join(text.split()).casefold()


def _collect_values(value, values, key=None):
    if isinstance(value, dict):
        for name, item in value.items():
            _collect_values(item, values, name)
    elif isinstance(value, list):
        for item in value:
            _collect_values(item, values, key)
    elif isinstance(value, bool):
        values.texts.add(str(value).casefold())
    elif isinstance(value, int):
        values.counts.add(Decimal(value))
    elif isinstance(value, str):
        if key not in FREE_TEXT_KEYS and NUMBER_PATTERN.fullmatch(value):
            values.numbers.add(Decimal(value))
        else:
            values.texts.add(_normalize_text(value))


def _is_data_tool_message(message):
    return (
        getattr(message, 'type', None) == 'tool'
        and getattr(message, 'status', None) != 'error'
        and getattr(message, 'name', None) != OUTPUT_TOOL_NAME
    )


def extract_tool_values(messages):
    """Return {tool name: ToolValues} with the data the tools really returned.

    Results that are errors, or that cannot be parsed, are not evidence.
    """
    values_by_tool = {}
    for message in messages:
        if not _is_data_tool_message(message):
            continue
        if not isinstance(message.content, str):
            continue
        try:
            data = json.loads(message.content)
        except ValueError:
            continue
        if isinstance(data, dict) and 'error' in data:
            continue
        values = values_by_tool.setdefault(message.name, ToolValues())
        _collect_values(data, values)
    return values_by_tool


def _is_evidence_found(evidence, values_by_tool):
    values = values_by_tool.get(evidence['source_tool'])
    if values is None:
        return False
    value = evidence['value'].strip()
    if not value:
        return False
    if NUMBER_PATTERN.fullmatch(value):
        number = Decimal(value)
        if number in values.numbers:
            return True
        return bool(
            INTEGER_PATTERN.fullmatch(value) and number in values.counts
        )
    return _normalize_text(value) in values.texts


def _is_item_verified(item, values_by_tool):
    evidence = item['evidence']
    return bool(evidence) and all(
        _is_evidence_found(entry, values_by_tool) for entry in evidence
    )


def validate_output(output, messages):
    """Check the evidence of an output, as dumped by model_dump(mode='json').

    The whole item is discarded if any of its evidence is not found, and the
    discard is recorded in data_limitations without the unverified text. The
    analysis is not verified if its main insight or all recommendations fail.
    """
    values_by_tool = extract_tool_values(messages)
    if not _is_item_verified(output['main_insight'], values_by_tool):
        return EvidenceCheck(is_verified=False, content={})

    content = {
        'main_insight': output['main_insight'],
        'data_limitations': list(output['data_limitations']),
    }
    for kind, note in DISCARDED_ITEM_NOTES.items():
        verified = []
        for item in output[kind]:
            if _is_item_verified(item, values_by_tool):
                verified.append(item)
            else:
                content['data_limitations'].append(note)
        content[kind] = verified

    if not content['recommendations']:
        return EvidenceCheck(is_verified=False, content={})
    return EvidenceCheck(is_verified=True, content=content)


def extract_tool_calls(messages):
    """Return name and arguments of the tools the model asked for.

    The output tool stays out, because its arguments hold the whole output.
    Calls refused by the tool limit are included.
    """
    return [
        {'name': call['name'], 'args': call['args']}
        for message in messages
        if getattr(message, 'type', None) == 'ai'
        for call in message.tool_calls
        if call['name'] != OUTPUT_TOOL_NAME
    ]


def _is_last_output_refused(messages):
    # A refusal comes with status='success', and only the text identifies it.
    # status='error' means the tool limit stopped the call, with no check.
    for message in reversed(messages):
        if (
            getattr(message, 'type', None) == 'tool'
            and getattr(message, 'name', None) == OUTPUT_TOOL_NAME
        ):
            return (
                message.status != 'error'
                and isinstance(message.content, str)
                and message.content.startswith(REFUSED_OUTPUT_PREFIX)
            )
    return False


def is_invalid_output(messages, max_model_calls):
    """Tell an empty or refused output from a run that hit the call limit.

    ModelCallLimitMiddleware ends the run by adding an AI message of its own,
    without tool calls, after the last allowed call. Counting the messages
    identifies it without depending on its text.
    """
    ai_messages = [
        message
        for message in messages
        if getattr(message, 'type', None) == 'ai'
    ]
    if len(ai_messages) > max_model_calls:
        ai_messages.pop()
    if ai_messages and not ai_messages[-1].tool_calls:
        return True
    return _is_last_output_refused(messages)

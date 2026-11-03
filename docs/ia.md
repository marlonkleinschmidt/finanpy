# Assistente Financeiro com IA

Documentação técnica da app `ai`: um agente LangChain 1.x com modelo da OpenAI que lê os dados financeiros do usuário logado, somente para leitura, e grava uma análise educativa com evidências conferidas. A especificação está na seção 14 do `PRD.md`; este documento descreve **o código como está**. Onde os dois divergem, vale o código, e a divergência fica em [Ajustes pendentes no PRD](#ajustes-pendentes-no-prd).

Conteúdo:

1. [Arquitetura](#arquitetura)
2. [Tools](#tools)
3. [Fluxo de execução](#fluxo-de-execução)
4. [Códigos de erro](#códigos-de-erro)
5. [Limites e configuração](#limites-e-configuração)
6. [Segurança e isolamento](#segurança-e-isolamento)
7. [Como trocar o modelo](#como-trocar-o-modelo)
8. [Teste real (tarefa 10.12.11)](#teste-real-tarefa-101211)
9. Registro das verificações feitas durante a implementação, a partir de [Comportamentos confirmados (tarefa 10.1.5)](#comportamentos-confirmados-tarefa-1015).

Versões instaladas (`requirements.txt`): `langchain==1.4.8`, `langchain-core==1.7.4`, `langchain-openai==1.7.3`, `langgraph==1.2.19`, `langgraph-prebuilt==1.1.1`, `langsmith==0.14.17` e `openai==3.42.1`. As dependências de IA são uma exceção à regra de usar só recursos nativos (PRD 14.19, item I-03).

## Arquitetura

O restante do sistema só conversa com `ai.services`. O agente roda de forma síncrona, dentro do POST, sem fila nem worker (PRD 14.6).

```text
AnalysisCreateView (POST ai:create) ─┐
DashboardView (core, só leitura) ────┴─> ai.services ──> FinancialAnalysis
                                              │
                                              ├─> ai.agent ──> ChatOpenAI (API da OpenAI)
                                              │       └─> ai.tools ──> ai.queries ──> ORM (Transaction, Account, Category)
                                              └─> ai.validators (evidências)
```

| Módulo             | Responsabilidade                                                                                                                                                                                                         |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `ai/context.py`    | `AnalysisContext`, `dataclass(frozen=True)` com `user_id`, `period_start`, `period_end`, `deadline` (valor de `time.monotonic()`) e `owner_thread_id`. Também `shift_month` e `calculate_analysis_period` (RN02).        |
| `ai/queries.py`    | Funções puras de ORM, sem LangChain. Todas recebem `user_id` como primeiro parâmetro, fazem **uma consulta** cada e devolvem dados prontos para JSON (dinheiro como texto com 2 casas, percentual com 1 casa, datas ISO). Argumento inválido levanta `ValueError`. |
| `ai/tools.py`      | Camada fina com `@tool`: lê `runtime.context`, valida os parâmetros contra o período, chama `queries`, limpa o texto livre e devolve sempre um `dict`. Exporta `FINANCIAL_TOOLS`.                                         |
| `ai/prompts.py`    | `SYSTEM_PROMPT` (em inglês, pedindo o texto em português) e `PROMPT_VERSION` (atual: `'1'`, gravado em cada análise). `build_request_text(context)` monta o pedido com o período, o mês parcial e o orçamento de chamadas, sem identificar o usuário. Toda mudança no texto enviado ao modelo incrementa `PROMPT_VERSION`. |
| `ai/schemas.py`    | Schemas Pydantic da saída: `AnalysisOutput` com `main_insight`, `insights` (até 4), `recommendations` (1 a 5), `alerts` (até 3, com `severity` `info`, `warning` ou `critical`) e `data_limitations` (até 5). Cada item tem de 1 a 5 `EvidenceItem` (`label`, `value`, `source_tool`). |
| `ai/agent.py`      | Único módulo que monta o modelo e o agente: `build_chat_model()`, `build_agent()` e `run_agent(context, tracker=None)`, que devolve `AgentRunResult`. Define os middlewares, os detectores de PII, `RunTracker` e `AGENT_RECURSION_LIMIT = 100`. |
| `ai/validators.py` | Confere cada evidência com os valores que a tool indicada realmente retornou na execução (`validate_output`), extrai as tool calls gravadas (`extract_tool_calls`) e distingue saída inválida de limite atingido (`is_invalid_output`). Não importa LangChain. |
| `ai/services.py`   | Único ponto de entrada e único módulo que grava análises: `generate_analysis(user)`, `get_dashboard_analysis_state(user)`, `get_latest_valid_analysis(user)` e `get_stale_notice(analysis)`. Define `GenerationOutcome` e `AnalysisState`. |
| `ai/models.py`     | `FinancialAnalysis` (herda `TimeStampedModel`), com `Status` (`pending`, `success`, `failed`), `ErrorCode`, conteúdo em `JSONField`, tokens, duração, modelo e versão do prompt. Restrição única de um `pending` por usuário e índice em `(user, status, -generated_at)`. |
| `ai/views.py`      | `AnalysisListView` (20 por página), `AnalysisDetailView` (404 para outro usuário, via `UserQuerySetMixin`) e `AnalysisCreateView` (somente POST, converte o `GenerationOutcome` em mensagem e redireciona ao dashboard). Rotas `ai:list`, `ai:create` e `ai:detail`. |
| `ai/admin.py`      | Admin sem inclusão nem edição. A exclusão continua permitida, para não bloquear a exclusão de usuários.                                                                                                                   |

**Carregamento tardio (RNF23).** Nenhuma página carrega LangChain ou OpenAI. `ai.services` importa `ai.agent` só dentro de `_run_and_record`, e `_error_code_for_exception` importa `openai`, `langchain` e `langgraph` só ao mapear uma exceção. `ai.validators` identifica as mensagens pelo atributo `type`, sem importar classes do LangChain. `LangChainNotImportedTests` abre o dashboard, o histórico e o detalhe em um interpretador novo e confirma que nenhum módulo `langchain*`, `langgraph*`, `langsmith*` ou `openai*` foi carregado.

**Agente.** `build_agent()` cria um agente novo a cada execução, com `create_agent`, `context_schema=AnalysisContext` e `response_format=ToolStrategy(AnalysisOutput)`, sem `checkpointer`, `store` nem memória. Os middlewares, nesta ordem:

| Ordem | Middleware                                       | Configuração                                                                                   |
| ----- | ------------------------------------------------ | ---------------------------------------------------------------------------------------------- |
| 1     | `ToolResultPIIMiddleware('email', ...)`          | `strategy='redact'`, `detector=EMAIL_PATTERN` (aceita acentos), `apply_to_tool_results=True`.  |
| 2     | `ToolResultPIIMiddleware('credit_card', ...)`    | `strategy='redact'`, `detector=CREDIT_CARD_PATTERN` (13 a 19 dígitos, sem Luhn), idem.         |
| 3     | `enforce_run_deadline`                           | `@before_model(can_jump_to=['end'])`: encerra sem chamar o modelo quando o prazo vence.        |
| 4     | `ModelCallLimitMiddleware`                       | `run_limit=AI_MAX_MODEL_CALLS`, `exit_behavior='end'`.                                         |
| 5     | `ToolCallLimitMiddleware`                        | `run_limit=AI_MAX_TOOL_CALLS`, `exit_behavior='continue'`.                                     |

`ToolResultPIIMiddleware` é um `PIIMiddleware` que repete a redação em `after_agent`. O motivo da ordem e desse acréscimo está em [Agente (tarefa 10.6)](#agente-tarefa-106). `run_agent` executa dentro de `langsmith.tracing_context(enabled=False)`, com `config={'callbacks': [RunTracker()], 'recursion_limit': 100}`. `RunTracker` (subclasse de `UsageMetadataCallbackHandler`, uma instância por execução) guarda tokens e `AIMessage` mesmo quando o `invoke` levanta exceção.

## Tools

Regras comuns, garantidas no código:

- **Nenhuma tool tem parâmetro de usuário.** O dono vem só de `runtime.context.user_id`. O parâmetro `runtime: ToolRuntime[AnalysisContext]` não aparece no schema enviado ao modelo.
- `closes_pool_connection` valida o contexto antes de qualquer consulta (`AnalysisContext` com `user_id` inteiro positivo, senão `RuntimeError`, que interrompe a execução) e fecha a conexão Django ao terminar, quando a tool roda fora de `owner_thread_id`.
- `returns_argument_errors` devolve ao modelo `{'error': <código>, 'detail': <texto>}` para `ToolArgumentError` e `ValueError`. Erro de tipo ou faixa no schema volta como `ToolMessage` com `status='error'`. Qualquer outra exceção interrompe a execução e vira `internal_error`.
- Datas devem estar em `[period_start, period_end]` do contexto, com `start_date <= end_date`.
- Transações com data futura ficam fora (RN03), exceto em `get_accounts_overview`, que segue `Account.current_balance`.
- `_owned_transactions` filtra `user_id`, `account__user_id` e `category__user_id`, então uma linha ligada a conta ou categoria de outro usuário nunca aparece.
- Os campos `description`, `category_name` e `account_name` passam por `_clean_text`: caracteres de controle, quebras de linha e tabulações viram espaço, e espaços repetidos são unidos.
- Retorno sempre em `dict`: as listas vêm dentro de uma chave (`months`, `changes`, `expenses`, `transactions`).

| Tool                       | Parâmetros do modelo                                                                    | Retorno                                                                                                                                                       | Observações                                                                                                                         |
| -------------------------- | --------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `get_financial_summary`    | `start_date`, `end_date`                                                                | `income_total`, `expense_total`, `net_result`, `savings_rate_percent`, `income_count`, `expense_count`                                                        | Taxa de poupança `null` sem entradas.                                                                                               |
| `get_monthly_evolution`    | `months` (1 a `AI_ANALYSIS_WINDOW_MONTHS`)                                              | `months`: lista com `month`, `income_total`, `expense_total`, `net_result`, `expense_change_percent`, `is_partial_month`                                       | Termina no mês corrente e inclui meses vazios. Variação `null` no primeiro mês, no mês parcial e sem gasto anterior. Erro `months_out_of_period` se passar do período. |
| `get_category_breakdown`   | `start_date`, `end_date`, `transaction_type` (`income` ou `expense`), `limit` (1 a 20)  | `categories`: lista com `category_name`, `total`, `transaction_count`, `share_percent`; mais `others_total`                                                   | Ordem por total decrescente. `others_total` soma as categorias além do `limit`.                                                     |
| `get_category_changes`     | `month` (`AAAA-MM`), `limit` (1 a 20)                                                   | `changes`: lista com `category_name`, `current_total`, `previous_total`, `absolute_change`, `percent_change`, `is_significant`                                | Só saídas. Aceita mês fechado cujo mês anterior esteja no período (`month_not_closed`, `month_out_of_period`). `is_significant` segue RN10 (alta de pelo menos 20% **e** de R$ 50,00; sem gasto no mês anterior, só o valor conta); os significativos vêm primeiro. |
| `get_recurring_expenses`   | `limit` (1 a 10)                                                                        | `expenses`: lista com `description`, `category_name`, `distinct_months`, `average_amount`, `last_date`                                                        | Usa o período do contexto. Agrupa por descrição em minúsculas e categoria, com pelo menos 3 meses distintos (RN09). Além do `limit`, os grupos são omitidos sem aviso. `Lower` do SQLite só converte ASCII. |
| `get_largest_transactions` | `start_date`, `end_date`, `transaction_type`, `limit` (1 a 10)                          | `transactions`: lista com `date`, `description`, `amount`, `category_name`, `account_name`                                                                    | Ordem por valor, data e `pk` decrescentes.                                                                                          |
| `get_accounts_overview`    | nenhum                                                                                  | `accounts`: lista com `account_name`, `account_type`, `current_balance`; mais `total_balance`                                                                 | Uma consulta com `annotate`, igual a `Account.current_balance` (teste dedicado). Inclui saldo inicial e datas futuras.               |

Códigos de erro que as tools devolvem ao modelo (não são `error_code` da análise): `invalid_date_range`, `date_out_of_period`, `month_not_closed`, `month_out_of_period`, `months_out_of_period` e `invalid_argument`.

Nunca chegam ao modelo: nome, e-mail e telefone do usuário, `Account.bank_name`, `Category.color` e identificadores internos (`id`, `pk`, `user_id`). Os e-mails e números com formato de cartão que estiverem em descrições ou nomes são redigidos pelos middlewares de PII, com as lacunas descritas em [Agente (tarefa 10.6)](#agente-tarefa-106).

## Fluxo de execução

`generate_analysis(user)` não depende de `request`, nunca propaga `Exception` e retorna um `GenerationOutcome`:

1. Marca como `failed` (`abandoned`) os `pending` do usuário criados há mais de `AI_ANALYSIS_PENDING_TIMEOUT_MINUTES`.
2. Sem `OPENAI_API_KEY`: retorna `disabled`.
3. Calcula o período (mês corrente e os `AI_ANALYSIS_WINDOW_MONTHS - 1` anteriores, até hoje) e o `metrics_snapshot` (1 consulta). Com menos de `AI_ANALYSIS_MIN_TRANSACTIONS` transações no período: retorna `insufficient_data`.
4. Com `AI_ANALYSIS_DAILY_LIMIT` registros criados hoje (dia local, **qualquer status**): retorna `limit_reached`.
5. Cria o registro `pending` com o snapshot, em uma transação curta. `IntegrityError` na restrição única: retorna `already_running`.
6. Verifica que não há transação aberta (`connection.in_atomic_block`; se houver, grava `internal_error` sem chamar o modelo), carrega `ai.agent`, monta o `AnalysisContext` com `deadline = monotonic() + AI_RUN_BUDGET_SECONDS` e executa `run_agent`.
7. Sem `structured_response`: `timeout` se o prazo venceu; senão `invalid_output` se a última resposta real do modelo não tem tool call ou a última `AnalysisOutput` foi recusada; senão `limit_exceeded`.
8. Valida as evidências. `main_insight` sem evidência conferida, ou nenhuma recomendação restante: `unverified_output`. Os demais itens não conferidos são descartados, com uma frase em `data_limitations`.
9. Grava resultado, tokens, `tool_calls` e `duration_ms`, **somente se o registro ainda estiver `pending`**. Retorna `success` ou `failed`.

Uma exceção nos passos 1 a 5 retorna `failed` sem registro. Uma falha na gravação final deixa o `pending`, que o passo 1 da próxima chamada encerra como `abandoned`. A view não pode envolver a chamada em `transaction.atomic()`, e `ATOMIC_REQUESTS` deve continuar desativado.

| `GenerationOutcome` | Mensagem da view (`django.contrib.messages`)                              |
| ------------------- | -------------------------------------------------------------------------- |
| `success`           | Sucesso: "Análise gerada com sucesso."                                    |
| `failed`            | Erro: "Não foi possível gerar a análise. Tente novamente mais tarde."     |
| `already_running`   | Erro: "Já existe uma análise em andamento."                               |
| `limit_reached`     | Erro: "Você atingiu o limite de análises de hoje."                        |
| `insufficient_data` | Erro: "Ainda não há transações suficientes para gerar uma análise."       |
| `disabled`          | Erro: "O assistente não está disponível no momento."                      |

**Card do dashboard.** `DashboardView` chama `get_dashboard_analysis_state(user)`, que faz até 3 consultas, não grava nada, não carrega LangChain e **nunca chama o modelo**. O formato do dict está em [Validação e serviço](#validação-e-serviço-tarefas-108-e-109). Estados (`AnalysisState`), na ordem de prioridade:

| Prioridade | `state`             | Condição                                                                 | Botão (`can_generate`)             |
| ---------- | ------------------- | ------------------------------------------------------------------------ | ---------------------------------- |
| 1          | `disabled`          | Sem `OPENAI_API_KEY`.                                                    | Sem botão                          |
| 2          | `running`           | `pending` mais recente que `AI_ANALYSIS_PENDING_TIMEOUT_MINUTES`.        | Desativado                         |
| 3          | `insufficient_data` | Menos de `AI_ANALYSIS_MIN_TRANSACTIONS` transações no período.           | Sem botão, com link **Nova transação** |
| 4          | `limit_reached`     | Limite diário atingido.                                                  | Desativado                         |
| 5          | `failed`            | Última falha mais recente que a última análise válida.                   | Ativo                              |
| 6          | `stale`             | Última válida com mais de `AI_ANALYSIS_STALE_DAYS` dias (RN06).          | Ativo                              |
| 7          | `no_analysis`       | Nenhuma análise `success`.                                               | Ativo                              |
| 8          | `with_analysis`     | Existe análise válida recente.                                           | Ativo                              |

O estado **Carregando** existe só no navegador (`static/js/analysis_form.js`), com o texto de `loading_message`, que arredonda `AI_RUN_BUDGET_SECONDS` para cima em minutos.

## Códigos de erro

`error_code` de `FinancialAnalysis` (o rótulo em português é o do `ErrorCode`). `error_detail` guarda só o nome da classe da exceção, nunca a mensagem.

| `error_code`           | Rótulo                          | Causa no código                                                                                                                           |
| ---------------------- | ------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `authentication_error` | Chave inválida ou revogada      | `openai.AuthenticationError` ou `openai.PermissionDeniedError`.                                                                           |
| `model_unavailable`    | Modelo indisponível             | `openai.NotFoundError`: nome errado em `AI_MODEL_NAME` ou modelo desligado (item I-01).                                                   |
| `rate_limited`         | Limite de uso ou cota esgotada  | `openai.RateLimitError`.                                                                                                                  |
| `timeout`              | Tempo esgotado                  | `openai.APITimeoutError` (testada antes de `APIConnectionError`, de que é subclasse), ou execução sem saída depois do prazo de `enforce_run_deadline`. |
| `provider_unavailable` | Provedor indisponível           | `openai.APIConnectionError` ou `openai.InternalServerError`.                                                                              |
| `limit_exceeded`       | Limite de chamadas atingido     | `GraphRecursionError`, ou execução sem saída dentro do prazo e sem os sinais de `invalid_output` (em geral, `AI_MAX_MODEL_CALLS` atingido). |
| `invalid_output`       | Saída inválida                  | Sem saída porque a última resposta do modelo veio sem tool call (inclusive vazia) ou a última `AnalysisOutput` foi recusada. `StructuredOutputValidationError` e `MultipleStructuredOutputsError` também mapeiam para cá, mas não ocorrem com `handle_errors=True`. |
| `unverified_output`    | Evidências não conferidas       | `validate_output`: `main_insight` sem evidência conferida ou nenhuma recomendação restante.                                               |
| `abandoned`            | Execução interrompida           | Passo 1 do fluxo: `pending` mais antigo que `AI_ANALYSIS_PENDING_TIMEOUT_MINUTES`.                                                        |
| `internal_error`       | Erro interno                    | Qualquer outra exceção: transação aberta, contexto ausente ou inválido em uma tool, erro de banco, `openai.BadRequestError` etc.          |

As classes de exceção de `langchain_openai` herdam das de `openai` e recebem o mesmo código. O log usa `logger.error` com `analysis_id`, `error_code`, nome da classe e `traceback.format_tb`, sem a mensagem nem as exceções encadeadas, que podem conter a chave ou descrições.

## Limites e configuração

Todos os settings vêm de variáveis de ambiente (ou do `.env`, que `core/settings.py` copia para `os.environ` sem sobrescrever o ambiente real).

| Variável / setting                    | Padrão       | Efeito                                                                                     |
| ------------------------------------- | ------------ | ------------------------------------------------------------------------------------------ |
| `OPENAI_API_KEY`                      | `''`         | Vazia: estado `disabled`, sem chamada ao modelo. O sistema inicia e os testes passam sem ela. |
| `AI_MODEL_NAME`                       | `gpt-5-mini` | Modelo usado e gravado em `model_name`.                                                    |
| `AI_REASONING_EFFORT`                 | `low`        | Enviado como `reasoning_effort`.                                                           |
| `AI_MODEL_TIMEOUT_SECONDS`            | `45`         | Tempo máximo de cada chamada HTTP ao modelo.                                               |
| `AI_MODEL_MAX_RETRIES`                | `1`          | Novas tentativas do cliente em erros temporários. Não há `ModelRetryMiddleware`.           |
| `AI_MAX_OUTPUT_TOKENS`                | `4000`       | `max_completion_tokens` por chamada, raciocínio incluído. Valor baixo pode gerar resposta vazia (`invalid_output`). |
| `AI_ANALYSIS_WINDOW_MONTHS`           | `6`          | Meses do período, incluindo o corrente (parcial). Também é o máximo de `months` em `get_monthly_evolution`, lido **ao importar `ai.tools`**. |
| `AI_ANALYSIS_MIN_TRANSACTIONS`        | `5`          | Mínimo de transações no período para chamar o modelo.                                      |
| `AI_ANALYSIS_DAILY_LIMIT`             | `3`          | Registros por usuário por dia local, de qualquer status.                                   |
| `AI_ANALYSIS_STALE_DAYS`              | `30`         | Dias até uma análise ser considerada desatualizada (RN06).                                 |
| `AI_ANALYSIS_PENDING_TIMEOUT_MINUTES` | `5`          | Tempo até um `pending` virar `abandoned`.                                                  |
| `AI_RUN_BUDGET_SECONDS`               | `120`        | Prazo da execução, checado antes de cada chamada ao modelo.                                |
| `AI_MAX_MODEL_CALLS`                  | `8`          | Chamadas ao modelo por execução (`ModelCallLimitMiddleware`).                              |
| `AI_MAX_TOOL_CALLS`                   | `10`         | Chamadas de tools por execução, **contando a `AnalysisOutput`** (`ToolCallLimitMiddleware`). |

Outros limites fixos no código:

- `AGENT_RECURSION_LIMIT = 100` cobre `AI_MAX_MODEL_CALLS` até 9 (10 passos por chamada mais 7). Ao subir esse setting para 10 ou mais, aumente o limite, senão a execução termina em `GraphRecursionError` (`limit_exceeded`) antes do limite de modelo.
- `limit` das tools: 20 em `get_category_breakdown` e `get_category_changes`, 10 em `get_recurring_expenses` e `get_largest_transactions`.
- Tempo máximo de uma geração: a última chamada pode começar perto de 120 s e durar 45 s × 2 tentativas, cerca de 210 s, abaixo dos 5 minutos de `abandoned`.
- Prompt: `PROMPT_VERSION = '1'`.

## Segurança e isolamento

Garantias do código:

- O dono dos dados vem de `request.user`, passa por `AnalysisContext` (imutável) e é lido em `runtime.context`. O modelo não tem como escolher o usuário.
- Toda função de `ai.queries` recebe `user_id` primeiro e filtra o dono da transação, da conta e da categoria.
- Somente leitura: sem tool de escrita, SQL dinâmico ou execução de código.
- Sem estado compartilhado: agente, modelo, `AnalysisContext` e `RunTracker` são criados a cada execução, sem `checkpointer`, `store` ou `thread_id`.
- Descrições e nomes são tratados como dados no prompt. Os templates não usam `|safe` em conteúdo gerado.
- O rastreamento do LangSmith fica desligado em `run_agent`, mesmo com `LANGSMITH_TRACING=true` no ambiente.
- Uma análise só é gravada com evidências conferidas contra o retorno real das tools.

O que os testes da tarefa 10.13 (`ai/tests.py`) demonstram, com os usuários A e B e dados diferentes, e com modelo falso:

| Classe de teste                 | O que garante                                                                                                                       |
| ------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `ForgedOwnerToolCallTests`      | O modelo envia o id de B (`user_id`, `user` etc.) em todas as tool calls de uma execução de A: só voltam e são gravados dados de A. |
| `QueryAndToolIsolationTests`    | Toda query recebe o dono primeiro, todas as tools são testadas, e nenhuma devolve dados de B, inclusive linhas "cruzadas" ligadas a conta ou categoria de B. |
| `ConcurrentAnalysesTests`       | Execuções de A e B ao mesmo tempo gravam só os próprios dados.                                                                      |
| `OtherUserAnalysisPagesTests`   | Detalhe de qualquer análise de A retorna 404 para B; lista e dashboard de B não mostram nada de A.                                  |
| `ForgedOwnerPostTests`          | Id ou e-mail de A no POST de B são ignorados.                                                                                       |
| `MaliciousAnalysisContentTests` | HTML no conteúdo é escapado, e os templates de análise não desligam o escape.                                                       |
| `PromptInjectionTests`          | Uma descrição com injeção, obedecida pelo modelo falso, só encontra tools de leitura e não altera nada.                            |
| `ReadOnlyToolsTests`            | Tools e queries não alteram nenhum registro, nem `updated_at`.                                                                      |
| `ModelInputPrivacyTests`        | O modelo nunca recebe nome, e-mail, telefone, `bank_name` nem chaves internas; a redação mantém o JSON válido.                     |
| `PerUserLimitTests`             | `pending`, `abandoned` e limite diário de A não afetam B.                                                                           |

Também cobrem segurança: `ToolsTests` (sem parâmetro de dono e contexto inválido), `AnalysisLoginRequiredTests` e as listas e detalhes em `AnalysisListViewTests` e `AnalysisDetailViewTests`.

Riscos conhecidos: a redação de PII é redução de risco, não garantia (lacunas de cartão em [Agente (tarefa 10.6)](#agente-tarefa-106)); a validação confere as evidências estruturadas, não cada número citado livremente em `description`; e a adequação à LGPD está em aberto (PRD 14.19, item I-05).

## Como trocar o modelo

O modelo é definido só por `AI_MODEL_NAME`, sem alteração de código. **A OpenAI desliga o `gpt-5-mini` em 11/12/2026** (PRD 14.8 e 14.19, item I-01, decidido em 02/11/2026: manter até a troca). A partir dessa data, sem troca, toda geração deve falhar com `model_unavailable`. O substituto indicado pela OpenAI no PRD é `gpt-5.6-terra`, ainda não testado neste projeto.

Parâmetros que `build_chat_model()` envia, confirmados com `gpt-5-mini` em 02/11/2026 (tarefa 10.3.6): `max_completion_tokens`, `reasoning_effort` e `tools` com `tool_choice='required'`. **`temperature` não é enviada.** Antes de trocar:

1. Verifique na documentação oficial da OpenAI, e anote a data, se o novo modelo aceita `reasoning_effort` (e quais valores), `max_completion_tokens` e tool calling, e qual o preço por milhão de tokens.
2. Ajuste `AI_REASONING_EFFORT` e `AI_MAX_OUTPUT_TOKENS`, se preciso, e atualize `LIVE_INPUT_PRICE_PER_MILLION` e `LIVE_OUTPUT_PRICE_PER_MILLION` em `ai/tests.py` com o novo preço.
3. Defina `AI_MODEL_NAME` no ambiente ou no `.env` e reinicie o servidor.
4. Rode a suíte sem custo: `venv\Scripts\python manage.py test ai`.
5. Com autorização do responsável, rode o teste real e registre o resultado neste documento.

**Teste real** (gera custo, usa a chave do ambiente ou do `.env`):

```powershell
$env:RUN_LIVE_AI_TESTS = 'True'
venv\Scripts\python manage.py test ai.tests.LiveAnalysisTests
Remove-Item Env:RUN_LIVE_AI_TESTS
```

O valor precisa ser exatamente `True`. Sem `OPENAI_API_KEY`, o teste é pulado. Ele cria um usuário no banco de teste, executa `generate_analysis` uma vez, imprime só números (modelo, resultado, tempo, tokens, tools e custo estimado) e exige `success`, tokens maiores que zero e tempo abaixo de `AI_RUN_BUDGET_SECONDS + 90`. Não coloque `RUN_LIVE_AI_TESTS` no `.env`: como o arquivo é copiado para `os.environ`, toda execução de `manage.py test` passaria a chamar a API.

## Teste real (tarefa 10.12.11)

Executado em 03/11/2026, com autorização do responsável, uma única vez: `ai.tests.LiveAnalysisTests`, modelo `gpt-5-mini`, com os settings padrão.

| Medida                         | Valor                         |
| ------------------------------ | ----------------------------- |
| Resultado                      | `success`                     |
| Tempo                          | 26,6 s (`duration_ms` 26640)  |
| Tokens de entrada              | 4.845                         |
| Tokens de saída                | 2.619                         |
| Total de tokens                | 7.464                         |
| Tools chamadas (`tool_calls`)  | 8                             |
| Custo estimado                 | US$ 0,00645                   |

O custo é calculado, não cobrado: 4.845 × US$ 0,25 + 2.619 × US$ 2,00 por milhão de tokens (preços do PRD 14.18, verificados em 02/11/2026), **sem o desconto de entrada em cache**. A saída, que inclui raciocínio, responde por cerca de 81% do custo.

Comparação com a estimativa do PRD 14.18 (20 mil tokens de entrada e 3 mil de saída, US$ 0,011 por análise): a execução medida usou cerca de um quarto da entrada estimada e custou cerca de 59% do valor estimado. Projetando a medição, um usuário no limite diário por 30 dias (90 análises) custaria cerca de US$ 0,58 por mês, contra US$ 1,00 estimado. É uma amostra com os dados de teste de `create_agent_data`; usuários com mais categorias e transações geram retornos de tools maiores. A primeira análise real observada pela aplicação (abaixo) teve números próximos: 28 s, 4.802 tokens de entrada e 2.269 de saída.

# Registro das verificações

As seções a seguir registram, por tarefa, o que foi confirmado com modelo falso ou com chamadas reais durante a implementação. Elas explicam as decisões descritas acima.

## Comportamentos confirmados (tarefa 10.1.5)

Testado em 02/11/2026, executando o agente com modelo falso (subclasse de `GenericFakeChatModel` com `bind_tools`), sem chave de API e sem chamadas à OpenAI. Versões: `langchain==1.4.8`, `langchain-core==1.7.4`, `langchain-openai==1.7.3`, `langgraph==1.2.19`, `langgraph-prebuilt==1.1.1`, em Python 3.12.0. Revalide se alguma delas mudar.

### a) `ToolStrategy` e `ToolCallLimitMiddleware`

A tool de saída **conta** no `run_limit`. Com `run_limit=2`, duas tools reais e a chamada de saída, a terceira chamada excede o limite:

| `exit_behavior`        | Resultado no caso limítrofe                                                                                                         |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `'continue'` (padrão)  | Termina com `structured_response`. Fica uma segunda `ToolMessage` com `status='error'` para o mesmo `tool_call_id`.                  |
| `'error'`              | Levanta `ToolCallLimitExceededError` e perde a saída já gerada.                                                                     |
| `'end'`                | Mantém `structured_response` nesse caso, mas perde a saída se o limite for excedido em uma mensagem com tools reais, antes da saída. |

Consequências:

- Manter `exit_behavior='continue'`. Com ele, a saída nunca é perdida pelo limite de tools.
- `AI_MAX_TOOL_CALLS=10` executa até 10 tools reais. As excedentes recebem uma `ToolMessage` de erro, mesmo em chamadas paralelas (12 pedidas, 10 executadas).
- Ao ler as `ToolMessage`, ignore `status='error'` e a tool de saída, inclusive em `tool_calls` da análise.
- Se a saída for inválida depois de esgotado o limite, a nova tentativa envia ao modelo duas `ToolMessage` com o mesmo `tool_call_id`. A reação da API real a isso **não foi verificada**.
- O encerramento pelo `ModelCallLimitMiddleware` não levanta exceção. Saída sempre inválida também termina assim, sem `StructuredOutputValidationError`, pois `handle_errors` é `True` por padrão.
- `structured_response` pode vir ausente (prazo vencido antes da primeira chamada) ou `None` (limite de modelo ou resposta sem tool call). Use `result.get('structured_response') is None`.
- Tool real e saída na mesma mensagem: a tool executa, o modelo não vê o resultado, e a execução termina.

### b) `PIIMiddleware` com JSON

A redação é feita por regex sobre o **texto** da `ToolMessage`, sem interpretar o JSON, e altera as mensagens do estado. Portanto, `result['messages']` traz o mesmo texto redigido que o modelo recebeu. Tools que retornam `dict` ou `list` são serializadas com `ensure_ascii=False`.

| Entrada                                                                                  | Resultado                                                                 |
| ---------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| E-mail ou cartão de 16 dígitos com separação comum dentro de uma string                  | Redigido, e o JSON continua válido.                                       |
| `'1234.56'`, `'-1234.56'`, `'9999999999.99'`, `'123456789012.34'`, datas e contagens     | Inalterados.                                                              |
| Exatamente 16 dígitos, válidos no algoritmo de Luhn, sem aspas: `4111111111111111`       | Redigido sem aspas: **JSON inválido**.                                    |
| Texto `'4111111111111111.00'` (Luhn válido)                                              | Vira `'[REDACTED_CREDIT_CARD].00'`. Não alcançável com valores reais.     |
| E-mail colado depois de um escape JSON (`\n`, `\t`, `ã`)                       | O detector consome a letra do escape: `\[REDACTED_EMAIL]`, **JSON inválido**. |
| E-mail com acento antes do `@`, com `ensure_ascii=False` (`joão@b.com`)                  | **Não é detectado e chega ao modelo.**                                    |
| Cartão colado depois de letra ou escape (`é4111...`, `\n4111...`)                        | **Não é detectado.**                                                      |
| 15 dígitos (Amex), 19 dígitos ou grupos separados por ponto                              | **Não é detectado.**                                                      |

Consequências:

- O validador de 10.8 pode comparar valores monetários, mas precisa tratar `json.JSONDecodeError` sem quebrar.
- A redação é uma camada de redução de risco, não uma garantia.
- Mitigação testada para os casos de e-mail e de JSON inválido: normalizar espaços do texto livre (`' '.join(text.split())`), retornar `dict` e passar a `PIIMiddleware('email', ...)` um `detector` com regex Unicode. O caso de cartão não foi tratado.

Com `enforce_run_deadline` antes dos middlewares de PII, um encerramento por prazo deixa o último resultado sem redação em `result['messages']`. Esse conteúdo não é enviado ao modelo, mas não deve ser persistido nem registrado.

### c) Threads

Com `agent.invoke`, **toda** tool roda fora da thread do chamador, inclusive quando há uma só. Seis chamadas usaram seis threads distintas, e três chamadas na mesma mensagem rodaram ao mesmo tempo (confirmado com `threading.Barrier(3)`). Os hooks `before_model` e o modelo rodaram na thread do chamador.

Cada thread tem sua conexão Django. O decorator de 10.5.4 funciona como previsto: compara `get_ident()` com `owner_thread_id` e chama `connection.close()`. A conexão da thread do chamador ficou intacta.

### d) `runtime.context` no middleware

Em `@before_model(can_jump_to=['end'])`, com a assinatura `(state, runtime)`, `runtime.context` é **o mesmo objeto** passado em `invoke(context=...)`, também com `dataclass(frozen=True)`. Atribuir um campo levanta `FrozenInstanceError`. Nas tools, `ToolRuntime.context` é o mesmo objeto.

- `return {'jump_to': 'end'}` encerra sem chamar o modelo.
- Sem `context=` no `invoke`, `runtime.context` é `None`, sem erro de validação. O serviço precisa sempre informá-lo.
- `runtime` não aparece no schema da tool. Um `runtime` ou `user_id` forjado pelo modelo não alterou o contexto recebido.

### `recursion_limit`

Com a pilha completa de 5 middlewares, o pior caso (8 chamadas ao modelo, todas com tool) precisa de `recursion_limit` igual a 83. O valor `100` funciona, com folga de 17 passos. Um middleware novo consome mais passos a cada volta, portanto o valor deve ser revisto nesse caso.

Essa medição é anterior à pilha final. Com `ToolResultPIIMiddleware` (tarefa 10.6), o pior caso de 8 chamadas passou a precisar de 87 passos; veja [Agente (tarefa 10.6)](#agente-tarefa-106).

## Chamada real (tarefa 10.3.6)

Executada em 02/11/2026, com autorização do responsável, somente com `gpt-5-mini`. Versões: `langchain-openai==1.7.3`, `langchain-core==1.7.4`, `openai==3.42.1`, em Python 3.12.0. Foram feitas **2 chamadas pagas**, com prompts genéricos e sem dados financeiros. O número vem do fluxo do script com `AI_MODEL_MAX_RETRIES=0`: o contador de requisições do script ficou em zero, porque observava `httpx.Client`, e o SDK `openai` instalado usa `httpx2.Client`.

Configuração: `AI_MAX_OUTPUT_TOKENS=300`, `AI_REASONING_EFFORT=low`, `AI_MODEL_TIMEOUT_SECONDS=45` e `LANGSMITH_TRACING=false`. O modelo retornado em `response_metadata` foi `gpt-5-mini-2025-08-07`, pela API de Chat Completions.

| Chamada                                      | Resposta                 | `finish_reason` | Entrada | Saída | Raciocínio | Tempo  |
| -------------------------------------------- | ------------------------ | --------------- | ------- | ----- | ---------- | ------ |
| 1. `invoke('Responda apenas: OK')`           | `OK`                     | `stop`          | 12      | 10    | 0          | 2,97 s |
| 2. `bind_tools([ping], tool_choice='any')`   | Tool call `ping`, sem argumentos | `tool_calls`    | 122     | 83    | 64         | 1,85 s |

Parâmetros aceitos, sem erro da API: `max_completion_tokens` e `reasoning_effort`, sem `temperature`, além de `tools` com `tool_choice`. O LangChain traduz `tool_choice='any'` para `'required'` no corpo da requisição, conforme o payload montado sem rede. As respostas com limite de 300 tokens não vieram vazias, portanto a terceira chamada não foi usada.

Não verificado: o comportamento com o limite padrão de 4000 tokens, a execução do agente completo com `ToolStrategy` e o caso das duas `ToolMessage` com o mesmo `tool_call_id`.

## Rastreamento do LangSmith (tarefa 10.3.5)

Testado em 02/11/2026 com `langsmith==0.14.17`, modelo falso e conexões bloqueadas e registradas em nível de socket. Nem o ambiente nem o `.env` definem variáveis `LANGSMITH_*` ou `LANGCHAIN_*`.

O rastreamento está desativado **porque essas variáveis não existem**. O projeto não tem código que o desative.

| Ambiente                                                | `tracing_is_enabled()` | Tentativas de conexão a `api.smith.langchain.com` |
| ------------------------------------------------------- | ---------------------- | ------------------------------------------------- |
| Sem variáveis                                           | `False`                | 0 (e nenhum tracer anexado)                       |
| `LANGSMITH_TRACING=true`, sem `LANGSMITH_API_KEY`       | `True`                 | Sim, inclusive `POST /runs/multipart`             |
| `LANGSMITH_TRACING=true`, com chave falsa               | `True`                 | Sim, inclusive `POST /runs/multipart`             |
| `LANGSMITH_TRACING=false` e `LANGCHAIN_TRACING_V2=true` | `True`                 | Sim: `LANGCHAIN_TRACING_V2` tem prioridade        |
| `LANGSMITH_TRACING=True` (maiúscula)                    | `False`                | 0                                                 |

**Risco em aberto (RNF26):** definir essa variável no ambiente liga o rastreamento, mesmo sem chave do LangSmith. O envio é tentado sem nenhuma alteração de código. Como `core/settings.py` copia o `.env` para `os.environ`, a variável no `.env` deve ter o mesmo efeito (conclusão da leitura do código, não testada).

Com o agente completo e `LANGSMITH_TRACING=true`, tanto `langsmith.tracing_context(enabled=False)` em volta do `invoke` quanto `langsmith.configure(enabled=False)` resultaram em 0 tentativas de conexão, inclusive com tools rodando em outras threads. Nenhum dos dois foi adicionado ao projeto.

## Comportamento das tools (tarefa 10.5)

Testado em 02/11/2026 com modelo falso, sem chave de API e sem rede.

- **Retorno sempre em dict:** o `ToolMessage` mantém uma lista vazia como lista de blocos de conteúdo (`content=[]`), e não como o texto `'[]'`. Por isso, as listas que o PRD 14.9 descreve vêm dentro de uma chave: `months`, `changes`, `expenses` e `transactions`.
- **Erros que voltam ao modelo:** erro de schema chega com `status='error'`. Erro de contexto chega com `status='success'` e JSON com a chave `error`. O validador da 10.8 precisa ignorar os dois casos.
- **Códigos de erro de contexto:** `invalid_date_range`, `date_out_of_period`, `month_not_closed`, `month_out_of_period`, `months_out_of_period` e `invalid_argument`.
- **`handle_tool_errors`:** `create_agent` não precisa de configuração. O padrão devolve ao modelo os erros de argumento e relança os demais. Um middleware `wrap_tool_call` que capture `Exception` impediria o `internal_error`.
- **Contexto ausente ou inválido:** a tool levanta `RuntimeError` antes de qualquer consulta, e a exceção sai de `agent.invoke`. O serviço deve convertê-la em `internal_error`.
- **Primeiro mês do período:** `get_category_changes` o recusa, porque o mês anterior fica fora da janela. Com janela de 1 ou 2 meses, nenhum mês é aceito.
- **Caractere de controle:** vira espaço em `_clean_text`, como quebras de linha e tabulações. Assim, `Pix\x01joao@b.com` e `Pix\x014111...` são redigidos e o JSON continua válido. A 10.8 ainda precisa tolerar `JSONDecodeError`, por segurança.
- **Testes de conexão:** no banco de teste em memória, `connection.close()` não faz nada. A 10.12 precisa de banco em arquivo ou de mock de `connection`.

## Agente (tarefa 10.6)

Testado em 02/11/2026 com modelo falso e sockets bloqueados, nas versões da tarefa 10.1.5. Nada foi enviado à OpenAI.

**Retorno:** `run_agent(context)` devolve `AgentRunResult`, com `structured_response` (`AnalysisOutput` ou `None`), `messages`, `input_tokens`, `output_tokens` e `total_tokens`. Exceções saem sem tratamento e, nesse caso, **as mensagens e os tokens da execução se perdem**. Os testes injetam o modelo com `patch('ai.agent.build_chat_model')`. `context.deadline` é um valor de `time.monotonic()`.

**Ordem dos middlewares:** PII de e-mail, PII de cartão, `enforce_run_deadline`, `ModelCallLimitMiddleware` (`exit_behavior='end'`) e `ToolCallLimitMiddleware` (`exit_behavior='continue'`). `ToolResultPIIMiddleware` é um `PIIMiddleware` que repete a redação em `after_agent`. Quantidade de textos sensíveis que restaram em `messages`, de 7 plantados:

| Variante                                   | Prazo vencido | Limite de modelo | Tool e saída na mesma mensagem |
| ------------------------------------------ | ------------- | ---------------- | ------------------------------ |
| Ordem do PRD, `PIIMiddleware` puro         | 7             | 7                | 7                              |
| PII primeiro, `PIIMiddleware` puro         | 0             | 0                | 7                              |
| Limites primeiro, com `after_agent`        | 0             | 7                | 0                              |
| **Adotada:** PII primeiro e `after_agent`  | 0             | 0                | 0                              |

A ordem sozinha não basta: tool e saída na mesma mensagem encerram a execução sem passar por outro `before_model`. O `after_agent` sozinho também não basta: o limite de modelo acrescenta uma `AIMessage`, e a redação só olha as mensagens depois da última `AIMessage`.

**Execução sem `structured_response`:** sempre sem exceção.

| Situação                       | Chamadas ao modelo | Última mensagem                                           |
| ------------------------------ | ------------------ | --------------------------------------------------------- |
| Prazo vencido antes do início  | 0                  | `HumanMessage`                                            |
| Prazo vencido durante          | Até o vencimento   | `ToolMessage` (sem mensagem de limite)                    |
| Limite de modelo               | 8                  | `AIMessage` `Model call limits exceeded: run limit (8/8)` |
| Saída sempre inválida          | 8                  | A mesma, depois de `ToolMessage` de erro de `AnalysisOutput` |
| Resposta sem tool call         | 1                  | `AIMessage` sem `tool_calls`, com ou sem texto            |

O `timeout` pode ser identificado com `time.monotonic() >= context.deadline`. `StructuredOutputValidationError` não ocorre, pois `handle_errors` é `True`: para obter `invalid_output`, é preciso olhar as mensagens. A recusa da saída vem em uma `ToolMessage` com `name='AnalysisOutput'`, **`status='success'`** e texto iniciado por `Error:`, portanto `status` não a identifica.

**`recursion_limit`:** a pilha final precisa de 10 passos por chamada ao modelo, mais 7. O mínimo medido foi 17 com 1 chamada, 87 com 8, 97 com 9 e 107 com 10. O valor 100 cobre `AI_MAX_MODEL_CALLS` até 9. Com 10 ou mais, a execução termina em `GraphRecursionError` antes do limite de modelo. Por isso, o limite precisa de revisão se esse setting subir.

**PII:** `PIIMiddleware` recebe `EMAIL_PATTERN` e `CREDIT_CARD_PATTERN`, ambos sem Luhn, e os valores monetários não mudam, mesmo acima de 13 dígitos. Passam a ser redigidos: e-mail com acento, 13 a 19 dígitos seguidos, grupos 4-4-4-4, 4-4-4-4-3 e 4-6-4/5 separados por espaço, hífen ou ponto, e número colado depois de letra. Um número longo que não seja de cartão, como telefone ou CNPJ sem pontuação, também é redigido com o rótulo de cartão.

Lacunas conhecidas, todas de cartão, com a saída observada:

- Número seguido de `.` e dígito (`4111111111111111.00`): não é redigido, e essa é a regra que protege os valores monetários.
- Outros separadores ou espaçamentos (`4111–1111–1111–1111`, `4111/1111/...`, `4111 - 1111 - ...`): não são redigidos.
- Outro número de 4 dígitos antes de um cartão agrupado (`2025 4111 1111 1111 1111`): redige `2025 4111 1111 1111` e os últimos 4 dígitos ficam visíveis.

**LangSmith (RNF26):** com `LANGSMITH_TRACING=true` e `LANGCHAIN_TRACING_V2=true`, `run_agent` fez 0 tentativas de conexão. O controle, com o mesmo agente sem `tracing_context(enabled=False)`, fez 7 tentativas a `api.smith.langchain.com`.

**Erros do provedor:** com o `ChatOpenAI` real e a conexão bloqueada, a exceção que sai de `run_agent` é `langchain_openai.chat_models.base.OpenAIConnectionError`. Pelo código-fonte, essa classe e as equivalentes herdam das exceções de `openai`, portanto os `except` da seção 14.16 do PRD continuam válidos. O corpo montado para a API não tem `temperature` e traz `tool_choice='required'`, `max_completion_tokens=4000`, `reasoning_effort='low'` e as 8 tools, com `AnalysisOutput`.

**Não verificado:** o comportamento do modelo real com este prompt, inclusive a saída estruturada depois de atingir o limite de tools.

## Validação e serviço (tarefas 10.8 e 10.9)

Testado em 02/11/2026 com modelo falso, sockets bloqueados e banco de teste em arquivo.

**Para a 10.10:** `generate_analysis(user)` não depende de `request`, não propaga `Exception` e retorna um `GenerationOutcome` (`success`, `failed`, `already_running`, `limit_reached`, `insufficient_data` ou `disabled`), que é um `StrEnum`. A view converte esse valor na mensagem da seção 14.15 do PRD. `failed` também é retornado sem registro se uma etapa anterior à criação do `pending` falhar. A chamada não pode ficar dentro de `transaction.atomic()`: o serviço recusa executar o agente nesse caso e grava `internal_error`, sem chamar o modelo. Portanto, `ATOMIC_REQUESTS` deve continuar desativado.

`get_dashboard_analysis_state(user)` faz até 3 consultas, não grava nada e não carrega LangChain. Retorna um dict:

| Chave             | Conteúdo                                                                                                                       |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `state`           | `AnalysisState`: `disabled`, `running`, `insufficient_data`, `limit_reached`, `failed`, `stale`, `no_analysis` ou `with_analysis`, nessa prioridade. |
| `analysis`        | Última análise válida ou `None`, em qualquer estado (RN05).                                                                    |
| `is_stale`        | `True` se `analysis` estiver desatualizada (RN06), mesmo com outro `state`.                                                    |
| `notices`         | Textos a exibir, já em português e com os números dos settings. O aviso de desatualização é mantido junto com o de outro estado. |
| `can_generate`    | Se o botão fica ativo.                                                                                                         |
| `loading_message` | Texto do estado **Carregando**, que só existe no navegador e, por isso, não é um valor de `state`.                             |

O link **Nova transação** depende de `state == 'insufficient_data'`. `get_latest_valid_analysis(user)` faz 1 consulta.

**Evidências:** compara somente os valores da `source_tool` na mesma execução, ignorando resultados com erro, JSON inválido e a própria `AnalysisOutput`.

| Evidência                                  | Resultado                                                                                     |
| ------------------------------------------ | --------------------------------------------------------------------------------------------- |
| `'1200'` e `'1200.00'`, `'12.5'` e `'12.50'` | Iguais, por `Decimal`.                                                                      |
| `'1.200,00'`, `'R$ 1200.00'`, `'12.5%'`, `'1e3'` | Recusados. O modelo pode reprovar por isso, pois o prompt exige copiar o valor da tool. |
| Contagem `1200`                            | Aceita `'1200'` e recusa `'1200.00'`.                                                         |
| Booleano                                   | Aceita somente `'true'` ou `'false'`.                                                         |
| Número em `description`, `category_name` ou `account_name` | Não vale como número. Texto é comparado por inteiro, sem diferenciar maiúsculas e espaços. |

Um item com qualquer evidência não encontrada é descartado por inteiro. `data_limitations` recebe uma frase por item, sem o título, para não exibir uma conclusão não verificada, e pode passar de 5 entradas. Em uma falha, nenhum conteúdo do modelo é gravado.

**Exceções:** `ai.services._error_code_for_exception` segue a seção 14.16 do PRD. As classes de `langchain_openai` herdam das de `openai` e têm o mesmo código. Sem correspondência, como `openai.BadRequestError`, o código é `internal_error`. `error_detail` guarda só o nome da classe.

**Sem `structured_response`:** prazo vencido gera `timeout`. Depois, a última `AIMessage` real sem `tool_calls` ou a última `AnalysisOutput` recusada geram `invalid_output`. O restante gera `limit_exceeded`. A mensagem que `ModelCallLimitMiddleware` acrescenta também não tem `tool_calls`, e é identificada por haver mais `AIMessage` que `AI_MAX_MODEL_CALLS`.

**Logs:** `logger.exception` não é usado, pois vazou a chave e a descrição na saída capturada, inclusive pela cadeia de exceções (`pydantic.ValidationError` traz `input_value`). O serviço registra `analysis_id`, `error_code`, a classe e os frames de `traceback.format_tb`, sem a mensagem.

**Tokens em falha:** `run_agent(context, tracker=None)` aceita um `RunTracker`, que guarda tokens e `AIMessage` mesmo se o `invoke` levantar exceção. Assim, `tool_calls` e tokens são gravados também nesse caso. Não contam os tokens da chamada que falhou, pois ela não devolveu uso, e `tool_calls` inclui chamadas recusadas pelo limite de tools. O uso só é somado se a mensagem trouxer `response_metadata['model_name']`, e o modelo falso precisa informá-lo.

**Para a 10.12:**

- Injete o modelo em `ai.agent.build_chat_model`, e não em `run_agent`, pois tokens e `tool_calls` vêm do `RunTracker`.
- Execuções do agente precisam de `TransactionTestCase`. Em `TestCase`, a proteção contra transação aberta resulta em `internal_error`. Caminhos que param antes do agente funcionam em `TestCase`.
- `user.delete()` levanta `ProtectedError` se o usuário tiver transações, pois `Transaction.account` e `category` usam `PROTECT`. Para simular a exclusão, apague as transações antes.
- A restrição de `pending` foi testada com 8 threads em 10 rodadas, e o fluxo completo com 2 threads em 8 rodadas, com banco em arquivo. Exatamente um registro foi criado em cada rodada, sem `database is locked`.

## Primeira análise real observada

Registrada em `db.sqlite3` de desenvolvimento em 02/11/2026, às 19:46 (horário local), feita pela aplicação, fora das verificações com modelo falso: `gpt-5-mini`, `success`, 28 s, 4.802 tokens de entrada, 2.269 de saída e 7 tools chamadas. Duas entradas de `data_limitations` registram itens descartados por evidência não conferida. É uma única amostra e não substitui a medição da tarefa 10.12.11.

## Ajustes pendentes no PRD

O código já segue o comportamento abaixo, e o PRD ainda precisa refleti-lo:

- **14.13 (passo 7) e 14.16:** incluir `invalid_output` na ausência de `structured_response`, com precedência de `timeout`. `StructuredOutputValidationError` e `MultipleStructuredOutputsError` não ocorrem com `handle_errors=True`.
- **14.16 e subtarefa 10.8.6:** trocar `logger.exception` pelo registro sem a mensagem da exceção.
- **14.16:** uma falha antes do `pending` retorna `failed` sem registro, e uma falha na gravação final deixa `pending` até o passo 1 da próxima chamada.
- **14.13 (passos 3 e 5):** `metrics_snapshot` é calculado no passo 3 e reaproveitado no passo 5.
- **14.11:** `data_limitations` pode passar de 5 entradas após os descartes.
- **14.15:** definir a prioridade dos estados. O texto "até 2 minutos" conflita com os cerca de 210 s da seção 14.18.
- **14.12 (linha 1043):** suavizar "remove e-mails e números de cartão", pois restam as lacunas de cartão listadas acima.
- **14.7:** registrar a ordem dos middlewares e os detectores próprios. **14.9:** registrar as listas dentro de um dict.
- **RNF23:** o serviço também importa `openai`, `langchain` e `langgraph`, de forma tardia, para mapear exceções.
- **RN07 e critério da 10.7:** `user.delete()` levanta `ProtectedError` se o usuário tiver transações, e o admin mostra a página de bloqueio. Isso é anterior ao Assistente: as análises só são removidas quando a exclusão do usuário é possível.
- **14.6:** `ai/models.py` não tem opções de severidade; `severity` existe só em `ai/schemas.py` (`Alert`) e fica no JSON de `alerts`. O admin não é "somente leitura" no sentido estrito: inclusão e edição estão bloqueadas, e a exclusão é mantida de propósito.
- **14.13 (passo 4) e 14.18:** o limite diário conta registros criados no dia local em qualquer status (`success`, `failed` e `pending`), e não só análises concluídas.
- **14.18:** substituir a estimativa de custo (20 mil tokens de entrada, US$ 0,011 por análise e US$ 1,00 por mês) pela medição da 10.12.11 (4.845 de entrada, 2.619 de saída, US$ 0,00645 por análise, cerca de US$ 0,58 por mês no limite diário).
- **14.8 e 14.18:** `AI_ANALYSIS_WINDOW_MONTHS` também limita `months` em `get_monthly_evolution`, lido na importação de `ai.tools`; mudar o setting exige reiniciar o processo.
- **14.17 (estratégia de testes):** `RUN_LIVE_AI_TESTS` precisa ser exatamente `True`, e não deve ir para o `.env`, que `core/settings.py` copia para `os.environ`.

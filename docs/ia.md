# Assistente Financeiro com IA

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

# Configuração do ambiente

## Requisitos

- Python 3.12+

## Instalação

```bash
# criar e ativar o ambiente virtual
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/macOS

# instalar as dependências
pip install -r requirements.txt

# instalar também as ferramentas de desenvolvimento (ruff e coverage)
pip install -r requirements-dev.txt

# copiar o arquivo de variáveis de ambiente
copy .env.example .env       # Windows
cp .env.example .env         # Linux/macOS

# gerar uma nova SECRET_KEY
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Cole a chave gerada em `SECRET_KEY` no arquivo `.env`, sem aspas. O projeto não inicia sem essa variável, e o `.env` não deve ser versionado.

## Rodando o projeto

```bash
python manage.py migrate
python manage.py runserver
```

O servidor sobe em `http://127.0.0.1:8000/`. O admin do Django fica em `/admin/`.

## Rodando com Docker

Com o `.env` criado a partir do `.env.example`:

```bash
docker compose up --build
```

A aplicação sobe em `http://localhost:8000/`, com o banco em um volume próprio. Essa configuração não é para produção. Os detalhes estão na seção Docker do `README.md`.

O container lê o mesmo `.env`, inclusive a `OPENAI_API_KEY` e as variáveis `AI_*` do Assistente. Sem a chave, a aplicação sobe normalmente, com o Assistente indisponível.

Depois de atualizar o projeto, rode de novo `docker compose up --build`: a inicialização aplica as migrations pendentes (incluindo a da app `ai`) e mantém os dados do volume. Na imagem, o banco fica por padrão em `DATABASE_PATH=/data/db.sqlite3`.

## Assistente Financeiro (IA)

O Assistente usa a API da OpenAI e é opcional: **sem `OPENAI_API_KEY`, o restante do sistema funciona normalmente** e o card do dashboard mostra "O assistente não está disponível no momento.". A arquitetura, os limites e os códigos de erro estão em [ia.md](ia.md).

Para ativá-lo, preencha no `.env` (criado a partir do `.env.example`):

```bash
OPENAI_API_KEY=sua-chave-da-openai
AI_MODEL_NAME=gpt-5-mini
```

O `gpt-5-mini` tem desligamento anunciado pela OpenAI para 11/12/2026. A troca do modelo é feita só em `AI_MODEL_NAME`, sem alterar código (ver [ia.md](ia.md) e o item I-01 da seção 14.19 do [PRD.md](../PRD.md)).

Os demais parâmetros têm valor padrão em `core/settings.py` e só precisam ir para o `.env` se forem alterados:

| Variável                              | Padrão | Uso                                                        |
| ------------------------------------- | ------ | ---------------------------------------------------------- |
| `AI_REASONING_EFFORT`                 | `low`  | Esforço de raciocínio do modelo.                           |
| `AI_MODEL_TIMEOUT_SECONDS`            | `45`   | Tempo máximo de cada chamada à API.                        |
| `AI_MODEL_MAX_RETRIES`                | `1`    | Novas tentativas do cliente da OpenAI.                     |
| `AI_MAX_OUTPUT_TOKENS`                | `4000` | Limite de tokens de saída por chamada.                     |
| `AI_ANALYSIS_WINDOW_MONTHS`           | `6`    | Meses analisados, incluindo o mês atual.                   |
| `AI_ANALYSIS_MIN_TRANSACTIONS`        | `5`    | Transações mínimas no período para gerar uma análise.      |
| `AI_ANALYSIS_DAILY_LIMIT`             | `3`    | Análises por usuário por dia.                              |
| `AI_ANALYSIS_STALE_DAYS`              | `30`   | Dias até a análise ser considerada desatualizada.          |
| `AI_ANALYSIS_PENDING_TIMEOUT_MINUTES` | `5`    | Minutos até uma análise pendente ser dada como abandonada. |
| `AI_RUN_BUDGET_SECONDS`               | `120`  | Orçamento de tempo de cada execução do agente.             |
| `AI_MAX_MODEL_CALLS`                  | `8`    | Chamadas ao modelo por execução.                           |
| `AI_MAX_TOOL_CALLS`                   | `10`   | Chamadas de tools por execução.                            |

Os valores são lidos na inicialização: reinicie o servidor depois de alterar o `.env`.

### Testes

Os testes da app `ai` usam um modelo falso e não acessam a rede, com ou sem chave. Existe um único teste real com a OpenAI (`ai.tests.LiveAnalysisTests`), ignorado por padrão porque **gera custo**. Para rodá-lo, com `OPENAI_API_KEY` preenchida e a autorização do responsável pela conta:

```powershell
$env:RUN_LIVE_AI_TESTS = 'True'
python manage.py test ai.tests.LiveAnalysisTests
Remove-Item Env:RUN_LIVE_AI_TESTS
```

Ele gera uma análise completa e imprime tempo, tokens e custo estimado. O custo e o tempo medidos estão em [ia.md](ia.md).

## Dependências

Ao instalar um novo pacote, atualize o arquivo de dependências, mantendo-o em UTF-8 (no PowerShell, o `>` grava em UTF-16):

```powershell
pip freeze | Out-File -Encoding utf8 requirements.txt
```

As dependências de IA (`langchain` e `langchain-openai`, com as que chegam com elas) são a única exceção à regra de usar apenas recursos nativos do Django (item I-03 da seção 14.19 do PRD). O `pip freeze` também lista o `ruff` e o `coverage` quando o `requirements-dev.txt` está instalado; eles não devem entrar no `requirements.txt`.

## Arquivos ignorados

O `.gitignore` já ignora, entre outros: `venv/`, `__pycache__/`, `*.pyc`, `db.sqlite3`, `.env`, `static/css/output.css` e `staticfiles/`.

# Estrutura do projeto

```
finanpy
├── accounts             # contas bancárias
├── ai                   # Assistente Financeiro com IA (LangChain + OpenAI)
├── categories           # categorias de transações
├── core                 # settings, URLs raiz, código compartilhado, home e dashboard
├── profiles             # perfis de usuários
├── transactions         # transações (entradas e saídas)
├── users                # usuário customizado
├── templates            # templates globais (base, home, dashboard, erros)
│   └── components       # componentes reutilizáveis ({% include %})
├── static
│   ├── css              # input.css do Tailwind (output.css é gerado)
│   └── js               # JavaScript puro (sidebar.js, analysis_form.js)
├── agents               # definições dos agentes de desenvolvimento
├── docs                 # esta documentação
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── manage.py
├── PRD.md
├── TASKS.md             # lista de tarefas das sprints
├── pyproject.toml       # configuração do ruff e do coverage
├── requirements.txt
└── requirements-dev.txt
```

## Responsabilidade das apps

Cada app tem uma responsabilidade única, definida no PRD (seções 8.3 e 14.6):

| App            | Responsabilidade                                                                     |
| -------------- | ------------------------------------------------------------------------------------ |
| `core`         | settings, URLs raiz, `TimeStampedModel`, mixins, `StyledFormMixin`, home e dashboard |
| `users`        | model `User` customizado (login por e-mail)                                          |
| `profiles`     | model `Profile` do usuário                                                           |
| `accounts`     | model `Account` (contas bancárias)                                                   |
| `categories`   | model `Category` (categorias de entrada e saída)                                     |
| `transactions` | model `Transaction` (entradas e saídas)                                              |
| `ai`           | model `FinancialAnalysis` e o agente que gera as análises financeiras                |

## Organização dentro de cada app

Cada app segue a estrutura padrão do Django (`models.py`, `views.py`, `admin.py`, `apps.py`, `tests.py`, `migrations/`) e, quando necessário:

- `urls.py` — rotas da app.
- `forms.py` — formulários da app.
- `signals.py` — signals da app (nunca em outro arquivo).
- `templates/<app>/` — templates específicos da app.

## App `ai`

A app `ai` separa o agente em módulos para que cada parte seja testável isoladamente. Os detalhes de arquitetura, tools, fluxo e limites estão em [ia.md](ia.md).

| Arquivo                                   | Responsabilidade                                                                        |
| ----------------------------------------- | --------------------------------------------------------------------------------------- |
| `ai/models.py`                            | Model `FinancialAnalysis`, com status, códigos de erro e severidade.                    |
| `ai/context.py`                           | `AnalysisContext`, com os dados confiáveis da execução, e o cálculo do período.         |
| `ai/schemas.py`                           | Schemas Pydantic da saída estruturada.                                                  |
| `ai/queries.py`                           | Consultas ao ORM, somente leitura, sempre filtradas por `user_id`. Sem LangChain.       |
| `ai/tools.py`                             | Tools do agente: leem `runtime.context`, validam os parâmetros e chamam `queries.py`.   |
| `ai/prompts.py`                           | Prompt de sistema e `PROMPT_VERSION`.                                                   |
| `ai/agent.py`                             | Único módulo que monta o modelo (`ChatOpenAI`) e o agente, com os middlewares.          |
| `ai/validators.py`                        | Confere as evidências da saída com os resultados reais das tools.                       |
| `ai/services.py`                          | Único ponto de entrada para o restante do sistema e único módulo que grava análises.    |
| `ai/views.py`, `ai/urls.py`               | Criação por POST (`ai:create`), histórico (`ai:list`) e detalhe (`ai:detail`).          |
| `ai/admin.py`                             | Admin somente leitura das análises.                                                     |
| `ai/templatetags/analysis_format.py`      | Filtros de formatação das evidências.                                                   |
| `ai/templates/ai/`                        | `analysis_list.html` e `analysis_detail.html`.                                          |
| `templates/components/analysis_card.html` | Card do Assistente no dashboard, com todos os estados.                                  |
| `templates/components/analysis_*.html`    | Partes do card e das páginas: itens, evidências, alertas, aviso e status.               |
| `static/js/analysis_form.js`              | Estado de carregamento do botão de gerar análise, em JavaScript puro.                   |

O LangChain e a OpenAI só são importados quando uma análise é gerada, nunca na inicialização do Django nem nas páginas comuns.

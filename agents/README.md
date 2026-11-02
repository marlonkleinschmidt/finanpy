# Agentes — Finanpy

Índice dos agentes de IA do time de desenvolvimento. Cada agente é especialista em uma parte da stack do projeto e segue o [PRD.md](../PRD.md) e o [CLAUDE.md](../CLAUDE.md).

| Agente                                                     | Função                                                               | MCP                                                     |
| ---------------------------------------------------------- | -------------------------------------------------------------------- | ------------------------------------------------------- |
| [backend-django](backend-django.md)                        | Models, migrations, views, forms, URLs, signals, admin e settings    | context7                                                |
| [frontend-django-tailwind](frontend-django-tailwind.md)    | Templates DTL, componentes, TailwindCSS e responsividade             | context7                                                |
| [qa-tester](qa-tester.md)                                  | Validação do sistema e do design no navegador; testes automatizados  | playwright (e context7 ao escrever testes)              |
| [devops-docker](devops-docker.md)                          | Ruff, Dockerfile, docker-compose e variáveis de ambiente             | context7                                                |
| [ai-langchain](ai-langchain.md)                            | Assistente Financeiro e agentes de IA com LangChain 1.x e OpenAI     | context7                                                |

## Quando usar cada agente

### backend-django

**Use quando** a tarefa envolver dados, regras de negócio ou o caminho da requisição.

- Criar ou alterar models, migrations, signals e admin.
- Implementar views (CBVs), forms, URLs e mixins de isolamento por usuário.
- Calcular saldos e KPIs; ajustar `settings.py`.

**Não use para** escrever HTML ou classes de layout. As classes dos widgets em `core/forms.py` são a exceção: ficam com este agente.

### frontend-django-tailwind

**Use quando** a tarefa envolver o que o usuário vê.

- Instalar e configurar o Tailwind CLI standalone.
- Criar `base.html`, `base_auth.html`, `templates/components/` e os templates das apps.
- Aplicar o design system (PRD, seção 9), a responsividade e o JavaScript puro do menu mobile.

**Não use para** alterar models, regras de validação ou querysets. Se faltar um dado no contexto, ele pede ao `backend-django`.

### qa-tester

**Use quando** uma entrega precisar ser verificada ou quando chegar a hora dos testes automatizados.

- Ao terminar uma tarefa com tela: validar fluxo, regras e design no navegador.
- Ao fim de cada sprint: validação geral e as tarefas de validação manual do PRD.
- Sprint 8: isolamento entre usuários e revisão visual nos três breakpoints.
- Sprint 9: testes com `django.test` e cobertura mínima de 80%.

**Não use para** corrigir código da aplicação: ele relata os defeitos para o agente responsável.

### devops-docker

**Use quando** a tarefa envolver ferramentas ou o ambiente de execução.

- Sprint 0: instalar e configurar o ruff.
- Sprint 11: Dockerfile, docker-compose, `.env` e `.dockerignore`.

**Não use para** escrever funcionalidades ou mudar regras de negócio.

### ai-langchain

**Especialidade:** arquitetura e desenvolvimento de agentes de IA com LangChain 1.x e OpenAI, com acesso controlado a dados financeiros.

**Responsabilidades:**

- Implementar o agente, as tools, os schemas, os prompts, a validação de evidências e o serviço de geração do Assistente Financeiro.
- Criar a persistência das análises (`FinancialAnalysis`) e os testes da app `ai`.
- Garantir o isolamento entre usuários, a proteção de dados e os limites de custo e de tempo.
- Orientar outras integrações de IA com LangChain aprovadas no PRD.

**Use quando** a tarefa envolver agentes de IA ou a app `ai`.

- Sprint 10: tarefas de 10.1 a 10.9, 10.12 a 10.14 (conforme a tabela abaixo).
- Criar ou alterar tools, prompts, saída estruturada e middlewares.
- Investigar respostas incorretas do agente, custo ou tempo de execução.
- Avaliar uma troca de modelo (`AI_MODEL_NAME`) ou uma nova integração de IA.

**Não use para** views, URLs, templates ou Docker; esses itens seguem com os demais agentes. Também não use para alterar as regras das apps existentes.

**Tecnologias e conhecimentos:** LangChain 1.x (`create_agent`, `ToolRuntime`, `ToolStrategy`, middlewares), `langchain-openai`, API da OpenAI, function calling, Pydantic, ORM do Django, segurança e isolamento de contexto, testes com modelo falso e controle de custos.

**Orientações de utilização:**

- O agente exige o MCP server `context7` e para a tarefa se ele não estiver disponível.
- Antes de iniciar a Sprint 10, resolva as decisões em aberto da seção 14.19 do `PRD.md`, principalmente o desligamento do `gpt-5-mini` (item I-01).
- Testes com a API real têm custo e só rodam com autorização do usuário.

## Responsável por sprint

Quando uma tarefa não aparece na coluna de um agente, ela não é dele.

| Sprint                 | backend-django                             | frontend-django-tailwind                | qa-tester                                    | devops-docker | ai-langchain                                 |
| ---------------------- | ------------------------------------------ | --------------------------------------- | -------------------------------------------- | ------------- | -------------------------------------------- |
| 0 — Setup              | 0.4                                        | —                                       | —                                            | 0.5           | —                                            |
| 1 — Autenticação       | 1.1 a 1.7                                  | 1.8.1, 1.8.2                            | 1.8.3                                        | —             | —                                            |
| 2 — Design system      | 2.4, 2.7.1, 2.7.2                          | 2.1, 2.2, 2.3, 2.5, 2.6, 2.7.3 a 2.7.6, 2.8 | 2.7.7                                    | —             | —                                            |
| 3 — Perfil             | 3.1, 3.2 (exceto 3.2.4), 3.3, 3.4.1 a 3.4.5 | 3.4.6                                  | 3.2.4                                        | —             | —                                            |
| 4 — Contas             | 4.1 a 4.6                                  | 4.7                                     | valida a sprint                              | —             | —                                            |
| 5 — Categorias         | 5.1 a 5.5                                  | 5.6                                     | valida a sprint                              | —             | —                                            |
| 6 — Transações         | 6.1, 6.2.1, 6.2.2, 6.3 a 6.8               | 6.2.3, 6.9                              | valida a sprint                              | —             | —                                            |
| 7 — Dashboard          | 7.1                                        | 7.2 (exceto 7.2.8)                      | 7.2.8, 7.3                                   | —             | —                                            |
| 8 — Revisão            | 8.1.1, 8.1.3, 8.1.4, 8.3, 8.4              | 8.2.1, 8.2.3, 8.2.5                     | 8.1.2, 8.2.2, 8.2.4                          | —             | —                                            |
| 9 — Testes             | corrige os defeitos encontrados            | corrige os defeitos encontrados         | 9.1 a 9.7                                    | —             | —                                            |
| 10 — Assistente com IA | 10.2.2, 10.10                              | 10.11 (exceto 10.11.9)                  | 10.11.9, 10.13.10, revisão do isolamento     | 10.3.2, 10.3.3, 10.14.4 | 10.1 a 10.9 (exceto 10.2.2, 10.3.2, 10.3.3), 10.12, 10.13 (exceto 10.13.10), 10.14 (exceto 10.14.4) |
| 11 — Docker            | —                                          | —                                       | valida a imagem                              | 11.1 a 11.3   | —                                            |

## Fluxo de uma funcionalidade

1. `backend-django` entrega model, form, view e URL.
2. `frontend-django-tailwind` entrega os templates.
3. `qa-tester` valida no navegador e relata os defeitos.
4. O agente responsável corrige, e o `qa-tester` valida de novo.

Cada agente marca no PRD (seção 13) somente as subtarefas que concluiu.

## Como usar

Mencione o arquivo do agente na conversa com o Claude Code:

```text
@agents/backend-django.md implemente a tarefa 1.2 do PRD
```

Os arquivos têm o frontmatter de subagente do Claude Code (`name` e `description`) e não definem `tools`, para herdar todas as ferramentas, inclusive as dos MCP servers. Para que o Claude Code os registre como subagentes, eles precisam estar em `.claude/agents/`; ele não procura em `agents/`.

## MCP servers necessários

Os agentes dependem destes servidores e param a tarefa quando eles não estão disponíveis. Instale uma vez, na raiz do projeto:

```bash
claude mcp add --scope project context7 -- npx -y @upstash/context7-mcp
claude mcp add --scope project playwright -- npx -y @playwright/mcp@latest
```

Os dois comandos usam `npx`, portanto exigem Node.js na máquina de desenvolvimento. O projeto em si continua sem Node.js.

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Finanpy is a personal finance web app (bank accounts, categories, income/expense transactions, dashboard, AI financial assistant) built with **Django full stack** (DTL templates, SQLite, no JS frameworks). `PRD.md` is the source of truth for scope, data model and design system (section 14 specifies the AI assistant, 14.19 lists its open items I-01…I-09). **The sprint task list lives in `TASKS.md`** (the PRD no longer has a task section). `docs/` summarizes the guidelines (index at `docs/README.md`; AI assistant details in `docs/ia.md`).

**Current state:** Sprints 0–9 and 11 (Docker) are done. Sprint 10 (AI financial assistant, app `ai`) is implemented and tested; only its documentation task (10.14) may still be open — check `TASKS.md`. Apps: `core`, `users`, `profiles`, `accounts`, `categories`, `transactions`, `ai`.

## Commands

Windows dev environment with a local `venv/` (Python 3.12, Django 6.1). Settings read a `.env` file (copy `.env.example`; `SECRET_KEY` is required).

```bash
venv\Scripts\activate
pip install -r requirements-dev.txt                      # app deps + ruff + coverage
python manage.py migrate
python manage.py runserver
python manage.py test                                    # all tests (no network)
python manage.py test accounts.tests.SomeTestCase.test_x # single test
ruff check .                                             # config in pyproject.toml
coverage run manage.py test && coverage report           # fails under 80%
.\tailwindcss.exe -i static/css/input.css -o static/css/output.css --watch  # or --minify
docker compose up --build                                # uses .env, DB in volume db_data
```

- `requirements.txt` holds only runtime deps and must stay UTF-8 (`pip freeze | Out-File -Encoding utf8 requirements.txt` in PowerShell; plain `>` writes UTF-16). Keep `ruff`/`coverage` in `requirements-dev.txt` only.
- `tailwindcss.exe` (standalone CLI v4, no Node.js) and `static/css/output.css` are not versioned.
- The only real OpenAI test (`ai.tests.LiveAnalysisTests`) is skipped unless `RUN_LIVE_AI_TESTS=True` and `OPENAI_API_KEY` are set. It costs money: run it only with the user's authorization.

## Mandatory conventions

- **Code in English** (names, URLs, models); **all user-facing text in Brazilian Portuguese** (labels, `verbose_name`, messages).
- PEP 8, line length 79 and **single quotes** in Python (enforced by ruff).
- Keep it simple: only native Django features, Class Based Views, and only what the PRD specifies — no extra libraries or features. **Sole authorized exception:** `langchain` and `langchain-openai` (plus their transitive deps), restricted to the `ai` app (PRD item I-03). Ask before adding anything else.
- Every model has `created_at` (`auto_now_add`) and `updated_at` (`auto_now`).
- Money uses `DecimalField(max_digits=12, decimal_places=2)`, never `float`.
- Signals live in the app's `signals.py`, connected in `AppConfig.ready()`.
- When finishing tasks, mark their subtasks `[x]` in `TASKS.md`; a task is checked only when all its subtasks are.

## Architecture

- **Custom user:** `users.User` (extends `AbstractUser`, `username = None`, `email` unique as `USERNAME_FIELD`, custom `UserManager`), `AUTH_USER_MODEL = 'users.User'`.
- **Shared code in `core`:** abstract `TimeStampedModel` (`core/models.py`), `INPUT_CLASSES` + `StyledFormMixin` applying Tailwind classes to all form widgets (`core/forms.py`), `UserQuerySetMixin` / `UserFormMixin` for per-user data isolation (`core/mixins.py`), plus `HomeView` (landing, `home`) and `DashboardView` (`dashboard`).
- **Data isolation:** every authenticated view uses `LoginRequiredMixin` and filters querysets by `request.user`; accessing another user's object must 404. Forms receiving `user` in `__init__` restrict account/category querysets to that user.
- **Data rules:** `Profile` is created by a `post_save` signal on `User`. `Account` balance is never stored — `current_balance` = `initial_balance` + income − expense via `aggregate(Sum)`. `Transaction.account`/`category` use `on_delete=PROTECT`; delete views catch `ProtectedError` and show an error message. A transaction's category must have the same type (`income`/`expense`) as the transaction. `Category` is unique per `(user, name, category_type)`.
- **URLs:** each app has `urls.py` with `app_name` (e.g. `accounts:list`), routes `''`, `new/`, `<int:pk>/edit/`, `<int:pk>/delete/`. Auth routes `signup`, `login`, `logout` (logout via POST); `LOGIN_REDIRECT_URL = 'dashboard'`, `LOGOUT_REDIRECT_URL = 'home'`. The `ai` app has `ai:list` (`/ai/`), `ai:create` (`new/`, POST only) and `ai:detail` (`<int:pk>/`).
- **Templates:** global ones in `templates/` (`base.html`, `base_auth.html` with sidebar, reusable `components/` included via `{% include %}`); app-specific ones in `<app>/templates/<app>/`. Dark theme with violet→indigo→cyan brand gradient; exact Tailwind classes per component are in PRD section 9. Plain JS only in `static/js/`.
- CRUD actions report success/error via `django.contrib.messages` (`SuccessMessageMixin`).

### AI assistant (`ai` app, PRD section 14, details in `docs/ia.md`)

- **Flow:** `ai:create` (POST) → `ai.services.generate_analysis(user)` → `ai.agent.run_agent()` (LangChain `create_agent` + `ChatOpenAI`, `ToolStrategy` structured output, call/tool/time-limit and PII middlewares) → tools in `ai/tools.py` → read-only ORM functions in `ai/queries.py` → `ai/validators.py` checks evidence against real tool results → result saved in `FinancialAnalysis`. Synchronous, on demand only; the dashboard only reads (`get_dashboard_analysis_state`) and never calls the model.
- **Boundaries:** `services.py` is the only entry point for the rest of the system and the only module that writes analyses; `agent.py` is the only module that builds the model/agent; every `queries.py` function takes `user_id` first and has no LangChain.
- **Isolation:** the data owner comes only from the immutable `AnalysisContext` (`ai/context.py`), passed as `context=` and read in tools via `runtime.context` — never from model-supplied arguments. Tool results are aggregated and limited; descriptions are treated as data, not instructions.
- **Lazy loading:** LangChain/OpenAI are imported only inside the functions that run the agent (`services._run_and_record`). Django startup and normal pages must not import them (`LangChainNotImportedTests`).
- **Configuration:** `OPENAI_API_KEY`, `AI_MODEL_NAME` (default `gpt-5-mini`, shutdown announced for 2026-12-11 — item I-01) and the other `AI_*` limits in `core/settings.py`. Without a key the assistant is disabled and the rest of the app works.
- **Tests never hit the network:** they patch `ai.agent.build_chat_model` with a fake chat model (`GenericFakeChatModel` subclass) or block the agent entirely (`ModelNotCalledMixin`).

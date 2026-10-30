# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Finanpy is a personal finance web app (bank accounts, categories, income/expense transactions, dashboard) built with **Django full stack** (DTL templates, SQLite, no JS frameworks). `PRD.md` is the source of truth for scope, data model, design system and the sprint task list; `docs/` summarizes the guidelines (index at `docs/README.md`).

**Current state:** Sprint 0 (setup). The Django project (`core`) and the apps `users`, `profiles`, `accounts`, `categories`, `transactions` exist and are registered, but have no models, views, URLs or templates yet. Only `admin/` is routed. Settings still have Django defaults (`LANGUAGE_CODE = 'en-us'`, `TIME_ZONE = 'UTC'`, no `TEMPLATES['DIRS']`/`STATICFILES_DIRS`) — task 0.4 of the PRD.

## Commands

Windows dev environment with a local `venv/` (Python 3.12, Django 6.1).

```bash
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
python manage.py test                                   # all tests
python manage.py test accounts.tests.SomeTestCase.test_x  # single test
```

- `requirements.txt` must stay UTF-8. In PowerShell, regenerate with `pip freeze | Out-File -Encoding utf8 requirements.txt` (plain `>` writes UTF-16).
- Linting with `ruff` (line-length 79, single quotes via `Q` rules) is planned in task 0.5 but not installed yet.
- TailwindCSS (standalone CLI, no Node.js) is planned for Sprint 2: `tailwindcss -i static/css/input.css -o static/css/output.css --watch` (dev) / `--minify` (prod). `output.css` is gitignored.

## Mandatory conventions

- **Code in English** (names, URLs, models); **all user-facing text in Brazilian Portuguese** (labels, `verbose_name`, messages).
- PEP 8 and **single quotes** in Python.
- Keep it simple: only native Django features, Class Based Views, and only what the PRD specifies — no extra libraries or features.
- Every model has `created_at` (`auto_now_add`) and `updated_at` (`auto_now`).
- Money uses `DecimalField(max_digits=12, decimal_places=2)`, never `float`.
- Signals live in the app's `signals.py`, connected in `AppConfig.ready()`.
- When finishing PRD tasks, mark their subtasks `[x]` in `PRD.md` section 13; a task is checked only when all its subtasks are.

## Architecture (as planned in the PRD)

- **Custom user first:** `users.User` (extends `AbstractUser`, `username = None`, `email` unique as `USERNAME_FIELD`, custom `UserManager`) and `AUTH_USER_MODEL = 'users.User'` must exist **before** the first migration of any other app. The existing `db.sqlite3` already has the default `auth` migrations applied, so it must be deleted and re-migrated once the custom user is added.
- **Shared code in `core`:** abstract `TimeStampedModel` (`core/models.py`), `INPUT_CLASSES` + `StyledFormMixin` applying Tailwind classes to all form widgets (`core/forms.py`), `UserQuerySetMixin` / `UserFormMixin` for per-user data isolation (`core/mixins.py`), plus `HomeView` (landing, `home`) and `DashboardView` (`dashboard`).
- **Data isolation:** every authenticated view uses `LoginRequiredMixin` and filters querysets by `request.user`; accessing another user's object must 404. Forms receiving `user` in `__init__` restrict account/category querysets to that user.
- **Data rules:** `Profile` is created by a `post_save` signal on `User`. `Account` balance is never stored — `current_balance` = `initial_balance` + income − expense via `aggregate(Sum)`. `Transaction.account`/`category` use `on_delete=PROTECT`; delete views catch `ProtectedError` and show an error message. A transaction's category must have the same type (`income`/`expense`) as the transaction. `Category` is unique per `(user, name, category_type)`.
- **URLs:** each app has `urls.py` with `app_name` (e.g. `accounts:list`), routes `''`, `new/`, `<int:pk>/edit/`, `<int:pk>/delete/`. Auth routes `signup`, `login`, `logout` (logout via POST); `LOGIN_REDIRECT_URL = 'dashboard'`, `LOGOUT_REDIRECT_URL = 'home'`.
- **Templates:** global ones in `templates/` (`base.html`, `base_auth.html` with sidebar, reusable `components/` included via `{% include %}`); app-specific ones in `<app>/templates/<app>/`. Dark theme with violet→indigo→cyan brand gradient; exact Tailwind classes per component are in PRD section 9.
- CRUD actions report success/error via `django.contrib.messages` (`SuccessMessageMixin`).

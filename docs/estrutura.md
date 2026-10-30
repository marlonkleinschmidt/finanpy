# Estrutura do projeto

```
finanpy
├── accounts          # contas bancárias
├── categories        # categorias de transações
├── core              # configurações globais (settings, urls, asgi, wsgi)
├── profiles          # perfis de usuários
├── transactions      # transações (entradas e saídas)
├── users             # usuário customizado
├── docs              # esta documentação
├── db.sqlite3
├── manage.py
├── PRD.md
└── requirements.txt
```

## Responsabilidade das apps

Cada app tem uma responsabilidade única, definida no PRD (seção 8.3):

| App            | Responsabilidade                                         |
| -------------- | -------------------------------------------------------- |
| `core`         | settings e URLs raiz                                     |
| `users`        | model `User` customizado (login por e-mail)              |
| `profiles`     | model `Profile` do usuário                               |
| `accounts`     | model `Account` (contas bancárias)                       |
| `categories`   | model `Category` (categorias de entrada e saída)         |
| `transactions` | model `Transaction` (entradas e saídas)                  |

## Organização dentro de cada app

Cada app segue a estrutura padrão do Django (`models.py`, `views.py`, `admin.py`, `apps.py`, `tests.py`, `migrations/`). Conforme o PRD, quando necessário, cada app também terá:

- `urls.py` — rotas da app.
- `forms.py` — formulários da app.
- `signals.py` — signals da app (nunca em outro arquivo).
- `templates/<app>/` — templates específicos da app.

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

## Dependências

Ao instalar um novo pacote, atualize o arquivo de dependências:

```bash
pip freeze > requirements.txt
```

## Arquivos ignorados

O `.gitignore` já ignora, entre outros: `venv/`, `__pycache__/`, `*.pyc`, `db.sqlite3`, `.env`, `static/css/output.css` e `staticfiles/`.

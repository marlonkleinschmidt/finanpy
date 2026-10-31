# Finanpy

Sistema web de gestão de finanças pessoais, com contas bancárias, categorias, transações e dashboard, feito com Django.

## Funcionalidades

- Cadastro e login com e-mail e senha, e edição de perfil.
- Contas bancárias, com saldo calculado a partir do saldo inicial e das transações.
- Categorias de receita e de despesa.
- Transações de receita e de despesa, com filtros na listagem.
- Dashboard com saldo total, receitas, despesas e resultado do mês, contas e últimas transações.

Cada usuário acessa apenas os próprios dados.

## Requisitos

- Python 3.12 ou superior.
- Tailwind CLI standalone, sem Node.js (veja [TailwindCSS](#tailwindcss)).

O banco de dados é SQLite, que dispensa instalação.

## Instalação

Os comandos deste documento são para Windows, em PowerShell, a partir da raiz do projeto.

Crie e ative o ambiente virtual:

```powershell
python -m venv venv
venv\Scripts\activate
```

Instale as dependências. O `requirements-dev.txt` inclui o `requirements.txt` e adiciona o `ruff`, usado apenas no desenvolvimento:

```powershell
pip install -r requirements-dev.txt
```

Para instalar somente o necessário para executar a aplicação, use `pip install -r requirements.txt`.

Copie o arquivo de variáveis de ambiente e gere uma `SECRET_KEY`:

```powershell
copy .env.example .env
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Cole a chave gerada em `SECRET_KEY` no arquivo `.env`, sem aspas. O projeto não inicia sem essa variável, e o `.env` não deve ser versionado.

| Variável        | Uso                                                                             |
| --------------- | ------------------------------------------------------------------------------- |
| `SECRET_KEY`    | Chave secreta do Django. Obrigatória.                                           |
| `DEBUG`         | `True` no desenvolvimento. Qualquer outro valor, ou a ausência dela, é `False`. |
| `ALLOWED_HOSTS` | Hosts aceitos, separados por vírgula.                                           |

Crie o banco de dados:

```powershell
python manage.py migrate
```

## TailwindCSS

O projeto usa o executável standalone do Tailwind CLI, sem Node.js. Ele não é versionado, então baixe-o na raiz do projeto a partir da [página de releases](https://github.com/tailwindlabs/tailwindcss/releases) (no Windows x64, o arquivo `tailwindcss-windows-x64.exe`) e renomeie-o para `tailwindcss.exe`. O projeto foi testado com a versão 4.3.3.

Em PowerShell, este comando baixa essa versão (cerca de 110 MB) já com o nome certo:

```powershell
Invoke-WebRequest https://github.com/tailwindlabs/tailwindcss/releases/download/v4.3.3/tailwindcss-windows-x64.exe -OutFile tailwindcss.exe
```

O arquivo `static/css/output.css` é gerado por estes comandos e também não é versionado. Sem ele, as páginas abrem sem estilo.

Desenvolvimento, recompilando a cada alteração (deixe rodando em um terminal separado):

```powershell
.\tailwindcss.exe -i static/css/input.css -o static/css/output.css --watch
```

Produção, com o CSS minificado:

```powershell
.\tailwindcss.exe -i static/css/input.css -o static/css/output.css --minify
```

## Como rodar

Com o ambiente virtual ativo, o `.env` preenchido, o banco criado e o CSS gerado:

```powershell
python manage.py runserver
```

A aplicação fica em `http://127.0.0.1:8000/`. Crie uma conta em `/signup/` para começar.

O `runserver` só serve os arquivos estáticos com `DEBUG=True`, como vem no `.env.example`. Com `DEBUG=False`, as páginas abrem sem CSS.

O admin do Django fica em `/admin/`. Para acessá-lo, crie um superusuário. O comando pede e-mail, nome, sobrenome e senha:

```powershell
python manage.py createsuperuser
```

## Testes e lint

```powershell
python manage.py test
ruff check .
```

Para rodar um único teste, informe o caminho dele, por exemplo `python manage.py test users.tests`.

O `ruff` é configurado no `pyproject.toml` e vem do `requirements-dev.txt`.

## Dependências

O `requirements.txt` lista apenas o que a aplicação precisa para rodar, e o `requirements-dev.txt` acrescenta as ferramentas de desenvolvimento. Mantenha o `requirements.txt` em UTF-8: no Windows PowerShell, o `>` grava em UTF-16.

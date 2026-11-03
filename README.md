# Finanpy

Sistema web de gestão de finanças pessoais, com contas bancárias, categorias, transações e dashboard, feito com Django.

## Funcionalidades

- Cadastro e login com e-mail e senha, e edição de perfil.
- Contas bancárias, com saldo calculado a partir do saldo inicial e das transações.
- Categorias de receita e de despesa.
- Transações de receita e de despesa, com filtros na listagem.
- Dashboard com saldo total, receitas, despesas e resultado do mês, contas e últimas transações.
- Assistente Financeiro com IA: sob demanda, analisa os últimos meses de transações e gera observações, alertas e recomendações, sempre acompanhados dos números que os sustentam, com histórico das análises. Usa a API da OpenAI e é opcional (veja [Assistente Financeiro](#assistente-financeiro)).

Cada usuário acessa apenas os próprios dados.

## Requisitos

- Python 3.12 ou superior.
- Tailwind CLI standalone, sem Node.js (veja [TailwindCSS](#tailwindcss)).

O banco de dados é SQLite, que dispensa instalação. Com o Docker, nada disso é necessário (veja [Docker](#docker)).

Para o Assistente Financeiro, é preciso uma chave da API da OpenAI. Sem ela, o restante do sistema funciona normalmente.

## Instalação

Os comandos deste documento são para Windows, em PowerShell, a partir da raiz do projeto.

Crie e ative o ambiente virtual:

```powershell
python -m venv venv
venv\Scripts\activate
```

Instale as dependências. O `requirements-dev.txt` inclui o `requirements.txt` e adiciona o `ruff` e o `coverage`, usados apenas no desenvolvimento:

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

| Variável         | Uso                                                                             |
| ---------------- | ------------------------------------------------------------------------------- |
| `SECRET_KEY`     | Chave secreta do Django. Obrigatória.                                           |
| `DEBUG`          | `True` no desenvolvimento. Qualquer outro valor, ou a ausência dela, é `False`. |
| `ALLOWED_HOSTS`  | Hosts aceitos, separados por vírgula.                                           |
| `DATABASE_PATH`  | Caminho do SQLite. Opcional: o padrão é `db.sqlite3`, na raiz do projeto.       |
| `OPENAI_API_KEY` | Chave da API da OpenAI. Opcional: sem ela, o Assistente fica indisponível.      |
| `AI_MODEL_NAME`  | Modelo usado pelo Assistente. Padrão: `gpt-5-mini`.                             |

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

## Assistente Financeiro

O Assistente fica no card "Assistente Financeiro" do dashboard e no histórico em `/ai/`. Cada análise é gerada quando o usuário clica no botão, nunca automaticamente, e usa somente os dados do próprio usuário.

Para ativá-lo, preencha `OPENAI_API_KEY` no `.env` e reinicie o servidor. Sem a chave, o card informa que o Assistente não está disponível e nenhuma chamada à OpenAI é feita.

**O `gpt-5-mini` tem desligamento anunciado pela OpenAI para 11/12/2026.** Depois dessa data, o Assistente para de funcionar até `AI_MODEL_NAME` ser trocado por outro modelo, o que não exige alteração de código.

Cada análise tem custo na API da OpenAI, e há um limite diário de análises por usuário. Os demais parâmetros (`AI_*`) e o teste real opcional estão em [docs/setup.md](docs/setup.md#assistente-financeiro-ia). A arquitetura, as tools, os limites, os códigos de erro e a troca do modelo estão em [docs/ia.md](docs/ia.md).

## Docker

Esta é a forma de rodar sem instalar Python nem o Tailwind CLI. Só é preciso ter o Docker com o Compose 2.30 ou superior.

**Esta configuração não é para produção.** A imagem usa o `runserver` do Django com a opção `--insecure`, que serve os arquivos estáticos também com `DEBUG=False`. A própria documentação do Django desaconselha esse uso em produção, por ser ineficiente e provavelmente inseguro. Use-a apenas para rodar a aplicação localmente.

Copie o arquivo de variáveis de ambiente e gere uma `SECRET_KEY`. O comando abaixo não exige Python na máquina:

```powershell
copy .env.example .env
docker run --rm python:3.12-slim python -c "import secrets; print(secrets.token_urlsafe(50))"
```

Cole a chave gerada em `SECRET_KEY` no arquivo `.env`, sem aspas. O Compose não inicia sem esse arquivo, e ele não entra na imagem: os valores chegam ao container apenas na execução. Uma chave com `$` funciona, mas o Compose mostra avisos de `variable is not set`.

Para usar o Assistente Financeiro no container, preencha também `OPENAI_API_KEY` (e, se quiser, `AI_MODEL_NAME` e as demais variáveis `AI_*`) no mesmo `.env`. Sem a chave, a aplicação sobe normalmente, com o Assistente indisponível. Depois de alterar o `.env`, rode `docker compose up -d` para recriar o container com os novos valores; não é preciso reconstruir a imagem.

Construa a imagem e inicie a aplicação:

```powershell
docker compose up --build
```

A aplicação fica em `http://localhost:8000/`. As migrations são aplicadas a cada inicialização, e o `output.css` é gerado durante o build, com o Tailwind CLI 4.3.3 para Linux, que o próprio build baixa.

Se a porta 8000 já estiver em uso, o Compose falha com `port is already allocated`. Libere a porta ou troque o primeiro número em `ports` no `docker-compose.yml`, por exemplo `'8001:8000'`.

O banco SQLite fica no volume `db_data`, separado do `db.sqlite3` usado fora do Docker. Os dois não compartilham dados. Na imagem, o caminho padrão do banco é `DATABASE_PATH=/data/db.sqlite3`, o diretório onde o volume é montado; por isso comandos como `docker run --rm -e SECRET_KEY=... <imagem> python manage.py check` também funcionam sem o Compose.

| Comando                                                    | Uso                                              |
| ---------------------------------------------------------- | ------------------------------------------------ |
| `docker compose up -d`                                     | Inicia em segundo plano.                         |
| `docker compose logs -f web`                               | Acompanha os logs.                               |
| `docker compose exec web python manage.py createsuperuser` | Cria um superusuário para o `/admin/`.           |
| `docker compose down`                                      | Remove o container e **mantém** os dados.        |
| `docker compose down -v`                                   | Remove o container e **apaga** o banco de dados. |

O código é copiado para a imagem no build. Depois de alterar código ou templates, ou de atualizar o projeto (`git pull`), rode novamente `docker compose up --build`. Na inicialização, o container aplica as migrations novas, como a da app `ai`, sobre o banco que já está no volume, sem perder os dados. Se o `.env` não tiver `OPENAI_API_KEY`, o Assistente aparece como indisponível e o restante da aplicação funciona normalmente.

## Testes e lint

```powershell
python manage.py test
ruff check .
```

Para rodar um único teste, informe o caminho dele, por exemplo `python manage.py test users.tests`.

Os testes do Assistente usam um modelo falso e não acessam a rede. O único teste com a API real da OpenAI é ignorado por padrão, porque gera custo; veja [docs/setup.md](docs/setup.md#testes).

O `ruff` é configurado no `pyproject.toml` e vem do `requirements-dev.txt`.

Para medir a cobertura dos testes:

```powershell
coverage run manage.py test
coverage report
```

O `coverage` também é configurado no `pyproject.toml` e vem do `requirements-dev.txt`. A medição ignora testes e migrations, e o `coverage report` termina com erro se a cobertura ficar abaixo de 80%.

## Dependências

O `requirements.txt` lista apenas o que a aplicação precisa para rodar, e o `requirements-dev.txt` acrescenta as ferramentas de desenvolvimento. Mantenha o `requirements.txt` em UTF-8: no Windows PowerShell, o `>` grava em UTF-16.

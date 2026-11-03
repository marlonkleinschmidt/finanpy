# Estágio do CSS: o executável do Tailwind (cerca de 110 MB) fica só aqui.
FROM python:3.12-slim AS css

ARG TAILWIND_VERSION=4.3.3

WORKDIR /app

RUN case "$(uname -m)" in \
      x86_64) arch=x64 ;; \
      aarch64) arch=arm64 ;; \
      *) echo "Arquitetura sem suporte: $(uname -m)" >&2; exit 1 ;; \
    esac \
    && python -c "import sys, urllib.request; urllib.request.urlretrieve(sys.argv[1], sys.argv[2])" \
      "https://github.com/tailwindlabs/tailwindcss/releases/download/v${TAILWIND_VERSION}/tailwindcss-linux-${arch}" \
      /usr/local/bin/tailwindcss \
    && chmod +x /usr/local/bin/tailwindcss

# Os @source do input.css apontam para templates e forms.py das apps.
COPY . .

RUN tailwindcss -i static/css/input.css -o static/css/output.css --minify


# Imagem final
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY --from=css /app/static/css/output.css static/css/output.css

# O valor abaixo existe só neste comando e não é segredo: o collectstatic não
# usa a chave, mas o settings.py não carrega sem ela.
RUN SECRET_KEY=somente-para-o-collectstatic \
    python manage.py collectstatic --noinput

# /data recebe o volume do SQLite. O volume novo herda este dono.
RUN useradd --system finanpy \
    && mkdir /data \
    && chown finanpy /data

# Padrão para rodar a imagem sem o Compose: /app pertence ao root.
ENV DATABASE_PATH=/data/db.sqlite3

USER finanpy

EXPOSE 8000

# Sem gunicorn ou whitenoise, o --insecure é o que serve os estáticos com
# DEBUG=False. Não é uma configuração para produção: veja o README.md.
CMD ["sh", "-c", "python manage.py migrate --noinput && exec python manage.py runserver --insecure --noreload 0.0.0.0:8000"]

# Padrões de código

Regras definidas no PRD (seções 7 e 8) que todo código do projeto deve seguir.

## Idioma

- **Código em inglês:** variáveis, funções, classes, models, URLs e nomes de apps.
- **Interface em português brasileiro:** textos exibidos ao usuário, labels, `verbose_name` e mensagens.

## Estilo

- Seguir a **PEP 8**.
- Usar **aspas simples** sempre que possível.

```python
# certo
name = models.CharField('Nome', max_length=100)

# errado
name = models.CharField("Nome", max_length=100)
```

## Simplicidade

- Usar apenas recursos nativos do Django; evitar bibliotecas extras sem necessidade.
  A única exceção autorizada são `langchain` e `langchain-openai`, restritos à app `ai` (PRD, seção 14.19, item I-03).
- Sem over engineering: implementar somente o que está no PRD.

## Models

- Todo model deve ter os campos `created_at` e `updated_at`:

```python
created_at = models.DateTimeField(auto_now_add=True)
updated_at = models.DateTimeField(auto_now=True)
```

- Valores monetários usam `DecimalField(max_digits=12, decimal_places=2)`, nunca `float`.
- Valores derivados (como o saldo de uma conta) são calculados, não armazenados.

## Views

- Usar preferencialmente **Class Based Views**.
- Páginas da área autenticada exigem login (`LoginRequiredMixin`).
- Todas as queries da área autenticada são filtradas pelo usuário logado (`request.user`), garantindo que cada usuário veja apenas os próprios dados.

## Signals

- Quando usados, ficam em `signals.py` dentro da app correspondente e são registrados no `ready()` do `AppConfig`.

## Segurança

- Autenticação com o sistema nativo `django.contrib.auth`.
- Proteção CSRF em todos os formulários.
- Senhas validadas pelos `AUTH_PASSWORD_VALIDATORS` nativos do Django.

## Banco de dados

- SQLite padrão do Django.

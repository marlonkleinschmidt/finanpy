# Visão geral

## O que é

O **Finanpy** é um sistema web de gestão de finanças pessoais, feito com Django full stack. O objetivo é permitir que o usuário cadastre contas bancárias, organize transações por categorias e acompanhe saldos em um dashboard (ver [PRD.md](../PRD.md), seções 1 a 5).

O projeto é intencionalmente simples: sem over engineering, usando apenas recursos nativos do Django.

## Stack

| Camada         | Tecnologia                         |
| -------------- | ---------------------------------- |
| Linguagem      | Python 3.12                        |
| Framework      | Django 6.1                         |
| Templates      | Django Template Language (DTL)     |
| Banco de dados | SQLite (`db.sqlite3`)              |

Dependências instaladas (`requirements.txt`): `Django`, `asgiref`, `sqlparse` e `tzdata`.

## Estado atual

O projeto está na **Sprint 0 (setup)**. Hoje existem:

- O projeto Django criado na pasta `core` (settings, urls, asgi e wsgi).
- As apps `users`, `profiles`, `accounts`, `categories` e `transactions`, criadas e registradas em `INSTALLED_APPS`, ainda sem models, views ou URLs.
- Apenas a rota `admin/` em `core/urls.py`.

Ainda **não** existem: model de usuário customizado, templates, arquivos estáticos, TailwindCSS, testes ou Docker. Essas etapas estão planejadas nas sprints do PRD (seção 13).

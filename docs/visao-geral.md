# Visão geral

## O que é

O **Finanpy** é um sistema web de gestão de finanças pessoais, feito com Django full stack. O objetivo é permitir que o usuário cadastre contas bancárias, organize transações por categorias e acompanhe saldos em um dashboard (ver [PRD.md](../PRD.md), seções 1 a 5).

O projeto é intencionalmente simples: sem over engineering, usando apenas recursos nativos do Django. A única exceção é o Assistente Financeiro, que usa `langchain` e `langchain-openai` (PRD, seção 14.19, item I-03).

## Stack

| Camada         | Tecnologia                                        |
| -------------- | ------------------------------------------------- |
| Linguagem      | Python 3.12                                       |
| Framework      | Django 6.1                                        |
| Templates      | Django Template Language (DTL)                    |
| Estilos        | TailwindCSS 4 (CLI standalone, sem Node.js)       |
| Banco de dados | SQLite                                            |
| IA             | LangChain 1.x e `langchain-openai` (`gpt-5-mini`) |
| Execução       | Docker e Docker Compose (opcional)                |

As versões exatas estão no `requirements.txt`. O `requirements-dev.txt` acrescenta o `ruff` e o `coverage`.

## Estado atual

As Sprints 0 a 9 e 11 estão concluídas: autenticação por e-mail, perfil, contas, categorias, transações, dashboard, testes automatizados e Docker. A Sprint 10 (Assistente Financeiro com IA, app `ai`) está implementada e testada, faltando apenas concluir a documentação. O andamento de cada tarefa está no [TASKS.md](../TASKS.md).

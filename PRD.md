# PRD — Finanpy

> Product Requirement Document do sistema de gestão de finanças pessoais **Finanpy**.

---

## 1. Visão geral

O **Finanpy** é um sistema web de gestão de finanças pessoais, desenvolvido em Python com Django full stack. Ele permite que o usuário cadastre suas contas bancárias, organize suas movimentações financeiras por categorias e acompanhe entradas, saídas e saldos em um dashboard único.

O projeto é intencionalmente simples e enxuto: sem over engineering, usando apenas recursos nativos do Django, Django Template Language (DTL) com TailwindCSS no frontend e SQLite como banco de dados.

---

## 2. Sobre o produto

O Finanpy é composto por duas áreas:

1. **Site público de apresentação (landing page):** apresenta o produto e oferece as opções **Cadastre-se** e **Entrar**.
2. **Área autenticada:** após o login (feito por e-mail e senha), o usuário é direcionado ao **dashboard**, de onde acessa:
   - Contas bancárias
   - Categorias
   - Transações (entradas e saídas)
   - Perfil

Toda a interface é em **português brasileiro**, com design moderno, responsivo, fundo escuro e gradientes de cores harmônicas, seguindo um design system único em todas as telas.

---

## 3. Propósito

Oferecer uma ferramenta simples, rápida e visualmente agradável para que pessoas físicas controlem o próprio dinheiro: saber quanto têm, de onde vem e para onde vai cada real, sem a complexidade de planilhas ou aplicativos sobrecarregados de funcionalidades.

---

## 4. Público alvo

- Pessoas físicas que desejam organizar suas finanças pessoais.
- Usuários que possuem uma ou mais contas bancárias e querem uma visão consolidada dos saldos.
- Pessoas que hoje usam planilhas ou anotações e buscam algo mais prático.
- Perfil de uso: desktop e mobile (navegador), com conhecimento básico de internet.

---

## 5. Objetivos

1. Permitir o cadastro e login de usuários utilizando **e-mail** como identificador.
2. Permitir o gerenciamento (CRUD) de **contas bancárias**.
3. Permitir o gerenciamento (CRUD) de **categorias** de entradas e saídas.
4. Permitir o registro (CRUD) de **transações** de entrada e saída, vinculadas a uma conta e a uma categoria.
5. Exibir um **dashboard** com saldo total, total de entradas e saídas do mês e últimas transações.
6. Garantir que cada usuário acesse **somente os próprios dados**.
7. Manter uma **identidade visual consistente** em todo o sistema.
8. Manter o código **simples**, em inglês, seguindo a PEP 8 e usando aspas simples.

---

## 6. Requisitos funcionais

### 6.1 Site público

| ID   | Requisito                                                                                        |
| ---- | ------------------------------------------------------------------------------------------------ |
| RF01 | O sistema deve exibir uma landing page pública apresentando o Finanpy.                           |
| RF02 | A landing page deve conter os botões **Cadastre-se** e **Entrar**.                               |
| RF03 | Usuários já autenticados que acessarem a landing page devem ver o botão **Ir para o dashboard**. |

### 6.2 Usuários e autenticação

| ID   | Requisito                                                                                                          |
| ---- | ------------------------------------------------------------------------------------------------------------------ |
| RF04 | O usuário deve poder se cadastrar informando nome, sobrenome, e-mail e senha (com confirmação).                    |
| RF05 | O e-mail deve ser único no sistema.                                                                                |
| RF06 | O login deve ser realizado com **e-mail e senha** (não com username).                                              |
| RF07 | Após o cadastro, o usuário deve ser autenticado automaticamente e redirecionado ao dashboard.                      |
| RF08 | Após o login, o usuário deve ser redirecionado ao dashboard.                                                       |
| RF09 | O usuário deve poder sair do sistema (logout), sendo redirecionado à landing page.                                 |
| RF10 | Páginas da área autenticada devem exigir login; usuários não autenticados são redirecionados para a tela de login. |

### 6.3 Perfil

| ID   | Requisito                                                                                   |
| ---- | ------------------------------------------------------------------------------------------- |
| RF11 | Um perfil deve ser criado automaticamente quando um usuário é cadastrado.                   |
| RF12 | O usuário deve poder visualizar e editar seus dados de perfil (nome, sobrenome e telefone). |

### 6.4 Contas bancárias

| ID   | Requisito                                                                                     |
| ---- | --------------------------------------------------------------------------------------------- |
| RF13 | O usuário deve poder cadastrar contas bancárias (nome, banco, tipo de conta e saldo inicial). |
| RF14 | O usuário deve poder listar, editar e excluir suas contas.                                    |
| RF15 | O sistema deve exibir o saldo atual de cada conta (saldo inicial + entradas − saídas).        |
| RF16 | Tipos de conta disponíveis: Conta corrente, Poupança, Carteira e Investimento.                |

### 6.5 Categorias

| ID   | Requisito                                                                                            |
| ---- | ---------------------------------------------------------------------------------------------------- |
| RF17 | O usuário deve poder cadastrar categorias informando nome, tipo (Entrada ou Saída) e cor.            |
| RF18 | O usuário deve poder listar, editar e excluir suas categorias.                                       |
| RF19 | Uma categoria vinculada a transações não pode ser excluída (o sistema deve exibir mensagem de erro). |

### 6.6 Transações

| ID   | Requisito                                                                                                             |
| ---- | --------------------------------------------------------------------------------------------------------------------- |
| RF20 | O usuário deve poder registrar transações informando tipo (Entrada/Saída), valor, data, descrição, conta e categoria. |
| RF21 | O usuário deve poder listar, editar e excluir suas transações.                                                        |
| RF22 | A listagem de transações deve ser ordenada da mais recente para a mais antiga e paginada.                             |
| RF23 | A listagem deve permitir filtro por período (data inicial e final), tipo, conta e categoria.                          |
| RF24 | Nos formulários, apenas contas e categorias do próprio usuário devem ser exibidas.                                    |
| RF25 | A categoria escolhida deve ser do mesmo tipo da transação (Entrada/Saída).                                            |
| RF26 | Uma conta vinculada a transações não pode ser excluída (o sistema deve exibir mensagem de erro).                      |

### 6.7 Dashboard

| ID   | Requisito                                                                |
| ---- | ------------------------------------------------------------------------ |
| RF27 | O dashboard deve exibir o saldo total consolidado de todas as contas.    |
| RF28 | O dashboard deve exibir o total de entradas e de saídas do mês corrente. |
| RF29 | O dashboard deve exibir o resultado do mês (entradas − saídas).          |
| RF30 | O dashboard deve exibir as 5 últimas transações.                         |
| RF31 | O dashboard deve exibir a lista de contas com seus saldos.               |

### 6.8 Mensagens de feedback

| ID   | Requisito                                                                                                     |
| ---- | ------------------------------------------------------------------------------------------------------------- |
| RF32 | Toda ação de criar, editar e excluir deve exibir uma mensagem de sucesso ou erro (Django messages framework). |

### 6.9 Flowchart dos fluxos de UX

```mermaid
flowchart TD
    A([Visitante acessa o site]) --> B[Landing page]
    B -->|Cadastre-se| C[Tela de cadastro]
    B -->|Entrar| D[Tela de login]

    C --> C1{Dados válidos?}
    C1 -->|Não| C2[Exibe erros no formulário] --> C
    C1 -->|Sim| C3[Cria usuário + perfil via signal]
    C3 --> C4[Login automático]
    C4 --> E[Dashboard]

    D --> D1{E-mail e senha corretos?}
    D1 -->|Não| D2[Exibe erro de autenticação] --> D
    D1 -->|Sim| E

    E --> F[Contas bancárias]
    E --> G[Categorias]
    E --> H[Transações]
    E --> I[Perfil]
    E --> J[Sair]

    F --> F1[Listar contas]
    F1 --> F2[Nova conta]
    F1 --> F3[Editar conta]
    F1 --> F4[Excluir conta]
    F4 --> F5{Possui transações?}
    F5 -->|Sim| F6[Exibe erro] --> F1
    F5 -->|Não| F7[Confirma exclusão] --> F1
    F2 --> F1
    F3 --> F1

    G --> G1[Listar categorias]
    G1 --> G2[Nova categoria]
    G1 --> G3[Editar categoria]
    G1 --> G4[Excluir categoria]
    G4 --> G5{Possui transações?}
    G5 -->|Sim| G6[Exibe erro] --> G1
    G5 -->|Não| G7[Confirma exclusão] --> G1
    G2 --> G1
    G3 --> G1

    H --> H1[Listar transações com filtros]
    H1 --> H2[Nova transação]
    H1 --> H3[Editar transação]
    H1 --> H4[Excluir transação]
    H2 --> H1
    H3 --> H1
    H4 --> H1

    I --> I1[Editar perfil] --> E
    J --> B
```

---

## 7. Requisitos não-funcionais

| ID    | Requisito                                                                                                                       |
| ----- | ------------------------------------------------------------------------------------------------------------------------------- |
| RNF01 | Backend e frontend em **Django full stack**, com templates em Django Template Language.                                         |
| RNF02 | Estilização exclusivamente com **TailwindCSS**.                                                                                 |
| RNF03 | Interface **responsiva** (mobile, tablet e desktop), com fundo escuro e gradientes.                                             |
| RNF04 | Toda a interface exibida ao usuário em **português brasileiro** (`LANGUAGE_CODE = 'pt-br'`, `TIME_ZONE = 'America/Sao_Paulo'`). |
| RNF05 | Todo o código (variáveis, funções, classes, models, URLs) em **inglês**.                                                        |
| RNF06 | Código seguindo a **PEP 8** e usando **aspas simples** sempre que possível.                                                     |
| RNF07 | Banco de dados **SQLite** padrão do Django.                                                                                     |
| RNF08 | Todo model deve possuir os campos `created_at` e `updated_at`.                                                                  |
| RNF09 | Uso preferencial de **Class Based Views** e recursos nativos do Django.                                                         |
| RNF10 | Signals, quando usados, ficam em `signals.py` dentro da app correspondente.                                                     |
| RNF11 | Autenticação com o sistema nativo do Django (`django.contrib.auth`), com login por e-mail.                                      |
| RNF12 | Isolamento de dados: todas as queries da área autenticada filtradas pelo usuário logado.                                        |
| RNF13 | Proteção CSRF em todos os formulários (nativa do Django).                                                                       |
| RNF14 | Senhas validadas pelos `AUTH_PASSWORD_VALIDATORS` nativos do Django.                                                            |
| RNF15 | Valores monetários armazenados em `DecimalField` e exibidos no formato brasileiro (R$ 1.234,56).                                |
| RNF16 | Testes automatizados e Docker ficam para as sprints finais.                                                                     |

---

## 8. Arquitetura técnica

### 8.1 Stack

| Camada                    | Tecnologia                                                                |
| ------------------------- | ------------------------------------------------------------------------- |
| Linguagem                 | Python 3.12+                                                              |
| Framework                 | Django 5.x                                                                |
| Templates                 | Django Template Language                                                  |
| Estilos                   | TailwindCSS (CLI standalone, sem Node.js)                                 |
| Banco de dados            | SQLite                                                                    |
| Autenticação              | `django.contrib.auth` com model de usuário customizado (login por e-mail) |
| Mensagens                 | `django.contrib.messages`                                                 |
| Formatação BR             | `django.contrib.humanize` + localização nativa (`USE_L10N`/`pt-br`)       |
| Containers (sprint final) | Docker + docker-compose                                                   |
| Testes (sprint final)     | `django.test` (TestCase nativo)                                           |

### 8.2 Estrutura de diretórios

```
finanpy
├── accounts          # contas bancárias
├── categories        # categorias de lançamentos/transações
├── core              # configurações globais, landing page e dashboard
├── profiles          # perfis de usuários (+ signals.py)
├── transactions      # transações - entradas e saídas
├── users             # usuário customizado (login por e-mail)
├── templates         # templates globais (base, componentes, landing)
│   ├── base.html
│   ├── base_auth.html
│   ├── components/
│   └── ...
├── static
│   ├── css/input.css
│   └── css/output.css
├── db.sqlite3
└── manage.py
```

Cada app possui sua própria pasta `templates/<app>/` para os templates específicos, além de `urls.py` e `forms.py` quando necessário.

### 8.3 Responsabilidade das apps

| App            | Responsabilidade                                                                  |
| -------------- | --------------------------------------------------------------------------------- |
| `core`         | settings, URLs raiz, landing page (`HomeView`) e dashboard (`DashboardView`)      |
| `users`        | model `User` customizado (e-mail como `USERNAME_FIELD`), cadastro, login e logout |
| `profiles`     | model `Profile`, signal de criação automática e edição de perfil                  |
| `accounts`     | model `Account` e CRUD de contas                                                  |
| `categories`   | model `Category` e CRUD de categorias                                             |
| `transactions` | model `Transaction`, CRUD e filtros                                               |

### 8.4 Estrutura de dados (schemas)

```mermaid
erDiagram
    USER ||--|| PROFILE : "possui"
    USER ||--o{ ACCOUNT : "possui"
    USER ||--o{ CATEGORY : "possui"
    USER ||--o{ TRANSACTION : "registra"
    ACCOUNT ||--o{ TRANSACTION : "movimenta"
    CATEGORY ||--o{ TRANSACTION : "classifica"

    USER {
        int id PK
        string email UK "USERNAME_FIELD"
        string first_name
        string last_name
        string password
        bool is_active
        bool is_staff
        bool is_superuser
        datetime last_login
        datetime date_joined
        datetime created_at
        datetime updated_at
    }

    PROFILE {
        int id PK
        int user_id FK "OneToOne"
        string phone "opcional"
        datetime created_at
        datetime updated_at
    }

    ACCOUNT {
        int id PK
        int user_id FK
        string name
        string bank_name
        string account_type "checking | savings | wallet | investment"
        decimal initial_balance
        datetime created_at
        datetime updated_at
    }

    CATEGORY {
        int id PK
        int user_id FK
        string name
        string category_type "income | expense"
        string color "hex, ex: #8B5CF6"
        datetime created_at
        datetime updated_at
    }

    TRANSACTION {
        int id PK
        int user_id FK
        int account_id FK "on_delete=PROTECT"
        int category_id FK "on_delete=PROTECT"
        string transaction_type "income | expense"
        decimal amount
        date date
        string description
        datetime created_at
        datetime updated_at
    }
```

**Observações de modelagem:**

- `User` herda de `AbstractUser`, remove o campo `username`, define `email` como único e `USERNAME_FIELD = 'email'`, com um `UserManager` customizado.
- O saldo atual da conta **não é armazenado**: é calculado (`initial_balance + soma de entradas − soma de saídas`) via método/propriedade no model, evitando inconsistências.
- `account` e `category` em `Transaction` usam `on_delete=models.PROTECT`, impedindo exclusão de registros em uso.
- `Category` possui `unique_together` (ou `UniqueConstraint`) em `(user, name, category_type)`.
- `amount` e `initial_balance` usam `DecimalField(max_digits=12, decimal_places=2)`; `amount` deve ser maior que zero.
- `created_at = models.DateTimeField(auto_now_add=True)` e `updated_at = models.DateTimeField(auto_now=True)` em todos os models.

---

## 9. Design system

Todo o visual é construído com classes utilitárias do TailwindCSS dentro dos templates DTL. Componentes reutilizáveis ficam em `templates/components/` e são incluídos com `{% include %}`.

### 9.1 Princípios

- **Fundo escuro** como base, com superfícies levemente mais claras para criar profundidade.
- **Gradiente de marca** (violeta → índigo → ciano) aplicado em destaques: logo, botões primários, títulos de hero e cards de destaque.
- **Cores semânticas** consistentes: verde para entradas, vermelho/rosa para saídas.
- **Cantos arredondados**, bordas sutis e sombras suaves.
- **Mobile first**: todo layout começa em uma coluna e expande em breakpoints `md` e `lg`.

### 9.2 Paleta de cores

| Token              | Uso                         | Classe Tailwind             | Hex                   |
| ------------------ | --------------------------- | --------------------------- | --------------------- |
| Fundo da página    | `body`                      | `bg-slate-950`              | `#020617`             |
| Superfície         | cards, sidebar, navbar      | `bg-slate-900`              | `#0F172A`             |
| Superfície elevada | inputs, hover de itens      | `bg-slate-800`              | `#1E293B`             |
| Borda              | divisórias e contornos      | `border-slate-700/50`       | `#334155`             |
| Texto principal    | títulos e valores           | `text-slate-100`            | `#F1F5F9`             |
| Texto secundário   | descrições e labels         | `text-slate-400`            | `#94A3B8`             |
| Primária           | ações e foco                | `violet-500` / `violet-600` | `#8B5CF6` / `#7C3AED` |
| Secundária         | apoio do gradiente          | `indigo-500`                | `#6366F1`             |
| Acento             | apoio do gradiente          | `cyan-400`                  | `#22D3EE`             |
| Entrada (sucesso)  | valores positivos           | `emerald-400`               | `#34D399`             |
| Saída (perigo)     | valores negativos, exclusão | `rose-400` / `rose-600`     | `#FB7185` / `#E11D48` |
| Alerta             | avisos                      | `amber-400`                 | `#FBBF24`             |

**Gradientes:**

| Nome                      | Classes                                                                                     |
| ------------------------- | ------------------------------------------------------------------------------------------- |
| Gradiente de marca        | `bg-gradient-to-r from-violet-600 via-indigo-500 to-cyan-400`                               |
| Gradiente de texto        | `bg-gradient-to-r from-violet-400 via-indigo-400 to-cyan-300 bg-clip-text text-transparent` |
| Gradiente de fundo (hero) | `bg-gradient-to-br from-slate-950 via-indigo-950 to-slate-950`                              |
| Card de entrada           | `bg-gradient-to-br from-emerald-500/20 to-emerald-500/5`                                    |
| Card de saída             | `bg-gradient-to-br from-rose-500/20 to-rose-500/5`                                          |

### 9.3 Tipografia

- **Fonte:** `Inter` (Google Fonts), com fallback `ui-sans-serif, system-ui, sans-serif`, configurada como `font-sans` no tema do Tailwind.
- **Valores monetários:** `tabular-nums` para alinhar dígitos.

| Elemento              | Classes                                                      |
| --------------------- | ------------------------------------------------------------ |
| Título da página (h1) | `text-2xl md:text-3xl font-bold text-slate-100`              |
| Título de seção (h2)  | `text-xl font-semibold text-slate-100`                       |
| Título de card (h3)   | `text-sm font-medium text-slate-400 uppercase tracking-wide` |
| Valor de destaque     | `text-2xl md:text-3xl font-bold tabular-nums`                |
| Texto padrão          | `text-sm text-slate-300`                                     |
| Texto auxiliar        | `text-xs text-slate-500`                                     |
| Título hero (landing) | `text-4xl md:text-6xl font-extrabold` + gradiente de texto   |

### 9.4 Botões

Base comum: `inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold transition focus:outline-none focus:ring-2 focus:ring-violet-500 focus:ring-offset-2 focus:ring-offset-slate-950`

| Variante   | Classes adicionais                                                                                                       | Uso                      |
| ---------- | ------------------------------------------------------------------------------------------------------------------------ | ------------------------ |
| Primário   | `bg-gradient-to-r from-violet-600 via-indigo-500 to-cyan-400 text-white shadow-lg shadow-violet-900/30 hover:opacity-90` | Salvar, criar, entrar    |
| Secundário | `bg-slate-800 text-slate-100 border border-slate-700 hover:bg-slate-700`                                                 | Cancelar, voltar         |
| Perigo     | `bg-rose-600 text-white hover:bg-rose-500`                                                                               | Confirmar exclusão       |
| Ghost      | `text-slate-300 hover:text-white hover:bg-slate-800`                                                                     | Ações de tabela, links   |
| Ícone      | `p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800`                                                      | Editar/excluir em linhas |

### 9.5 Inputs e forms

| Elemento                  | Classes                                                                                                                                                                                    |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Label                     | `block text-sm font-medium text-slate-300 mb-1.5`                                                                                                                                          |
| Input / select / textarea | `w-full rounded-xl bg-slate-800 border border-slate-700 px-4 py-2.5 text-slate-100 placeholder-slate-500 focus:border-violet-500 focus:ring-2 focus:ring-violet-500/40 focus:outline-none` |
| Input com erro            | adicionar `border-rose-500 focus:ring-rose-500/40`                                                                                                                                         |
| Mensagem de erro          | `mt-1 text-xs text-rose-400`                                                                                                                                                               |
| Texto de ajuda            | `mt-1 text-xs text-slate-500`                                                                                                                                                              |
| Container do form         | `bg-slate-900 border border-slate-700/50 rounded-2xl p-6 md:p-8 space-y-5`                                                                                                                 |
| Rodapé do form            | `flex flex-col-reverse sm:flex-row sm:justify-end gap-3 pt-4`                                                                                                                              |

As classes dos inputs são aplicadas nos `widgets` dos forms Django (atributo `attrs={'class': ...}`), centralizadas em um mixin/constante reutilizável para não repetir strings. Os campos são renderizados pelo componente `components/form_field.html`.

### 9.6 Cards

| Elemento                       | Classes                                                                                                             |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------- |
| Card padrão                    | `bg-slate-900 border border-slate-700/50 rounded-2xl p-6 shadow-xl shadow-black/20`                                 |
| Card de métrica (KPI)          | card padrão + gradiente semântico e ícone                                                                           |
| Card de destaque (saldo total) | `rounded-2xl p-6 bg-gradient-to-br from-violet-600/30 via-indigo-600/20 to-cyan-500/10 border border-violet-500/30` |

### 9.7 Grids e layout

| Contexto             | Classes                                                            |
| -------------------- | ------------------------------------------------------------------ |
| Container da página  | `max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6`                      |
| Grid de KPIs         | `grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4`             |
| Grid de duas colunas | `grid grid-cols-1 lg:grid-cols-3 gap-6` (conteúdo `lg:col-span-2`) |
| Grid de formulário   | `grid grid-cols-1 md:grid-cols-2 gap-5`                            |
| Layout autenticado   | sidebar fixa à esquerda (`lg:w-64`) + conteúdo `flex-1`            |

### 9.8 Menus e navegação

- **Navbar pública (landing):** `sticky top-0 backdrop-blur bg-slate-950/70 border-b border-slate-800`; logo com gradiente à esquerda; botões **Entrar** (ghost) e **Cadastre-se** (primário) à direita.
- **Sidebar autenticada (desktop, `lg+`):** `bg-slate-900 border-r border-slate-800`, itens:
  - Dashboard, Contas, Categorias, Transações, Perfil, Sair.
  - Item padrão: `flex items-center gap-3 px-4 py-2.5 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800`
  - Item ativo: `bg-gradient-to-r from-violet-600/20 to-transparent text-white border-l-2 border-violet-500`
- **Menu mobile:** topbar com botão hambúrguer que abre/fecha a sidebar (toggle com poucas linhas de JavaScript puro, sem bibliotecas).

### 9.9 Tabelas e listas

| Elemento         | Classes                                                                                         |
| ---------------- | ----------------------------------------------------------------------------------------------- |
| Wrapper          | `overflow-x-auto rounded-2xl border border-slate-700/50`                                        |
| Tabela           | `min-w-full divide-y divide-slate-800 text-sm`                                                  |
| Cabeçalho        | `bg-slate-900 text-left text-xs font-semibold uppercase tracking-wide text-slate-400 px-4 py-3` |
| Linha            | `bg-slate-900/50 hover:bg-slate-800/60 transition`                                              |
| Célula           | `px-4 py-3 text-slate-300`                                                                      |
| Valor de entrada | `text-emerald-400 font-semibold tabular-nums` (prefixo `+`)                                     |
| Valor de saída   | `text-rose-400 font-semibold tabular-nums` (prefixo `−`)                                        |

No mobile, listas longas podem ser exibidas como cards empilhados em vez de tabela (`hidden md:table` / `md:hidden`).

### 9.10 Badges, alertas e estados

| Elemento           | Classes                                                                                         |
| ------------------ | ----------------------------------------------------------------------------------------------- |
| Badge entrada      | `inline-flex px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/15 text-emerald-400` |
| Badge saída        | `inline-flex px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-500/15 text-rose-400`       |
| Badge de categoria | bolinha com a cor da categoria (`style="background-color: {{ category.color }}"`) + nome        |
| Alerta sucesso     | `rounded-xl border border-emerald-500/30 bg-emerald-500/10 text-emerald-300 px-4 py-3`          |
| Alerta erro        | `rounded-xl border border-rose-500/30 bg-rose-500/10 text-rose-300 px-4 py-3`                   |
| Estado vazio       | card centralizado com ícone, texto `text-slate-400` e botão primário de criação                 |

### 9.11 Componentes de template

| Arquivo                                    | Descrição                                                     |
| ------------------------------------------ | ------------------------------------------------------------- |
| `templates/base.html`                      | HTML base: fonte, CSS do Tailwind, bloco `content`, mensagens |
| `templates/base_auth.html`                 | Estende `base.html` com sidebar + topbar mobile               |
| `templates/components/navbar_public.html`  | Navbar da landing e telas de login/cadastro                   |
| `templates/components/sidebar.html`        | Menu lateral da área autenticada                              |
| `templates/components/messages.html`       | Alertas do messages framework                                 |
| `templates/components/form_field.html`     | Label + campo + erro + ajuda                                  |
| `templates/components/page_header.html`    | Título da página + botão de ação                              |
| `templates/components/empty_state.html`    | Estado vazio de listagens                                     |
| `templates/components/pagination.html`     | Paginação padrão                                              |
| `templates/components/confirm_delete.html` | Tela de confirmação de exclusão                               |
| `templates/components/kpi_card.html`       | Card de métrica do dashboard                                  |

---

## 10. User stories

### Épico 1 — Site público e autenticação

**US01 — Conhecer o produto**
Como visitante, quero ver uma página de apresentação do Finanpy, para entender o que o sistema oferece antes de me cadastrar.

- [ ] A landing page é acessível sem login.
- [ ] Exibe título, descrição do produto e seção de benefícios.
- [ ] Exibe os botões **Cadastre-se** e **Entrar**, que levam às telas corretas.
- [ ] É responsiva e segue o design system.

**US02 — Criar conta**
Como visitante, quero me cadastrar com nome, e-mail e senha, para começar a usar o sistema.

- [ ] O formulário solicita nome, sobrenome, e-mail, senha e confirmação de senha.
- [ ] E-mail já cadastrado exibe erro "Já existe um usuário com este e-mail."
- [ ] Senhas diferentes ou fracas exibem erro em português.
- [ ] Após o cadastro, o usuário é logado e redirecionado ao dashboard.
- [ ] Um perfil é criado automaticamente.

**US03 — Entrar no sistema**
Como usuário, quero entrar com meu e-mail e senha, para acessar meus dados.

- [ ] O formulário solicita e-mail e senha (não username).
- [ ] Credenciais inválidas exibem "E-mail ou senha inválidos."
- [ ] Após o login, o usuário é redirecionado ao dashboard.

**US04 — Sair do sistema**
Como usuário, quero sair da minha conta, para proteger meus dados.

- [ ] A opção **Sair** está disponível no menu.
- [ ] O logout é feito via POST e redireciona à landing page.

### Épico 2 — Perfil

**US05 — Editar meu perfil**
Como usuário, quero editar meu nome, sobrenome e telefone.

- [ ] A tela de perfil exibe os dados atuais preenchidos.
- [ ] Ao salvar, exibe "Perfil atualizado com sucesso."
- [ ] O e-mail é exibido, mas não editável.

### Épico 3 — Contas bancárias

**US06 — Cadastrar conta**
Como usuário, quero cadastrar minhas contas bancárias com saldo inicial.

- [ ] O formulário pede nome, banco, tipo e saldo inicial.
- [ ] A conta fica vinculada ao usuário logado.
- [ ] Exibe mensagem de sucesso e redireciona para a listagem.

**US07 — Gerenciar contas**
Como usuário, quero listar, editar e excluir minhas contas e ver o saldo atual de cada uma.

- [ ] A listagem mostra nome, banco, tipo e saldo atual em R$.
- [ ] Só são exibidas contas do usuário logado; acessar conta de outro usuário retorna 404.
- [ ] A exclusão pede confirmação.
- [ ] Conta com transações não pode ser excluída e exibe mensagem de erro.
- [ ] Sem contas cadastradas, exibe estado vazio com botão "Nova conta".

### Épico 4 — Categorias

**US08 — Gerenciar categorias**
Como usuário, quero criar, listar, editar e excluir categorias de entrada e saída, para organizar minhas transações.

- [ ] O formulário pede nome, tipo (Entrada/Saída) e cor.
- [ ] Não é possível duplicar nome + tipo para o mesmo usuário.
- [ ] A listagem separa ou identifica visualmente entradas e saídas.
- [ ] Categoria com transações não pode ser excluída e exibe mensagem de erro.
- [ ] Só são exibidas categorias do usuário logado.

### Épico 5 — Transações

**US09 — Registrar transação**
Como usuário, quero registrar entradas e saídas com valor, data, descrição, conta e categoria.

- [ ] O valor deve ser maior que zero.
- [ ] Os selects exibem apenas contas e categorias do usuário.
- [ ] A categoria deve ser do mesmo tipo da transação; caso contrário, exibe erro.
- [ ] A data vem preenchida com o dia atual.
- [ ] Após salvar, o saldo da conta reflete a transação.

**US10 — Consultar transações**
Como usuário, quero listar e filtrar minhas transações, para analisar meus gastos e receitas.

- [ ] A listagem é ordenada da mais recente para a mais antiga.
- [ ] Possui paginação (20 itens por página).
- [ ] Permite filtrar por período, tipo, conta e categoria, mantendo os filtros na paginação.
- [ ] Entradas aparecem em verde e saídas em vermelho.

**US11 — Editar e excluir transação**
Como usuário, quero corrigir ou remover transações lançadas.

- [ ] A edição aplica as mesmas validações do cadastro.
- [ ] A exclusão pede confirmação e exibe mensagem de sucesso.
- [ ] Transações de outro usuário retornam 404.

### Épico 6 — Dashboard

**US12 — Visão geral das finanças**
Como usuário, quero ver um resumo das minhas finanças ao entrar no sistema.

- [ ] Exibe saldo total consolidado.
- [ ] Exibe total de entradas, total de saídas e resultado do mês corrente.
- [ ] Exibe as 5 últimas transações com link para a listagem completa.
- [ ] Exibe a lista de contas com saldos.
- [ ] Sem dados, exibe estados vazios orientando o usuário a cadastrar contas e transações.

---

## 11. Métricas de sucesso

### 11.1 KPIs de produto

| KPI                                                                               | Meta                 |
| --------------------------------------------------------------------------------- | -------------------- |
| Taxa de conversão landing → cadastro                                              | ≥ 10% dos visitantes |
| Taxa de ativação (usuário que cadastra ao menos 1 conta e 1 transação em até 24h) | ≥ 60%                |
| Tempo médio para registrar uma transação                                          | ≤ 30 segundos        |
| Erros 500 em produção                                                             | 0                    |

### 11.2 KPIs de usuário

| KPI                                                       | Meta  |
| --------------------------------------------------------- | ----- |
| Retenção semanal (usuários que voltam na semana seguinte) | ≥ 40% |
| Média de transações registradas por usuário ativo/mês     | ≥ 20  |
| Média de contas cadastradas por usuário                   | ≥ 2   |
| Média de categorias personalizadas por usuário            | ≥ 5   |

### 11.3 KPIs técnicos

| KPI                                    | Meta     |
| -------------------------------------- | -------- |
| Tempo de resposta das páginas          | ≤ 500 ms |
| Conformidade com PEP 8 (flake8/ruff)   | 100%     |
| Cobertura de testes (sprint de testes) | ≥ 80%    |
| Telas seguindo o design system         | 100%     |

---

## 12. Riscos e mitigações

| Risco                                                | Impacto | Mitigação                                                                                             |
| ---------------------------------------------------- | ------- | ----------------------------------------------------------------------------------------------------- |
| Usuário acessar dados de outro usuário               | Alto    | Filtrar todos os querysets por `request.user` via mixin; `get_object_or_404` sobre queryset filtrado. |
| Troca do model de usuário após migrations criadas    | Alto    | Criar o `User` customizado e definir `AUTH_USER_MODEL` **antes** da primeira migration.               |
| Saldo inconsistente                                  | Médio   | Calcular saldo dinamicamente a partir das transações, sem armazenar valor derivado.                   |
| Exclusão de conta/categoria apagar histórico         | Alto    | `on_delete=PROTECT` e tratamento de `ProtectedError` com mensagem amigável.                           |
| Erros de arredondamento em valores                   | Médio   | Usar `DecimalField`, nunca `float`.                                                                   |
| Inconsistência visual entre telas                    | Médio   | Componentes de template reutilizáveis e constantes de classes CSS para widgets.                       |
| CSS do Tailwind não gerado em produção               | Médio   | Documentar comando de build e versionar/gerar `output.css` no deploy; incluir no Dockerfile.          |
| Escopo crescer além do necessário (over engineering) | Médio   | Seguir estritamente este PRD; novas funcionalidades só com nova aprovação.                            |
| SQLite com limitação de concorrência                 | Baixo   | Adequado ao porte do projeto; reavaliar banco apenas se houver necessidade real.                      |
| Ausência de testes nas sprints iniciais              | Médio   | Validação manual ao fim de cada sprint; sprint dedicada a testes antes do Docker.                     |

---

## 14. Assistente Financeiro com IA

> **Numeração:** a seção 13 (lista de tarefas) foi movida para o `TASKS.md`. O número 13 não foi reutilizado porque `CLAUDE.md`, `agents/` e `docs/` ainda citam "seção 13" com aquele significado.
>
> **Relação com as seções anteriores:** esta seção complementa o PRD e prevalece apenas no que trata do Assistente. As exceções às regras gerais estão listadas na seção 14.19.
>
> **Verificação técnica:** as APIs citadas foram conferidas em 02/11/2026 no Context7 (`/websites/langchain_oss_python_langchain`), na documentação oficial do LangChain e da OpenAI, no PyPI e no código-fonte do `ToolNode`. Os itens que dependem de execução real estão marcados como **a confirmar na tarefa 10.1**.

### 14.1 Descrição e objetivos

O Assistente é um agente de IA, acionado pelo usuário, que consulta somente os dados financeiros desse usuário, gera insights, recomendações e alertas fundamentados nesses dados, grava cada análise no banco e exibe a última análise válida no dashboard.

**Objetivos:**

1. Transformar os lançamentos do usuário em conclusões claras, em português brasileiro.
2. Fundamentar cada conclusão em valores realmente retornados pelas tools.
3. Manter o histórico de análises de cada usuário, sem sobrescrever análises anteriores.
4. Garantir que o agente nunca acesse dados de outro usuário.
5. Manter custo, tempo de execução e complexidade limitados e mensuráveis.

**Posicionamento:** o Assistente atua em **educação e organização financeira pessoal**. Ele não é consultor de investimentos, não recomenda ativos ou produtos financeiros específicos e não garante resultados.

**Fora de escopo nesta versão:** chat livre com o agente, memória entre análises, ações que alterem dados, análises agendadas, notificações, orçamentos e metas (o sistema não possui esses dados).

### 14.2 Problema

O dashboard atual (RF27 a RF31) mostra saldos e totais do mês corrente, mas não responde perguntas como "em que categoria meus gastos aumentaram?", "quais gastos se repetem todo mês?" ou "estou gastando mais do que recebo ao longo dos meses?". Hoje, o usuário precisa cruzar filtros de transações por conta própria para chegar a essas conclusões.

### 14.3 Requisitos funcionais

| ID   | Requisito                                                                                                                                                  |
| ---- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| RF33 | O usuário autenticado deve poder solicitar uma nova análise pelo botão **Gerar análise**, enviado por POST com CSRF.                                       |
| RF34 | A análise deve considerar transações, entradas, saídas, categorias, saldos das contas e a evolução mensal do próprio usuário.                              |
| RF35 | A análise deve identificar, quando houver dados: categorias com aumento significativo, gastos recorrentes, entradas × saídas e evolução ao longo dos meses. |
| RF36 | A análise deve produzir um insight principal, de 1 a 5 recomendações, até 4 insights adicionais, até 3 alertas e as limitações dos dados.                  |
| RF37 | Cada insight, recomendação e alerta deve conter evidências com valores retornados pelas tools.                                                             |
| RF38 | Toda execução deve ser gravada em `FinancialAnalysis`, inclusive as que falharem, sem sobrescrever registros anteriores.                                   |
| RF39 | O dashboard deve exibir a última análise válida: insight principal, recomendações, alertas, período analisado e data da análise.                           |
| RF40 | O dashboard deve tratar os estados da seção 14.15: sem análise, em andamento, falha, desatualizada, limite atingido, dados insuficientes e indisponível.    |
| RF41 | O usuário deve poder consultar o histórico das próprias análises em lista paginada e abrir o detalhe de cada uma.                                          |
| RF42 | Acessar a análise de outro usuário deve retornar 404.                                                                                                      |
| RF43 | Com menos de `AI_ANALYSIS_MIN_TRANSACTIONS` transações no período, o sistema não deve chamar o modelo e deve exibir uma mensagem orientando o usuário.     |
| RF44 | Cada usuário pode iniciar até `AI_ANALYSIS_DAILY_LIMIT` análises por dia e ter somente uma em andamento.                                                   |
| RF45 | Toda análise deve exibir o aviso fixo de caráter educativo definido na seção 14.15.                                                                        |

### 14.4 Requisitos não funcionais

| ID    | Requisito                                                                                                                                           |
| ----- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| RNF17 | Toda a lógica de IA fica na app `ai`. As demais apps apenas consomem `ai.services`.                                                                 |
| RNF18 | Agente construído com LangChain 1.x (`create_agent`). É proibido usar `create_react_agent`, `AgentExecutor`, `initialize_agent` e `langchain_classic`. |
| RNF19 | Dependências diretas novas: somente `langchain` e `langchain-openai`, com versão fixada no `requirements.txt`.                                      |
| RNF20 | `OPENAI_API_KEY` vem do ambiente, nunca do código, do banco, de logs ou de templates.                                                               |
| RNF21 | Sem a chave, o sistema deve iniciar normalmente, com o Assistente indisponível. `check`, `test`, `migrate` e `collectstatic` não podem exigir a chave. |
| RNF22 | O dashboard nunca chama o modelo e executa no máximo 3 consultas adicionais. A meta de 500 ms (seção 11.3) vale para ele, não para a geração.       |
| RNF23 | LangChain e OpenAI são importados somente em `ai/agent.py` e `ai/tools.py`, carregados pelo serviço em tempo de execução, nunca ao iniciar o Django. |
| RNF24 | Limites por execução: chamadas ao modelo, chamadas de tools, itens por tool e tempo total (seção 14.18).                                            |
| RNF25 | Testes automatizados nunca chamam a API da OpenAI. O teste real é opcional, manual e exige variável própria (seção 14.17).                          |
| RNF26 | Prompts e descrições de transações não são registrados em logs. O rastreamento externo do LangSmith permanece desativado.                           |
| RNF27 | Código em inglês, PEP 8, aspas simples e 79 colunas. Textos da interface e das análises em português brasileiro.                                    |
| RNF28 | Valores monetários trafegam como `Decimal` no backend e como texto (`'1234.56'`) em JSON. Nunca como `float`.                                       |

### 14.5 Regras de negócio

| ID   | Regra                                                                                                                                                                                       |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| RN01 | O dono da análise é sempre `request.user`. Nenhum parâmetro do formulário ou do modelo define o usuário.                                                                                    |
| RN02 | Período analisado: de `period_start`, primeiro dia do mês `AI_ANALYSIS_WINDOW_MONTHS − 1` meses antes do atual, até `period_end`, a data local de hoje. Padrão de 6 meses.                  |
| RN03 | Transações com data futura ficam fora da análise, exceto no saldo das contas, que segue a regra de `Account.current_balance`.                                                               |
| RN04 | O mês corrente é parcial. Ele não pode ser comparado como se estivesse completo: comparações entre meses usam somente meses fechados, e tools sinalizam `is_partial_month`.                 |
| RN05 | Análise válida é aquela com `status = success`. Análises com falha nunca substituem a última válida no dashboard.                                                                           |
| RN06 | Análise desatualizada: `generated_at` com mais de `AI_ANALYSIS_STALE_DAYS` dias (padrão 30). Ela continua visível, com aviso.                                                               |
| RN07 | Análises finalizadas são imutáveis. Não há edição nem exclusão pela interface. A exclusão do usuário remove as análises dele (`CASCADE`).                                                   |
| RN08 | O limite diário conta todos os registros criados no dia local do usuário, inclusive com falha, pois podem ter consumido tokens. Dados insuficientes não criam registro nem consomem o limite. |
| RN09 | Recorrência é uma **heurística**: mesma descrição (sem diferenciar maiúsculas) e mesma categoria em pelo menos 3 meses distintos. O texto deve tratá-la como provável, nunca como certa.    |
| RN10 | "Aumento significativo" de categoria: variação de pelo menos 20% **e** R$ 50,00 entre dois meses fechados. Sem gasto no mês anterior, a variação percentual é nula e o texto usa o valor absoluto. |
| RN11 | O agente não pode recomendar ativos, corretoras ou produtos específicos, prometer rentabilidade, nem dar orientação jurídica ou tributária.                                                 |
| RN12 | Se os dados não sustentarem uma conclusão, o agente deve omiti-la e registrar o motivo em `data_limitations`.                                                                               |

Os limites de RN10 são parâmetros iniciais de produto, definidos em `ai/queries.py` como constantes, e podem ser ajustados sem migration.

### 14.6 Arquitetura proposta

Segue o padrão do projeto: Django full stack, Class Based Views e renderização no servidor. **O projeto não possui API REST, e esta funcionalidade não cria uma.** A integração acontece por CBVs e por chamadas Python a `ai.services`.

```mermaid
flowchart LR
    U[Usuário] -->|POST ai:create| V[ai/views.py]
    D[core DashboardView] -->|leitura| S
    V --> S[ai/services.py]
    S -->|cria e finaliza| M[(FinancialAnalysis)]
    S -->|invoke com AnalysisContext| A[ai/agent.py]
    A <-->|ChatOpenAI| O[API da OpenAI]
    A -->|tool calls| T[ai/tools.py]
    T --> Q[ai/queries.py]
    Q -->|ORM somente leitura, filtrado por user_id| DB[(Transaction, Account, Category)]
    S --> X[ai/validators.py]
```

| Arquivo                                    | Responsabilidade                                                                                        |
| ------------------------------------------ | ------------------------------------------------------------------------------------------------------- |
| `ai/models.py`                             | Model `FinancialAnalysis` e suas opções de status, erro e severidade.                                   |
| `ai/context.py`                            | `AnalysisContext`: dataclass imutável com os dados confiáveis da execução.                              |
| `ai/schemas.py`                            | Schemas Pydantic da saída estruturada.                                                                  |
| `ai/queries.py`                            | Funções puras de consulta. Todas recebem `user_id` como primeiro parâmetro. Testáveis sem LangChain.    |
| `ai/tools.py`                              | Tools `@tool`: leem `runtime.context`, validam os parâmetros, chamam `queries` e serializam o resultado. |
| `ai/prompts.py`                            | `SYSTEM_PROMPT` e `PROMPT_VERSION`.                                                                     |
| `ai/agent.py`                              | Cria `ChatOpenAI` e `create_agent`, com middlewares. Único módulo que monta o agente.                   |
| `ai/validators.py`                         | Valida as evidências da saída contra os resultados reais das tools.                                     |
| `ai/services.py`                           | Orquestra a geração, aplica os limites, trata erros e expõe as leituras para dashboard e views.         |
| `ai/views.py`, `ai/urls.py`, `ai/admin.py` | Criação por POST, histórico, detalhe e admin somente leitura.                                           |
| `ai/templates/ai/`                         | `analysis_list.html` e `analysis_detail.html`.                                                          |
| `templates/components/analysis_card.html`  | Card do Assistente no dashboard, com todos os estados.                                                  |
| `static/js/analysis_form.js`               | Estado de carregamento do botão, em JavaScript puro.                                                    |

**Decisão — execução síncrona:** a geração roda dentro do POST, limitada pelo orçamento de tempo da seção 14.18. O projeto não tem fila nem worker, e o PRD pede o mínimo necessário. Uma thread própria perderia execuções em reinícios e exigiria polling. O `django.tasks` do Django 6.1 só traz os backends `immediate` e `dummy`, que não executam em segundo plano. `generate_analysis()` não depende de `request`, portanto pode migrar para um worker sem alterar o agente (seção 14.18).

### 14.7 Integração com LangChain 1.0

**Pacotes:** `langchain` e `langchain-openai`, instalados e fixados na linha 1.x. Em 02/11/2026, as versões mais recentes são `langchain==1.4.8` e `langchain-openai==1.7.3`, ambas compatíveis com Python 3.12. O `langgraph` e o `pydantic` chegam como dependências do `langchain`.

| Necessidade        | API definida                                                                 | Observação                                                                 |
| ------------------ | ---------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| Agente             | `from langchain.agents import create_agent`                                  | Sem `checkpointer` e sem `store`: cada execução nasce sem memória.         |
| Tools              | `from langchain.tools import tool, ToolRuntime`                              | O parâmetro `runtime` fica oculto do modelo.                               |
| Dados confiáveis   | `context_schema=AnalysisContext` e `agent.invoke(..., context=...)`          | Lidos com `runtime.context`.                                               |
| Saída estruturada  | `from langchain.agents.structured_output import ToolStrategy`                | Resultado em `result['structured_response']`.                              |
| Limites            | `ModelCallLimitMiddleware`, `ToolCallLimitMiddleware`                        | Import de `langchain.agents.middleware`.                                   |
| Dados sensíveis    | `PIIMiddleware`                                                              | Com `apply_to_tool_results=True`.                                          |
| Orçamento de tempo | `before_model(can_jump_to=['end'])`                                          | Encerra a execução quando o prazo termina.                                 |
| Uso de tokens      | `from langchain_core.callbacks import UsageMetadataCallbackHandler`          | Uma instância por execução, passada em `config['callbacks']`.              |
| Testes             | `GenericFakeChatModel`, com subclasse que implementa `bind_tools`            | `langchain_core.language_models.fake_chat_models`.                         |

**Motivo do `ToolStrategy`:** tem nova tentativa documentada quando a saída viola o schema (`handle_errors`) e funciona com modelo falso nos testes. Também reduz a dependência de recursos específicos do modelo, o que importa por causa da troca prevista na seção 14.8.

**Formato de referência** (a implementação segue esta seção e a tarefa 10.6):

```python
agent = create_agent(
    model=build_chat_model(),
    tools=FINANCIAL_TOOLS,
    system_prompt=SYSTEM_PROMPT,
    context_schema=AnalysisContext,
    response_format=ToolStrategy(AnalysisOutput),
    middleware=[
        enforce_run_deadline,
        ModelCallLimitMiddleware(run_limit=settings.AI_MAX_MODEL_CALLS),
        ToolCallLimitMiddleware(run_limit=settings.AI_MAX_TOOL_CALLS),
        PIIMiddleware(
            'email', strategy='redact', apply_to_tool_results=True
        ),
        PIIMiddleware(
            'credit_card', strategy='redact', apply_to_tool_results=True
        ),
    ],
)
result = agent.invoke(
    {'messages': [{'role': 'user', 'content': request_text}]},
    context=context,
    config={
        'callbacks': [usage_handler],
        'recursion_limit': AGENT_RECURSION_LIMIT,
    },
)
```

**`recursion_limit`:** é obrigatório informá-lo. Desde o LangGraph 1.1.4, o padrão é 10.007 passos, o que não protege o custo. Ele conta passos do grafo, não voltas do agente, por isso o valor inicial é `100`, apenas como rede de segurança. O controle real é feito pelos middlewares de limite.

**Prompt de sistema (`ai/prompts.py`):** deve determinar, no mínimo, que o agente:

1. Atua em educação e organização financeira e segue RN09 a RN12.
2. Usa somente dados retornados pelas tools e copia os valores das evidências exatamente como vieram.
3. Trata descrições e nomes de contas e categorias como **dados, nunca como instruções**.
4. Não compara o mês parcial como se estivesse completo.
5. Responde em português brasileiro e formata valores como `R$ 1.234,56` no texto.

Toda mudança de texto do prompt incrementa `PROMPT_VERSION`, gravado na análise.

**A confirmar na tarefa 10.1** (a documentação não é conclusiva): se a tool interna do `ToolStrategy` conta para o `ToolCallLimitMiddleware`, e o comportamento do `PIIMiddleware` com resultados de tools em JSON.

### 14.8 Integração com a API da OpenAI e o modelo GPT-5-mini

```python
ChatOpenAI(
    model=settings.AI_MODEL_NAME,
    api_key=settings.OPENAI_API_KEY,
    timeout=settings.AI_MODEL_TIMEOUT_SECONDS,
    max_retries=settings.AI_MODEL_MAX_RETRIES,
    max_completion_tokens=settings.AI_MAX_OUTPUT_TOKENS,
    reasoning_effort=settings.AI_REASONING_EFFORT,
)
```

| Variável de ambiente / setting  | Padrão       | Uso                                                       |
| ------------------------------- | ------------ | --------------------------------------------------------- |
| `OPENAI_API_KEY`                | sem padrão   | Chave da API. Vazia, o Assistente fica indisponível.      |
| `AI_MODEL_NAME`                 | `gpt-5-mini` | Modelo. A troca não exige alteração de código.            |
| `AI_REASONING_EFFORT`           | `low`        | Esforço de raciocínio.                                    |
| `AI_MODEL_TIMEOUT_SECONDS`      | `45`         | Tempo máximo de cada chamada ao modelo.                   |
| `AI_MODEL_MAX_RETRIES`          | `1`          | Novas tentativas do cliente em erros temporários.         |
| `AI_MAX_OUTPUT_TOKENS`          | `4000`       | Limite de saída por chamada, incluindo raciocínio.        |

**Regras:**

- Não enviar `temperature`. O suporte nos modelos GPT-5 é inconsistente nas fontes consultadas, e a OpenAI não publica uma matriz clara.
- `reasoning_effort` exige `langchain-openai>=1.4.1`.
- Um `AI_MAX_OUTPUT_TOKENS` baixo pode gerar resposta vazia, porque o raciocínio consome tokens de saída. Resposta vazia é tratada como falha `invalid_output`.
- Não usar `ModelRetryMiddleware` junto com `max_retries`, para que as novas tentativas não se multipliquem.

> ⚠️ **Atenção — desligamento do modelo:** a OpenAI lista `gpt-5-mini` como **Deprecated**, com desligamento em **11/12/2026** e `gpt-5.6-terra` como substituto indicado. O modelo foi mantido como padrão porque é um requisito desta funcionalidade, mas a análise deixará de funcionar nessa data se nada mudar. A decisão de manter o modelo está registrada na seção 14.19 (item I-01). Por isso o modelo é configurável e a saída independe de recursos específicos dele.

### 14.9 Definição e responsabilidades das tools

**Regras comuns a todas as tools:**

- Somente leitura, via ORM. Sem SQL dinâmico e sem tool de escrita.
- **Nenhuma tool possui parâmetro de usuário.** O usuário vem de `runtime.context.user_id`.
- Datas devem estar dentro de `[context.period_start, context.period_end]`.
- Listas têm `limit` com máximo fixo. Os totais usam `aggregate`/`annotate`, sem carregar transações na memória.
- Valores são texto com duas casas (`'1234.56'`), após `quantize(Decimal('0.01'))`, pois o `Sum` no SQLite retorna valores sem o arredondamento do campo.
- Percentuais são texto com uma casa (`'12.5'`) ou `null`, quando não houver base de cálculo.

| Tool                       | Responsabilidade                                                     | Parâmetros do modelo                                               | Retorno                                                                                                                       |
| -------------------------- | -------------------------------------------------------------------- | ------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------- |
| `get_financial_summary`    | Comparar entradas e saídas em um período.                            | `start_date`, `end_date`                                           | `income_total`, `expense_total`, `net_result`, `savings_rate_percent`, `income_count`, `expense_count`                        |
| `get_monthly_evolution`    | Mostrar a evolução mês a mês, inclusive meses sem movimento.         | `months` (1 a `AI_ANALYSIS_WINDOW_MONTHS`)                         | Lista com `month`, `income_total`, `expense_total`, `net_result`, `expense_change_percent`, `is_partial_month`                |
| `get_category_breakdown`   | Mostrar a distribuição por categoria.                                | `start_date`, `end_date`, `transaction_type`, `limit` (1 a 20)     | Lista com `category_name`, `total`, `transaction_count`, `share_percent`; mais `others_total`                                 |
| `get_category_changes`     | Comparar saídas por categoria entre um mês fechado e o anterior.     | `month` (`AAAA-MM`), `limit` (1 a 20)                              | Lista com `category_name`, `current_total`, `previous_total`, `absolute_change`, `percent_change`, `is_significant`           |
| `get_recurring_expenses`   | Identificar gastos provavelmente recorrentes (RN09).                 | `limit` (1 a 10)                                                   | Lista com `description`, `category_name`, `distinct_months`, `average_amount`, `last_date`                                    |
| `get_largest_transactions` | Mostrar as maiores movimentações de um período.                      | `start_date`, `end_date`, `transaction_type`, `limit` (1 a 10)     | Lista com `date`, `description`, `amount`, `category_name`, `account_name`                                                    |
| `get_accounts_overview`    | Mostrar saldos atuais, usados nos alertas de desequilíbrio.          | nenhum                                                             | Lista com `account_name`, `account_type`, `current_balance`; mais `total_balance`                                             |

**Dados que nunca são enviados ao modelo:** nome, e-mail e telefone do usuário, `Account.bank_name`, identificadores internos (`id`, `user_id`), `Category.color`, senhas, tokens e dados de sessão.

**Validação dos parâmetros:**

1. Tipos e limites são declarados na assinatura, com `Annotated`, `Literal` e `pydantic.Field`. Erros desse tipo voltam ao modelo como erro de invocação, para correção.
2. Regras que dependem do contexto (como data fora do período, `start_date > end_date` ou `month` não fechado) levantam `ToolArgumentError`. A própria tool captura essa exceção e retorna `{'error': <código>, 'detail': <texto>}`.
3. **O retorno com `error` é necessário:** por padrão, o `ToolNode` só devolve ao modelo erros de argumento, e qualquer outra exceção interrompe a execução. Exceções inesperadas devem mesmo interromper e resultam em `internal_error`.

**Conexões de banco:** no caminho síncrono, o `ToolNode` executa as tools em um pool de threads. Como conexões Django são por thread, cada tool usa um decorator que chama `connection.close()` ao terminar, se estiver em uma thread diferente de `context.owner_thread_id`. Sem isso, as conexões das threads do pool não seriam fechadas de forma controlada.

### 14.10 Integração com o banco de dados

- Fontes: `transactions.Transaction`, `accounts.Account` e `categories.Category`, usando os relacionamentos existentes. **Nenhuma app existente tem o schema alterado.**
- Entradas e saídas não são tabelas separadas: ambas são `Transaction`, diferenciadas por `transaction_type`.
- O sistema não possui campos de recorrência, orçamento ou meta. Por isso a recorrência é inferida (RN09), e nenhuma análise pode citar orçamentos ou metas.
- `current_balance` não é armazenado. `get_accounts_overview` calcula o saldo em uma única consulta com `annotate` e `Sum`, evitando uma consulta por conta, e um teste garante resultado igual ao de `Account.current_balance`.
- `ATOMIC_REQUESTS` permanece desativado, como hoje. **Nenhuma transação de banco fica aberta durante a chamada ao modelo**, para não bloquear escritas no SQLite. A criação do registro `pending` e a finalização são gravações curtas e separadas.
- Limitação conhecida: `Lower` no SQLite só converte caracteres ASCII, então "AÇÃO" e "ação" não são agrupadas em `get_recurring_expenses`. O erro é aceito, pois só reduz a detecção da heurística.

### 14.11 Estrutura da tabela de análises

Model `ai.FinancialAnalysis`, herdando de `TimeStampedModel` (tabela `ai_financialanalysis`).

| Campo              | Tipo                                                         | Regra                                                                                 |
| ------------------ | ------------------------------------------------------------ | ------------------------------------------------------------------------------------- |
| `user`             | `ForeignKey(AUTH_USER_MODEL, CASCADE)`                       | `related_name='financial_analyses'`. Definido pelo backend.                           |
| `status`           | `CharField(20, choices)`                                     | `pending` (Em andamento), `success` (Concluída), `failed` (Falhou). Padrão `pending`. |
| `period_start`     | `DateField`                                                  | Início do período analisado (RN02).                                                   |
| `period_end`       | `DateField`                                                  | Fim do período analisado (RN02).                                                      |
| `generated_at`     | `DateTimeField(null=True, blank=True)`                       | Data e hora da conclusão com sucesso.                                                 |
| `finished_at`      | `DateTimeField(null=True, blank=True)`                       | Data e hora do término, com sucesso ou falha.                                         |
| `main_insight`     | `JSONField(default=dict)`                                    | Insight principal, no formato abaixo.                                                 |
| `insights`         | `JSONField(default=list)`                                    | Insights adicionais.                                                                  |
| `recommendations`  | `JSONField(default=list)`                                    | Dicas e recomendações.                                                                |
| `alerts`           | `JSONField(default=list)`                                    | Alertas, com severidade.                                                              |
| `data_limitations` | `JSONField(default=list)`                                    | Limitações dos dados e itens descartados na validação.                                |
| `metrics_snapshot` | `JSONField(default=dict)`                                    | Totais do período calculados pelo backend antes do agente, para auditoria.            |
| `tool_calls`       | `JSONField(default=list)`                                    | Nome e argumentos das tools chamadas, sem os resultados.                              |
| `model_name`       | `CharField(100)`                                             | Modelo usado na execução.                                                             |
| `prompt_version`   | `CharField(20)`                                              | Versão do prompt.                                                                     |
| `input_tokens`     | `PositiveIntegerField(default=0)`                            | Tokens de entrada.                                                                    |
| `output_tokens`    | `PositiveIntegerField(default=0)`                            | Tokens de saída.                                                                      |
| `total_tokens`     | `PositiveIntegerField(default=0)`                            | Total de tokens.                                                                      |
| `duration_ms`      | `PositiveIntegerField(null=True, blank=True)`                | Duração da execução.                                                                  |
| `error_code`       | `CharField(30, blank=True, choices)`                         | Código da seção 14.16.                                                                |
| `error_detail`     | `CharField(255, blank=True)`                                 | Somente a classe da exceção. Sem a mensagem, que poderia conter dados ou segredos.    |

`created_at` e `updated_at` vêm de `TimeStampedModel`. Os custos em dinheiro não são gravados, pois o preço muda: calcula-se a partir dos tokens e de `model_name`.

**`Meta`:**

```python
ordering = ['-created_at']
verbose_name = 'Análise financeira'
verbose_name_plural = 'Análises financeiras'
indexes = [
    models.Index(
        fields=['user', 'status', '-generated_at'],
        name='ai_analysis_user_status_idx',
    ),
]
constraints = [
    models.UniqueConstraint(
        fields=['user'],
        condition=models.Q(status='pending'),
        name='unique_pending_analysis_per_user',
    ),
]
```

**Formato dos itens JSON** (espelham `ai/schemas.py`):

```json
{
  "title": "Gastos com alimentação aumentaram",
  "description": "Em setembro, alimentação somou R$ 1.200,00...",
  "severity": "warning",
  "evidence": [
    {
      "label": "Alimentação em setembro",
      "value": "1200.00",
      "source_tool": "get_category_changes"
    }
  ]
}
```

| Schema           | Regras                                                                                                                                                                                                                 |
| ---------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `EvidenceItem`   | `label` (até 120 caracteres), `value` (texto), `source_tool` (`Literal` com os nomes das tools).                                                                                                                       |
| `Insight`        | `title` (até 120), `description` (até 500), `evidence` (1 a 5 itens).                                                                                                                                                  |
| `Recommendation` | Mesmos campos de `Insight`.                                                                                                                                                                                            |
| `Alert`          | Campos de `Insight` e `severity` (`info`, `warning` ou `critical`).                                                                                                                                                    |
| `AnalysisOutput` | `main_insight` (`Insight`), `insights` (0 a 4), `recommendations` (1 a 5), `alerts` (0 a 3), `data_limitations` (0 a 5 textos). Gravado com `model_dump(mode='json')`.                                                 |

```mermaid
erDiagram
    USER ||--o{ FINANCIAL_ANALYSIS : "possui"

    FINANCIAL_ANALYSIS {
        int id PK
        int user_id FK "on_delete=CASCADE"
        string status "pending | success | failed"
        date period_start
        date period_end
        datetime generated_at "nulo até o sucesso"
        datetime finished_at
        json main_insight
        json insights
        json recommendations
        json alerts
        json data_limitations
        json metrics_snapshot
        json tool_calls
        string model_name
        string prompt_version
        int input_tokens
        int output_tokens
        int total_tokens
        int duration_ms
        string error_code
        string error_detail
        datetime created_at
        datetime updated_at
    }
```

### 14.12 Isolamento e segurança dos dados dos usuários

**Contrato de identidade:**

```python
@dataclass(frozen=True)
class AnalysisContext:
    user_id: int
    period_start: date
    period_end: date
    deadline: float
    owner_thread_id: int
```

| Camada       | Controle                                                                                                                                  |
| ------------ | ----------------------------------------------------------------------------------------------------------------------------------------- |
| View         | `LoginRequiredMixin`. O usuário vem somente de `request.user`.                                                                            |
| Serviço      | `generate_analysis(user)` cria o registro e o `AnalysisContext`. A finalização é feita sempre sobre o mesmo registro `pending`.           |
| Tool         | Sem parâmetro de usuário. O `ToolNode` remove dos argumentos do modelo qualquer valor que tente forjar campos injetados.                  |
| Consulta     | Toda função de `ai/queries.py` filtra por `user_id`, que é parâmetro obrigatório e posicional. Um teste verifica todas as funções.        |
| Histórico    | `UserQuerySetMixin` nas views. Objeto de outro usuário resulta em 404.                                                                    |
| Concorrência | Sem `checkpointer`, `store`, `thread_id`, cache de modelo ou variável global mutável. O contexto é imutável, e o `invoke` recebe apenas mensagens novas. |

**Somente leitura:** não há tool de escrita nem SQL gerado pelo modelo. Apenas `ai/services.py` grava, e somente em `FinancialAnalysis`. Essa garantia é de código, não do banco: a mesma conexão SQLite é usada pela aplicação, e um usuário de banco separado não existe nesse cenário.

**Injeção de prompt:** descrição e nomes de contas e categorias são texto livre e chegam ao modelo. As mitigações são: tratar esses campos como dados no prompt, ausência de tools de escrita ou de parâmetro de usuário, validação das evidências e autoescape do DTL (é **proibido** usar `|safe` em conteúdo de análise). O pior caso é uma análise incorreta do próprio autor do texto, sem acesso a dados de terceiros.

**Privacidade:** dados financeiros do usuário são enviados a um provedor externo (OpenAI). Por isso:

- Só são enviados os dados necessários, com a exclusão da seção 14.9, e `PIIMiddleware` remove e-mails e números de cartão presentes nas descrições.
- A geração só ocorre por ação explícita do usuário, e o aviso junto ao botão informa o envio (seção 14.15).
- A base legal e os termos de uso (LGPD) precisam de decisão do responsável pelo produto (seção 14.19, item I-05).

**Admin:** `FinancialAnalysis` é somente leitura, sem inclusão ou edição. A permissão de exclusão é mantida, pois o admin bloquearia a exclusão de um usuário caso não pudesse excluir as análises vinculadas a ele.

### 14.13 Fluxo de execução do agente

```mermaid
sequenceDiagram
    actor U as Usuário
    participant V as AnalysisCreateView
    participant S as ai.services
    participant DB as Banco
    participant A as Agente (create_agent)
    participant O as OpenAI
    participant T as Tools

    U->>V: POST /ai/new/ (CSRF)
    V->>S: generate_analysis(request.user)
    S->>DB: Encerra pending antigos; verifica chave, dados e limites
    alt Bloqueado
        S-->>V: Resultado sem chamar o modelo
    else Permitido
        S->>DB: Cria registro pending com metrics_snapshot (commit)
        S->>A: invoke(messages, context=AnalysisContext)
        loop Até concluir ou atingir um limite
            A->>O: Chamada ao modelo
            O-->>A: Tool calls
            A->>T: Executa com runtime.context
            T->>DB: Consulta filtrada por user_id
            T-->>A: JSON limitado
        end
        O-->>A: AnalysisOutput
        A-->>S: structured_response e mensagens
        S->>S: Valida evidências
        S->>DB: Grava success ou failed (commit)
    end
    S-->>V: Resultado
    V-->>U: Redireciona ao dashboard com mensagem
```

Passos de `generate_analysis(user)`:

1. Marcar como `failed` (`abandoned`) os registros `pending` do usuário mais antigos que `AI_ANALYSIS_PENDING_TIMEOUT_MINUTES`.
2. Se não houver `OPENAI_API_KEY`, retornar `disabled`.
3. Calcular o período (RN02). Abaixo do mínimo de transações, retornar `insufficient_data`.
4. Se o limite diário foi atingido, retornar `limit_reached`.
5. Calcular `metrics_snapshot` e criar o registro `pending`. Em caso de `IntegrityError` na restrição única, retornar `already_running`.
6. Montar `AnalysisContext` e executar o agente, fora de transação de banco.
7. Sem `structured_response`, marcar `failed` com o código correspondente (`timeout` se o prazo terminou, senão `limit_exceeded`).
8. Validar as evidências (seção 14.16).
9. Gravar o resultado, os tokens, as tools chamadas e a duração. Retornar `success` ou `failed`.

O resultado é um enum `GenerationOutcome`, que a view converte na mensagem correspondente da seção 14.15.

**Validação de evidências (`ai/validators.py`):** cada `evidence.value` é normalizado e comparado aos valores retornados pela tool indicada em `source_tool` na mesma execução, lidos das `ToolMessage` de `result['messages']`.

- Se o `main_insight` tiver evidência não encontrada, a análise falha com `unverified_output`.
- Demais itens com evidência não encontrada são descartados, e o descarte é registrado em `data_limitations`.
- Se nenhuma recomendação restar, a análise falha com `unverified_output`.

**Limitação:** a validação cobre as evidências estruturadas, não cada número citado livremente em `description`. Para esse texto, a proteção é a instrução do prompt e o fato de o usuário ver as evidências ao lado.

### 14.14 Persistência e recuperação do histórico

| Rota                 | Nome        | View                                                     | Regra                                                  |
| -------------------- | ----------- | -------------------------------------------------------- | ------------------------------------------------------ |
| `ai/`                | `ai:list`   | `AnalysisListView(LoginRequiredMixin, UserQuerySetMixin, ListView)`     | Paginação de 20 itens, da mais recente à mais antiga.  |
| `ai/new/`            | `ai:create` | `AnalysisCreateView(LoginRequiredMixin, View)`           | Somente POST. GET retorna 405. Redireciona ao dashboard. |
| `ai/<int:pk>/`       | `ai:detail` | `AnalysisDetailView(LoginRequiredMixin, UserQuerySetMixin, DetailView)` | Objeto de outro usuário retorna 404.                   |

Leituras em `ai/services.py`:

- `get_latest_valid_analysis(user)`: última análise `success`, por `generated_at`.
- `get_dashboard_analysis_state(user)`: dados e estado do card do dashboard.

A rota `ai/new/` e o nome `ai:create` seguem o padrão das demais apps (`accounts:create`). Não há rotas de edição ou exclusão (RN07). A sidebar recebe o item **Assistente IA**, e o histórico mostra data, período, status e título do insight principal.

### 14.15 Integração com o dashboard

`DashboardView` adiciona `analysis_state` ao contexto, chamando `ai.services.get_dashboard_analysis_state(user)`, e nada mais muda em seus cálculos atuais. Em `templates/dashboard.html`, o card é incluído **entre o grid de KPIs e a seção de últimas transações**, ocupando a largura total.

**Conteúdo do card com análise válida:**

- Título **Assistente financeiro**, com "Período analisado: dd/mm/aaaa a dd/mm/aaaa" e "Última análise: dd/mm/aaaa às hh:mm".
- Insight principal em destaque, com as evidências abaixo do texto.
- Alertas com cor por severidade. Até 3 recomendações, com link **Ver análise completa** e link **Ver histórico**.
- Botão **Gerar nova análise** e o aviso educativo.

**Classes:** card de destaque (`rounded-2xl p-6 bg-gradient-to-br from-violet-600/30 via-indigo-600/20 to-cyan-500/10 border border-violet-500/30`) e botões da seção 9.4. Alertas: `info` usa `border-slate-700 bg-slate-800/60 text-slate-300`; `warning` usa `border-amber-500/30 bg-amber-500/10 text-amber-300`; `critical` usa o "Alerta erro" da seção 9.10.

| Estado               | Condição                                                  | Exibição                                                                                                                                  |
| -------------------- | --------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| Com análise          | Existe análise válida recente                             | Conteúdo acima.                                                                                                                           |
| Sem análise          | Nenhum registro `success`                                 | "Você ainda não tem análises. Gere a primeira para receber dicas sobre suas finanças." + botão.                                           |
| Carregando           | Clique no botão, durante o POST                           | `analysis_form.js` desativa o botão e mostra "Gerando análise... isso pode levar até 2 minutos." Sem JavaScript, o formulário funciona normalmente. |
| Em andamento         | `pending` mais recente que o tempo limite                 | "Há uma análise em andamento. Atualize a página em instantes." Botão desativado. Exibe a última válida, se houver.                        |
| Falha                | Última execução `failed`, mais recente que a última válida | Aviso "Não foi possível concluir a última análise." + botão. Mantém a última válida, se houver.                                          |
| Desatualizada        | RN06                                                      | Mantém a análise e mostra "Esta análise tem mais de 30 dias. Gere uma nova para refletir seus dados atuais."                              |
| Limite atingido      | Limite diário alcançado                                   | Botão desativado com "Você atingiu o limite de análises de hoje. Tente novamente amanhã."                                                 |
| Dados insuficientes  | Abaixo do mínimo de transações                            | "Registre pelo menos 5 transações para gerar uma análise." + link **Nova transação**.                                                     |
| Indisponível         | Sem `OPENAI_API_KEY`                                      | "O assistente não está disponível no momento." Sem botão. O restante do dashboard não muda.                                               |

Os números nos textos vêm dos settings, e não são escritos de forma fixa no template.

**Aviso educativo (RF45), fixo em todas as telas de análise:** "Conteúdo gerado por inteligência artificial, com caráter educativo, a partir dos seus lançamentos. Pode conter erros e não substitui orientação profissional nem constitui recomendação de investimento."

**Aviso junto ao botão:** "Ao gerar a análise, seus lançamentos financeiros são enviados à OpenAI para processamento. Nome, e-mail e telefone não são enviados."

**Mensagens (`django.contrib.messages`):**

| Resultado           | Tipo    | Texto                                                                   |
| ------------------- | ------- | ----------------------------------------------------------------------- |
| `success`           | sucesso | "Análise gerada com sucesso."                                           |
| `failed`            | erro    | "Não foi possível gerar a análise. Tente novamente mais tarde."         |
| `already_running`   | erro    | "Já existe uma análise em andamento."                                   |
| `limit_reached`     | erro    | "Você atingiu o limite de análises de hoje."                            |
| `insufficient_data` | erro    | "Ainda não há transações suficientes para gerar uma análise."           |
| `disabled`          | erro    | "O assistente não está disponível no momento."                          |

### 14.16 Tratamento de erros e situações excepcionais

Toda falha termina em um registro `failed`, com `error_code`, e em uma mensagem amigável. Detalhes técnicos nunca aparecem para o usuário, e o dashboard continua funcionando.

| `error_code`           | Situação                                                              | Origem                                                                     |
| ---------------------- | --------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| `authentication_error` | Chave inválida ou revogada.                                           | `openai.AuthenticationError`, `openai.PermissionDeniedError`               |
| `model_unavailable`    | Modelo inexistente ou desligado (risco real: item I-01).              | `openai.NotFoundError`                                                     |
| `rate_limited`         | Limite de uso ou cota esgotada.                                       | `openai.RateLimitError`                                                    |
| `timeout`              | Tempo esgotado em uma chamada ou no orçamento total.                  | `openai.APITimeoutError` ou `enforce_run_deadline`                         |
| `provider_unavailable` | Falha de conexão ou erro do servidor da OpenAI.                       | `openai.APIConnectionError`, `openai.InternalServerError`                  |
| `limit_exceeded`       | Limite de chamadas atingido sem saída final.                          | `GraphRecursionError` ou ausência de `structured_response`                 |
| `invalid_output`       | Saída vazia ou inválida após as tentativas do `ToolStrategy`.         | `StructuredOutputValidationError`, `MultipleStructuredOutputsError`        |
| `unverified_output`    | Evidências não conferem com os resultados das tools.                  | `ai/validators.py`                                                         |
| `abandoned`            | Processo interrompido com o registro em `pending`.                    | Passo 1 da seção 14.13                                                     |
| `internal_error`       | Qualquer outra exceção, inclusive erro de banco em uma tool.          | `except Exception`, registrado com `logger.exception`, sem dados da análise |

**Requisitos adicionais:**

- `generate_analysis` nunca propaga exceção do agente para a view.
- Se a gravação final falhar, o erro é registrado em log, e o registro `pending` é encerrado depois pelo passo 1.
- Editar ou excluir contas, categorias e transações depois da análise não altera o histórico: a análise guarda o próprio conteúdo em JSON e não tem chave estrangeira para esses registros.

### 14.17 Critérios de aceite

**US13 — Gerar análise**
Como usuário, quero solicitar uma análise das minhas finanças, para receber dicas baseadas nos meus dados.

- [ ] O botão envia POST com CSRF e, durante a geração, fica desativado com mensagem de carregamento.
- [ ] Após a geração, o usuário volta ao dashboard com mensagem de sucesso ou erro.
- [ ] Com poucos dados, o limite atingido ou uma análise em andamento, o modelo não é chamado.
- [ ] O registro guarda período, conteúdo, modelo, versão do prompt, tokens, duração e status.

**US14 — Ver a análise no dashboard**
Como usuário, quero ver minha última análise no dashboard, para entender rapidamente minha situação.

- [ ] O card mostra insight principal, recomendações, alertas, período e data da análise.
- [ ] Todos os estados da seção 14.15 são exibidos conforme especificado, nos três breakpoints.
- [ ] Uma falha não substitui a última análise válida.
- [ ] Abrir o dashboard não chama a OpenAI.

**US15 — Consultar o histórico**
Como usuário, quero rever análises anteriores, para acompanhar minha evolução.

- [ ] A lista é paginada e mostra apenas análises próprias, sem sobrescrever as antigas.
- [ ] Análise de outro usuário retorna 404.

**US16 — Confiar nos dados usados**
Como usuário, quero saber em que se baseia cada conclusão, e que meus dados são só meus.

- [ ] Cada item mostra evidências que conferem com os lançamentos.
- [ ] Toda análise exibe o aviso educativo e não recomenda produtos financeiros específicos.
- [ ] O modelo não consegue obter dados de outro usuário, mesmo enviando um `user_id` forjado na tool call.

**Critérios técnicos:**

- [ ] `manage.py test` passa sem `OPENAI_API_KEY` e sem acesso à internet.
- [ ] Testes cobrem isolamento, com execuções simultâneas de dois usuários, e todos os códigos de erro.
- [ ] Cobertura da app `ai` de pelo menos 80%, e `ruff check .` sem apontamentos.
- [ ] Nenhuma alteração em schemas ou regras das apps existentes.
- [ ] Teste real opcional com a API executado uma vez, e o resultado de tempo e tokens registrado na documentação técnica.

**Estratégia de testes:** `ai/queries.py` usa `TestCase`. Testes que executam o agente completo usam `TransactionTestCase`, pois as tools rodam em outras threads e não enxergam a transação aberta por `TestCase`. O modelo real é substituído por uma subclasse de `GenericFakeChatModel`. O teste real só é executado com `RUN_LIVE_AI_TESTS=True`.

### 14.18 Considerações de desempenho, custos e escalabilidade

| Setting                               | Padrão | Finalidade                                                     |
| ------------------------------------- | ------ | -------------------------------------------------------------- |
| `AI_ANALYSIS_WINDOW_MONTHS`           | `6`    | Tamanho do período analisado.                                  |
| `AI_ANALYSIS_MIN_TRANSACTIONS`        | `5`    | Mínimo de transações para chamar o modelo.                     |
| `AI_ANALYSIS_DAILY_LIMIT`             | `3`    | Análises por usuário ao dia.                                   |
| `AI_ANALYSIS_STALE_DAYS`              | `30`   | Dias até a análise ser considerada desatualizada.              |
| `AI_ANALYSIS_PENDING_TIMEOUT_MINUTES` | `5`    | Tempo até `pending` ser considerado abandonado.                |
| `AI_RUN_BUDGET_SECONDS`               | `120`  | Prazo checado antes de cada chamada ao modelo.                 |
| `AI_MAX_MODEL_CALLS`                  | `8`    | Chamadas ao modelo por execução.                               |
| `AI_MAX_TOOL_CALLS`                   | `10`   | Chamadas de tools por execução.                                |

**Tempo:** o prazo é checado antes de cada chamada. No pior caso, a última chamada começa perto de 120 s e dura mais 90 s (45 s × 2 tentativas), totalizando cerca de 210 s. Esse valor é inferior aos 5 minutos que definem `abandoned`.

**Custo:** preços oficiais do `gpt-5-mini` por 1 milhão de tokens: entrada US$ 0,25, entrada em cache US$ 0,025 e saída US$ 2,00.

| Cenário (**estimativa, a medir na tarefa 10.12**)                          | Custo aproximado      |
| -------------------------------------------------------------------------- | --------------------- |
| Uma análise, com 20 mil tokens de entrada e 3 mil de saída no total        | US$ 0,011             |
| Um usuário no limite diário por 30 dias (90 análises)                      | US$ 1,00 por mês      |

Medidas de contenção: tools com retorno agregado e limitado, limites por execução e por dia, nenhuma chamada no dashboard, modelo econômico com `reasoning_effort` baixo e tokens gravados em toda execução. O preço do modelo substituto (item I-01) deve ser verificado antes da troca.

**Escalabilidade:**

- Cada geração ocupa uma thread do servidor por até cerca de 210 s. Isso é adequado ao porte atual, mas o `runserver` usado no Docker não é um servidor de produção (limitação já registrada no projeto).
- O caminho de evolução, **somente se houver necessidade real**, é mover `generate_analysis` para um worker, usando o estado `pending` já existente. Os itens que exigiriam mudança são a view e o estado de carregamento; agente, tools e model continuam iguais.
- O SQLite segue adequado, pois as gravações são curtas e nenhuma transação fica aberta durante a chamada ao modelo.
- O crescimento da tabela é baixo: até 3 registros por usuário ao dia, com índice em `(user, status, -generated_at)`. Uma política de retenção pode ser avaliada depois.

### 14.19 Inconsistências, exceções e decisões em aberto

| ID   | Situação encontrada                                                                                                     | Tratamento nesta especificação                                                                                                                                         | Status                 |
| ---- | ----------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------- |
| I-01 | `gpt-5-mini` é requisito, mas está **Deprecated**, com desligamento em 11/12/2026.                                      | Mantido como padrão, configurável por `AI_MODEL_NAME`. A troca precisa ocorrer até 11/12/2026, e o preço de `gpt-5.6-terra` deve ser verificado antes dela. | **Decidido em 02/11/2026:** manter `gpt-5-mini` |
| I-02 | O pedido cita "LangChain 1.0", e a versão atual é 1.4.8.                                                                | Interpretado como a linha 1.x, pois `reasoning_effort` exige versões posteriores à 1.0 no `langchain-openai`. Fixar a versão com `pip freeze`.                          | Recomendação aplicada  |
| I-03 | O PRD (seções 1 e 12) e o `CLAUDE.md` pedem apenas recursos nativos, sem bibliotecas extras.                            | Exceção restrita a `langchain` e `langchain-openai`, solicitados para esta funcionalidade. O `CLAUDE.md` deve registrá-la na implementação (tarefa 10.14).              | Exceção documentada    |
| I-04 | O pedido cita integração com "APIs existentes", mas o projeto não possui API.                                           | Integração por CBVs e `ai.services`, sem criar API REST.                                                                                                               | Recomendação aplicada  |
| I-05 | Dados financeiros passam a ser enviados a um terceiro, e o projeto não possui termos de uso nem política de privacidade. | Minimização de dados e aviso junto ao botão. A adequação à LGPD, a retenção de dados na OpenAI e a eventual necessidade de consentimento registrado não foram definidas. | **Decisão do responsável** |
| I-06 | Pede-se estado de carregamento, mas não há fila nem worker.                                                             | Execução síncrona (seção 14.6). A alternativa é uma fila, que exigiria nova dependência.                                                                               | Recomendação aplicada  |
| I-07 | Os parâmetros da seção 14.18, RN02 e RN10 não foram definidos no pedido.                                                | Valores iniciais definidos aqui, todos ajustáveis.                                                                                                                     | Validar com o responsável |
| I-08 | A seção 8 cita Django 5.x e não lista a app `ai`. O projeto usa Django 6.1.2.                                           | Seções existentes preservadas, conforme pedido. Vale a versão de `requirements.txt`.                                                                                   | Registrado             |
| I-09 | `CLAUDE.md`, `agents/` e `docs/` citam "PRD, seção 13" e o `CLAUDE.md` descreve o projeto como na Sprint 0.             | Fora do escopo desta etapa. As tarefas vivem no `TASKS.md`. Atualizar na tarefa 10.14.                                                                                 | Registrado             |

---

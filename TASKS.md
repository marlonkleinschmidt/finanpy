## Lista de tarefas

> Marque com `X` (`[X]`) cada subtarefa concluída. Uma tarefa só é marcada como concluída quando todas as suas subtarefas estiverem marcadas.

---

### [x] Sprint 0 — Setup do projeto

- [x] **0.1 Criar ambiente do projeto**
  - [x] 0.1.1 Criar a pasta raiz `finanpy` e inicializar repositório Git.
  - [x] 0.1.2 Criar ambiente virtual (`python -m venv venv`) e ativá-lo.
  - [x] 0.1.3 Instalar Django (`pip install django`).
  - [x] 0.1.4 Gerar `requirements.txt` com `pip freeze > requirements.txt`.
  - [x] 0.1.5 Criar `.gitignore` ignorando `venv/`, `__pycache__/`, `*.pyc`, `db.sqlite3`, `.env` e `static/css/output.css` (caso gerado no deploy).

- [x] **0.2 Criar projeto Django**
  - [x] 0.2.1 Executar `django-admin startproject core .` para criar a pasta `core` com settings, urls, asgi e wsgi.
  - [x] 0.2.2 Validar com `python manage.py runserver` que a página padrão do Django abre.

- [x] **0.3 Criar as apps**
  - [x] 0.3.1 `python manage.py startapp users`.
  - [x] 0.3.2 `python manage.py startapp profiles`.
  - [x] 0.3.3 `python manage.py startapp accounts`.
  - [x] 0.3.4 `python manage.py startapp categories`.
  - [x] 0.3.5 `python manage.py startapp transactions`.
  - [x] 0.3.6 Registrar todas as apps em `INSTALLED_APPS` em `core/settings.py`.
  - [x] 0.3.7 Adicionar `django.contrib.humanize` em `INSTALLED_APPS`.

- [x] **0.4 Configurar settings globais e variáveis de ambiente**
  - [x] 0.4.1 Criar o arquivo `.env` na raiz do projeto com `SECRET_KEY`, `DEBUG` e `ALLOWED_HOSTS` (já ignorado pelo `.gitignore`).
  - [x] 0.4.2 Criar `.env.example` versionado, com as mesmas variáveis e sem segredos.
  - [x] 0.4.3 Carregar o `.env` em `core/settings.py` apenas com a biblioteca padrão (`os.environ`), sem dependências novas, dividindo cada linha só no primeiro `=` e sem sobrescrever variáveis já definidas no ambiente.
  - [x] 0.4.4 Mover `SECRET_KEY` para o `.env`, sem valor padrão no código, gerando uma nova chave com `get_random_secret_key()` (a atual já está no histórico do Git).
  - [x] 0.4.5 Configurar `DEBUG` por variável de ambiente, com padrão `False` (`os.environ.get('DEBUG', 'False') == 'True'`).
  - [x] 0.4.6 Configurar `ALLOWED_HOSTS` por variável de ambiente, separada por vírgulas (`localhost,127.0.0.1` em desenvolvimento).
  - [x] 0.4.7 Criar `pyproject.toml` com a configuração de aspas simples do ruff (`[tool.ruff.lint.flake8-quotes] inline-quotes = 'single'` e `[tool.ruff.format] quote-style = 'single'`).
  - [x] 0.4.8 Definir `LANGUAGE_CODE = 'pt-br'`.
  - [x] 0.4.9 Definir `TIME_ZONE = 'America/Sao_Paulo'`.
  - [x] 0.4.10 Definir `USE_I18N = True`.
  - [x] 0.4.11 Definir `USE_TZ = True`.
  - [x] 0.4.12 Configurar `TEMPLATES['DIRS'] = [BASE_DIR / 'templates']`.
  - [x] 0.4.13 Configurar `STATIC_URL = 'static/'` e `STATICFILES_DIRS = [BASE_DIR / 'static']`.
  - [x] 0.4.14 Confirmar banco SQLite padrão em `DATABASES`.
  - [x] 0.4.15 Criar as pastas `templates/`, `templates/components/` e `static/css/`.
  - [x] 0.4.16 Revisar `settings.py` garantindo aspas simples e PEP 8.
  - [x] 0.4.17 Atualizar `docs/setup.md` com o passo de copiar `.env.example` para `.env` antes de rodar o projeto.

- [x] **0.5 Ferramentas de padronização de código**
  - [x] 0.5.1 Instalar `ruff` como dependência de desenvolvimento.
  - [x] 0.5.2 Completar o `pyproject.toml` criado na tarefa 0.4.7 com as regras do ruff (`Q`, line-length 79, PEP 8).
  - [x] 0.5.3 Executar `ruff check .` e corrigir os apontamentos do código gerado.

---

### Sprint 1 — Usuário customizado e autenticação

- [x] **1.1 Criar model base com timestamps**
  - [x] 1.1.1 Decidir local do model abstrato `TimeStampedModel` (`core/models.py`).
  - [x] 1.1.2 Implementar `TimeStampedModel` com `created_at = DateTimeField(auto_now_add=True)` e `updated_at = DateTimeField(auto_now=True)`, `class Meta: abstract = True`.
  - [x] 1.1.3 Definir `verbose_name` em português para os campos (`'Criado em'`, `'Atualizado em'`).

- [x] **1.2 Criar model `User` customizado**
  - [x] 1.2.1 Em `users/models.py`, criar `UserManager(BaseUserManager)` com `create_user(email, password, **extra_fields)` normalizando o e-mail.
  - [x] 1.2.2 Implementar `create_superuser` definindo `is_staff` e `is_superuser` como `True`.
  - [x] 1.2.3 Criar `User(AbstractUser, TimeStampedModel)` com `username = None`.
  - [x] 1.2.4 Definir `email = models.EmailField('E-mail', unique=True)`.
  - [x] 1.2.5 Definir `USERNAME_FIELD = 'email'` e `REQUIRED_FIELDS = ['first_name', 'last_name']`.
  - [x] 1.2.6 Atribuir `objects = UserManager()`.
  - [x] 1.2.7 Implementar `__str__` retornando o e-mail e `verbose_name` em português.
  - [x] 1.2.8 Definir `AUTH_USER_MODEL = 'users.User'` no settings.

- [x] **1.3 Primeiras migrations**
  - [x] 1.3.1 Executar `python manage.py makemigrations users`.
  - [x] 1.3.2 Executar `python manage.py migrate`.
  - [x] 1.3.3 Criar superusuário com `createsuperuser` e confirmar que o prompt pede e-mail.

- [x] **1.4 Admin de usuários**
  - [x] 1.4.1 Em `users/admin.py`, criar `UserAdmin` herdando de `django.contrib.auth.admin.UserAdmin`.
  - [x] 1.4.2 Ajustar `ordering`, `list_display` (`email`, `first_name`, `last_name`, `is_staff`) e `search_fields` sem `username`.
  - [x] 1.4.3 Ajustar `fieldsets` e `add_fieldsets` substituindo `username` por `email`.
  - [x] 1.4.4 Validar login no `/admin/` com e-mail.

- [x] **1.5 Formulários de autenticação**
  - [x] 1.5.1 Criar `users/forms.py`.
  - [x] 1.5.2 Criar `SignUpForm(UserCreationForm)` com `Meta.model = User` e `fields = ('first_name', 'last_name', 'email')`.
  - [x] 1.5.3 Definir labels em português para todos os campos.
  - [x] 1.5.4 Criar `EmailAuthenticationForm(AuthenticationForm)` com label do campo `username` como `'E-mail'` e widget `EmailInput`.
  - [x] 1.5.5 Personalizar mensagem `invalid_login` para `'E-mail ou senha inválidos.'`.

- [x] **1.6 Views de autenticação**
  - [x] 1.6.1 Criar `SignUpView(CreateView)` com `form_class = SignUpForm` e `template_name = 'users/signup.html'`.
  - [x] 1.6.2 Sobrescrever `form_valid` para salvar o usuário e chamar `login(self.request, user)`.
  - [x] 1.6.3 Redirecionar para o dashboard (`success_url = reverse_lazy('dashboard')`).
  - [x] 1.6.4 Redirecionar usuário já autenticado que acessar o cadastro para o dashboard (sobrescrever `dispatch`).
  - [x] 1.6.5 Criar `SignInView(LoginView)` com `authentication_form = EmailAuthenticationForm`, `template_name = 'users/login.html'` e `redirect_authenticated_user = True`.
  - [x] 1.6.6 Usar `LogoutView` nativa.

- [x] **1.7 URLs e settings de autenticação**
  - [x] 1.7.1 Criar `users/urls.py` com rotas `signup/`, `login/` e `logout/` (names: `signup`, `login`, `logout`).
  - [x] 1.7.2 Incluir `users.urls` em `core/urls.py`.
  - [x] 1.7.3 Definir `LOGIN_URL = 'login'`, `LOGIN_REDIRECT_URL = 'dashboard'` e `LOGOUT_REDIRECT_URL = 'home'`.

- [x] **1.8 Templates provisórios de autenticação**
  - [x] 1.8.1 Criar `users/templates/users/signup.html` com formulário simples (será estilizado na Sprint 2).
  - [x] 1.8.2 Criar `users/templates/users/login.html` com formulário simples.
  - [x] 1.8.3 Testar manualmente cadastro, login com e-mail e logout.

---

### [x] Sprint 2 — Design system, layout base e landing page

- [x] **2.1 Instalar TailwindCSS**
  - [x] 2.1.1 Baixar o executável standalone do Tailwind CLI para a plataforma de desenvolvimento.
  - [x] 2.1.2 Criar `static/css/input.css` com `@import 'tailwindcss';`.
  - [x] 2.1.3 Configurar `@source` para varrer `templates/**/*.html` e `*/templates/**/*.html` (e `*/forms.py`, onde ficam classes de widgets).
  - [x] 2.1.4 Definir no `@theme` a fonte `--font-sans: 'Inter', ui-sans-serif, system-ui, sans-serif`.
  - [x] 2.1.5 Gerar `static/css/output.css` com `tailwindcss -i static/css/input.css -o static/css/output.css --watch`.
  - [x] 2.1.6 Documentar os comandos de build (dev com `--watch` e produção com `--minify`) no `README.md`.

- [x] **2.2 Template base**
  - [x] 2.2.1 Criar `templates/base.html` com `<!DOCTYPE html>`, `lang="pt-br"`, meta viewport e charset.
  - [x] 2.2.2 Carregar `{% load static %}` e o `output.css`.
  - [x] 2.2.3 Incluir a fonte Inter via Google Fonts.
  - [x] 2.2.4 Aplicar no `body`: `bg-slate-950 text-slate-100 font-sans antialiased min-h-screen`.
  - [x] 2.2.5 Criar blocos `{% block title %}`, `{% block content %}` e `{% block extra_js %}`.
  - [x] 2.2.6 Incluir `components/messages.html`.

- [x] **2.3 Componentes reutilizáveis**
  - [x] 2.3.1 Criar `components/messages.html` com alertas de sucesso/erro/aviso conforme `message.tags`.
  - [x] 2.3.2 Criar `components/form_field.html` renderizando label, campo, erros e help_text.
  - [x] 2.3.3 Criar `components/page_header.html` recebendo `title` e, opcionalmente, `action_url` e `action_label`.
  - [x] 2.3.4 Criar `components/empty_state.html` recebendo mensagem, url e texto do botão.
  - [x] 2.3.5 Criar `components/pagination.html` preservando parâmetros GET da URL.
  - [x] 2.3.6 Criar `components/confirm_delete.html` com card de confirmação, botão perigo e botão cancelar.
  - [x] 2.3.7 Criar `components/kpi_card.html` recebendo título, valor e variante de cor.

- [x] **2.4 Classes de widgets dos forms**
  - [x] 2.4.1 Criar `core/forms.py` com constante `INPUT_CLASSES` contendo as classes padrão de input.
  - [x] 2.4.2 Criar `StyledFormMixin` que, no `__init__`, aplica `INPUT_CLASSES` em todos os widgets do form.
  - [x] 2.4.3 Tratar checkbox e input de cor com classes específicas no mixin.
  - [x] 2.4.4 Aplicar o mixin em `SignUpForm` e `EmailAuthenticationForm`.

- [x] **2.5 Navbar pública**
  - [x] 2.5.1 Criar `components/navbar_public.html` com logo "Finanpy" em gradiente de texto.
  - [x] 2.5.2 Exibir **Entrar** e **Cadastre-se** para visitantes.
  - [x] 2.5.3 Exibir **Ir para o dashboard** para usuários autenticados.
  - [x] 2.5.4 Garantir comportamento responsivo (botões compactos no mobile).

- [x] **2.6 Layout autenticado**
  - [x] 2.6.1 Criar `templates/base_auth.html` estendendo `base.html`.
  - [x] 2.6.2 Criar `components/sidebar.html` com links Dashboard, Contas, Categorias, Transações e Perfil.
  - [x] 2.6.3 Destacar o item ativo comparando `request.resolver_match.app_name`/`url_name`.
  - [x] 2.6.4 Adicionar botão **Sair** como formulário POST com `{% csrf_token %}`.
  - [x] 2.6.5 Exibir nome e e-mail do usuário logado no rodapé da sidebar.
  - [x] 2.6.6 Criar topbar mobile com botão hambúrguer.
  - [x] 2.6.7 Implementar toggle da sidebar no mobile com JavaScript puro (poucas linhas, em `{% block extra_js %}` ou `static/js/sidebar.js`).
  - [x] 2.6.8 Aplicar container padrão de conteúdo (`max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6`).

- [x] **2.7 Landing page**
  - [x] 2.7.1 Criar `HomeView(TemplateView)` em `core/views.py` com `template_name = 'home.html'`.
  - [x] 2.7.2 Registrar rota `''` com name `home` em `core/urls.py`.
  - [x] 2.7.3 Criar `templates/home.html` estendendo `base.html` com a navbar pública.
  - [x] 2.7.4 Implementar seção hero com fundo em gradiente, título em gradiente de texto, subtítulo e botões **Cadastre-se** e **Entrar**.
  - [x] 2.7.5 Implementar seção de benefícios com 3 cards (Contas, Categorias, Dashboard).
  - [x] 2.7.6 Implementar rodapé simples com nome do produto e ano.
  - [x] 2.7.7 Validar responsividade em 375px, 768px e 1280px.

- [x] **2.8 Estilizar telas de autenticação**
  - [x] 2.8.1 Reescrever `users/signup.html` com card centralizado, logo, título "Crie sua conta" e campos via `form_field.html`.
  - [x] 2.8.2 Adicionar link "Já tem conta? Entrar" no cadastro.
  - [x] 2.8.3 Reescrever `users/login.html` com card centralizado e título "Entrar no Finanpy".
  - [x] 2.8.4 Adicionar link "Ainda não tem conta? Cadastre-se" no login.
  - [x] 2.8.5 Exibir erros não vinculados a campos (`form.non_field_errors`) com alerta de erro.

---

### [x] Sprint 3 — Perfil

- [x] **3.1 Model `Profile`**
  - [x] 3.1.1 Em `profiles/models.py`, criar `Profile(TimeStampedModel)`.
  - [x] 3.1.2 Adicionar `user = OneToOneField(settings.AUTH_USER_MODEL, on_delete=CASCADE, related_name='profile')`.
  - [x] 3.1.3 Adicionar `phone = CharField('Telefone', max_length=20, blank=True)`.
  - [x] 3.1.4 Implementar `__str__` e `verbose_name` em português.
  - [x] 3.1.5 Gerar e aplicar migration.

- [x] **3.2 Signal de criação de perfil**
  - [x] 3.2.1 Criar `profiles/signals.py` com receiver `post_save` do `User`.
  - [x] 3.2.2 Criar o `Profile` quando `created` for `True`.
  - [x] 3.2.3 Registrar os signals no método `ready()` de `ProfilesConfig` em `profiles/apps.py`.
  - [x] 3.2.4 Testar manualmente: cadastrar usuário e verificar perfil criado no admin.
  - [x] 3.2.5 Criar perfis para usuários já existentes (ex.: superusuário) via shell ou migration de dados simples.

- [x] **3.3 Admin de perfil**
  - [x] 3.3.1 Registrar `Profile` no admin com `list_display` (`user`, `phone`, `created_at`).

- [x] **3.4 Edição de perfil**
  - [x] 3.4.1 Criar `profiles/forms.py` com `UserUpdateForm` (first_name, last_name) e `ProfileForm` (phone), ambos com `StyledFormMixin`.
  - [x] 3.4.2 Criar `ProfileUpdateView(LoginRequiredMixin, UpdateView)` baseada em `Profile`, com `get_object` retornando `self.request.user.profile`.
  - [x] 3.4.3 Incluir o `UserUpdateForm` no contexto e salvá-lo junto no `post`/`form_valid`.
  - [x] 3.4.4 Exibir mensagem "Perfil atualizado com sucesso." (`SuccessMessageMixin`).
  - [x] 3.4.5 Criar `profiles/urls.py` com rota `profile/` (name `profile`) e incluir no `core/urls.py`.
  - [x] 3.4.6 Criar template `profiles/profile_form.html` estendendo `base_auth.html`, com e-mail exibido somente leitura.

---

### [x] Sprint 4 — Contas bancárias

- [x] **4.1 Mixin de isolamento por usuário**
  - [x] 4.1.1 Criar em `core/mixins.py` o `UserQuerySetMixin` que filtra `get_queryset()` por `user=self.request.user`.
  - [x] 4.1.2 Criar `UserFormMixin` que atribui `form.instance.user = self.request.user` no `form_valid`.

- [x] **4.2 Model `Account`**
  - [x] 4.2.1 Criar `Account(TimeStampedModel)` com `user` (FK, `related_name='accounts'`).
  - [x] 4.2.2 Adicionar `name = CharField('Nome', max_length=100)`.
  - [x] 4.2.3 Adicionar `bank_name = CharField('Banco', max_length=100, blank=True)`.
  - [x] 4.2.4 Criar `AccountType(TextChoices)` com `CHECKING='checking', 'Conta corrente'`, `SAVINGS='savings', 'Poupança'`, `WALLET='wallet', 'Carteira'`, `INVESTMENT='investment', 'Investimento'`.
  - [x] 4.2.5 Adicionar `account_type = CharField('Tipo', choices=AccountType.choices, default=AccountType.CHECKING)`.
  - [x] 4.2.6 Adicionar `initial_balance = DecimalField('Saldo inicial', max_digits=12, decimal_places=2, default=0)`.
  - [x] 4.2.7 Definir `Meta.ordering = ['name']` e `verbose_name` em português.
  - [x] 4.2.8 Implementar `__str__` retornando o nome.
  - [x] 4.2.9 Gerar e aplicar migration.

- [x] **4.3 Admin de contas**
  - [x] 4.3.1 Registrar `Account` com `list_display`, `list_filter` (`account_type`) e `search_fields` (`name`, `bank_name`).

- [x] **4.4 Formulário de conta**
  - [x] 4.4.1 Criar `accounts/forms.py` com `AccountForm(StyledFormMixin, ModelForm)` e campos `name`, `bank_name`, `account_type`, `initial_balance`.

- [x] **4.5 Views de contas**
  - [x] 4.5.1 `AccountListView(LoginRequiredMixin, UserQuerySetMixin, ListView)`.
  - [x] 4.5.2 `AccountCreateView(LoginRequiredMixin, UserFormMixin, SuccessMessageMixin, CreateView)` com mensagem "Conta criada com sucesso."
  - [x] 4.5.3 `AccountUpdateView(LoginRequiredMixin, UserQuerySetMixin, SuccessMessageMixin, UpdateView)` com mensagem "Conta atualizada com sucesso."
  - [x] 4.5.4 `AccountDeleteView(LoginRequiredMixin, UserQuerySetMixin, DeleteView)` com mensagem de sucesso.
  - [x] 4.5.5 Definir `success_url = reverse_lazy('accounts:list')` nas views de criação, edição e exclusão.

- [x] **4.6 URLs de contas**
  - [x] 4.6.1 Criar `accounts/urls.py` com `app_name = 'accounts'`.
  - [x] 4.6.2 Rotas: `''` (list), `new/` (create), `<int:pk>/edit/` (update), `<int:pk>/delete/` (delete).
  - [x] 4.6.3 Incluir em `core/urls.py` com prefixo `accounts/`.

- [x] **4.7 Templates de contas**
  - [x] 4.7.1 `accounts/account_list.html`: page header com botão "Nova conta", tabela (desktop) e cards (mobile).
  - [x] 4.7.2 Exibir colunas Nome, Banco, Tipo (`get_account_type_display`), Saldo inicial e ações.
  - [x] 4.7.3 Exibir estado vazio quando não houver contas.
  - [x] 4.7.4 `accounts/account_form.html` reutilizado para criar/editar, com título dinâmico ("Nova conta" / "Editar conta").
  - [x] 4.7.5 `accounts/account_confirm_delete.html` usando o componente de confirmação.
  - [x] 4.7.6 Adicionar link "Contas" funcional na sidebar.

---

### [x] Sprint 5 — Categorias

- [x] **5.1 Model `Category`**
  - [x] 5.1.1 Criar `Category(TimeStampedModel)` com `user` (FK, `related_name='categories'`).
  - [x] 5.1.2 Adicionar `name = CharField('Nome', max_length=100)`.
  - [x] 5.1.3 Criar `CategoryType(TextChoices)` com `INCOME='income', 'Entrada'` e `EXPENSE='expense', 'Saída'`.
  - [x] 5.1.4 Adicionar `category_type = CharField('Tipo', choices=CategoryType.choices)`.
  - [x] 5.1.5 Adicionar `color = CharField('Cor', max_length=7, default='#8B5CF6')`.
  - [x] 5.1.6 Adicionar `UniqueConstraint(fields=['user', 'name', 'category_type'], name='unique_category_per_user')`.
  - [x] 5.1.7 Definir `Meta.ordering = ['category_type', 'name']` e `verbose_name` em português.
  - [x] 5.1.8 Gerar e aplicar migration.

- [x] **5.2 Admin de categorias**
  - [x] 5.2.1 Registrar `Category` com `list_display` (`name`, `category_type`, `user`) e `list_filter`.

- [x] **5.3 Formulário de categoria**
  - [x] 5.3.1 Criar `CategoryForm(StyledFormMixin, ModelForm)` com campos `name`, `category_type`, `color`.
  - [x] 5.3.2 Usar widget `TextInput(attrs={'type': 'color'})` para o campo cor.
  - [x] 5.3.3 Receber `user` no `__init__` e validar duplicidade de nome + tipo no `clean`, com mensagem "Você já possui uma categoria com este nome e tipo."
  - [x] 5.3.4 Passar `user` via `get_form_kwargs` nas views.

- [x] **5.4 Views de categorias**
  - [x] 5.4.1 `CategoryListView` com mixins de login e isolamento.
  - [x] 5.4.2 `CategoryCreateView` com mensagem "Categoria criada com sucesso."
  - [x] 5.4.3 `CategoryUpdateView` com mensagem "Categoria atualizada com sucesso."
  - [x] 5.4.4 `CategoryDeleteView` com mensagem de sucesso.

- [x] **5.5 URLs de categorias**
  - [x] 5.5.1 Criar `categories/urls.py` com `app_name = 'categories'` e rotas list/new/edit/delete.
  - [x] 5.5.2 Incluir em `core/urls.py` com prefixo `categories/`.

- [x] **5.6 Templates de categorias**
  - [x] 5.6.1 `categories/category_list.html` exibindo duas seções: "Entradas" e "Saídas".
  - [x] 5.6.2 Exibir bolinha com a cor da categoria, nome, badge de tipo e ações.
  - [x] 5.6.3 Exibir estado vazio quando não houver categorias.
  - [x] 5.6.4 `categories/category_form.html` com título dinâmico.
  - [x] 5.6.5 `categories/category_confirm_delete.html` usando o componente de confirmação.
  - [x] 5.6.6 Adicionar link "Categorias" funcional na sidebar.

---

### [x] Sprint 6 — Transações

- [x] **6.1 Model `Transaction`**
  - [x] 6.1.1 Criar `Transaction(TimeStampedModel)` com `user` (FK, `related_name='transactions'`).
  - [x] 6.1.2 Criar `TransactionType(TextChoices)` com `INCOME='income', 'Entrada'` e `EXPENSE='expense', 'Saída'`.
  - [x] 6.1.3 Adicionar `transaction_type = CharField('Tipo', choices=TransactionType.choices)`.
  - [x] 6.1.4 Adicionar `amount = DecimalField('Valor', max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])`.
  - [x] 6.1.5 Adicionar `date = DateField('Data', default=timezone.localdate)`.
  - [x] 6.1.6 Adicionar `description = CharField('Descrição', max_length=255)`.
  - [x] 6.1.7 Adicionar `account = ForeignKey('accounts.Account', on_delete=PROTECT, related_name='transactions')`.
  - [x] 6.1.8 Adicionar `category = ForeignKey('categories.Category', on_delete=PROTECT, related_name='transactions')`.
  - [x] 6.1.9 Definir `Meta.ordering = ['-date', '-created_at']` e `verbose_name` em português.
  - [x] 6.1.10 Gerar e aplicar migration.

- [x] **6.2 Saldo atual da conta**
  - [x] 6.2.1 Adicionar em `Account` a propriedade `current_balance` usando `aggregate(Sum)` das transações de entrada e de saída.
  - [x] 6.2.2 Tratar `None` do `aggregate` como `Decimal('0')`.
  - [x] 6.2.3 Exibir a coluna "Saldo atual" na listagem de contas.

- [x] **6.3 Proteção de exclusão**
  - [x] 6.3.1 No `AccountDeleteView`, sobrescrever `form_valid` capturando `ProtectedError` e exibindo "Esta conta possui transações e não pode ser excluída."
  - [x] 6.3.2 No `CategoryDeleteView`, capturar `ProtectedError` e exibir "Esta categoria possui transações e não pode ser excluída."
  - [x] 6.3.3 Redirecionar para a listagem após o erro.

- [x] **6.4 Admin de transações**
  - [x] 6.4.1 Registrar `Transaction` com `list_display` (`date`, `description`, `transaction_type`, `amount`, `account`, `category`), `list_filter` e `date_hierarchy = 'date'`.

- [x] **6.5 Formulário de transação**
  - [x] 6.5.1 Criar `TransactionForm(StyledFormMixin, ModelForm)` com campos `transaction_type`, `amount`, `date`, `description`, `account`, `category`.
  - [x] 6.5.2 Receber `user` no `__init__` e filtrar `account.queryset` e `category.queryset` pelo usuário.
  - [x] 6.5.3 Usar widget `DateInput(attrs={'type': 'date'}, format='%Y-%m-%d')` para a data.
  - [x] 6.5.4 Validar no `clean` que `category.category_type == transaction_type`, com mensagem "A categoria deve ser do mesmo tipo da transação."
  - [x] 6.5.5 Agrupar as categorias no select por tipo (`optgroup` Entradas/Saídas) para facilitar a escolha.

- [x] **6.6 Filtros da listagem**
  - [x] 6.6.1 Criar `TransactionFilterForm(StyledFormMixin, Form)` com `start_date`, `end_date`, `transaction_type`, `account`, `category` (todos opcionais).
  - [x] 6.6.2 Filtrar querysets de conta e categoria do filtro pelo usuário.
  - [x] 6.6.3 Aplicar os filtros no `get_queryset` da `TransactionListView` quando o form for válido.
  - [x] 6.6.4 Usar `select_related('account', 'category')` na listagem.

- [x] **6.7 Views de transações**
  - [x] 6.7.1 `TransactionListView` com `paginate_by = 20` e filtro no contexto.
  - [x] 6.7.2 Exibir no contexto o total de entradas e saídas do resultado filtrado.
  - [x] 6.7.3 `TransactionCreateView` com `get_form_kwargs` passando `user` e mensagem "Transação registrada com sucesso."
  - [x] 6.7.4 `TransactionUpdateView` com mensagem "Transação atualizada com sucesso."
  - [x] 6.7.5 `TransactionDeleteView` com mensagem de sucesso.

- [x] **6.8 URLs de transações**
  - [x] 6.8.1 Criar `transactions/urls.py` com `app_name = 'transactions'` e rotas list/new/edit/delete.
  - [x] 6.8.2 Incluir em `core/urls.py` com prefixo `transactions/`.

- [x] **6.9 Templates de transações**
  - [x] 6.9.1 `transactions/transaction_list.html` com page header e botão "Nova transação".
  - [x] 6.9.2 Barra de filtros em grid responsivo com botões "Filtrar" e "Limpar".
  - [x] 6.9.3 Tabela com Data, Descrição, Categoria (com cor), Conta, Tipo (badge) e Valor colorido.
  - [x] 6.9.4 Formatar valores como R$ com separadores brasileiros (`floatformat:2` + `intcomma` / localização).
  - [x] 6.9.5 Cards empilhados no mobile.
  - [x] 6.9.6 Paginação mantendo os filtros na query string.
  - [x] 6.9.7 Estado vazio quando não houver transações (e mensagem específica quando o filtro não retornar resultados).
  - [x] 6.9.8 `transactions/transaction_form.html` com título dinâmico e aviso caso o usuário não tenha contas ou categorias, com links para cadastrá-las.
  - [x] 6.9.9 `transactions/transaction_confirm_delete.html` usando o componente de confirmação.
  - [x] 6.9.10 Adicionar link "Transações" funcional na sidebar.

---

### [x] Sprint 7 — Dashboard

- [x] **7.1 View do dashboard**
  - [x] 7.1.1 Criar `DashboardView(LoginRequiredMixin, TemplateView)` em `core/views.py` com `template_name = 'dashboard.html'`.
  - [x] 7.1.2 Registrar rota `dashboard/` com name `dashboard`.
  - [x] 7.1.3 Calcular o saldo total somando `current_balance` das contas do usuário.
  - [x] 7.1.4 Calcular total de entradas do mês corrente (`date__year`, `date__month`).
  - [x] 7.1.5 Calcular total de saídas do mês corrente.
  - [x] 7.1.6 Calcular resultado do mês (entradas − saídas).
  - [x] 7.1.7 Buscar as 5 últimas transações com `select_related`.
  - [x] 7.1.8 Buscar a lista de contas do usuário.
  - [x] 7.1.9 Adicionar o nome do mês atual em português no contexto (ex.: "outubro de 2026").

- [x] **7.2 Template do dashboard**
  - [x] 7.2.1 Criar `templates/dashboard.html` estendendo `base_auth.html`.
  - [x] 7.2.2 Saudação "Olá, {{ user.first_name }}" e subtítulo com o mês atual.
  - [x] 7.2.3 Grid de 4 KPI cards: Saldo total (destaque em gradiente), Entradas do mês (verde), Saídas do mês (vermelho), Resultado do mês (verde ou vermelho conforme sinal).
  - [x] 7.2.4 Seção "Últimas transações" com lista e link "Ver todas".
  - [x] 7.2.5 Seção "Minhas contas" com nome, tipo e saldo de cada conta.
  - [x] 7.2.6 Botões de ação rápida: "Nova transação" e "Nova conta".
  - [x] 7.2.7 Estados vazios para usuário sem contas e sem transações.
  - [x] 7.2.8 Validar responsividade do dashboard.

- [x] **7.3 Integração de navegação**
  - [x] 7.3.1 Confirmar que login e cadastro redirecionam ao dashboard.
  - [x] 7.3.2 Confirmar que o link "Dashboard" da sidebar fica ativo na página.
  - [x] 7.3.3 Confirmar que a landing mostra "Ir para o dashboard" para usuários logados.

---

### [x] Sprint 8 — Revisão, padronização e refinamento

- [x] **8.1 Revisão de segurança e isolamento**
  - [x] 8.1.1 Verificar que todas as views autenticadas usam `LoginRequiredMixin`.
  - [x] 8.1.2 Testar manualmente o acesso por URL a objetos de outro usuário (deve retornar 404) em contas, categorias e transações.
  - [x] 8.1.3 Verificar que o logout é feito via POST.
  - [x] 8.1.4 Verificar que `SECRET_KEY`, `DEBUG` e `ALLOWED_HOSTS` continuam vindo do `.env` (tarefa 0.4) e que nenhum segredo está versionado.

- [x] **8.2 Revisão de interface**
  - [x] 8.2.1 Revisar todos os textos da interface em português brasileiro.
  - [x] 8.2.2 Revisar consistência visual de todas as telas com o design system.
  - [x] 8.2.3 Revisar formatação de valores (R$) e datas (dd/mm/aaaa) em todas as telas.
  - [x] 8.2.4 Revisar todas as telas nos breakpoints 375px, 768px e 1280px.
  - [x] 8.2.5 Adicionar `{% block title %}` específico em cada página (ex.: "Contas | Finanpy").

- [x] **8.3 Revisão de código**
  - [x] 8.3.1 Executar `ruff check .` e corrigir todos os apontamentos.
  - [x] 8.3.2 Verificar uso de aspas simples em todo o código Python.
  - [x] 8.3.3 Verificar que todo o código (nomes, URLs, models) está em inglês.
  - [x] 8.3.4 Verificar que todos os models possuem `created_at` e `updated_at`.
  - [x] 8.3.5 Remover código não utilizado e arquivos desnecessários.

- [x] **8.4 Documentação**
  - [x] 8.4.1 Criar `README.md` com descrição, requisitos, instalação, comandos de build do Tailwind e como rodar o projeto.
  - [x] 8.4.2 Atualizar `requirements.txt`.

---

### [x] Sprint 9 — Testes automatizados

- [x] **9.1 Testes de usuários e autenticação** (`users/tests.py`)
  - [x] 9.1.1 Testar `create_user` com e-mail e senha.
  - [x] 9.1.2 Testar `create_superuser` com flags corretas.
  - [x] 9.1.3 Testar que e-mail duplicado é rejeitado.
  - [x] 9.1.4 Testar cadastro via view: cria usuário, autentica e redireciona ao dashboard.
  - [x] 9.1.5 Testar login com e-mail correto e com senha incorreta.
  - [x] 9.1.6 Testar logout redirecionando à landing.

- [x] **9.2 Testes de perfil** (`profiles/tests.py`)
  - [x] 9.2.1 Testar que o signal cria o perfil ao criar um usuário.
  - [x] 9.2.2 Testar edição de perfil e de nome do usuário.

- [x] **9.3 Testes de contas** (`accounts/tests.py`)
  - [x] 9.3.1 Testar CRUD de contas pelo usuário dono.
  - [x] 9.3.2 Testar que outro usuário recebe 404 ao acessar/editar/excluir.
  - [x] 9.3.3 Testar cálculo de `current_balance` com entradas e saídas.
  - [x] 9.3.4 Testar bloqueio de exclusão de conta com transações.

- [x] **9.4 Testes de categorias** (`categories/tests.py`)
  - [x] 9.4.1 Testar CRUD de categorias.
  - [x] 9.4.2 Testar validação de duplicidade de nome + tipo.
  - [x] 9.4.3 Testar isolamento entre usuários.
  - [x] 9.4.4 Testar bloqueio de exclusão de categoria com transações.

- [x] **9.5 Testes de transações** (`transactions/tests.py`)
  - [x] 9.5.1 Testar CRUD de transações.
  - [x] 9.5.2 Testar validação de valor maior que zero.
  - [x] 9.5.3 Testar validação de tipo da categoria igual ao tipo da transação.
  - [x] 9.5.4 Testar que o form só exibe contas e categorias do usuário.
  - [x] 9.5.5 Testar filtros por período, tipo, conta e categoria.
  - [x] 9.5.6 Testar isolamento entre usuários.

- [x] **9.6 Testes de core**
  - [x] 9.6.1 Testar que a landing é pública (status 200).
  - [x] 9.6.2 Testar que o dashboard exige login (redireciona ao login).
  - [x] 9.6.3 Testar os valores de KPIs do dashboard com dados conhecidos.

- [x] **9.7 Cobertura**
  - [x] 9.7.1 Instalar `coverage` como dependência de desenvolvimento.
  - [x] 9.7.2 Executar `coverage run manage.py test` e `coverage report`.
  - [x] 9.7.3 Atingir cobertura mínima de 80%.

---

### Sprint 10 — Assistente Financeiro com IA

> **Especificação:** `PRD.md`, seção 14. Em caso de dúvida, vale o PRD. **Responsáveis:** `agents/README.md`.
>
> **Pré-requisito:** decidir o item I-01 do PRD (`gpt-5-mini` será desligado em 11/12/2026) antes de concluir a tarefa 10.3.

- [x] **10.1 Preparar a arquitetura e as dependências**
  - **Objetivo:** instalar as bibliotecas e confirmar, antes de escrever a funcionalidade, os comportamentos que a documentação não deixa claros.
  - **Arquivos:** `requirements.txt`; rascunhos fora do repositório.
  - **Dependências:** nenhuma.
  - **Resultado esperado:** dependências fixadas e dúvidas técnicas respondidas.
  - **Critérios de conclusão:** `manage.py check` e os testes atuais passam com as novas dependências, e as respostas de 10.1.5 estão registradas na documentação técnica ou no relato da tarefa.
  - [x] 10.1.1 Consultar no Context7 a documentação de `create_agent`, `ToolRuntime`, `ToolStrategy` e dos middlewares usados (`/websites/langchain_oss_python_langchain`).
  - [x] 10.1.2 Instalar `langchain` e `langchain-openai` na linha 1.x, com `langchain-openai>=1.4.1`.
  - [x] 10.1.3 Regenerar o `requirements.txt` em UTF-8 (`pip freeze | Out-File -Encoding utf8 requirements.txt`), sem incluir as ferramentas de `requirements-dev.txt`.
  - [x] 10.1.4 Executar `manage.py check` e `manage.py test` e comparar o resultado com o estado anterior.
  - [x] 10.1.5 Confirmar com modelo falso: se a tool do `ToolStrategy` conta no `ToolCallLimitMiddleware`; como o `PIIMiddleware` trata resultados em JSON; se as tools rodam em thread separada; e como o middleware lê `runtime.context`.
  - [x] 10.1.6 Confirmar que `create_react_agent`, `AgentExecutor`, `initialize_agent` e `langchain_classic` não são necessários nem usados.

- [x] **10.2 Configurar a app `ai`**
  - **Objetivo:** deixar a app pronta para receber os módulos, sem efeito nas demais.
  - **Arquivos:** `ai/apps.py`, `ai/urls.py`, `core/urls.py`, `core/settings.py`.
  - **Dependências:** 10.1.
  - **Resultado esperado:** app registrada, com rotas vazias e settings carregados do ambiente.
  - **Critérios de conclusão:** `manage.py check` passa sem `OPENAI_API_KEY`, e as rotas existentes não mudam.
  - [x] 10.2.1 Confirmar `ai` em `INSTALLED_APPS` e definir `verbose_name = 'Assistente IA'` em `AiConfig`.
  - [x] 10.2.2 Criar `ai/urls.py` com `app_name = 'ai'` e incluir em `core/urls.py` com o prefixo `ai/`.
  - [x] 10.2.3 Adicionar a `core/settings.py` os settings do Assistente (PRD 14.8 e 14.18), lendo do ambiente, com os padrões do PRD e conversão de tipos.
  - [x] 10.2.4 Criar a estrutura vazia de `ai/context.py`, `schemas.py`, `queries.py`, `tools.py`, `prompts.py`, `agent.py`, `validators.py` e `services.py`.

- [x] **10.3 Configurar a integração com a OpenAI**
  - **Objetivo:** criar o cliente do modelo em um único ponto, com chave segura e parâmetros configuráveis.
  - **Arquivos:** `ai/agent.py`, `.env.example`, `.env` local.
  - **Dependências:** 10.2 e a decisão do item I-01.
  - **Resultado esperado:** `build_chat_model()` funcionando, com o modelo definido por variável de ambiente.
  - **Critérios de conclusão:** a chave não aparece em código, logs ou Git; importar `ai.services` não carrega o LangChain; o sistema inicia sem a chave.
  - [x] 10.3.1 Implementar `build_chat_model()` conforme PRD 14.8, sem enviar `temperature`.
  - [x] 10.3.2 Adicionar `OPENAI_API_KEY` vazia e `AI_MODEL_NAME` ao `.env.example`, com comentário sobre o desligamento do `gpt-5-mini`.
  - [x] 10.3.3 Confirmar que `.env` continua no `.gitignore` e no `.dockerignore`.
  - [x] 10.3.4 Garantir o carregamento tardio do LangChain (RNF23).
  - [x] 10.3.5 Confirmar que o rastreamento do LangSmith permanece desativado (RNF26).
  - [x] 10.3.6 Com autorização do responsável, pois há custo, testar uma chamada real com `gpt-5-mini` e com o modelo substituto, se a decisão I-01 o incluir, confirmando os parâmetros aceitos.

- [x] **10.4 Implementar o contrato de isolamento e as consultas**
  - **Objetivo:** criar a camada de leitura que torna impossível consultar dados sem indicar o dono.
  - **Arquivos:** `ai/context.py`, `ai/queries.py`.
  - **Dependências:** 10.2.
  - **Resultado esperado:** `AnalysisContext` imutável e funções puras de consulta, filtradas por usuário, com custo limitado.
  - **Critérios de conclusão:** toda função recebe `user_id` como primeiro parâmetro obrigatório, não grava nada, usa número fixo de consultas e não carrega transações sem limite.
  - [x] 10.4.1 Criar `AnalysisContext` (`dataclass(frozen=True)`), conforme PRD 14.12.
  - [x] 10.4.2 Implementar a função que calcula o período (RN02) a partir de `timezone.localdate()`.
  - [x] 10.4.3 Implementar `get_financial_summary` e o cálculo de `metrics_snapshot`, excluindo datas futuras (RN03).
  - [x] 10.4.4 Implementar `get_monthly_evolution` com `TruncMonth`, preenchendo meses sem movimento e marcando `is_partial_month` (RN04).
  - [x] 10.4.5 Implementar `get_category_breakdown` com `others_total`.
  - [x] 10.4.6 Implementar `get_category_changes` somente para meses fechados, com `is_significant` conforme RN10.
  - [x] 10.4.7 Implementar `get_recurring_expenses` conforme RN09.
  - [x] 10.4.8 Implementar `get_largest_transactions` com `select_related` e `limit`.
  - [x] 10.4.9 Implementar `get_accounts_overview` em uma só consulta, sem expor `bank_name`.
  - [x] 10.4.10 Serializar valores como texto com `quantize(Decimal('0.01'))`, nunca como `float`.

- [x] **10.5 Desenvolver as tools de acesso aos dados financeiros**
  - **Objetivo:** expor as consultas ao agente sem dar a ele controle sobre o usuário.
  - **Arquivos:** `ai/tools.py`.
  - **Dependências:** 10.4.
  - **Resultado esperado:** as 7 tools da seção 14.9 do PRD, reunidas em `FINANCIAL_TOOLS`.
  - **Critérios de conclusão:** nenhum schema de tool tem campo de usuário; parâmetros inválidos retornam erro ao modelo sem encerrar a execução; nenhuma conexão de banco fica aberta nas threads do pool.
  - [x] 10.5.1 Criar as tools com `@tool`, docstring em inglês para o modelo e `runtime: ToolRuntime[AnalysisContext]`.
  - [x] 10.5.2 Declarar tipos e limites com `Annotated`, `Literal` e `Field`.
  - [x] 10.5.3 Implementar `ToolArgumentError` e a validação de contexto, com retorno `{'error', 'detail'}`.
  - [x] 10.5.4 Implementar o decorator que fecha a conexão ao rodar em thread diferente de `owner_thread_id`.
  - [x] 10.5.5 Verificar o schema gerado de cada tool (`tool.args`), confirmando que `runtime` não aparece.

- [x] **10.6 Implementar o agente com LangChain 1.0**
  - **Objetivo:** montar o agente com saída estruturada, limites e sem memória entre execuções.
  - **Arquivos:** `ai/schemas.py`, `ai/prompts.py`, `ai/agent.py`.
  - **Dependências:** 10.3 e 10.5.
  - **Resultado esperado:** `run_agent(context)` retornando saída estruturada, mensagens e uso de tokens.
  - **Critérios de conclusão:** o agente executa de ponta a ponta com modelo falso; não há `checkpointer`, `store` nem API obsoleta; todos os limites foram verificados por teste.
  - [x] 10.6.1 Criar `EvidenceItem`, `Insight`, `Recommendation`, `Alert` e `AnalysisOutput` (PRD 14.11).
  - [x] 10.6.2 Escrever `SYSTEM_PROMPT` (PRD 14.7) e `PROMPT_VERSION`.
  - [x] 10.6.3 Montar `create_agent` com `context_schema` e `response_format=ToolStrategy(AnalysisOutput)`.
  - [x] 10.6.4 Configurar `ModelCallLimitMiddleware`, `ToolCallLimitMiddleware` e `PIIMiddleware`.
  - [x] 10.6.5 Implementar `enforce_run_deadline` com `before_model(can_jump_to=['end'])`.
  - [x] 10.6.6 Executar com `recursion_limit` explícito e uma instância de `UsageMetadataCallbackHandler` por execução.

- [x] **10.7 Criar a estrutura de persistência das análises**
  - **Objetivo:** guardar cada execução com histórico, auditoria e proteção contra duplicidade.
  - **Arquivos:** `ai/models.py`, `ai/migrations/`, `ai/admin.py`.
  - **Dependências:** 10.2.
  - **Resultado esperado:** model `FinancialAnalysis` e migration, sem alterar nenhuma outra app.
  - **Critérios de conclusão:** `makemigrations --check` limpo; a migration cria somente a tabela da app `ai`; a restrição impede dois `pending` para o mesmo usuário; excluir usuário pelo admin continua funcionando.
  - [x] 10.7.1 Criar `FinancialAnalysis` com os campos da seção 14.11 do PRD, herdando de `TimeStampedModel`.
  - [x] 10.7.2 Criar as opções de status e `error_code`, com rótulos em português.
  - [x] 10.7.3 Adicionar o índice e a `UniqueConstraint` condicional.
  - [x] 10.7.4 Gerar e aplicar a migration, conferindo o SQL com `sqlmigrate`.
  - [x] 10.7.5 Registrar o model no admin como somente leitura, mantendo a permissão de exclusão (PRD 14.12).

- [x] **10.8 Implementar a validação dos resultados e o tratamento de erros**
  - **Objetivo:** impedir que conclusões sem evidência sejam gravadas e transformar qualquer falha em um estado conhecido.
  - **Arquivos:** `ai/validators.py`, `ai/services.py`.
  - **Dependências:** 10.6 e 10.7.
  - **Resultado esperado:** validação de evidências e mapeamento de todas as exceções para `error_code`.
  - **Critérios de conclusão:** cada código da seção 14.16 do PRD é alcançado em teste; nenhuma exceção do agente chega à view; `error_detail` guarda só a classe da exceção.
  - [x] 10.8.1 Extrair os valores retornados pelas tools a partir das `ToolMessage` de `result['messages']`.
  - [x] 10.8.2 Comparar cada evidência com os valores da tool indicada em `source_tool`, com normalização numérica.
  - [x] 10.8.3 Implementar as regras de descarte e de falha `unverified_output` (PRD 14.13).
  - [x] 10.8.4 Mapear as exceções de OpenAI, LangChain e LangGraph para `error_code` (PRD 14.16).
  - [x] 10.8.5 Tratar a ausência de `structured_response`, separando `timeout` de `limit_exceeded`.
  - [x] 10.8.6 Confirmar com `logger.exception` que os logs não contêm prompt, descrições nem a chave.

- [x] **10.9 Implementar o serviço de geração das análises**
  - **Objetivo:** concentrar o fluxo completo em um único ponto de entrada.
  - **Arquivos:** `ai/services.py`.
  - **Dependências:** 10.8.
  - **Resultado esperado:** `generate_analysis(user)`, `get_latest_valid_analysis(user)` e `get_dashboard_analysis_state(user)`.
  - **Critérios de conclusão:** os 9 passos da seção 14.13 do PRD estão cobertos; nenhuma transação de banco fica aberta durante o agente; a função não depende de `request`.
  - [x] 10.9.1 Criar o enum `GenerationOutcome` (`success`, `failed`, `already_running`, `limit_reached`, `insufficient_data`, `disabled`).
  - [x] 10.9.2 Implementar o encerramento de `pending` antigos como `abandoned`.
  - [x] 10.9.3 Implementar as verificações de chave, mínimo de transações e limite diário, nessa ordem, sem chamar o modelo.
  - [x] 10.9.4 Criar o registro `pending`, tratando `IntegrityError` como `already_running`.
  - [x] 10.9.5 Executar o agente e gravar resultado, tokens, tools chamadas e duração.
  - [x] 10.9.6 Implementar as leituras do dashboard em no máximo 3 consultas, sem gravar e sem importar o LangChain.

- [x] **10.10 Integrar com o backend existente**
  - **Objetivo:** ligar o serviço às rotas e ao dashboard, usando CBVs, pois o projeto não possui API REST.
  - **Arquivos:** `ai/views.py`, `ai/urls.py`, `core/views.py`.
  - **Dependências:** 10.9.
  - **Resultado esperado:** rotas `ai:list`, `ai:create` e `ai:detail`, e `analysis_state` no contexto do dashboard.
  - **Critérios de conclusão:** as rotas exigem login; GET em `ai:create` retorna 405; análise de outro usuário retorna 404; os KPIs atuais do dashboard não mudam.
  - [x] 10.10.1 Implementar `AnalysisListView` e `AnalysisDetailView` com `LoginRequiredMixin` e `UserQuerySetMixin`.
  - [x] 10.10.2 Implementar `AnalysisCreateView`, somente POST, usando somente `request.user`.
  - [x] 10.10.3 Converter cada `GenerationOutcome` na mensagem da seção 14.15 do PRD.
  - [x] 10.10.4 Adicionar `analysis_state` a `DashboardView`, sem alterar os cálculos existentes.
  - [x] 10.10.5 Informar ao frontend as rotas, as variáveis de contexto e os estados.

- [x] **10.11 Integrar com o dashboard no frontend**
  - **Objetivo:** apresentar as análises e todos os estados com clareza, seguindo o design system.
  - **Arquivos:** `templates/components/analysis_card.html`, `templates/dashboard.html`, `templates/components/sidebar.html`, `ai/templates/ai/analysis_list.html`, `ai/templates/ai/analysis_detail.html`, `static/js/analysis_form.js`.
  - **Dependências:** 10.10.
  - **Resultado esperado:** card no dashboard, histórico, detalhe e item na sidebar.
  - **Critérios de conclusão:** os 9 estados são exibidos sem erro nos três breakpoints; sem rolagem horizontal; conteúdo gerado sempre escapado, sem `|safe`; `output.css` regenerado.
  - [x] 10.11.1 Criar `analysis_card.html` com o conteúdo da seção 14.15 do PRD.
  - [x] 10.11.2 Implementar os 9 estados, com textos em português e números vindos dos settings.
  - [x] 10.11.3 Incluir o card entre os KPIs e as últimas transações em `dashboard.html`.
  - [x] 10.11.4 Criar `analysis_form.js`, com o formulário funcionando também sem JavaScript.
  - [x] 10.11.5 Criar `analysis_list.html`, com paginação e estado vazio.
  - [x] 10.11.6 Criar `analysis_detail.html`, com insights, recomendações, alertas, evidências, limitações e o aviso educativo.
  - [x] 10.11.7 Adicionar **Assistente IA** à sidebar, com `app_name='ai'`.
  - [x] 10.11.8 Definir `{% block title %}` em cada nova página.
  - [x] 10.11.9 Validar no navegador nos três breakpoints e todos os estados, com o `qa-tester`.

- [ ] **10.12 Implementar testes unitários e de integração**
  - **Objetivo:** verificar a funcionalidade sem custo, sem rede e sem depender de respostas variáveis do modelo.
  - **Arquivos:** `ai/tests.py` e `core/tests.py`.
  - **Dependências:** 10.11.
  - **Resultado esperado:** suíte da app `ai` com modelo falso, mais um teste real opcional.
  - **Critérios de conclusão:** `manage.py test` passa sem chave e sem internet; cobertura da app `ai` de pelo menos 80%; `ruff check .` sem apontamentos.
  - [ ] 10.12.1 Criar a subclasse de `GenericFakeChatModel` com `bind_tools`, instanciando o iterador em cada teste.
  - [ ] 10.12.2 Testar cada função de `queries.py` com valores calculados à mão, incluindo datas futuras, mês parcial e meses sem movimento.
  - [ ] 10.12.3 Testar que `get_accounts_overview` confere com `Account.current_balance`.
  - [ ] 10.12.4 Testar com `assertNumQueries` que o custo das consultas não cresce com o volume de dados.
  - [ ] 10.12.5 Testar as tools: parâmetros válidos, fora do período e acima dos limites.
  - [ ] 10.12.6 Testar o agente com `TransactionTestCase`: chamada de tool, saída estruturada e nova tentativa após saída inválida.
  - [ ] 10.12.7 Testar os limites de chamadas e o prazo total.
  - [ ] 10.12.8 Testar a validação de evidências: válida, inventada, descarte e `main_insight` rejeitado.
  - [ ] 10.12.9 Testar `generate_analysis` em cada resultado, e cada `error_code` com exceções simuladas.
  - [ ] 10.12.10 Testar as views e o dashboard: login, POST, 405, mensagens, estados e ausência de chamada ao modelo.
  - [ ] 10.12.11 Criar o teste real ativado só por `RUN_LIVE_AI_TESTS=True` e, com autorização do responsável, executá-lo para medir tempo, tokens e custo.

- [ ] **10.13 Testar a segurança e o isolamento entre usuários**
  - **Objetivo:** demonstrar por testes que o agente não acessa dados de outro usuário, mesmo se o modelo tentar.
  - **Arquivos:** `ai/tests.py`.
  - **Dependências:** 10.12.
  - **Resultado esperado:** testes adversariais, com os usuários A e B e dados diferentes.
  - **Critérios de conclusão:** todos os cenários passam; qualquer vazamento é defeito **Crítico** e bloqueia o encerramento da sprint.
  - [ ] 10.13.1 Simular tool calls com `user_id` forjado para B em execução de A e confirmar que só retornam dados de A.
  - [ ] 10.13.2 Verificar que todas as funções de `queries.py` e todas as tools ignoram dados de B.
  - [ ] 10.13.3 Executar análises de A e B em threads simultâneas e confirmar que cada registro contém só dados do próprio dono.
  - [ ] 10.13.4 Testar, com B autenticado, 404 no detalhe de A e ausência de análises de A na lista e no dashboard.
  - [ ] 10.13.5 Testar que `user_id` enviado no POST é ignorado.
  - [ ] 10.13.6 Inserir instruções maliciosas e código HTML em descrições e confirmar que o conteúdo é escapado e que continuam disponíveis só as tools de leitura.
  - [ ] 10.13.7 Testar que as tools não alteram nenhum registro (contagem e conteúdo iguais antes e depois).
  - [ ] 10.13.8 Testar que o conteúdo enviado ao modelo não contém nome, e-mail, telefone, `bank_name` nem identificadores internos, e que e-mails e cartões em descrições são removidos.
  - [ ] 10.13.9 Testar a restrição de análise em andamento e o limite diário por usuário, sem afetar outro usuário.
  - [ ] 10.13.10 Validar o isolamento no navegador, com o `qa-tester`.

- [ ] **10.14 Documentar a implementação**
  - **Objetivo:** deixar a funcionalidade operável por quem não participou da implementação.
  - **Arquivos:** `docs/ia.md`, `docs/README.md`, `docs/setup.md`, `docs/estrutura.md`, `README.md`, `CLAUDE.md`, `.env.example`.
  - **Dependências:** 10.13.
  - **Resultado esperado:** documentação técnica e de configuração atualizada, com a imagem Docker validada.
  - **Critérios de conclusão:** um novo desenvolvedor configura o Assistente seguindo só os documentos; a imagem sobe com e sem a chave; todas as tarefas desta sprint estão marcadas.
  - [ ] 10.14.1 Criar `docs/ia.md` com arquitetura, tools, fluxo, códigos de erro, limites e como trocar o modelo.
  - [ ] 10.14.2 Registrar em `docs/ia.md` as respostas da tarefa 10.1.5 e o custo e o tempo medidos em 10.12.11.
  - [ ] 10.14.3 Atualizar `docs/setup.md`, `docs/estrutura.md`, `docs/README.md` e o `README.md`.
  - [ ] 10.14.4 Reconstruir a imagem Docker com as novas dependências e validar o sistema com e sem `OPENAI_API_KEY`.
  - [ ] 10.14.5 Atualizar o `CLAUDE.md` com a app `ai`, a exceção de dependências e o local real das tarefas (itens I-03 e I-09 do PRD).
  - [ ] 10.14.6 Corrigir as referências antigas a "Sprint 10" (Docker) em `agents/devops-docker.md` e a "PRD, seção 13" em `agents/` e `docs/`.

---

### [x] Sprint 11 — Docker

- [x] **11.1 Dockerfile**
  - [x] 11.1.1 Criar `Dockerfile` baseado em `python:3.12-slim`.
  - [x] 11.1.2 Instalar dependências do `requirements.txt`.
  - [x] 11.1.3 Baixar o Tailwind CLI standalone e gerar `output.css` com `--minify` durante o build.
  - [x] 11.1.4 Executar `collectstatic` durante o build.
  - [x] 11.1.5 Definir comando de inicialização (`migrate` + servidor).

- [x] **11.2 docker-compose**
  - [x] 11.2.1 Criar `docker-compose.yml` com o serviço `web`.
  - [x] 11.2.2 Mapear a porta 8000.
  - [x] 11.2.3 Criar volume para persistir o arquivo SQLite.
  - [x] 11.2.4 Configurar variáveis de ambiente (`SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`) via `.env`.

- [x] **11.3 Finalização**
  - [x] 11.3.1 Criar `.dockerignore` (venv, `__pycache__`, `.git`, `db.sqlite3`).
  - [x] 11.3.2 Testar `docker compose up --build` do zero.
  - [x] 11.3.3 Atualizar o `README.md` com instruções de uso do Docker.

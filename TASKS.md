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

- [ ] **1.8 Templates provisórios de autenticação**
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

### Sprint 9 — Testes automatizados

- [ ] **9.1 Testes de usuários e autenticação** (`users/tests.py`)
  - [ ] 9.1.1 Testar `create_user` com e-mail e senha.
  - [ ] 9.1.2 Testar `create_superuser` com flags corretas.
  - [ ] 9.1.3 Testar que e-mail duplicado é rejeitado.
  - [ ] 9.1.4 Testar cadastro via view: cria usuário, autentica e redireciona ao dashboard.
  - [ ] 9.1.5 Testar login com e-mail correto e com senha incorreta.
  - [ ] 9.1.6 Testar logout redirecionando à landing.

- [ ] **9.2 Testes de perfil** (`profiles/tests.py`)
  - [ ] 9.2.1 Testar que o signal cria o perfil ao criar um usuário.
  - [ ] 9.2.2 Testar edição de perfil e de nome do usuário.

- [ ] **9.3 Testes de contas** (`accounts/tests.py`)
  - [ ] 9.3.1 Testar CRUD de contas pelo usuário dono.
  - [ ] 9.3.2 Testar que outro usuário recebe 404 ao acessar/editar/excluir.
  - [ ] 9.3.3 Testar cálculo de `current_balance` com entradas e saídas.
  - [ ] 9.3.4 Testar bloqueio de exclusão de conta com transações.

- [ ] **9.4 Testes de categorias** (`categories/tests.py`)
  - [ ] 9.4.1 Testar CRUD de categorias.
  - [ ] 9.4.2 Testar validação de duplicidade de nome + tipo.
  - [ ] 9.4.3 Testar isolamento entre usuários.
  - [ ] 9.4.4 Testar bloqueio de exclusão de categoria com transações.

- [ ] **9.5 Testes de transações** (`transactions/tests.py`)
  - [ ] 9.5.1 Testar CRUD de transações.
  - [ ] 9.5.2 Testar validação de valor maior que zero.
  - [ ] 9.5.3 Testar validação de tipo da categoria igual ao tipo da transação.
  - [ ] 9.5.4 Testar que o form só exibe contas e categorias do usuário.
  - [ ] 9.5.5 Testar filtros por período, tipo, conta e categoria.
  - [ ] 9.5.6 Testar isolamento entre usuários.

- [ ] **9.6 Testes de core**
  - [ ] 9.6.1 Testar que a landing é pública (status 200).
  - [ ] 9.6.2 Testar que o dashboard exige login (redireciona ao login).
  - [ ] 9.6.3 Testar os valores de KPIs do dashboard com dados conhecidos.

- [ ] **9.7 Cobertura**
  - [ ] 9.7.1 Instalar `coverage` como dependência de desenvolvimento.
  - [ ] 9.7.2 Executar `coverage run manage.py test` e `coverage report`.
  - [ ] 9.7.3 Atingir cobertura mínima de 80%.

---

### Sprint 10 — Docker

- [ ] **10.1 Dockerfile**
  - [ ] 10.1.1 Criar `Dockerfile` baseado em `python:3.12-slim`.
  - [ ] 10.1.2 Instalar dependências do `requirements.txt`.
  - [ ] 10.1.3 Baixar o Tailwind CLI standalone e gerar `output.css` com `--minify` durante o build.
  - [ ] 10.1.4 Executar `collectstatic` durante o build.
  - [ ] 10.1.5 Definir comando de inicialização (`migrate` + servidor).

- [ ] **10.2 docker-compose**
  - [ ] 10.2.1 Criar `docker-compose.yml` com o serviço `web`.
  - [ ] 10.2.2 Mapear a porta 8000.
  - [ ] 10.2.3 Criar volume para persistir o arquivo SQLite.
  - [ ] 10.2.4 Configurar variáveis de ambiente (`SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`) via `.env`.

- [ ] **10.3 Finalização**
  - [ ] 10.3.1 Criar `.dockerignore` (venv, `__pycache__`, `.git`, `db.sqlite3`).
  - [ ] 10.3.2 Testar `docker compose up --build` do zero.
  - [ ] 10.3.3 Atualizar o `README.md` com instruções de uso do Docker.

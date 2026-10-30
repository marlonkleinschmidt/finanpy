# Design system

Diretrizes visuais definidas no PRD (seção 9). O TailwindCSS e os templates ainda não foram configurados no projeto; este documento resume as regras a seguir quando forem criados. Para as classes completas de cada componente, consulte o [PRD.md](../PRD.md#9-design-system).

## Princípios

- Estilização exclusivamente com **TailwindCSS**, dentro dos templates DTL.
- **Fundo escuro** como base, com superfícies levemente mais claras.
- **Gradiente de marca** (violeta → índigo → ciano) em destaques: logo, botões primários e títulos.
- **Cores semânticas:** verde para entradas, vermelho/rosa para saídas.
- Cantos arredondados, bordas sutis e sombras suaves.
- **Mobile first** e responsivo (mobile, tablet e desktop).
- Interface em **português brasileiro**.

## Cores principais

| Uso                | Classe Tailwind  |
| ------------------ | ---------------- |
| Fundo da página    | `bg-slate-950`   |
| Superfície (cards) | `bg-slate-900`   |
| Inputs / hover     | `bg-slate-800`   |
| Texto principal    | `text-slate-100` |
| Texto secundário   | `text-slate-400` |
| Primária           | `violet-500/600` |
| Entrada            | `emerald-400`    |
| Saída              | `rose-400/600`   |
| Alerta             | `amber-400`      |

Gradiente de marca: `bg-gradient-to-r from-violet-600 via-indigo-500 to-cyan-400`

## Tipografia

- Fonte **Inter** (Google Fonts).
- Valores monetários com `tabular-nums`, no formato brasileiro (R$ 1.234,56).

## Reutilização

- Componentes reutilizáveis ficam em `templates/components/` e são incluídos com `{% include %}`.
- Classes CSS dos inputs ficam centralizadas no código dos forms, sem repetir strings.

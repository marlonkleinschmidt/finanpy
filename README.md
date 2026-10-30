# Finanpy

Sistema web de gestão de finanças pessoais, com contas bancárias, categorias, transações e dashboard, feito com Django.

## TailwindCSS

O projeto usa o executável standalone do Tailwind CLI, sem Node.js. Ele não é versionado, então baixe-o na raiz do projeto a partir da [página de releases](https://github.com/tailwindlabs/tailwindcss/releases/latest) (no Windows x64, o arquivo `tailwindcss-windows-x64.exe`) e renomeie-o para `tailwindcss.exe`.

Em PowerShell:

```powershell
Invoke-WebRequest https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-windows-x64.exe -OutFile tailwindcss.exe
```

O arquivo `static/css/output.css` é gerado por estes comandos e também não é versionado.

Desenvolvimento, recompilando a cada alteração:

```powershell
.\tailwindcss.exe -i static/css/input.css -o static/css/output.css --watch
```

Produção, com o CSS minificado:

```powershell
.\tailwindcss.exe -i static/css/input.css -o static/css/output.css --minify
```

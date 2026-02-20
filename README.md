# Pet Story

Gera um **livro de colorir** a partir das fotos do pet: o usuário envia nome, email e até 5 imagens; a API transforma as fotos em desenhos em linha (IA) e devolve um PDF por email.

---

## O que temos até o momento

### Frontend
- Formulário com **nome do pet**, **email** e **fotos** (até 5 imagens, máx. 10 MB cada).
- **Drag-and-drop** para seleção de imagens; validação no cliente (quantidade e tamanho).
- Envio via `POST` para a API; mensagem de sucesso ou erro em modal.

### API (FastAPI)
- **POST /pet** — Cria pedido (nome, email, arquivos). Valida: máx. 5 arquivos, 10 MB cada. Salva arquivos em `api/uploads/<order_id>/`.
- **GET /order/{order_id}** — Retorna dados do pedido.
- **GET /health** — Health check.
- Pedidos armazenados em JSON em `api/data/orders.json` (status: pendente → processado).

### Processamento (`uv run process.py`)
- Roda em separado; pega pedidos **pendentes** e:
  1. **Imagens:** para cada foto original (jpg, jpeg, png, webp), gera versão “line art” com **Gemini** e salva `gerado_<nome>.png`. Se o arquivo já existir, pula.
  2. **PDF:** monta um livro com capa (nome do pet), uma página por imagem gerada e contracapa (“petstory.live”). Usa fontes da pasta `api/fonts/` (qualquer `.ttf`). Salva `livro.pdf` na pasta do pedido. Se o PDF já foi gerado, reutiliza.
  3. **Email:** envia para o **email do cliente** (formulário) com o PDF anexado; opcionalmente envia cópia em BCC para `EMAIL_TO` do `.env`.
- Marca o pedido como **processado** e registra sucesso/falha em `api/email.log`.

### Serviços (pasta `api/`)
| Arquivo   | Função |
|-----------|--------|
| `main.py` | Rotas FastAPI e validação de upload. |
| `store.py` | CRUD de pedidos em JSON; flags `images_generated` e `pdf_generated`. |
| `gemini.py` | Geração de imagens estilo livro de colorir via API Gemini (SDK google-genai). |
| `pdf.py`   | Geração do PDF (capa, páginas com imagens, contracapa); uso de fontes em `api/fonts/`. |
| `mail.py`  | Envio de email (SMTP) com corpo e anexo PDF. |
| `process.py` | Loop de pedidos pendentes: imagens → PDF → email. |

### Configuração (`.env`)
- **API:** `API_HOST`, `API_PORT`.
- **SMTP:** `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `EMAIL_FROM`, `EMAIL_FROM_NAME`; `EMAIL_TO` opcional (BCC).
- **Gemini:** `GEMINI_API_KEY`, `GEMINI_MODEL` (ex.: `models/gemini-2.0-flash-exp` ou o modelo que gera imagem).

Copie `api/.env.example` para `api/.env` e preencha.

---

## Como rodar

1. **API** (na pasta `api`):
   ```bash
   cd api && uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```
2. **Processador** (pedidos pendentes):
   ```bash
   cd api && uv run process.py
   ```
3. **Frontend:** abra `index.html` no navegador (ou sirva a pasta raiz com um servidor estático). O `script.js` chama `http://localhost:8000` por padrão.

4. **Checkout Asaas:** o Asaas não aceita `localhost` nas URLs de retorno (success/cancel). Use uma URL pública HTTPS para o frontend:
   - **Opção A – GitHub Pages:** faça deploy do frontend (ex.: `https://seu-usuario.github.io/petstory-mvp/`). No `api/.env`, defina `FRONTEND_BASE_URL=https://seu-usuario.github.io/petstory-mvp` (sem barra no final).
   - **Opção B – ngrok:** rode `ngrok http 5500` e use `FRONTEND_BASE_URL=https://xxx.ngrok-free.app`.
   - No painel do Asaas, **Configurações da conta > Informações**, cadastre o domínio (ex.: `seu-usuario.github.io` ou o domínio do ngrok).
   - Se o frontend estiver em um site (ex.: GitHub Pages) e a API em outro (ex.: ngrok), no `index.html` descomente a linha que define `window.API_URL` e coloque a URL pública da API (ngrok ou backend em produção), para o formulário chamar a API correta.

---

## Estrutura do projeto

```
petstory-mvp/
├── README.md
├── index.html          # Página do formulário
├── script.js           # Envio do form e drag-and-drop
└── api/
    ├── main.py         # FastAPI
    ├── store.py        # Pedidos (JSON)
    ├── process.py      # Processamento em lote
    ├── gemini.py       # Geração de imagens (Gemini)
    ├── pdf.py          # Geração do PDF do livro
    ├── mail.py         # Envio de email
    ├── .env.example
    ├── data/           # orders.json (não versionado)
    ├── uploads/        # Arquivos por order_id (não versionado)
    └── fonts/         # Fontes .ttf para o PDF
```

Arquivos gerados (uploads, PDFs, data, `.env`) estão no `.gitignore` e não vão para o remoto.

---

*Pet Story — feito com carinho pela [finderbit](https://www.finderbit.com.br).*

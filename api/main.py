import logging
import os
import uvicorn
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi import Form, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

import store
import asaas
from process import processar_pedido

MAX_FILES = 5
MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB

logger = logging.getLogger(__name__)
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


def _checkout_value() -> float:
    try:
        return float(os.getenv("ASAAS_CHECKOUT_VALUE", "29.90").replace(",", "."))
    except ValueError:
        return 29.90


@app.post("/pet")
async def create_pet(
    pet_name: str = Form(..., alias="pet-name"),
    user_email: str = Form(..., alias="user-email"),
    pet_file: list[UploadFile] = File(default=[], alias="pet-file"),
):
    """Cria pedido, salva arquivos e gera checkout Asaas; retorna checkout_url para redirecionar."""
    if len(pet_file) > MAX_FILES:
        raise HTTPException(status_code=400, detail="Máximo 5 imagens.")
    file_names: list[str] = []
    order_id = store.create_order(pet_name=pet_name, user_email=user_email, file_names=[])
    order_dir = store.UPLOADS_DIR / order_id
    order_dir.mkdir(parents=True, exist_ok=True)
    for f in pet_file:
        if f.filename:
            content = await f.read()
            if len(content) > MAX_FILE_BYTES:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cada arquivo deve ter no máximo 10 MB. ({f.filename})",
                )
            path = order_dir / f.filename
            path.write_bytes(content)
            file_names.append(f.filename)
    store.update_order_file_names(order_id, file_names)

    # Asaas exige successUrl/cancelUrl em domínio cadastrado na conta; localhost é rejeitado.
    # Use FRONTEND_BASE_URL com URL pública HTTPS (ex.: ngrok) e cadastre o domínio no Asaas.
    base = (os.getenv("FRONTEND_BASE_URL") or "").strip().rstrip("/")
    if not base:
        base = "http://localhost:5500"
    if not base.startswith("http://") and not base.startswith("https://"):
        base = "http://" + base
    if "localhost" in base or "127.0.0.1" in base:
        raise HTTPException(
            status_code=400,
            detail=(
                "O Asaas não aceita localhost nas URLs de retorno. "
                "Use uma URL pública HTTPS: rode o frontend com ngrok (ex.: ngrok http 5500), "
                "defina FRONTEND_BASE_URL com a URL do ngrok (ex.: https://xxx.ngrok-free.app) "
                "e cadastre esse domínio no Asaas (Configurações da conta > Informações)."
            ),
        )
    if base.startswith("http://") and not base.startswith("http://localhost"):
        raise HTTPException(
            status_code=400,
            detail="Para o checkout Asaas, use FRONTEND_BASE_URL com HTTPS (ex.: https://...).",
        )
    success_url = f"{base}/?checkout=success"
    cancel_url = f"{base}/?checkout=cancel"
    try:
        result = asaas.criar_checkout(
            order_id=order_id,
            valor=_checkout_value(),
            nome_cliente=pet_name,
            email_cliente=user_email,
            success_url=success_url,
            cancel_url=cancel_url,
        )
    except ValueError as e:
        logger.warning("Falha ao criar checkout Asaas: %s", e)
        raise HTTPException(status_code=502, detail="Falha ao criar checkout. Tente novamente.") from e

    store.update_order_asaas_checkout_id(order_id, result["id"])
    return {"ok": True, "checkout_url": result["checkout_url"]}


@app.post("/webhook/asaas")
async def webhook_asaas(request: Request, background_tasks: BackgroundTasks):
    """Recebe eventos do Asaas (ex.: CHECKOUT_PAID). Valida token; marca como pago e enfileira processamento em background."""
    token_recebido = request.headers.get("asaas-access-token")
    token_esperado = os.getenv("ASAAS_WEBHOOK_TOKEN", "").strip()
    if not asaas.webhook_token_valido(token_recebido, token_esperado):
        raise HTTPException(status_code=401, detail="Token do webhook inválido.")
    try:
        body = await request.json()
    except Exception:
        return {}
    order_id = asaas.processar_webhook(body)
    if order_id:
        order = store.get_order(order_id)
        if order:
            pedido = {**order, "order_id": order_id}
            background_tasks.add_task(processar_pedido, pedido)
    return {"received": True}


@app.get("/order/{order_id}")
async def get_order(order_id: str):
    """Retorna dados do pedido."""
    order = store.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    return order


if __name__ == "__main__":
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    uvicorn.run("main:app", host=host, port=port, reload=True)
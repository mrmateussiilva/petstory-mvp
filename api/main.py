import logging
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi import Form, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware

import store

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


@app.post("/pet")
async def create_pet(
    pet_name: str = Form(..., alias="pet-name"),
    user_email: str = Form(..., alias="user-email"),
    pet_file: list[UploadFile] = File(default=[], alias="pet-file"),
):
    """Cria pedido com status pendente, salva arquivos e retorna order_id para redirecionar ao checkout."""
    file_names: list[str] = []
    order_id = store.create_order(pet_name=pet_name, user_email=user_email, file_names=[])
    order_dir = store.UPLOADS_DIR / order_id
    order_dir.mkdir(parents=True, exist_ok=True)
    for f in pet_file:
        if f.filename:
            path = order_dir / f.filename
            content = await f.read()
            path.write_bytes(content)
            file_names.append(f.filename)
    store.update_order_file_names(order_id, file_names)
    return {
        "order_id": order_id,
        "checkout_url": f"checkout.html?order_id={order_id}",
    }


@app.get("/order/{order_id}")
async def get_order(order_id: str):
    """Retorna dados do pedido para a página de checkout."""
    order = store.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    return order


@app.post("/webhook/payment")
async def payment_webhook(request: Request) -> dict[str, str]:
    """Recebe notificação de pagamento e atualiza status do pedido para pago."""
    try:
        body = await request.json()
    except Exception:
        body = {}
    logger.info("Webhook pagamento recebido: %s", body)
    order_id = body.get("order_id") or body.get("orderId") or body.get("payment_id") or body.get("paymentId")
    if order_id and store.update_order_status(order_id, "pago"):
        logger.info("Pedido %s marcado como pago", order_id)
    return {"received": "ok"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
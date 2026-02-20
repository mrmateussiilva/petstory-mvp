import logging
import os
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi import Form, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

import store

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


@app.post("/pet")
async def create_pet(
    pet_name: str = Form(..., alias="pet-name"),
    user_email: str = Form(..., alias="user-email"),
    pet_file: list[UploadFile] = File(default=[], alias="pet-file"),
):
    """Cria pedido com pagamento ok e status pendente, salva arquivos (máx. 5 imagens, 10 MB cada)."""
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
    return {"ok": True, "message": "Pedido registrado."}


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
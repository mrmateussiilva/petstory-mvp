"""Armazenamento simples de pedidos em JSON (MVP)."""
import json
import uuid
from pathlib import Path
from datetime import datetime

DATA_DIR = Path(__file__).resolve().parent / "data"
ORDERS_FILE = DATA_DIR / "orders.json"
UPLOADS_DIR = Path(__file__).resolve().parent / "uploads"


def _ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    if not ORDERS_FILE.exists():
        ORDERS_FILE.write_text("{}", encoding="utf-8")


def _load_orders() -> dict:
    _ensure_dirs()
    return json.loads(ORDERS_FILE.read_text(encoding="utf-8"))


def _save_orders(orders: dict) -> None:
    _ensure_dirs()
    ORDERS_FILE.write_text(json.dumps(orders, ensure_ascii=False, indent=2), encoding="utf-8")


def create_order(pet_name: str, user_email: str, file_names: list[str]) -> str:
    """Cria pedido com status pendente. Retorna order_id."""
    orders = _load_orders()
    order_id = str(uuid.uuid4())
    orders[order_id] = {
        "order_id": order_id,
        "pet_name": pet_name,
        "user_email": user_email,
        "file_names": file_names,
        "status": "pendente",
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    _save_orders(orders)
    return order_id


def get_order(order_id: str) -> dict | None:
    """Retorna pedido ou None se não existir."""
    orders = _load_orders()
    return orders.get(order_id)


def update_order_status(order_id: str, status: str) -> bool:
    """Atualiza status do pedido. Retorna True se existir."""
    orders = _load_orders()
    if order_id not in orders:
        return False
    orders[order_id]["status"] = status
    orders[order_id]["updated_at"] = datetime.utcnow().isoformat() + "Z"
    _save_orders(orders)
    return True


def update_order_file_names(order_id: str, file_names: list[str]) -> bool:
    """Atualiza lista de arquivos do pedido."""
    orders = _load_orders()
    if order_id not in orders:
        return False
    orders[order_id]["file_names"] = file_names
    _save_orders(orders)
    return True

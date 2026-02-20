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
    """Cria pedido com pagamento e status pendentes. Retorna order_id."""
    orders = _load_orders()
    order_id = str(uuid.uuid4())
    orders[order_id] = {
        "order_id": order_id,
        "pet_name": pet_name,
        "user_email": user_email,
        "file_names": file_names,
        "pagamento": "pendente",
        "status": "pendente",
        "asaas_checkout_id": None,
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    _save_orders(orders)
    return order_id


def list_pending_production() -> list[dict]:
    """Retorna pedidos com pagamento ok e status pendente, ordenados por created_at (mais antigo primeiro)."""
    orders = _load_orders()
    pending = [
        {**o, "order_id": oid}
        for oid, o in orders.items()
        if o.get("pagamento") == "ok" and o.get("status") == "pendente"
    ]
    pending.sort(key=lambda p: p.get("created_at", ""))
    return pending


def get_order(order_id: str) -> dict | None:
    """Retorna pedido ou None se não existir."""
    orders = _load_orders()
    return orders.get(order_id)


def get_order_by_asaas_checkout_id(checkout_id: str) -> dict | None:
    """Retorna o pedido que possui o asaas_checkout_id dado, ou None."""
    orders = _load_orders()
    for oid, o in orders.items():
        if o.get("asaas_checkout_id") == checkout_id:
            return {**o, "order_id": oid}
    return None


def update_order_asaas_checkout_id(order_id: str, checkout_id: str) -> bool:
    """Associa o id do checkout Asaas ao pedido. Retorna True se existir."""
    orders = _load_orders()
    if order_id not in orders:
        return False
    orders[order_id]["asaas_checkout_id"] = checkout_id
    _save_orders(orders)
    return True


def update_order_pagamento(order_id: str, valor: str) -> bool:
    """Atualiza o campo pagamento do pedido (ex.: 'ok', 'pendente'). Retorna True se existir."""
    orders = _load_orders()
    if order_id not in orders:
        return False
    orders[order_id]["pagamento"] = valor
    orders[order_id]["updated_at"] = datetime.utcnow().isoformat() + "Z"
    _save_orders(orders)
    return True


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


def update_order_images_generated(order_id: str, value: bool) -> bool:
    """Marca se as imagens (gerado_*.png) já foram geradas para o pedido."""
    orders = _load_orders()
    if order_id not in orders:
        return False
    orders[order_id]["images_generated"] = value
    _save_orders(orders)
    return True


def update_order_pdf_generated(order_id: str, value: bool) -> bool:
    """Marca se o PDF do pedido já foi gerado."""
    orders = _load_orders()
    if order_id not in orders:
        return False
    orders[order_id]["pdf_generated"] = value
    _save_orders(orders)
    return True

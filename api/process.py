"""
Processa pedidos com pagamento ok e status pendente.
Envia os dados do pedido por email e marca como processado.
Rode com: uv run process.py (na pasta api) ou python -m api.process
"""
import store
from mail import enviar_email, log_email


def processar_pedido(pedido: dict) -> None:
    """
    Processa um pedido: envia dados por email e marca como processado.
    Em falha no envio, não atualiza o status (pedido será reprocessado).
    """
    order_id = pedido.get("order_id")
    if not order_id:
        return
    try:
        enviar_email(pedido)
        store.update_order_status(order_id, "processado")
    except Exception as e:
        msg = f"Pedido {order_id} - falha: {e}"
        print(msg)
        log_email(msg)


def run() -> None:
    pendentes = store.list_pending_production()
    if not pendentes:
        return
    for pedido in pendentes:
        processar_pedido(pedido)


if __name__ == "__main__":
    run()

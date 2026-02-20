"""
Processa pedidos com pagamento ok e status pendente.
Envia email, gera imagens (Gemini) e marca como processado.
Rode com: uv run process.py (na pasta api) ou python -m api.process
"""
from pathlib import Path

import store
from gemini import PROMPT_LINE_ART, gerar_imagem
from mail import enviar_email, log_email

EXTENSOES_IMAGEM = (".jpg", ".jpeg", ".png", ".webp")


def processar_pedido(pedido: dict) -> None:
    """
    Processa um pedido: envia email, gera imagens via Gemini, marca como processado.
    Em falha (email ou geração), não atualiza o status (pedido será reprocessado).
    """
    order_id = pedido.get("order_id")
    if not order_id:
        return
    try:
        enviar_email(pedido)
        pasta = store.UPLOADS_DIR / order_id
        file_names = pedido.get("file_names") or []
        for filename in file_names:
            path = pasta / filename
            if not path.exists() or path.suffix.lower() not in EXTENSOES_IMAGEM:
                continue
            image_bytes = path.read_bytes()
            out_bytes = gerar_imagem(image_bytes, PROMPT_LINE_ART)
            out_path = pasta / f"gerado_{path.stem}.png"
            out_path.write_bytes(out_bytes)
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

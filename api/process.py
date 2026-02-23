"""
Processa pedidos com pagamento ok e status pendente.
Gera imagens (Gemini): 1 line art fiel + 2 cenas de aventura por foto; monta PDF, envia email e marca como processado.
Rode com: uv run process.py (na pasta api) ou python -m api.process
"""
from pathlib import Path

import store
from gemini import PROMPT_LINE_ART, TEMAS_AVENTURA_V1, gerar_imagem, prompt_aventura
from mail import enviar_email, log_email
from pdf import gerar_pdf_pedido

EXTENSOES_IMAGEM = (".jpg", ".jpeg", ".png", ".webp")
LIVRO_PDF_NAME = "livro.pdf"


def processar_pedido(pedido: dict) -> None:
    """
    Processa um pedido: gera imagens via Gemini (1 fiel + 2 aventuras por foto, só as que faltam),
    monta PDF (ou usa o já gerado), envia email com anexo e marca como processado.
    Em falha (email ou geração), não atualiza o status (pedido será reprocessado).
    """
    order_id = pedido.get("order_id")
    if not order_id:
        return
    try:
        pasta = store.UPLOADS_DIR / order_id
        pet_name = pedido.get("pet_name", "")
        file_names = pedido.get("file_names") or []

        file_names_validos = [
            f for f in file_names
            if (pasta / f).exists() and Path(f).suffix.lower() in EXTENSOES_IMAGEM
        ]
        for filename in file_names_validos:
            path = pasta / filename
            stem = path.stem
            image_bytes = path.read_bytes()

            # 1) Line art fiel
            out_fiel = pasta / f"gerado_{stem}_fiel.png"
            if not out_fiel.exists():
                out_bytes = gerar_imagem(image_bytes, PROMPT_LINE_ART)
                out_fiel.write_bytes(out_bytes)

            # 2) Duas cenas de aventura (temas fixos v1: superhero, astronaut)
            for i, (tema_id, _) in enumerate(TEMAS_AVENTURA_V1, start=1):
                out_aventura = pasta / f"gerado_{stem}_aventura_{i}.png"
                if not out_aventura.exists():
                    prompt = prompt_aventura(tema_id, pet_name)
                    out_bytes = gerar_imagem(image_bytes, prompt)
                    out_aventura.write_bytes(out_bytes)

        store.update_order_images_generated(order_id, True)

        pdf_path = pasta / LIVRO_PDF_NAME
        if pedido.get("pdf_generated") and pdf_path.exists():
            pdf_bytes = pdf_path.read_bytes()
        else:
            pdf_bytes = b""
            try:
                pdf_bytes = gerar_pdf_pedido(pasta, pet_name, file_names_validos)
                pdf_path.write_bytes(pdf_bytes)
                store.update_order_pdf_generated(order_id, True)
            except ValueError:
                pass

        enviar_email(pedido, pdf_bytes=pdf_bytes if pdf_bytes else None)
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

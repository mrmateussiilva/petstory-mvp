"""
Envio de email com dados de pedido (SMTP via .env).
Registra sucesso e falha em email.log.
"""
import os
import smtplib
from datetime import datetime
from pathlib import Path
from email.message import EmailMessage

from dotenv import load_dotenv

load_dotenv()

EMAIL_LOG = Path(__file__).resolve().parent / "email.log"


def _log(message: str) -> None:
    """Append one line to email.log with timestamp."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(EMAIL_LOG, "a", encoding="utf-8") as f:
        f.write(f"{ts} - {message}\n")


def log_email(message: str) -> None:
    """Registra mensagem em email.log (sucesso ou falha)."""
    _log(message)


def enviar_email(pedido: dict, pdf_bytes: bytes | None = None) -> None:
    """Envia email com os dados do pedido. Se pdf_bytes for fornecido, anexa o PDF. Levanta exceção em falha."""
    server = os.getenv("SMTP_SERVER", "").strip()
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "").strip()
    password = os.getenv("SMTP_PASSWORD", "").strip()
    email_from = os.getenv("EMAIL_FROM", "").strip()
    from_name = os.getenv("EMAIL_FROM_NAME", "PetStory").strip()
    email_to = os.getenv("EMAIL_TO", "").strip()

    if not all([server, user, password, email_from]):
        raise ValueError("Variáveis SMTP/EMAIL incompletas no .env (EMAIL_TO é opcional)")

    order_id = pedido.get("order_id", "")
    pet_name = pedido.get("pet_name", "")
    user_email = (pedido.get("user_email") or "").strip()
    if not user_email:
        raise ValueError("Pedido sem email do usuário")
    file_names = pedido.get("file_names") or []
    created_at = pedido.get("created_at", "")

    body = "\n".join([
        f"Pedido: {order_id}",
        f"Nome do pet: {pet_name}",
        f"Arquivos: {', '.join(file_names) or 'nenhum'}",
        f"Data: {created_at}",
    ])

    msg = EmailMessage()
    msg["Subject"] = f"Pedido PetStory - {order_id}"
    msg["From"] = f"{from_name} <{email_from}>" if from_name else email_from
    msg["To"] = user_email
    if email_to:
        msg["Bcc"] = email_to
    msg.set_content(body)

    if pdf_bytes:
        msg.add_attachment(pdf_bytes, maintype="application", subtype="pdf", filename="livro_pet.pdf")

    with smtplib.SMTP(server, port) as smtp:
        smtp.starttls()
        smtp.login(user, password)
        smtp.send_message(msg)
    log_email(f"Pedido {order_id} - enviado com sucesso")

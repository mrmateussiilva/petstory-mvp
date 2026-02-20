"""Integração Asaas: criar checkout e processar webhook (CHECKOUT_PAID)."""
import json
import os
import urllib.request
import urllib.error

import store


def _base_url() -> str:
    """URL base da API: sandbox ou produção conforme ASAAS_PRODUCTION."""
    prod = os.getenv("ASAAS_PRODUCTION", "false").lower() in ("true", "1")
    return "https://api.asaas.com" if prod else "https://api-sandbox.asaas.com"


def _checkout_page_url(checkout_id: str) -> str:
    """URL da página de checkout para o cliente."""
    prod = os.getenv("ASAAS_PRODUCTION", "false").lower() in ("true", "1")
    host = "asaas.com" if prod else "sandbox.asaas.com"
    return f"https://{host}/checkoutSession/show?id={checkout_id}"


def criar_checkout(
    order_id: str,
    valor: float,
    nome_cliente: str,
    email_cliente: str,
    success_url: str,
    cancel_url: str,
) -> dict:
    """
    Cria sessão de checkout no Asaas. Retorna {"id": checkout_id, "checkout_url": url}.
    Levanta ValueError em falha de API ou resposta inválida.
    """
    api_key = os.getenv("ASAAS_API_KEY", "").strip()
    if not api_key:
        raise ValueError("ASAAS_API_KEY não configurada")

    payload = {
        "billingTypes": ["CREDIT_CARD", "PIX"],
        "chargeTypes": ["DETACHED"],
        "externalReference": order_id,
        "callback": {
            "successUrl": success_url,
            "cancelUrl": cancel_url,
        },
        "items": [
            {
                "name": "Livro Pet Story",
                "description": "Livro de colorir personalizado do seu pet",
                "quantity": 1,
                "value": round(valor, 2),
                "imageBase64": _placeholder_image_base64(),
            }
        ],
        "customerData": {
            "name": nome_cliente[:255],
            "email": email_cliente,
        },
        "minutesToExpire": 30,
    }

    req = urllib.request.Request(
        f"{_base_url()}/v3/checkouts",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "access_token": api_key,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        try:
            err = json.loads(body)
            msg = err.get("errors", [{}])[0].get("description", body) if isinstance(err.get("errors"), list) else body
        except Exception:
            msg = body or str(e)
        raise ValueError(f"Asaas: {msg}") from e
    except urllib.error.URLError as e:
        raise ValueError(f"Asaas: falha de conexão — {e.reason}") from e

    checkout_id = data.get("id")
    if not checkout_id:
        raise ValueError("Asaas: resposta sem id de checkout")

    return {
        "id": checkout_id,
        "checkout_url": _checkout_page_url(checkout_id),
    }


def _placeholder_image_base64() -> str:
    """Imagem 1x1 PNG transparente em base64 (obrigatória no item do checkout)."""
    return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="


def webhook_token_valido(token_recebido: str | None, token_esperado: str | None) -> bool:
    """
    Valida o token do webhook. O Asaas envia o token no header asaas-access-token.
    Se token_esperado estiver vazio (não configurado), aceita qualquer requisição.
    Caso contrário, exige que token_recebido seja igual ao configurado.
    """
    if not (token_esperado or "").strip():
        return True
    return (token_recebido or "").strip() == (token_esperado or "").strip()


def processar_webhook(body: dict) -> bool:
    """
    Processa POST do webhook Asaas. Trata CHECKOUT_PAID e marca pedido como pago.
    Retorna True se processou com sucesso, False se evento ignorado.
    """
    event = body.get("event")
    if event != "CHECKOUT_PAID":
        return False

    checkout = body.get("checkout")
    if not checkout:
        return False

    checkout_id = checkout.get("id")
    if not checkout_id:
        return False

    order = store.get_order_by_asaas_checkout_id(checkout_id)
    if not order:
        return False

    order_id = order.get("order_id")
    if not order_id:
        return False

    return store.update_order_pagamento(order_id, "ok")

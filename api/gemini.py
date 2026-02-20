"""
Geração de imagem estilo livro de colorir via API Gemini.
Key e model vêm do .env (GEMINI_API_KEY, GEMINI_MODEL).
"""
import base64
import io
import os
import time

import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
from PIL import Image

from dotenv import load_dotenv

load_dotenv()

PROMPT_LINE_ART = (
    "Convert this pet photo into a clean, realistic line art illustration suitable for a coloring book.\n\n"
    "CORE GOAL: Preserve the pet's real appearance, proportions, and expression. The pet must remain clearly recognizable.\n\n"
    "STYLE: Black-and-white outline drawing. Smooth, confident, continuous black lines. Medium-to-thick clean outlines. "
    "No sketchy lines, no cross-hatching, no shading, no gradients, no gray tones.\n\n"
    "DETAILS: Simplify fur into clean contour shapes. Keep facial features accurate but simplified. "
    "Pure white background. Black lines only. Center the pet. Remove background elements completely.\n\n"
    "OUTPUT: Clean, printable coloring book page."
)


def gerar_imagem(image_bytes: bytes, prompt: str) -> bytes:
    """
    Gera imagem a partir de foto (bytes) e prompt. Retorna PNG em bytes.
    Levanta ValueError se key/model faltando ou se a resposta não contiver imagem.
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    model_name = os.getenv("GEMINI_MODEL", "").strip()
    if not api_key or not model_name:
        raise ValueError("GEMINI_API_KEY e GEMINI_MODEL devem estar definidos no .env")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)

    img = Image.open(io.BytesIO(image_bytes))
    if img.mode != "RGB":
        img = img.convert("RGB")

    max_retries = 2
    for attempt in range(max_retries):
        try:
            response = model.generate_content(
                [prompt, img],
                generation_config={"temperature": 0.4},
            )
            break
        except ResourceExhausted:
            if attempt < max_retries - 1:
                time.sleep(5)
                continue
            raise

    if not response.candidates or not response.candidates[0].content.parts:
        raise ValueError("Resposta do Gemini sem conteúdo")

    for part in response.candidates[0].content.parts:
        if not getattr(part, "inline_data", None):
            continue
        data = part.inline_data.data
        if isinstance(data, str):
            image_data = base64.b64decode(data)
        elif isinstance(data, bytes):
            image_data = data
        else:
            image_data = bytes(data)
        if not image_data:
            continue
        out_img = Image.open(io.BytesIO(image_data))
        if out_img.mode != "RGB":
            out_img = out_img.convert("RGB")
        buf = io.BytesIO()
        out_img.save(buf, format="PNG")
        return buf.getvalue()

    raise ValueError("Nenhuma imagem encontrada na resposta do Gemini")

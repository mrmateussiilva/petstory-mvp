"""
Geração de imagem estilo livro de colorir via API Gemini (SDK google-genai).
Key e model vêm do .env (GEMINI_API_KEY, GEMINI_MODEL).
"""
import io
import os
import tempfile
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image

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
    if not model_name.startswith("models/"):
        model_name = f"models/{model_name}"

    client = genai.Client(api_key=api_key)
    image = Image.open(io.BytesIO(image_bytes))
    if image.mode != "RGB":
        image = image.convert("RGB")

    max_retries = 2
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=[prompt, image],
            )
            break
        except Exception as e:
            if "quota" in str(e).lower() or "resource_exhausted" in str(e).lower():
                if attempt < max_retries - 1:
                    time.sleep(5)
                    continue
            raise

    for part in response.parts:
        if part.text is not None:
            continue
        if part.inline_data is not None:
            image = part.as_image()
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                tmp_path = f.name
            try:
                image.save(tmp_path)
                with open(tmp_path, "rb") as f:
                    return f.read()
            finally:
                os.unlink(tmp_path)

    raise ValueError("Nenhuma imagem encontrada na resposta do Gemini")

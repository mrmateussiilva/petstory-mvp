from google import genai
from google.genai import types
from PIL import Image
from dotenv import load_dotenv
import os
load_dotenv()
client = genai.Client()

PROMPT_LINE_ART = (
    "Convert this pet photo into a clean, realistic line art illustration suitable for a coloring book.\n\n"
    "CORE GOAL: Preserve the pet's real appearance, proportions, and expression. The pet must remain clearly recognizable.\n\n"
    "STYLE: Black-and-white outline drawing. Smooth, confident, continuous black lines. Medium-to-thick clean outlines. "
    "No sketchy lines, no cross-hatching, no shading, no gradients, no gray tones.\n\n"
    "DETAILS: Simplify fur into clean contour shapes. Keep facial features accurate but simplified. "
    "Pure white background. Black lines only. Center the pet. Remove background elements completely.\n\n"
    "OUTPUT: Clean, printable coloring book page."
)

filename = r"/home/mateus/Images/dog1.jpg"
image = Image.open(filename)

response = client.models.generate_content(
    model=os.getenv("GEMINI_MODEL", "").strip(),
    contents=[PROMPT_LINE_ART, image],
)

for part in response.parts:
    if part.text is not None:
        print(part.text)
    elif part.inline_data is not None:
        image = part.as_image()
        image.save("dog1_line_art.png")

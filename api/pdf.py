"""
Gera PDF do pedido: capa (nome do pet), uma página por imagem gerada, contracapa petstory.live.
Usa fontes da pasta api/fonts (qualquer .ttf) nas escritas do livro.
"""
from pathlib import Path

from fpdf import FPDF

FONTS_DIR = Path(__file__).resolve().parent / "fonts"
FONT_FAMILY_LIVRO = "Livro"


def _setup_font(pdf: FPDF) -> bool:
    """Registra fonte da pasta api/fonts se existir algum .ttf. Retorna True se registrou."""
    ttfs = sorted(FONTS_DIR.glob("*.ttf"))
    if not ttfs:
        return False
    try:
        pdf.add_font(FONT_FAMILY_LIVRO, "", str(ttfs[0]), uni=True)
        return True
    except Exception:
        return False


def gerar_pdf_pedido(pasta: Path, pet_name: str) -> bytes:
    """
    Gera PDF com capa (nome do pet), uma página por gerado_*.png e contracapa.
    Retorna os bytes do PDF. Levanta ValueError se não houver nenhum gerado_*.png.
    """
    imagens = sorted(pasta.glob("gerado_*.png"))
    if not imagens:
        raise ValueError("Nenhuma imagem gerada para o pedido")

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    use_custom_font = _setup_font(pdf)
    font_name = FONT_FAMILY_LIVRO if use_custom_font else "helvetica"

    # Capa
    pdf.add_page()
    pdf.set_font(font_name, "B" if font_name == "helvetica" else "", size=24)
    pdf.ln(80)
    pdf.multi_cell(0, 12, pet_name, align="C")
    pdf.ln(20)
    pdf.set_font(font_name, "", size=14)
    pdf.cell(0, 10, "Livro de colorir", align="C", new_x="LMARGIN", new_y="NEXT")

    # Uma página por imagem
    for path in imagens:
        pdf.add_page()
        pdf.image(str(path), x=15, y=20, w=pdf.epw, h=pdf.eph, keep_aspect_ratio=True)

    # Contracapa
    pdf.add_page()
    pdf.set_font(font_name, "", size=16)
    pdf.ln(100)
    pdf.multi_cell(0, 12, "Gerado com muito amor pela\npetstory.live", align="C")

    return bytes(pdf.output())

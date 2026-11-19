from pathlib import Path
from typing import Any

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from app.services.generator.formatting_rules import (
    get_formatting_for_segment,
)


ALIGNMENT_MAP = {
    "left": WD_ALIGN_PARAGRAPH.LEFT,
    "center": WD_ALIGN_PARAGRAPH.CENTER,
    "right": WD_ALIGN_PARAGRAPH.RIGHT,
    "justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
}


def _set_paragraph_rtl(paragraph) -> None:
    """Set paragraph direction to right-to-left."""

    p_pr = paragraph._p.get_or_add_pPr()

    bidi = OxmlElement("w:bidi")
    bidi.set(qn("w:val"), "1")

    p_pr.append(bidi)


def _set_run_rtl(run) -> None:
    """Set run text direction to right-to-left."""

    r_pr = run._r.get_or_add_rPr()

    rtl = OxmlElement("w:rtl")
    rtl.set(qn("w:val"), "1")

    r_pr.append(rtl)


def _set_run_font(run, font_name: str, font_size: int) -> None:
    """Configure Latin and Arabic font settings."""

    run.font.name = font_name
    run.font.size = Pt(font_size)

    r_pr = run._r.get_or_add_rPr()

    fonts = r_pr.rFonts

    if fonts is None:
        fonts = OxmlElement("w:rFonts")
        r_pr.insert(0, fonts)

    fonts.set(qn("w:ascii"), font_name)
    fonts.set(qn("w:hAnsi"), font_name)
    fonts.set(qn("w:cs"), font_name)
    fonts.set(qn("w:eastAsia"), font_name)


def _configure_paragraph(
    paragraph,
    formatting,
) -> None:
    """Apply paragraph-level formatting."""

    paragraph.alignment = ALIGNMENT_MAP.get(
        formatting.alignment,
        WD_ALIGN_PARAGRAPH.RIGHT,
    )

    paragraph.paragraph_format.space_before = Pt(
        formatting.space_before
    )

    paragraph.paragraph_format.space_after = Pt(
        formatting.space_after
    )

    paragraph.paragraph_format.keep_with_next = (
        formatting.keep_with_next
    )

    if formatting.first_line_indent:
        paragraph.paragraph_format.first_line_indent = Pt(
            formatting.first_line_indent
        )

    if formatting.left_indent:
        paragraph.paragraph_format.left_indent = Pt(
            formatting.left_indent
        )

    if formatting.rtl:
        _set_paragraph_rtl(paragraph)


def _add_segment(
    doc: Document,
    segment: dict[str, Any],
) -> None:
    """
    Add one classified segment to the DOCX.

    Text is taken from original_text.
    Formatting is selected using selected_type.
    """

    text = segment.get("original_text", "")

    if text is None:
        text = ""

    segment_type = segment.get("selected_type")

    formatting = get_formatting_for_segment(
        segment_type
    )

    paragraph = doc.add_paragraph()

    _configure_paragraph(
        paragraph,
        formatting,
    )

    # Add a bullet marker for list items.
    if segment_type == "list_item":
        run = paragraph.add_run("• ")

        _set_run_font(
            run,
            formatting.font_name,
            formatting.font_size,
        )

        _set_run_rtl(run)

    run = paragraph.add_run(text)

    run.bold = formatting.bold
    run.italic = formatting.italic

    _set_run_font(
        run,
        formatting.font_name,
        formatting.font_size,
    )

    if formatting.rtl:
        _set_run_rtl(run)


def generate_docx(
    title: str,
    segments: list[dict[str, Any]],
    output_path: str | Path,
) -> Path:
    """
    Generate a deterministic editable DOCX document.

    Parameters
    ----------
    title:
        Document title.

    segments:
        Ordered segments containing original_text and selected_type.

    output_path:
        Destination path for the generated DOCX.

    Returns
    -------
    Path:
        The saved DOCX file path.
    """

    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    doc = Document()

    # Configure document defaults.
    styles = doc.styles

    normal_style = styles["Normal"]

    normal_style.font.name = "Arial"
    normal_style.font.size = Pt(14)

    # Document title.
    if title:
        title_paragraph = doc.add_paragraph()

        title_paragraph.alignment = (
            WD_ALIGN_PARAGRAPH.CENTER
        )

        _set_paragraph_rtl(title_paragraph)

        title_run = title_paragraph.add_run(title)

        title_run.bold = True
        title_run.font.size = Pt(24)

        _set_run_font(
            title_run,
            "Arial",
            24,
        )

        _set_run_rtl(title_run)

    # Avoid duplicating the document title when the first segment
    # already contains the same title.
    title_added = bool(title)

    for segment in segments:
        segment_type = segment.get("selected_type")
        segment_text = segment.get("original_text", "").strip()

        if (
            title_added
            and segment_type == "title"
            and segment_text == title.strip()
        ):
            title_added = False
            continue

        _add_segment(
            doc,
            segment,
        )

    # Save the document.
    doc.save(output_path)

    return output_path
from docx import Document
import sys
from pathlib import Path

# Add backend directory to Python's import path
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
from app.services.generator.docx_generator import generate_docx
def test_generate_docx_preserves_text(tmp_path):
    """Test that the generated DOCX preserves the original text."""

    original_text = "الشبكة هي مجموعة من الأجهزة المتصلة ببعضها البعض."

    segments = [
        {
            "original_text": original_text,
            "selected_type": "paragraph",
        }
    ]

    output_path = tmp_path / "test_text_preservation.docx"

    generate_docx(
        title="اختبار النص",
        segments=segments,
        output_path=output_path,
    )

    generated_doc = Document(output_path)

    generated_text = "\n".join(
        paragraph.text
        for paragraph in generated_doc.paragraphs
    )

    assert original_text in generated_text

def test_generate_docx_preserves_segment_order(tmp_path):
    """Test that segments appear in the same order as input."""

    segments = [
        {
            "original_text": "الجزء الأول",
            "selected_type": "heading",
        },
        {
            "original_text": "الجزء الثاني",
            "selected_type": "paragraph",
        },
        {
            "original_text": "الجزء الثالث",
            "selected_type": "conclusion",
        },
    ]

    output_path = tmp_path / "test_segment_order.docx"

    generate_docx(
        title="اختبار الترتيب",
        segments=segments,
        output_path=output_path,
    )

    generated_doc = Document(output_path)

    generated_text = [
        paragraph.text
        for paragraph in generated_doc.paragraphs
    ]

    expected_order = [
        "اختبار الترتيب",
        "الجزء الأول",
        "الجزء الثاني",
        "الجزء الثالث",
    ]

    assert generated_text == expected_order
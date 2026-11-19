import sys
from pathlib import Path

# Add backend directory to Python's import path
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
from app.services.generator.docx_generator import generate_docx

test_segments = [
    {
        "original_text": "الدرس الأول: الشبكات",
        "selected_type": "title",
    },
    {
        "original_text": "تعريف الشبكة",
        "selected_type": "heading",
    },
    {
        "original_text": "الشبكة هي مجموعة من الأجهزة المتصلة ببعضها البعض بهدف تبادل المعلومات والموارد.",
        "selected_type": "definition",
    },
    {
        "original_text": "تسمح الشبكات للأجهزة بالتواصل وتبادل البيانات بسرعة وفعالية.",
        "selected_type": "paragraph",
    },
    {
        "original_text": "مثال: شبكة محلية داخل مؤسسة تسمح للموظفين بمشاركة الملفات والطابعات.",
        "selected_type": "example",
    },
    {
        "original_text": "مشاركة الملفات",
        "selected_type": "list_item",
    },
    {
        "original_text": "مشاركة الطابعات",
        "selected_type": "list_item",
    },
    {
        "original_text": "تبادل المعلومات",
        "selected_type": "list_item",
    },
    {
        "original_text": "في النهاية، تساعد الشبكات على تسهيل الاتصال وتبادل الموارد بين الأجهزة.",
        "selected_type": "conclusion",
    },
    
]

output_path = Path("../storage/documents/test_multisegment.docx")
output_path.parent.mkdir(parents=True, exist_ok=True)

generate_docx(
    title="الدرس الأول: الشبكات",
    segments=test_segments,
    output_path=output_path,
)

print(f"Document generated successfully: {output_path}")


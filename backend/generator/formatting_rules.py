from dataclasses import dataclass
from typing import Literal


Alignment = Literal["left", "center", "right", "justify"]


@dataclass(frozen=True)
class SegmentFormatting:
    """
    Formatting configuration for an educational document segment.
    """

    font_name: str = "Arial"
    font_size: int = 14
    bold: bool = False
    italic: bool = False
    alignment: Alignment = "right"
    rtl: bool = True

    space_before: int = 0
    space_after: int = 8

    first_line_indent: int = 0
    left_indent: int = 0

    keep_with_next: bool = False


SEGMENT_FORMATTING_RULES: dict[str, SegmentFormatting] = {
    "title": SegmentFormatting(
        font_size=24,
        bold=True,
        alignment="center",
        space_before=12,
        space_after=20,
        keep_with_next=True,
    ),

    "subtitle": SegmentFormatting(
        font_size=18,
        bold=True,
        alignment="center",
        space_before=4,
        space_after=16,
        keep_with_next=True,
    ),

    "heading": SegmentFormatting(
        font_size=20,
        bold=True,
        alignment="right",
        space_before=16,
        space_after=10,
        keep_with_next=True,
    ),

    "subheading": SegmentFormatting(
        font_size=16,
        bold=True,
        alignment="right",
        space_before=12,
        space_after=8,
        keep_with_next=True,
    ),

    "paragraph": SegmentFormatting(
        font_size=14,
        alignment="justify",
        space_after=8,
        first_line_indent=0,
    ),

    "definition": SegmentFormatting(
        font_size=14,
        bold=False,
        alignment="justify",
        space_before=6,
        space_after=10,
        left_indent=10,
    ),

    "example": SegmentFormatting(
        font_size=14,
        italic=False,
        alignment="justify",
        space_before=8,
        space_after=10,
        left_indent=10,
    ),

    "quotation": SegmentFormatting(
        font_size=14,
        italic=True,
        alignment="justify",
        space_before=8,
        space_after=12,
        left_indent=20,
    ),

    "list_item": SegmentFormatting(
        font_size=14,
        alignment="right",
        space_after=4,
        left_indent=10,
    ),

    "question": SegmentFormatting(
        font_size=14,
        bold=True,
        alignment="right",
        space_before=8,
        space_after=6,
        keep_with_next=True,
    ),

    "answer": SegmentFormatting(
        font_size=14,
        alignment="justify",
        space_after=10,
        left_indent=10,
    ),

    "exercise_instruction": SegmentFormatting(
        font_size=14,
        bold=True,
        alignment="right",
        space_before=12,
        space_after=8,
        keep_with_next=True,
    ),

    "table": SegmentFormatting(
        font_size=12,
        alignment="center",
        space_before=8,
        space_after=8,
    ),

    "conclusion": SegmentFormatting(
        font_size=14,
        bold=False,
        alignment="justify",
        space_before=12,
        space_after=12,
    ),

    "other": SegmentFormatting(
        font_size=14,
        alignment="justify",
        space_after=8,
    ),
}


def get_formatting_for_segment(
    segment_type: str | None,
) -> SegmentFormatting:
    """
    Return formatting rules for a confirmed segment type.

    Unknown or missing types fall back to 'other'.
    """

    if not segment_type:
        return SEGMENT_FORMATTING_RULES["other"]

    return SEGMENT_FORMATTING_RULES.get(
        segment_type,
        SEGMENT_FORMATTING_RULES["other"],
    )
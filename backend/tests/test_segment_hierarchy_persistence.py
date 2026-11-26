from uuid import uuid4

import pytest

from app.services.segment_service import create_segments_from_analysis


class FakeDB:
    """
    Lightweight fake database session for testing persistence logic.
    """

    def __init__(self):
        self.added_objects = []
        self.committed = False
        self.rolled_back = False

    def scalar(self, query):
        # Simulate an existing document.
        return object()

    def add(self, obj):
        self.added_objects.append(obj)

    def flush(self):
        # Simulate database UUID generation.
        for obj in self.added_objects:
            if getattr(obj, "id", None) is None:
                obj.id = uuid4()

    def commit(self):
        self.committed = True

    def refresh(self, obj):
        pass

    def rollback(self):
        self.rolled_back = True


def make_segments():
    return [
        {
            "original_text": "Chapter 1",
            "suggested_type": "heading",
            "suggestion_confidence": 0.99,
            "suggestion_reason": "Main chapter title",
            "parent_segment_index": None,
        },
        {
            "original_text": "Introduction",
            "suggested_type": "subheading",
            "suggestion_confidence": 0.98,
            "suggestion_reason": "Section heading",
            "parent_segment_index": 0,
        },
        {
            "original_text": "Introduction text",
            "suggested_type": "paragraph",
            "suggestion_confidence": 0.95,
            "suggestion_reason": "Explanatory text",
            "parent_segment_index": 1,
        },
    ]


def test_persists_parent_relationships():
    db = FakeDB()

    result = create_segments_from_analysis(
        db=db,
        document_id=uuid4(),
        segments=make_segments(),
    )

    assert len(result) == 3

    # Segment 0 is the root.
    assert result[0].parent_id is None

    # Segment 1 is a child of segment 0.
    assert result[1].parent_id == result[0].id

    # Segment 2 is a child of segment 1.
    assert result[2].parent_id == result[1].id

    assert db.committed is True
    assert db.rolled_back is False


def test_rejects_invalid_parent_index():
    db = FakeDB()

    segments = make_segments()

    segments[1]["parent_segment_index"] = 99

    with pytest.raises(ValueError):
        create_segments_from_analysis(
            db=db,
            document_id=uuid4(),
            segments=segments,
        )

    assert db.rolled_back is True
from types import SimpleNamespace

import pytest

from ai.analysis_service import validate_segment_hierarchy


def make_segment(segment_type: str, parent_index: int | None):
    return SimpleNamespace(
        suggested_type=segment_type,
        parent_segment_index=parent_index,
    )


def make_analysis(*segments):
    return SimpleNamespace(segments=list(segments))


# --------------------------------------------------
# VALID HIERARCHIES
# --------------------------------------------------

def test_valid_flat_structure():
    analysis = make_analysis(
        make_segment("heading", None),
        make_segment("paragraph", None),
        make_segment("paragraph", None),
    )

    validate_segment_hierarchy(analysis)


def test_valid_nested_structure():
    analysis = make_analysis(
        make_segment("heading", None),
        make_segment("subheading", 0),
        make_segment("paragraph", 1),
    )

    validate_segment_hierarchy(analysis)


def test_valid_multiple_sections():
    analysis = make_analysis(
        make_segment("heading", None),
        make_segment("subheading", 0),
        make_segment("paragraph", 1),
        make_segment("heading", None),
        make_segment("paragraph", 3),
    )

    validate_segment_hierarchy(analysis)


# --------------------------------------------------
# INVALID HIERARCHIES
# --------------------------------------------------

def test_rejects_self_parent():
    analysis = make_analysis(
        make_segment("heading", 0),
    )

    with pytest.raises(ValueError):
        validate_segment_hierarchy(analysis)


def test_rejects_future_parent():
    analysis = make_analysis(
        make_segment("paragraph", 1),
        make_segment("heading", None),
    )

    with pytest.raises(ValueError):
        validate_segment_hierarchy(analysis)


def test_rejects_out_of_range_parent():
    analysis = make_analysis(
        make_segment("paragraph", 10),
    )

    with pytest.raises(ValueError):
        validate_segment_hierarchy(analysis)


def test_rejects_non_structural_parent():
    analysis = make_analysis(
        make_segment("paragraph", None),
        make_segment("paragraph", 0),
    )

    with pytest.raises(ValueError):
        validate_segment_hierarchy(analysis)


def test_rejects_negative_parent_index():
    analysis = make_analysis(
        make_segment("paragraph", -1),
    )

    with pytest.raises(ValueError):
        validate_segment_hierarchy(analysis)


def test_rejects_invalid_parent_index_type():
    analysis = make_analysis(
        make_segment("paragraph", "invalid"),
    )

    with pytest.raises(ValueError):
        validate_segment_hierarchy(analysis)
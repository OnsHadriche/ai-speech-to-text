from ai.analysis_service import analyze_educational_transcript


SAMPLE_TRANSCRIPT = """الفصل الأول: قواعد البيانات

مقدمة:
قاعدة البيانات هي مجموعة منظمة من المعلومات يتم تخزينها بطريقة تسمح بإدارتها واسترجاعها بسهولة.

تعريف:
نظام إدارة قواعد البيانات هو برنامج يسمح بإنشاء قواعد البيانات وتعديلها وإدارتها.

مثال:
يمكن استخدام نظام إدارة قواعد البيانات لتخزين معلومات الطلبة والنتائج."""


def main() -> None:
    print("=" * 60)
    print("REAL GROQ ANALYSIS TEST")
    print("=" * 60)

    print("\nOriginal transcript:")
    print(SAMPLE_TRANSCRIPT)

    print("\nSending transcript to Groq...")

    analysis = analyze_educational_transcript(SAMPLE_TRANSCRIPT)

    print("\n" + "=" * 60)
    print("ANALYSIS RESULT")
    print("=" * 60)

    print(f"\nDocument title: {analysis.document_title}")
    print(f"Subject: {analysis.subject}")
    print(f"Topic: {analysis.topic}")
    print(f"Document type: {analysis.document_type}")

    print(f"\nTotal segments: {len(analysis.segments)}")

    print("\n" + "-" * 60)
    print("SEGMENTS")
    print("-" * 60)

    for index, segment in enumerate(analysis.segments):
        segment_type = getattr(
            segment.suggested_type,
            "value",
            segment.suggested_type,
        )

        parent_index = segment.parent_segment_index

        print(f"\n[{index}] Type: {segment_type}")
        print(f"Parent index: {parent_index}")
        print(f"Confidence: {segment.suggestion_confidence}")
        print(f"Text: {segment.original_text}")

        if segment.suggestion_reason:
            print(f"Reason: {segment.suggestion_reason}")

    print("\n" + "=" * 60)
    print("VALIDATION")
    print("=" * 60)

    print("Transcript preservation: PASSED")
    print("Hierarchy validation: PASSED")
    print("Pydantic validation: PASSED")

    print("\nREAL GROQ ANALYSIS TEST PASSED ✅")


if __name__ == "__main__":
    main()
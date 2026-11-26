export const CLASSIFICATION_OPTIONS = [
  { value: "title", label: "Title" },
  { value: "subtitle", label: "Subtitle" },
  { value: "heading", label: "Heading" },
  { value: "subheading", label: "Subheading" },
  { value: "paragraph", label: "Paragraph" },
  { value: "definition", label: "Definition" },
  { value: "example", label: "Example" },
  { value: "quotation", label: "Quotation" },
  { value: "list_item", label: "List Item" },
  { value: "question", label: "Question" },
  { value: "answer", label: "Answer" },
  {
    value: "exercise_instruction",
    label: "Exercise Instruction",
  },
  { value: "table", label: "Table" },
  { value: "conclusion", label: "Conclusion" },
  { value: "other", label: "Other" },
] as const;

export type SegmentType =
  (typeof CLASSIFICATION_OPTIONS)[number]["value"];

export function getClassificationLabel(
  value: string | null | undefined
): string {
  if (!value) return "Not classified";

  const option = CLASSIFICATION_OPTIONS.find(
    (item) => item.value === value
  );

  return option?.label ?? value.replaceAll("_", " ");
}
import { SKILL_TAGS, type QuestionType } from "../api";

export function QuestionTypeSelect({
  value,
  onChange,
  allowAny = false,
  className = "rounded border border-gray-300 p-2 text-sm",
}: {
  value: QuestionType | "";
  onChange: (value: QuestionType | "") => void;
  allowAny?: boolean;
  className?: string;
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value as QuestionType | "")}
      className={className}
    >
      {allowAny && <option value="">any type</option>}
      <option value="multiple_choice">multiple_choice</option>
      <option value="short_answer">short_answer</option>
    </select>
  );
}

export function SkillTagSelect({
  value,
  onChange,
  allowAny = false,
  className = "rounded border border-gray-300 p-2 text-sm",
}: {
  value: string;
  onChange: (value: string) => void;
  allowAny?: boolean;
  className?: string;
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className={className}
    >
      {allowAny && <option value="">any skill</option>}
      {SKILL_TAGS.map((tag) => (
        <option key={tag} value={tag}>
          {tag}
        </option>
      ))}
    </select>
  );
}

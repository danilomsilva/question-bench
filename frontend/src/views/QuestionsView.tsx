import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, type QuestionType, type ListParams } from "../api";
import { QuestionTypeSelect, TopicSelect } from "../components/QuestionFilters";

export default function QuestionsView({
  onSelect,
}: {
  onSelect: (id: string) => void;
}) {
  const [questionType, setQuestionType] = useState<QuestionType | "">("");
  const [topic, setTopic] = useState("");

  const filters: ListParams = {};
  if (questionType) filters.question_type = questionType;
  if (topic) filters.topic = topic;

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["questions", filters],
    queryFn: () => api.listQuestions(filters),
  });

  return (
    <section>
      <h2 className="mb-3 text-lg font-semibold">Questions</h2>

      <div className="mb-3 flex gap-2">
        <QuestionTypeSelect value={questionType} onChange={setQuestionType} allowAny />
        <TopicSelect value={topic} onChange={setTopic} allowAny />
      </div>

      {isLoading && <p className="text-sm text-gray-500">Loading…</p>}
      {isError && <p className="text-sm text-red-600">{String(error)}</p>}
      {data?.length === 0 && (
        <p className="text-sm text-gray-500">No questions match.</p>
      )}

      {data && data.length > 0 && (
        <table className="w-full text-left text-sm">
          <thead className="border-b border-gray-200 text-gray-500">
            <tr>
              <th className="py-2 font-medium">Stem</th>
              <th className="font-medium">Type</th>
              <th className="font-medium">Topic</th>
              <th className="font-medium">Prompt</th>
            </tr>
          </thead>
          <tbody>
            {data.map((question) => (
              <tr
                key={question.id}
                onClick={() => onSelect(question.id)}
                className="cursor-pointer border-b border-gray-100 hover:bg-gray-50"
              >
                <td className="py-2 pr-4">{question.stem}</td>
                <td className="pr-4">{question.type}</td>
                <td className="pr-4">{question.topic}</td>
                <td>{question.prompt_version}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}

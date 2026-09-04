import { useState, type FormEvent } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api, type QuestionType } from "../api";
import { QuestionTypeSelect, SkillTagSelect } from "../components/QuestionFilters";

export default function GenerateView() {
  const queryClient = useQueryClient();
  const [questionType, setQuestionType] = useState<QuestionType>("multiple_choice");
  const [skillTag, setSkillTag] = useState("arithmetic");
  const [count, setCount] = useState(1);

  const mutation = useMutation({
    mutationFn: () =>
      api.generate({ question_type: questionType, skill_tag: skillTag, count }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["questions"] }),
  });

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    mutation.mutate();
  }

  return (
    <section>
      <h2 className="mb-3 text-lg font-semibold">Generate questions</h2>
      <form onSubmit={onSubmit} className="space-y-3">
        <label className="block">
          <span className="text-sm text-gray-600">Type</span>
          <QuestionTypeSelect
            value={questionType}
            onChange={(value) => value && setQuestionType(value)}
            className="mt-1 block w-full rounded border border-gray-300 p-2"
          />
        </label>

        <label className="block">
          <span className="text-sm text-gray-600">Skill tag</span>
          <SkillTagSelect
            value={skillTag}
            onChange={setSkillTag}
            className="mt-1 block w-full rounded border border-gray-300 p-2"
          />
        </label>

        <label className="block">
          <span className="text-sm text-gray-600">Count (1-10)</span>
          <input
            type="number"
            min={1}
            max={10}
            value={count}
            onChange={(e) => setCount(Number(e.target.value))}
            className="mt-1 block w-32 rounded border border-gray-300 p-2"
          />
        </label>

        <button
          type="submit"
          disabled={mutation.isPending}
          className="rounded bg-black px-4 py-2 text-white disabled:opacity-50"
        >
          {mutation.isPending ? "Generating…" : "Generate"}
        </button>
      </form>

      {mutation.isError && (
        <p className="mt-3 text-sm text-red-600">{String(mutation.error)}</p>
      )}
      {mutation.isSuccess && (
        <p className="mt-3 text-sm text-green-700">
          Created {mutation.data.length} question(s) — see the Questions tab.
        </p>
      )}
    </section>
  );
}

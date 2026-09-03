import { useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type Item } from "../api";

export default function ItemDetailView({
  id,
  onBack,
}: {
  id: string;
  onBack: () => void;
}) {
  const { data: item, isLoading, isError, error } = useQuery({
    queryKey: ["item", id],
    queryFn: () => api.getItem(id),
  });

  return (
    <section>
      <button onClick={onBack} className="mb-3 text-sm text-blue-600">
        ← back to items
      </button>
      {isLoading && <p className="text-sm text-gray-500">Loading…</p>}
      {isError && <p className="text-sm text-red-600">{String(error)}</p>}
      {item && (
        <>
          <Meta item={item} />
          <EditForm key={item.updated_at} item={item} />
        </>
      )}
    </section>
  );
}

function Meta({ item }: { item: Item }) {
  return (
    <dl className="mb-4 grid grid-cols-[8rem_1fr] gap-x-4 gap-y-1 text-sm">
      <dt className="text-gray-500">id</dt>
      <dd className="font-mono text-xs">{item.id}</dd>
      <dt className="text-gray-500">type</dt>
      <dd>{item.type}</dd>
      <dt className="text-gray-500">skill_tag</dt>
      <dd>{item.skill_tag}</dd>
      <dt className="text-gray-500">prompt_version</dt>
      <dd>{item.prompt_version}</dd>
      <dt className="text-gray-500">updated_at</dt>
      <dd>{item.updated_at}</dd>
    </dl>
  );
}

function EditForm({ item }: { item: Item }) {
  const queryClient = useQueryClient();
  const [stem, setStem] = useState(item.stem);
  const [optionsText, setOptionsText] = useState(
    item.type === "multiple_choice" ? item.options.join("\n") : "",
  );
  const [correctAnswer, setCorrectAnswer] = useState(
    item.type === "multiple_choice" ? item.correct_answer : "",
  );
  const [answer, setAnswer] = useState(
    item.type === "short_answer" ? item.answer : "",
  );

  const mutation = useMutation({
    mutationFn: () => {
      const body: Record<string, unknown> = { stem };
      if (item.type === "multiple_choice") {
        body.options = optionsText
          .split("\n")
          .map((line) => line.trim())
          .filter(Boolean);
        body.correct_answer = correctAnswer;
      } else {
        body.answer = answer;
      }
      return api.patchItem(item.id, body);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["item", item.id] });
      queryClient.invalidateQueries({ queryKey: ["items"] });
    },
  });

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    mutation.mutate();
  }

  return (
    <form onSubmit={onSubmit} className="space-y-3">
      <label className="block">
        <span className="text-sm text-gray-600">Stem</span>
        <textarea
          value={stem}
          onChange={(e) => setStem(e.target.value)}
          rows={2}
          className="mt-1 block w-full rounded border border-gray-300 p-2"
        />
      </label>

      {item.type === "multiple_choice" ? (
        <>
          <label className="block">
            <span className="text-sm text-gray-600">Options (one per line)</span>
            <textarea
              value={optionsText}
              onChange={(e) => setOptionsText(e.target.value)}
              rows={4}
              className="mt-1 block w-full rounded border border-gray-300 p-2 font-mono text-sm"
            />
          </label>
          <label className="block">
            <span className="text-sm text-gray-600">Correct answer</span>
            <input
              value={correctAnswer}
              onChange={(e) => setCorrectAnswer(e.target.value)}
              className="mt-1 block w-full rounded border border-gray-300 p-2"
            />
          </label>
        </>
      ) : (
        <label className="block">
          <span className="text-sm text-gray-600">Answer</span>
          <input
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            className="mt-1 block w-full rounded border border-gray-300 p-2"
          />
        </label>
      )}

      <button
        type="submit"
        disabled={mutation.isPending}
        className="rounded bg-black px-4 py-2 text-white disabled:opacity-50"
      >
        {mutation.isPending ? "Saving…" : "Save changes"}
      </button>

      {mutation.isError && (
        <p className="text-sm text-red-600">{String(mutation.error)}</p>
      )}
      {mutation.isSuccess && (
        <p className="text-sm text-green-700">Saved.</p>
      )}
    </form>
  );
}

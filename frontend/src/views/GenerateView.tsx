import { useState, type FormEvent } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api, type ItemType } from "../api";

export default function GenerateView() {
  const queryClient = useQueryClient();
  const [itemType, setItemType] = useState<ItemType>("multiple_choice");
  const [skillTag, setSkillTag] = useState("arithmetic");
  const [count, setCount] = useState(1);

  const mutation = useMutation({
    mutationFn: () =>
      api.generate({ item_type: itemType, skill_tag: skillTag, count }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["items"] }),
  });

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    mutation.mutate();
  }

  return (
    <section>
      <h2 className="mb-3 text-lg font-semibold">Generate items</h2>
      <form onSubmit={onSubmit} className="space-y-3">
        <label className="block">
          <span className="text-sm text-gray-600">Type</span>
          <select
            value={itemType}
            onChange={(e) => setItemType(e.target.value as ItemType)}
            className="mt-1 block w-full rounded border border-gray-300 p-2"
          >
            <option value="multiple_choice">multiple_choice</option>
            <option value="short_answer">short_answer</option>
          </select>
        </label>

        <label className="block">
          <span className="text-sm text-gray-600">Skill tag</span>
          <input
            value={skillTag}
            onChange={(e) => setSkillTag(e.target.value)}
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
          Created {mutation.data.length} item(s) — see the Items tab.
        </p>
      )}
    </section>
  );
}

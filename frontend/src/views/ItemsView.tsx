import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, type ItemType, type ListParams } from "../api";

export default function ItemsView({
  onSelect,
}: {
  onSelect: (id: string) => void;
}) {
  const [itemType, setItemType] = useState<ItemType | "">("");
  const [skillTag, setSkillTag] = useState("");

  const filters: ListParams = {};
  if (itemType) filters.item_type = itemType;
  if (skillTag) filters.skill_tag = skillTag;

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["items", filters],
    queryFn: () => api.listItems(filters),
  });

  return (
    <section>
      <h2 className="mb-3 text-lg font-semibold">Items</h2>

      <div className="mb-3 flex gap-2">
        <select
          value={itemType}
          onChange={(e) => setItemType(e.target.value as ItemType | "")}
          className="rounded border border-gray-300 p-2 text-sm"
        >
          <option value="">any type</option>
          <option value="multiple_choice">multiple_choice</option>
          <option value="short_answer">short_answer</option>
        </select>
        <input
          value={skillTag}
          onChange={(e) => setSkillTag(e.target.value)}
          placeholder="skill tag"
          className="rounded border border-gray-300 p-2 text-sm"
        />
      </div>

      {isLoading && <p className="text-sm text-gray-500">Loading…</p>}
      {isError && <p className="text-sm text-red-600">{String(error)}</p>}
      {data?.length === 0 && (
        <p className="text-sm text-gray-500">No items match.</p>
      )}

      {data && data.length > 0 && (
        <table className="w-full text-left text-sm">
          <thead className="border-b border-gray-200 text-gray-500">
            <tr>
              <th className="py-2 font-medium">Stem</th>
              <th className="font-medium">Type</th>
              <th className="font-medium">Skill</th>
              <th className="font-medium">Prompt</th>
            </tr>
          </thead>
          <tbody>
            {data.map((item) => (
              <tr
                key={item.id}
                onClick={() => onSelect(item.id)}
                className="cursor-pointer border-b border-gray-100 hover:bg-gray-50"
              >
                <td className="py-2 pr-4">{item.stem}</td>
                <td className="pr-4">{item.type}</td>
                <td className="pr-4">{item.skill_tag}</td>
                <td>{item.prompt_version}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}

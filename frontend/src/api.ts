// Types mirror the Pydantic models in src/item_bench/. Kept by hand -
// the surface is tiny and this repo isn't demonstrating codegen.

export type ItemType = "multiple_choice" | "short_answer";

interface BaseItem {
  id: string;
  stem: string;
  skill_tag: string;
  prompt_version: string;
  created_at: string;
  updated_at: string;
}

export interface MultipleChoiceItem extends BaseItem {
  type: "multiple_choice";
  options: string[];
  correct_answer: string;
}

export interface ShortAnswerItem extends BaseItem {
  type: "short_answer";
  answer: string;
}

export type Item = MultipleChoiceItem | ShortAnswerItem;

export interface RuleResult {
  rule: string;
  passed: boolean;
  detail: string | null;
}

export interface EvaluationReport {
  item_id: string;
  prompt_version: string;
  results: RuleResult[];
  passed: boolean;
  score: number;
  evaluated_at: string;
}

export interface GenerateRequest {
  item_type: ItemType;
  skill_tag: string;
  count: number;
}

export interface PromptVersionStats {
  prompt_version: string;
  evaluations: number;
  passed: number;
  pass_rate: number;
}

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { "content-type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    throw new Error(`${res.status} ${res.statusText}: ${await res.text()}`);
  }
  return (await res.json()) as T;
}

export interface ListParams {
  item_type?: ItemType;
  skill_tag?: string;
}

export const api = {
  generate: (req: GenerateRequest) =>
    http<Item[]>("/generate", { method: "POST", body: JSON.stringify(req) }),

  listItems: (params: ListParams = {}) => {
    const query = new URLSearchParams();
    if (params.item_type) query.set("item_type", params.item_type);
    if (params.skill_tag) query.set("skill_tag", params.skill_tag);
    const qs = query.toString();
    return http<Item[]>(`/items${qs ? `?${qs}` : ""}`);
  },

  getItem: (id: string) => http<Item>(`/items/${id}`),

  patchItem: (id: string, body: Record<string, unknown>) =>
    http<Item>(`/items/${id}`, { method: "PATCH", body: JSON.stringify(body) }),

  evaluate: (id: string) =>
    http<EvaluationReport>(`/items/${id}/evaluate`, { method: "POST" }),

  passRate: () => http<PromptVersionStats[]>("/stats/pass-rate"),
};

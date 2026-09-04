// Types mirror the Pydantic models in src/question_bench/. Kept by hand -
// the surface is tiny and this repo isn't demonstrating codegen.

export type QuestionType = "multiple_choice" | "short_answer";

// Mirrors question_bench.skill_tags.ALLOWED_SKILL_TAGS.
export const SKILL_TAGS = [
  "arithmetic",
  "fractions",
  "algebra",
  "geometry",
  "measurement",
  "data-and-statistics",
] as const;

interface BaseQuestion {
  id: string;
  stem: string;
  skill_tag: string;
  prompt_version: string;
  created_at: string;
  updated_at: string;
}

export interface MultipleChoiceQuestion extends BaseQuestion {
  type: "multiple_choice";
  options: string[];
  correct_answer: string;
}

export interface ShortAnswerQuestion extends BaseQuestion {
  type: "short_answer";
  answer: string;
}

export type Question = MultipleChoiceQuestion | ShortAnswerQuestion;

export interface RuleResult {
  rule: string;
  passed: boolean;
  detail: string | null;
}

export interface EvaluationReport {
  question_id: string;
  prompt_version: string;
  results: RuleResult[];
  passed: boolean;
  score: number;
  evaluated_at: string;
}

export interface GenerateRequest {
  question_type: QuestionType;
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
  question_type?: QuestionType;
  skill_tag?: string;
}

export const api = {
  generate: (req: GenerateRequest) =>
    http<Question[]>("/generate", { method: "POST", body: JSON.stringify(req) }),

  listQuestions: (params: ListParams = {}) => {
    const query = new URLSearchParams();
    if (params.question_type) query.set("question_type", params.question_type);
    if (params.skill_tag) query.set("skill_tag", params.skill_tag);
    const qs = query.toString();
    return http<Question[]>(`/questions${qs ? `?${qs}` : ""}`);
  },

  getQuestion: (id: string) => http<Question>(`/questions/${id}`),

  patchQuestion: (id: string, body: Record<string, unknown>) =>
    http<Question>(`/questions/${id}`, { method: "PATCH", body: JSON.stringify(body) }),

  evaluate: (id: string) =>
    http<EvaluationReport>(`/questions/${id}/evaluate`, { method: "POST" }),

  passRate: () => http<PromptVersionStats[]>("/stats/pass-rate"),
};

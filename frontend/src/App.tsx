import { useState } from "react";
import GenerateView from "./views/GenerateView";
import QuestionsView from "./views/QuestionsView";
import QuestionDetailView from "./views/QuestionDetailView";
import PassRateView from "./views/PassRateView";

type Tab = "generate" | "questions" | "passrate";

const TABS: Tab[] = ["generate", "questions", "passrate"];
const LABELS: Record<Tab, string> = {
  generate: "generate",
  questions: "questions",
  passrate: "pass rates",
};

export default function App() {
  const [tab, setTab] = useState<Tab>("generate");
  const [selectedId, setSelectedId] = useState<string | null>(null);

  function switchTab(next: Tab) {
    setTab(next);
    setSelectedId(null);
  }

  return (
    <div className="mx-auto max-w-4xl p-6">
      <header className="mb-6">
        <h1 className="text-2xl font-bold">question-bench</h1>
        <nav className="mt-3 flex gap-2">
          {TABS.map((t) => (
            <button
              key={t}
              onClick={() => switchTab(t)}
              className={`rounded px-3 py-1 text-sm ${
                tab === t ? "bg-black text-white" : "bg-gray-100"
              }`}
            >
              {LABELS[t]}
            </button>
          ))}
        </nav>
      </header>

      {tab === "generate" && <GenerateView />}

      {tab === "questions" && selectedId === null && (
        <QuestionsView onSelect={setSelectedId} />
      )}
      {tab === "questions" && selectedId !== null && (
        <QuestionDetailView id={selectedId} onBack={() => setSelectedId(null)} />
      )}

      {tab === "passrate" && <PassRateView />}
    </div>
  );
}

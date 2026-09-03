import { useState } from "react";
import GenerateView from "./views/GenerateView";

type Tab = "generate" | "items" | "passrate";

const TABS: Tab[] = ["generate", "items", "passrate"];
const LABELS: Record<Tab, string> = {
  generate: "generate",
  items: "items",
  passrate: "pass rates",
};

export default function App() {
  const [tab, setTab] = useState<Tab>("generate");

  return (
    <div className="mx-auto max-w-4xl p-6">
      <header className="mb-6">
        <h1 className="text-2xl font-bold">item-bench</h1>
        <nav className="mt-3 flex gap-2">
          {TABS.map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
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
      {tab !== "generate" && (
        <p className="text-sm text-gray-500">Coming in the next step.</p>
      )}
    </div>
  );
}

import { useQuery } from "@tanstack/react-query";
import { api } from "../api";

export default function PassRateView() {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["pass-rate"],
    queryFn: api.passRate,
  });

  return (
    <section>
      <h2 className="mb-1 text-lg font-semibold">Pass rate by prompt version</h2>
      <p className="mb-3 text-sm text-gray-500">
        Every evaluation ever run, grouped by the prompt that produced the question.
      </p>

      {isLoading && <p className="text-sm text-gray-500">Loading…</p>}
      {isError && <p className="text-sm text-red-600">{String(error)}</p>}
      {data?.length === 0 && (
        <p className="text-sm text-gray-500">
          No evaluations yet — run a quality check on a question first.
        </p>
      )}

      {data && data.length > 0 && (
        <table className="w-full text-left text-sm">
          <thead className="border-b border-gray-200 text-gray-500">
            <tr>
              <th className="py-2 font-medium">Prompt version</th>
              <th className="font-medium">Evaluations</th>
              <th className="font-medium">Passed</th>
              <th className="font-medium">Pass rate</th>
            </tr>
          </thead>
          <tbody>
            {data.map((row) => (
              <tr key={row.prompt_version} className="border-b border-gray-100">
                <td className="py-2 pr-4 font-mono">{row.prompt_version}</td>
                <td className="pr-4">{row.evaluations}</td>
                <td className="pr-4">{row.passed}</td>
                <td>{(row.pass_rate * 100).toFixed(0)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}

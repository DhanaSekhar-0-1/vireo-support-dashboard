import { useState } from "react";
import {
  explainAgentPerformance,
  type AgentExplanationRequest,
} from "../../services/ai";

interface Props {
  agent: AgentExplanationRequest;
}

export default function AgentAiExplanation({
  agent,
}: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [explanation, setExplanation] = useState("");

  async function handleExplain() {
    try {
      setLoading(true);
      setError(null);

      const result = await explainAgentPerformance(agent);
      setExplanation(result.explanation);
    } catch (err: any) {
      setError(
        err?.response?.data?.detail ||
          err?.message ||
          "Unable to generate AI explanation."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="ai-explanation">
      <div className="panel-header">
        <div>
          <h3>AI Performance Explanation</h3>
          <p>
            AI explains calculated performance signals.
            Dashboard metrics remain deterministic.
          </p>
        </div>

        <button
          type="button"
          onClick={handleExplain}
          disabled={loading}
          className="ai-explain-button"
        >
          {loading ? "Analyzing..." : "Explain with AI"}
        </button>
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {explanation && (
        <div className="ai-explanation-content">
          {explanation.split("\n").map((line, index) => {
            if (!line.trim()) {
              return (
                <div
                  key={index}
                  className="ai-spacer"
                />
              );
            }

            if (
              [
                "Summary",
                "Signals",
                "Coaching focus",
                "Caveat",
              ].includes(line.trim())
            ) {
              return (
                <h4 key={index}>
                  {line.trim()}
                </h4>
              );
            }

            return (
              <p key={index}>
                {line}
              </p>
            );
          })}
        </div>
      )}
    </div>
  );
}

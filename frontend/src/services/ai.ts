import api from "./api";

export interface AgentExplanationRequest {
  agent_id: string;
  name: string;
  site: string;
  team: string;
  tier: number;

  tickets: number;
  csat_responses: number;
  csat: number | null;

  avg_handle_time_minutes: number | null;

  sla_breaches: number;
  sla_breach_rate: number;

  replacements: number;
  transfers: number;
  attendance_rate: number;

  peer_csat?: number | null;
  peer_gap?: number | null;

  confidence?: number | null;
  priority_score?: number | null;

  priority?: string | null;
}

export interface AgentExplanationResponse {
  agent_id: string;
  provider: string;
  model: string;
  explanation: string;
}

export async function explainAgentPerformance(
  agent: AgentExplanationRequest
): Promise<AgentExplanationResponse> {
  const response =
    await api.post<AgentExplanationResponse>(
      "/api/ai/agent-explanation",
      agent
    );

  return response.data;
}
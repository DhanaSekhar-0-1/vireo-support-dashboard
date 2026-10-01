import axios from "axios";

export interface DashboardSummary {
  tickets: number;
  agents: number;
  customers: number;
  orders: number;
  products: number;
}

export interface Agent {
  agent_id: string;
  name: string;
  site: string;
  team: string;
  shift: string;
  tier: number;
  tickets: number;
  csat_responses: number;
  csat: number | null;
  avg_handle_time_minutes: number | null;
  sla_breaches: number;
  sla_eligible: number;
  sla_breach_rate: number;
  replacements: number;
  transfers: number;
  attendance_rate: number;
}

export interface TrainingPriority extends Agent {
  peer_csat: number | null;
  peer_gap: number | null;
  confidence: number;
  priority_score: number;
  priority: string;
}

export interface MonthlyTrend {
  created_month: string;
  tickets: number;
  csat_responses: number;
  csat: number | null;
  sla_breaches: number;
  sla_eligible: number;
  replacements: number;
  avg_handle_time_minutes: number | null;
  sla_breach_rate: number;
  replacement_rate: number;
}

export interface DataQuality {
  total_tickets: number;
  duplicate_ticket_ids: number;
  missing_agent_id: number;
  unknown_agent_ids: number;
  missing_first_response: number;
  negative_first_response: number;
  resolved_without_resolution: number;
  negative_handle_time?: number;
  invalid_handle_time: number;
  invalid_channels: number;
  invalid_csat: number;
  missing_sla_target: number;
  legacy_tickets: number;
  helpdesk_tickets: number;
  missing_resolution_total: number;
}

const api = axios.create({
  baseURL: "http://127.0.0.1:8000",
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30_000,
});

export const getTrends = async (): Promise<MonthlyTrend[]> => {
  const response = await api.get<MonthlyTrend[]>("/api/trends");
  return response.data;
};

export const getSummary = async (): Promise<DashboardSummary> => {
  const response = await api.get<DashboardSummary>("/api/data/summary");
  return response.data;
};

export const getAgents = async (
  startDate?: string,
  endDate?: string
): Promise<Agent[]> => {
  const response = await api.get<Agent[]>("/api/agents", {
    params:
      startDate && endDate
        ? { start_date: startDate, end_date: endDate }
        : undefined,
  });

  return response.data;
};

export const getTrainingPriority = async (
  startDate?: string,
  endDate?: string
): Promise<TrainingPriority[]> => {
  const response = await api.get<TrainingPriority[]>(
    "/api/training-priority",
    {
      params:
        startDate && endDate
          ? { start_date: startDate, end_date: endDate }
          : undefined,
    }
  );

  return response.data;
};

export const getDataQuality = async (): Promise<DataQuality> => {
  const response = await api.get<DataQuality>("/api/data/quality");
  return response.data;
};

export default api;

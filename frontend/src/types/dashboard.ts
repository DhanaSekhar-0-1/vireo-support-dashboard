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

export interface TrainingPriority {
  agent_id: string;
  name: string;
  site: string;
  team: string;
  tier: number;

  tickets: number;
  csat_responses: number;
  csat: number | null;

  avg_handle_time_minutes: number | null;

  peer_csat: number | null;
  peer_gap: number | null;

  sla_breach_rate: number;

  confidence: number;
  priority_score: number;
  priority: string;
}

export interface MonthlyTrend {
  month: string;

  tickets: number;
  csat_responses: number;
  csat: number | null;

  sla_breaches: number;
  sla_eligible: number;
  sla_breach_rate: number;

  replacements: number;
  replacement_rate: number;

  avg_handle_time_minutes: number | null;
}

export interface DataQuality {
  total_tickets: number;

  duplicate_ticket_ids: number;
  missing_agent_id: number;
  unknown_agent_ids: number;

  missing_first_response: number;
  negative_first_response: number;

  resolved_without_resolution: number;

  negative_handle_time: number;
  invalid_handle_time: number;

  invalid_channels: number;
  invalid_csat: number;
  missing_sla_target: number;

  legacy_tickets: number;
  helpdesk_tickets: number;

  missing_resolution_total: number;
}
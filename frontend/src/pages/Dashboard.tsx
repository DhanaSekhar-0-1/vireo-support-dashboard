import { useEffect, useMemo, useState } from "react";
import * as XLSX from "xlsx";
import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";
import AgentAiExplanation from "../components/ai/AgentAiExplanation";

import {
  getSummary,
  getAgents,
  getTrainingPriority,
  getTrends,
  getDataQuality,
} from "../services/api";

import OperationsCharts from "../components/charts/OperationsCharts";

type PeriodKey =
  | "H1_2025"
  | "H2_2025"
  | "H1_2026"
  | "ALL";

const PERIODS: {
  key: PeriodKey;
  label: string;
  start: string;
  end: string;
}[] = [
  {
    key: "H1_2025",
    label: "H1 2025 · Jan–Jun",
    start: "2025-01",
    end: "2025-06",
  },
  {
    key: "H2_2025",
    label: "H2 2025 · Jul–Dec",
    start: "2025-07",
    end: "2025-12",
  },
  {
    key: "H1_2026",
    label: "H1 2026 · Jan–Jun",
    start: "2026-01",
    end: "2026-06",
  },
  {
    key: "ALL",
    label: "All Periods",
    start: "0000-00",
    end: "9999-99",
  },
];

function exportToCSV(
  data: Record<string, any>[],
  filename: string
) {
  if (!data.length) return;

  const worksheet = XLSX.utils.json_to_sheet(data);
  const workbook = XLSX.utils.book_new();

  XLSX.utils.book_append_sheet(workbook, worksheet, "Data");

  XLSX.writeFile(workbook, `${filename}.csv`, {
    bookType: "csv",
  });
}

function exportToExcel(
  data: Record<string, any>[],
  filename: string
) {
  if (!data.length) return;

  const worksheet = XLSX.utils.json_to_sheet(data);
  const workbook = XLSX.utils.book_new();

  XLSX.utils.book_append_sheet(workbook, worksheet, "Data");

  XLSX.writeFile(workbook, `${filename}.xlsx`);
}

function exportToPDF(
  data: Record<string, any>[],
  filename: string,
  title: string
) {
  if (!data.length) return;

  const doc = new jsPDF("landscape");

  const headers = Object.keys(data[0]);

  const rows = data.map(row =>
    headers.map(header => {
      const value = row[header];

      if (value === null || value === undefined) {
        return "";
      }

      return String(value);
    })
  );

  doc.setFontSize(16);
  doc.text(title, 14, 15);

  autoTable(doc, {
    head: [headers],
    body: rows,
    startY: 22,
    styles: {
      fontSize: 8,
      cellPadding: 3,
    },
    headStyles: {
      fontSize: 8,
    },
  });

  doc.save(`${filename}.pdf`);
}

function DownloadMenu({
  data,
  filename,
  title,
}: {
  data: Record<string, any>[];
  filename: string;
  title: string;
}) {
  const [open, setOpen] = useState(false);

  return (
    <div className="download-menu">
      <button
        type="button"
        className="download-button"
        onClick={() => setOpen(!open)}
      >
        ↓ Download
        <span className="download-chevron">⌄</span>
      </button>

      {open && (
        <div className="download-dropdown">
          <button
            type="button"
            onClick={() => {
              exportToCSV(data, filename);
              setOpen(false);
            }}
          >
            <span>CSV</span>
            <small>.csv</small>
          </button>

          <button
            type="button"
            onClick={() => {
              exportToExcel(data, filename);
              setOpen(false);
            }}
          >
            <span>Excel</span>
            <small>.xlsx</small>
          </button>

          <button
            type="button"
            onClick={() => {
              exportToPDF(data, filename, title);
              setOpen(false);
            }}
          >
            <span>PDF</span>
            <small>.pdf</small>
          </button>
        </div>
      )}
    </div>
  );
}

function Dashboard() {
  const [summary, setSummary] =
    useState<DashboardSummary | null>(null);

  const [agents, setAgents] =
    useState<Agent[]>([]);

  const [priority, setPriority] =
    useState<TrainingPriority[]>([]);

  const [trends, setTrends] =
    useState<MonthlyTrend[]>([]);

  // --------------------------------------------------
  // PERIOD FILTER
  // --------------------------------------------------

  const [selectedPeriod, setSelectedPeriod] =
    useState<PeriodKey>("H1_2026");

  // --------------------------------------------------
  // ADDITIONAL FILTERS
  // --------------------------------------------------

  const [selectedTeam, setSelectedTeam] =
    useState("All");

  const [selectedSite, setSelectedSite] =
    useState("All");

  const [selectedTier, setSelectedTier] =
    useState("All");
  
  const [selectedAgent, setSelectedAgent] = 
    useState<Agent | null>(null);
  // --------------------------------------------------
  // LOADING STATES
  // --------------------------------------------------

  const [loading, setLoading] =
    useState(true);

  const [periodLoading, setPeriodLoading] =
    useState(false);

  const [hasLoaded, setHasLoaded] =
    useState(false);

  // --------------------------------------------------
  // ERROR
  // --------------------------------------------------

  const [error, setError] =
    useState<string | null>(null);
   
   const [dataQuality, setDataQuality] =
  useState<DataQuality | null>(null);
   
  // --------------------------------------------------
  // LOAD DASHBOARD
  // --------------------------------------------------

  useEffect(() => {
    async function loadDashboard() {
      try {
        /*
         * Initial page load:
         * show full-page loading.
         *
         * Period change:
         * keep existing dashboard visible.
         */
        if (!hasLoaded) {
          setLoading(true);
        } else {
          setPeriodLoading(true);
        }

        setError(null);

        const period =
          PERIODS.find(
            (item) =>
              item.key === selectedPeriod
          );

        const startDate =
          selectedPeriod === "ALL"
            ? undefined
            : `${period?.start}-01`;

        let endDate: string | undefined;

        if (selectedPeriod !== "ALL") {
          const [year, month] =
            period!.end
              .split("-")
              .map(Number);

          const lastDay = new Date(
            year,
            month,
            0
          ).getDate();

          endDate =
            `${year}-${String(month).padStart(
              2,
              "0"
            )}-${String(lastDay).padStart(
              2,
              "0"
            )}`;
        }

        const [
          summaryData,
          agentsData,
          priorityData,
          trendsData,
		  qualityData,
        ] = await Promise.all([
          getSummary(),

          getAgents(
            startDate,
            endDate
          ),

          getTrainingPriority(
            startDate,
            endDate
          ),

          getTrends(),
		  getDataQuality(),
        ]);

        setSummary(summaryData);
        setAgents(agentsData);
        setPriority(priorityData);
        setTrends(trendsData);
        setDataQuality(qualityData);

        setHasLoaded(true);

      } catch (err: any) {
        console.error(
          "Dashboard API error:",
          err
        );

        const message =
          err?.response?.data?.detail ||
          err?.message ||
          "Unable to load dashboard data.";

        setError(message);

      } finally {
        setLoading(false);
        setPeriodLoading(false);
      }
    }

    loadDashboard();

    // selectedPeriod intentionally controls API refresh
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedPeriod]);

  // --------------------------------------------------
  // CURRENT PERIOD
  // --------------------------------------------------

  const currentPeriod = useMemo(() => {
    return (
      PERIODS.find(
        (period) =>
          period.key === selectedPeriod
      ) ?? PERIODS[2]
    );
  }, [selectedPeriod]);

  // --------------------------------------------------
  // MONTHLY TRENDS FOR SELECTED PERIOD
  // --------------------------------------------------

  const filteredTrends = useMemo(() => {
    if (selectedPeriod === "ALL") {
      return trends;
    }

    return trends.filter(
      (item) =>
        item.created_month >=
          currentPeriod.start &&
        item.created_month <=
          currentPeriod.end
    );
  }, [
    trends,
    selectedPeriod,
    currentPeriod,
  ]);
  
  
  // --------------------------------------------------
  // PERIOD KPI CALCULATIONS
  // --------------------------------------------------

  const periodMetrics = useMemo(() => {
    if (filteredTrends.length === 0) {
      return {
        tickets: 0,
        csat: 0,
        slaBreachRate: 0,
        replacementRate: 0,
        avgHandleTime: 0,
        replacements: 0,
        slaBreaches: 0,
        slaEligible: 0,
        csatResponses: 0,
      };
    }
    
    const tickets =
      filteredTrends.reduce(
        (sum, item) =>
          sum + Number(item.tickets || 0),
        0
      );

    const replacements =
      filteredTrends.reduce(
        (sum, item) =>
          sum +
          Number(item.replacements || 0),
        0
      );

    const slaBreaches =
      filteredTrends.reduce(
        (sum, item) =>
          sum +
          Number(item.sla_breaches || 0),
        0
      );

    const slaEligible =
      filteredTrends.reduce(
        (sum, item) =>
          sum +
          Number(item.sla_eligible || 0),
        0
      );

    const csatResponses =
      filteredTrends.reduce(
        (sum, item) =>
          sum +
          Number(
            item.csat_responses || 0
          ),
        0
      );

    /*
     * Weighted CSAT.
     *
     * Monthly CSAT values should not simply
     * be averaged because response counts differ.
     */
    const weightedCsat =
      csatResponses > 0
        ? filteredTrends.reduce(
            (sum, item) =>
              sum +
              Number(item.csat || 0) *
                Number(
                  item.csat_responses || 0
                ),
            0
          ) / csatResponses
        : 0;

    /*
     * Weighted AHT based on ticket volume.
     */
    const weightedAht =
      tickets > 0
        ? filteredTrends.reduce(
            (sum, item) =>
              sum +
              Number(
                item.avg_handle_time_minutes ||
                  0
              ) *
                Number(
                  item.tickets || 0
                ),
            0
          ) / tickets
        : 0;

    return {
      tickets,

      csat: weightedCsat,

      slaBreachRate:
        slaEligible > 0
          ? slaBreaches / slaEligible
          : 0,

      replacementRate:
        tickets > 0
          ? replacements / tickets
          : 0,

      avgHandleTime: weightedAht,

      replacements,

      slaBreaches,

      slaEligible,

      csatResponses,
    };
  }, [filteredTrends]);
  
  //---------------------------------------------------
  // Bussiness Logic
  //---------------------------------------------------
  const businessImpact = useMemo(() => {
  const q2Tickets = 2067;
  const q2Replacements = 361;
  const q2ReplacementRate = q2Replacements / q2Tickets;

  const q2ReplacementCost = 646630;
  const targetRate = 0.15;

  const targetReplacements = q2Tickets * targetRate;
  const replacementsAvoided =
    q2Replacements - targetReplacements;

  const averageReplacementCost =
    q2ReplacementCost / q2Replacements;

  const quarterlyCostAvoided =
    replacementsAvoided * averageReplacementCost;

  return {
    tickets: q2Tickets,
    replacements: q2Replacements,
    replacementRate: q2ReplacementRate,
    targetRate,
    replacementsAvoided,
    quarterlyCostAvoided,
  };
}, []);
  
  // --------------------------------------------------
  // FILTER OPTIONS
  // --------------------------------------------------

  const teamOptions = useMemo(() => {
    const teams = Array.from(
      new Set(
        agents
          .map((agent) => agent.team)
          .filter(Boolean)
      )
    ).sort();

    return ["All", ...teams];
  }, [agents]);

  const siteOptions = useMemo(() => {
    const sites = Array.from(
      new Set(
        agents
          .map((agent) => agent.site)
          .filter(Boolean)
      )
    ).sort();

    return ["All", ...sites];
  }, [agents]);

  const tierOptions = useMemo(() => {
    const tiers = Array.from(
      new Set(
        agents
          .map((agent) =>
            String(agent.tier)
          )
          .filter(Boolean)
      )
    ).sort(
      (a, b) =>
        Number(a) - Number(b)
    );

    return ["All", ...tiers];
  }, [agents]);

  // --------------------------------------------------
  // FILTER AGENTS
  // --------------------------------------------------

  const filteredAgents = useMemo(() => {
    return agents.filter((agent) => {
      const teamMatch =
        selectedTeam === "All" ||
        agent.team === selectedTeam;

      const siteMatch =
        selectedSite === "All" ||
        agent.site === selectedSite;

      const tierMatch =
        selectedTier === "All" ||
        String(agent.tier) ===
          selectedTier;

      return (
        teamMatch &&
        siteMatch &&
        tierMatch
      );
    });
  }, [
    agents,
    selectedTeam,
    selectedSite,
    selectedTier,
  ]);

  // --------------------------------------------------
  // FILTER TRAINING PRIORITY
  // --------------------------------------------------

  const filteredPriority = useMemo(() => {
    return priority.filter((agent) => {
      const teamMatch =
        selectedTeam === "All" ||
        agent.team === selectedTeam;

      const siteMatch =
        selectedSite === "All" ||
        agent.site === selectedSite;

      const tierMatch =
        selectedTier === "All" ||
        String(agent.tier) ===
          selectedTier;

      return (
        teamMatch &&
        siteMatch &&
        tierMatch
      );
    });
  }, [
    priority,
    selectedTeam,
    selectedSite,
    selectedTier,
  ]);

  // --------------------------------------------------
  // SELECTED AGENT PRIORITY
  // --------------------------------------------------

  const selectedAgentPriority = useMemo(() => {
    if (!selectedAgent) {
      return null;
    }

    return (
      filteredPriority.find(
        (item) => item.agent_id === selectedAgent.agent_id
      ) ?? null
    );
  }, [selectedAgent, filteredPriority]);

  // --------------------------------------------------
  // TRAINING COUNTS
  // --------------------------------------------------

  const priorityReviewCount =
    filteredPriority.filter(
      (agent) =>
        agent.priority ===
        "Priority review"
    ).length;

  const watchCount =
    filteredPriority.filter(
      (agent) =>
        agent.priority === "Watch"
    ).length;
   
   // ========================================
// EXPORT DATA
// ========================================

const trainingPriorityExport = useMemo(
  () =>
    filteredPriority.map(agent => ({
      Agent: agent.name,
      "Agent ID": agent.agent_id,
      Team: agent.team,
      Tier: `Tier ${agent.tier}`,
      Tickets: agent.tickets,
      CSAT: agent.csat?.toFixed(2) ?? "",
      "AHT (min)": agent.avg_handle_time_minutes?.toFixed(1) ?? "",
      "Peer Gap": agent.peer_gap?.toFixed(2) ?? "",
      "SLA Breach": `${(agent.sla_breach_rate * 100).toFixed(1)}%`,
      Priority: agent.priority,
    })),
  [filteredPriority]
);

const agentPerformanceExport = useMemo(
  () =>
    filteredAgents.map(agent => ({
      Agent: agent.name,
      "Agent ID": agent.agent_id,
      Site: agent.site,
      Team: agent.team,
      Tier: `Tier ${agent.tier}`,
      Tickets: agent.tickets,
      CSAT: agent.csat?.toFixed(2) ?? "",
      "AHT (min)": agent.avg_handle_time_minutes?.toFixed(1) ?? "",
      "SLA Breach": `${(agent.sla_breach_rate * 100).toFixed(1)}%`,
      Replacement: `${(
        (agent.replacements / Math.max(agent.tickets, 1)) *
        100
      ).toFixed(1)}%`,
      Attendance: `${(agent.attendance_rate * 100).toFixed(1)}%`,
    })),
  [filteredAgents]
);

  // --------------------------------------------------
  // CLEAR FILTERS
  // --------------------------------------------------

  const clearFilters = () => {
    setSelectedTeam("All");
    setSelectedSite("All");
    setSelectedTier("All");
  };

  // --------------------------------------------------
  // INITIAL LOADING
  // --------------------------------------------------

  if (loading) {
    return (
      <div className="loading">
        Loading dashboard...
      </div>
    );
  }

  // --------------------------------------------------
  // ERROR
  // --------------------------------------------------

  if (error) {
    return (
      <div className="error">
        {error}
      </div>
    );
  }

  // --------------------------------------------------
  // DASHBOARD
  // --------------------------------------------------

  return (
    <div className="dashboard">

      {/* HEADER */}

      <header className="dashboard-header">

        <div>
          <h1>Vireo Audio</h1>

          <p>
            Support Operations Dashboard
          </p>
        </div>

        <div className="status">
          ● API Connected
        </div>

      </header>

      {/* PERIOD FILTER */}

      <section className="dashboard-controls">

        <div className="period-control">

          <label htmlFor="period">
            Reporting Period
          </label>

          <select
            id="period"
            value={selectedPeriod}
            onChange={(event) =>
              setSelectedPeriod(
                event.target.value as PeriodKey
              )
            }
          >
            {PERIODS.map((period) => (
              <option
                key={period.key}
                value={period.key}
              >
                {period.label}
              </option>
            ))}
          </select>

        </div>

        <div className="period-info">

          <strong>
            {currentPeriod.label}
          </strong>

          <span>
            Monthly trends within selected
            period
          </span>

        </div>

        {periodLoading && (
          <div className="period-loading">
            <span className="loading-dot"></span>
            Updating...
          </div>
        )}

      </section>

      {/* ADDITIONAL FILTERS */}

      <section className="filter-bar">

        {/* TEAM */}

        <div className="filter-item">

          <label htmlFor="team-filter">
            Team
          </label>

          <select
            id="team-filter"
            value={selectedTeam}
            onChange={(event) =>
              setSelectedTeam(
                event.target.value
              )
            }
          >
            {teamOptions.map((team) => (
              <option
                key={team}
                value={team}
              >
                {team}
              </option>
            ))}
          </select>

        </div>

        {/* SITE */}

        <div className="filter-item">

          <label htmlFor="site-filter">
            Site
          </label>

          <select
            id="site-filter"
            value={selectedSite}
            onChange={(event) =>
              setSelectedSite(
                event.target.value
              )
            }
          >
            {siteOptions.map((site) => (
              <option
                key={site}
                value={site}
              >
                {site}
              </option>
            ))}
          </select>

        </div>

        {/* TIER */}

        <div className="filter-item">

          <label htmlFor="tier-filter">
            Tier
          </label>

          <select
            id="tier-filter"
            value={selectedTier}
            onChange={(event) =>
              setSelectedTier(
                event.target.value
              )
            }
          >
            {tierOptions.map((tier) => (
              <option
                key={tier}
                value={tier}
              >
                {tier === "All"
                  ? "All"
                  : `Tier ${tier}`}
              </option>
            ))}
          </select>

        </div>

        {/* CLEAR FILTERS */}

        <button
          type="button"
          className="clear-filters"
          onClick={clearFilters}
        >
          Clear Filters
        </button>

      </section>

      {/* ACTIVE FILTER SUMMARY */}

      {(selectedTeam !== "All" ||
        selectedSite !== "All" ||
        selectedTier !== "All") && (
        <div className="active-filters">

          <span>
            Showing filtered agents:
          </span>

          {selectedTeam !== "All" && (
            <span className="filter-chip">
              Team: {selectedTeam}
            </span>
          )}

          {selectedSite !== "All" && (
            <span className="filter-chip">
              Site: {selectedSite}
            </span>
          )}

          {selectedTier !== "All" && (
            <span className="filter-chip">
              Tier {selectedTier}
            </span>
          )}

        </div>
      )}
       
      {/* KPI CARDS */}

      <section className="kpi-grid">

        <KpiCard
          title="Tickets"
          value={periodMetrics.tickets.toLocaleString()}
        />

        <KpiCard
          title="Overall CSAT"
          value={periodMetrics.csat.toFixed(
            2
          )}
        />

        <KpiCard
          title="SLA Breach Rate"
          value={`${(
            periodMetrics.slaBreachRate *
            100
          ).toFixed(1)}%`}
        />

        <KpiCard
          title="Replacement Rate"
          value={`${(
            periodMetrics.replacementRate *
            100
          ).toFixed(1)}%`}
        />

        <KpiCard
          title="Avg Handle Time"
          value={`${periodMetrics.avgHandleTime.toFixed(
            1
          )} min`}
        />

        <KpiCard
          title="Support Agents"
          value={summary?.agents}
        />

      </section>

      {/* TRAINING SUMMARY */}

      <section className="kpi-grid">

        <KpiCard
          title="Priority Review"
          value={priorityReviewCount}
        />

        <KpiCard
          title="Watch"
          value={watchCount}
        />

        <KpiCard
          title="CSAT Responses"
          value={periodMetrics.csatResponses.toLocaleString()}
        />

        <KpiCard
          title="Replacements"
          value={periodMetrics.replacements.toLocaleString()}
        />

      </section>
      {/*Bussiness logics*/}
	  <section className="business-impact">
  <div className="business-impact-header">
    <div>
      <h2>Business Impact</h2>
      <p>
        Q2 2026 replacement-cost opportunity
      </p>
    </div>

    <span className="impact-basis">
      Based on observed Q2 volume
    </span>
  </div>

  <div className="impact-grid">

    <div className="impact-card">
      <span>Current Replacement Rate</span>

      <strong>
        {(businessImpact.replacementRate * 100).toFixed(2)}%
      </strong>

      <small>
        {businessImpact.replacements.toLocaleString()} replacements
        / {businessImpact.tickets.toLocaleString()} tickets
      </small>
    </div>

    <div className="impact-card">
      <span>Target Replacement Rate</span>

      <strong>
        {(businessImpact.targetRate * 100).toFixed(0)}%
      </strong>

      <small>
        Proposed operating target
      </small>
    </div>

    <div className="impact-card">
      <span>Potential Replacements Avoided</span>

      <strong>
        ~{Math.round(businessImpact.replacementsAvoided)}
      </strong>

      <small>
        per quarter at current volume
      </small>
    </div>

    <div className="impact-card impact-highlight">
      <span>Estimated Quarterly Cost Avoided</span>

      <strong>
        ₹{Math.round(
          businessImpact.quarterlyCostAvoided
        ).toLocaleString("en-IN")}
      </strong>

      <small>
        Based on unit cost + ₹340 logistics
      </small>
    </div>

  </div>

  <div className="impact-note">
    <strong>Business goal:</strong>{" "}
    Reduce the Q2 2026 replacement rate from{" "}
    {(businessImpact.replacementRate * 100).toFixed(2)}%
    {" "}to ≤15%, avoiding approximately{" "}
    {Math.round(businessImpact.replacementsAvoided)}
    {" "}replacements and ₹
    {Math.round(
      businessImpact.quarterlyCostAvoided
    ).toLocaleString("en-IN")}
    {" "}in replacement cost per quarter at the observed Q2 volume.
  </div>

  <div className="impact-disclaimer">
    This is a potential cost opportunity, not a guaranteed saving
    attributable solely to agent training. Replacement activity
    can depend on queue, product and case characteristics.
  </div>
</section>
	  
	  {dataQuality && (
  <section className="validation-panel">

    <div className="validation-header">
      <div>
        <h2>Data Validation</h2>
        <p>
          Automated integrity checks across the source ticket dataset
        </p>
      </div>

      <span className="validation-status">
        ✓ Core checks passed
      </span>
    </div>

    <div className="validation-summary">

      <div>
        <strong>
          {dataQuality.total_tickets.toLocaleString()}
        </strong>
        <span>Total tickets</span>
      </div>

      <div>
        <strong>
          {dataQuality.duplicate_ticket_ids}
        </strong>
        <span>Duplicate IDs</span>
      </div>

      <div>
        <strong>
          {dataQuality.unknown_agent_ids}
        </strong>
        <span>Unknown agents</span>
      </div>

      <div>
        <strong>
          {dataQuality.invalid_csat}
        </strong>
        <span>Invalid CSAT</span>
      </div>

    </div>

    <div className="validation-checks">

      <ValidationCheck
        label="Agent IDs"
        value={
          dataQuality.missing_agent_id +
          dataQuality.unknown_agent_ids
        }
      />

      <ValidationCheck
        label="First-response timestamps"
        value={dataQuality.negative_first_response}
      />

      <ValidationCheck
        label="Handle-time calculations"
        value={dataQuality.invalid_handle_time}
      />

      <ValidationCheck
        label="Channels"
        value={dataQuality.invalid_channels}
      />

      <ValidationCheck
        label="CSAT values"
        value={dataQuality.invalid_csat}
      />

      <ValidationCheck
        label="SLA targets"
        value={dataQuality.missing_sla_target}
      />

    </div>

    <div className="validation-source">

      <strong>Source coverage</strong>

      <span>
        Legacy:{" "}
        {dataQuality.legacy_tickets.toLocaleString()}
      </span>

      <span>
        Current helpdesk:{" "}
        {dataQuality.helpdesk_tickets.toLocaleString()}
      </span>

      <span>
        Missing resolution timestamp:{" "}
        {dataQuality.missing_resolution_total.toLocaleString()}
        {" "}expected for open/pending tickets
      </span>

    </div>

  </section>
)}
      {/* MONTHLY TREND CHARTS */}

      <OperationsCharts
        data={filteredTrends}
      />
 
       {/* AGENT PERFORMANCE */}

      <section className="panel">

		<div className="panel-header">
		  <div>
			<h2>Agent Performance</h2>
			<p>Operational metrics by agent</p>
		  </div>

		  <div className="panel-actions">
			<div className="panel-count">
			  {filteredAgents.length} agents
			</div>

			<DownloadMenu
			  data={agentPerformanceExport}
			  filename="vireo-agent-performance"
			  title="Vireo Audio — Agent Performance"
			/>
		  </div>
		</div>

        <div className="table-container">

          <table>

            <thead>

              <tr>
                <th>Agent</th>
                <th>Site</th>
                <th>Team</th>
                <th>Tickets</th>
                <th>CSAT</th>
                <th>AHT</th>
                <th>SLA Breach</th>
                <th>Replacement</th>
                <th>Attendance</th>
              </tr>

            </thead>

            <tbody>

              {filteredAgents.length === 0 ? (
                <tr>
                  <td
                    colSpan={9}
                    className="empty-state"
                  >
                    No agents match the
                    selected filters.
                  </td>
                </tr>
              ) : (
                filteredAgents.map(agent => (
				  <tr
					key={agent.agent_id}
					className="clickable-row"
					onClick={() => setSelectedAgent(agent)}
				  >

                      <td>
                        <strong>
                          {agent.name}
                        </strong>

                        <small>
                          {agent.agent_id}
                        </small>
                      </td>

                      <td>
                        {agent.site}
                      </td>

                      <td>
                        {agent.team}
                      </td>

                      <td>
                        {agent.tickets}
                      </td>

                      <td>
                        {agent.csat?.toFixed(
                          2
                        )}
                      </td>

                      <td>
                        {agent.avg_handle_time_minutes?.toFixed(
                          1
                        )}{" "}
                        min
                      </td>

                      <td>
                        {(
                          agent.sla_breach_rate *
                          100
                        ).toFixed(1)}
                        %
                      </td>

                      <td>
                        {(
                          (agent.replacements /
                            Math.max(
                              agent.tickets,
                              1
                            )) *
                          100
                        ).toFixed(1)}
                        %
                      </td>

                      <td>
                        {(
                          agent.attendance_rate *
                          100
                        ).toFixed(1)}
                        %
                      </td>

                    </tr>

                  )
                )
              )}

            </tbody>

          </table>

        </div>

      </section> 
 
      {/* TRAINING PRIORITY */}

      <section className="panel">

        <div className="panel-header">
		  <div>
			<h2>Training Priority</h2>
			<p>Agents requiring coaching review</p>
		  </div>

		  <div className="panel-actions">
			<div className="panel-count">
			  {filteredPriority.length} agents
			</div>

			<DownloadMenu
			  data={trainingPriorityExport}
			  filename="vireo-training-priority"
			  title="Vireo Audio — Training Priority"
			/>
		  </div>
		</div>

        <div className="table-container">

          <table>

            <thead>

              <tr>
                <th>Agent</th>
                <th>Team</th>
                <th>Tier</th>
                <th>Tickets</th>
                <th>CSAT</th>
                <th>AHT</th>
                <th>Peer Gap</th>
                <th>SLA Breach</th>
                <th>Priority</th>
              </tr>

            </thead>

            <tbody>

              {filteredPriority.length === 0 ? (
                <tr>
                  <td
                    colSpan={9}
                    className="empty-state"
                  >
                    No agents match the
                    selected filters.
                  </td>
                </tr>
              ) : (
                filteredPriority.map(
                  (agent) => (

                    <tr
                      key={agent.agent_id}
                    >

                      <td>
                        <strong>
                          {agent.name}
                        </strong>

                        <small>
                          {agent.agent_id}
                        </small>
                      </td>

                      <td>
                        {agent.team}
                      </td>

                      <td>
                        Tier {agent.tier}
                      </td>

                      <td>
                        {agent.tickets}
                      </td>

                      <td>
                        {agent.csat?.toFixed(
                          2
                        )}
                      </td>

                      <td>
                        {agent.avg_handle_time_minutes?.toFixed(
                          1
                        )}{" "}
                        min
                      </td>

                      <td>
                        {agent.peer_gap?.toFixed(
                          2
                        )}
                      </td>

                      <td>
                        {(
                          agent.sla_breach_rate *
                          100
                        ).toFixed(1)}
                        %
                      </td>

                      <td>
                        <PriorityBadge
                          priority={
                            agent.priority
                          }
                        />
                      </td>

                    </tr>

                  )
                )
              )}

            </tbody>

          </table>

        </div>

      </section>
      {selectedAgent && (
        <AgentDetailDrawer
          agent={selectedAgent}
          priorityInfo={selectedAgentPriority}
          onClose={() => setSelectedAgent(null)}
        />
      )}

    </div>
  );
}

function ValidationCheck({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  const passed = value === 0;

  return (
    <div className="validation-check">
      <span className="validation-check-icon">
        {passed ? "✓" : "!"}
      </span>

      <div>
        <strong>{label}</strong>

        <small>
          {passed
            ? "No issues detected"
            : `${value} issue(s) detected`}
        </small>
      </div>
    </div>
  );
}
function AgentDetailDrawer({
  agent,
  priorityInfo,
  onClose,
}: {
  agent: Agent;
  priorityInfo: TrainingPriority | null;
  onClose: () => void;
}) {
  const replacementRate =
    (agent.replacements / Math.max(agent.tickets, 1)) * 100;

  return (
    <div className="drawer-overlay" onClick={onClose}>
      <aside
        className="agent-drawer"
        onClick={event => event.stopPropagation()}
      >
        {/* Header */}
        <div className="drawer-header">
          <div>
            <div className="drawer-title-row">
              <h2>{agent.name}</h2>

              <span className="drawer-tier">
                Tier {agent.tier}
              </span>
            </div>

            <p>{agent.agent_id}</p>
          </div>

          <button
            type="button"
            className="drawer-close"
            onClick={onClose}
            aria-label="Close"
          >
            ×
          </button>
        </div>

        {/* Basic information */}
        <div className="drawer-meta">
          <div>
            <span>Team</span>
            <strong>{agent.team}</strong>
          </div>

          <div>
            <span>Site</span>
            <strong>{agent.site}</strong>
          </div>
        </div>

        {/* Priority */}
        <div className="drawer-section">
          <div className="drawer-section-header">
            <h3>Training Status</h3>

            <PriorityBadge priority={priorityInfo?.priority ?? "Normal"} />
          </div>

          <p className="drawer-description">
            Current coaching priority based on the dashboard's
            deterministic training-priority calculation.
          </p>
        </div>

        {/* AI explanation */}
        <AgentAiExplanation
          agent={{
            agent_id: agent.agent_id,
            name: agent.name,
            site: agent.site,
            team: agent.team,
            tier: agent.tier,
            tickets: agent.tickets,
            csat_responses: agent.csat_responses,
            csat: agent.csat,
            avg_handle_time_minutes:
              agent.avg_handle_time_minutes,
            sla_breaches: agent.sla_breaches,
            sla_breach_rate: agent.sla_breach_rate,
            replacements: agent.replacements,
            transfers: agent.transfers,
            attendance_rate: agent.attendance_rate,
            peer_csat: priorityInfo?.peer_csat ?? null,
            peer_gap: priorityInfo?.peer_gap ?? null,
            priority: priorityInfo?.priority ?? null,
            confidence: priorityInfo?.confidence ?? null,
            priority_score: priorityInfo?.priority_score ?? null,
          }}
        />

        {/* KPI grid */}
        <div className="drawer-section">
          <h3>Performance</h3>

          <div className="drawer-kpi-grid">
            <div className="drawer-kpi">
              <span>Tickets</span>
              <strong>{agent.tickets}</strong>
            </div>

            <div className="drawer-kpi">
              <span>CSAT</span>
              <strong>
                {agent.csat?.toFixed(2) ?? "-"}
              </strong>
            </div>

            <div className="drawer-kpi">
              <span>CSAT Responses</span>
              <strong>
                {agent.csat_responses ?? "-"}
              </strong>
            </div>

            <div className="drawer-kpi">
              <span>Avg Handle Time</span>
              <strong>
                {agent.avg_handle_time_minutes?.toFixed(1) ?? "-"} min
              </strong>
            </div>

            <div className="drawer-kpi">
              <span>SLA Breach</span>
              <strong>
                {(agent.sla_breach_rate * 100).toFixed(1)}%
              </strong>
            </div>

            <div className="drawer-kpi">
              <span>Replacement</span>
              <strong>
                {replacementRate.toFixed(1)}%
              </strong>
            </div>

            <div className="drawer-kpi">
              <span>Attendance</span>
              <strong>
                {(agent.attendance_rate * 100).toFixed(1)}%
              </strong>
            </div>

            <div className="drawer-kpi">
              <span>Peer Gap</span>
              <strong>
                {priorityInfo?.peer_gap?.toFixed(2) ?? "-"}
              </strong>
            </div>
          </div>
        </div>

        {/* Operational signals */}
        <div className="drawer-section">
          <h3>Operational Signals</h3>

          <div className="signal-list">
            <div className="signal-row">
              <span>SLA breaches</span>
              <strong>{agent.sla_breaches}</strong>
            </div>

            <div className="signal-row">
              <span>Replacements</span>
              <strong>{agent.replacements}</strong>
            </div>

            <div className="signal-row">
              <span>Transfers</span>
              <strong>{agent.transfers}</strong>
            </div>

            <div className="signal-row">
              <span>Attendance</span>
              <strong>
                {(agent.attendance_rate * 100).toFixed(1)}%
              </strong>
            </div>
          </div>
        </div>

        {/* Interpretation */}
        <div className="drawer-section">
          <h3>How to read this</h3>

          <div className="drawer-note">
            <p>
              <strong>Peer Gap</strong> compares the agent's CSAT
              with the relevant peer benchmark used by the training
              priority calculation.
            </p>

            <p>
              A negative peer gap indicates CSAT below the peer
              benchmark.
            </p>

            <p>
              Replacement activity should not automatically be
              interpreted as agent-controlled performance.
            </p>
          </div>
        </div>
      </aside>
    </div>
  );
}

/* --------------------------------------------------
   KPI CARD
-------------------------------------------------- */

function KpiCard({
  title,
  value,
}: {
  title: string;
  value: string | number | undefined;
}) {
  return (
    <div className="kpi-card">

      <span>
        {title}
      </span>

      <strong>
        {value ?? "-"}
      </strong>

    </div>
  );
}


/* --------------------------------------------------
   PRIORITY BADGE
-------------------------------------------------- */

function PriorityBadge({
  priority,
}: {
  priority: string | null | undefined;
}) {
  const normalized = (priority ?? "Normal").toLowerCase();

  const className =
    normalized === "priority review"
      ? "badge priority"
      : normalized === "watch"
      ? "badge watch"
      : "badge normal";

  return (
    <span className={className}>
      {priority ?? "Normal"}
    </span>
  );
}


export default Dashboard;
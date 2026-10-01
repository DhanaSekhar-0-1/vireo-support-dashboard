import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

import type { MonthlyTrend } from "../../services/api";

interface Props {
  data: MonthlyTrend[];
}

function OperationsCharts({ data }: Props) {
  const chartData = data.map((item) => ({
    month: item.created_month,
    tickets: item.tickets,
    csat: Number(item.csat.toFixed(2)),
    sla: Number(
      (item.sla_breach_rate * 100).toFixed(2)
    ),
    replacement: Number(
      (item.replacement_rate * 100).toFixed(2)
    ),
    aht: Number(
      item.avg_handle_time_minutes.toFixed(1)
    ),
  }));

  return (
    <div className="charts-grid">

      {/* Ticket Volume */}

      <div className="chart-card">

        <div className="chart-header">
          <h3>Ticket Volume</h3>
          <p>Monthly support demand</p>
        </div>

        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>

            <CartesianGrid strokeDasharray="3 3" />

            <XAxis dataKey="month" />

            <YAxis />

            <Tooltip />

            <Bar
              dataKey="tickets"
              name="Tickets"
            />

          </BarChart>
        </ResponsiveContainer>

      </div>

      {/* CSAT */}

      <div className="chart-card">

        <div className="chart-header">
          <h3>CSAT Trend</h3>
          <p>Average customer satisfaction</p>
        </div>

        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>

            <CartesianGrid strokeDasharray="3 3" />

            <XAxis dataKey="month" />

            <YAxis
              domain={[1, 5]}
            />

            <Tooltip />

            <Line
              type="monotone"
              dataKey="csat"
              name="CSAT"
              strokeWidth={2}
              dot
            />

          </LineChart>
        </ResponsiveContainer>

      </div>

      {/* SLA */}

      <div className="chart-card">

        <div className="chart-header">
          <h3>SLA Breach Rate</h3>
          <p>Percentage of eligible tickets breached</p>
        </div>

        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>

            <CartesianGrid strokeDasharray="3 3" />

            <XAxis dataKey="month" />

            <YAxis unit="%" />

            <Tooltip
              formatter={(value) => [
                `${value}%`,
                "SLA breach",
              ]}
            />

            <Line
              type="monotone"
              dataKey="sla"
              name="SLA breach"
              strokeWidth={2}
              dot
            />

          </LineChart>
        </ResponsiveContainer>

      </div>

      {/* Replacement */}

      <div className="chart-card">

        <div className="chart-header">
          <h3>Replacement Rate</h3>
          <p>Share of tickets resulting in replacement</p>
        </div>

        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>

            <CartesianGrid strokeDasharray="3 3" />

            <XAxis dataKey="month" />

            <YAxis unit="%" />

            <Tooltip
              formatter={(value) => [
                `${value}%`,
                "Replacement",
              ]}
            />

            <Line
              type="monotone"
              dataKey="replacement"
              name="Replacement"
              strokeWidth={2}
              dot
            />

          </LineChart>
        </ResponsiveContainer>

      </div>

      {/* AHT */}

      <div className="chart-card">

        <div className="chart-header">
          <h3>Average Handle Time</h3>
          <p>First response to resolution</p>
        </div>

        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>

            <CartesianGrid strokeDasharray="3 3" />

            <XAxis dataKey="month" />

            <YAxis />

            <Tooltip
              formatter={(value) => [
                `${value} min`,
                "AHT",
              ]}
            />

            <Line
              type="monotone"
              dataKey="aht"
              name="AHT"
              strokeWidth={2}
              dot
            />

          </LineChart>
        </ResponsiveContainer>

      </div>

    </div>
  );
}

export default OperationsCharts;
import PropTypes from "prop-types";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  LineChart,
  Line,
  CartesianGrid,
} from "recharts";
import {
  pieItemShape,
  lineItemShape,
  categoryItemShape,
  priorityItemShape,
} from "./propTypes";

const CATEGORY_COLORS = [
  "#6366f1",
  "#f59e0b",
  "#22c55e",
  "#ef4444",
  "#8b5cf6",
  "#06b6d4",
];

const PRIORITY_COLORS = {
  urgent: "#7c3aed",
  high: "#ef4444",
  medium: "#f59e0b",
  low: "#22c55e",
};

const STATUS_COLORS = {
  Open: "#ef4444",
  "In Progress": "#f59e0b",
  Closed: "#22c55e",
};

const chartAxisStyle = { fontSize: 12, fill: "#6b7280" };

const tooltipStyle = {
  backgroundColor: "#111827",
  border: "1px solid rgba(255,255,255,0.08)",
  borderRadius: "14px",
  color: "#fff",
};

function ChartsSection({ pieData, lineData, categoryData, priorityData }) {
  const statusChartData = pieData.map((entry) => ({
    ...entry,
    fill: STATUS_COLORS[entry.name] || "#6366f1",
  }));

  const categoryChartData = categoryData.map((entry, index) => ({
    ...entry,
    fill: CATEGORY_COLORS[index % CATEGORY_COLORS.length],
  }));

  const priorityChartData = priorityData.map((entry) => ({
    ...entry,
    fill: PRIORITY_COLORS[entry.name] || "#6366f1",
  }));

  return (
    <>
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-6">
        <div className="bg-[#0f1117] border border-white/5 rounded-2xl p-5">
          <h3 className="text-base font-semibold text-white mb-1">
            Status Breakdown
          </h3>
          <p className="text-xs text-gray-600 mb-4">
            Distribution of open, active, and resolved tickets
          </p>

          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie
                data={statusChartData}
                cx="50%"
                cy="50%"
                innerRadius={62}
                outerRadius={96}
                paddingAngle={4}
                dataKey="value"
                label={({ name, percent }) =>
                  `${name} ${((percent || 0) * 100).toFixed(0)}%`
                }
                labelLine={false}
              />
              <Tooltip contentStyle={tooltipStyle} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-[#0f1117] border border-white/5 rounded-2xl p-5">
          <h3 className="text-base font-semibold text-white mb-1">
            Tickets Last 7 Days
          </h3>
          <p className="text-xs text-gray-600 mb-4">
            Daily incoming ticket volume trend
          </p>

          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={lineData}>
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="rgba(255,255,255,0.05)"
              />
              <XAxis dataKey="date" tick={chartAxisStyle} />
              <YAxis allowDecimals={false} tick={chartAxisStyle} />
              <Tooltip contentStyle={tooltipStyle} />
              <Line
                type="monotone"
                dataKey="count"
                stroke="#818cf8"
                strokeWidth={2.5}
                dot={{ r: 4, fill: "#818cf8" }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-6">
        <div className="bg-[#0f1117] border border-white/5 rounded-2xl p-5">
          <h3 className="text-base font-semibold text-white mb-1">
            Tickets by Category
          </h3>
          <p className="text-xs text-gray-600 mb-4">
            Category distribution across all tickets
          </p>

          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={categoryChartData} barSize={34}>
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="rgba(255,255,255,0.05)"
              />
              <XAxis dataKey="name" tick={chartAxisStyle} />
              <YAxis allowDecimals={false} tick={chartAxisStyle} />
              <Tooltip contentStyle={tooltipStyle} />
              <Bar dataKey="count" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-[#0f1117] border border-white/5 rounded-2xl p-5">
          <h3 className="text-base font-semibold text-white mb-1">
            Tickets by Priority
          </h3>
          <p className="text-xs text-gray-600 mb-4">
            Priority mix currently handled by the system
          </p>

          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={priorityChartData} barSize={34}>
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="rgba(255,255,255,0.05)"
              />
              <XAxis dataKey="name" tick={chartAxisStyle} />
              <YAxis allowDecimals={false} tick={chartAxisStyle} />
              <Tooltip contentStyle={tooltipStyle} />
              <Bar dataKey="count" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </>
  );
}

ChartsSection.propTypes = {
  pieData: PropTypes.arrayOf(pieItemShape).isRequired,
  lineData: PropTypes.arrayOf(lineItemShape).isRequired,
  categoryData: PropTypes.arrayOf(categoryItemShape).isRequired,
  priorityData: PropTypes.arrayOf(priorityItemShape).isRequired,
};

export default ChartsSection;

import { useEffect, useState } from "react";
import { getTicketStats, getTickets } from "../services/api";
import StatsCards from "../components/dashboard/StatsCards";
import ChartsSection from "../components/dashboard/ChartsSection";
import AgentWorkloadTable from "../components/dashboard/AgentWorkloadTable";
import RecentTicketsSection from "../components/dashboard/RecentTicketsSection";

function Dashboard() {
  const role = localStorage.getItem("role");

  const [stats, setStats] = useState({
    total: 0,
    open: 0,
    in_progress: 0,
    closed: 0,
    by_category: [],
    by_priority: [],
    by_date: [],
    agent_workload: [],
  });

  const [recentTickets, setRecentTickets] = useState([]);
  const [loadingStats, setLoadingStats] = useState(true);
  const [loadingTickets, setLoadingTickets] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("access");
    if (!token) return;

    setLoadingStats(true);

    getTicketStats()
      .then((res) => {
        setStats({
          total: res.data?.total ?? 0,
          open: res.data?.open ?? 0,
          in_progress: res.data?.in_progress ?? 0,
          closed: res.data?.closed ?? 0,
          by_category: res.data?.by_category ?? [],
          by_priority: res.data?.by_priority ?? [],
          by_date: res.data?.by_date ?? [],
          agent_workload: res.data?.agent_workload ?? [],
        });
      })
      .catch(() => {
        setStats({
          total: 0,
          open: 0,
          in_progress: 0,
          closed: 0,
          by_category: [],
          by_priority: [],
          by_date: [],
          agent_workload: [],
        });
      })
      .finally(() => setLoadingStats(false));
  }, []);

  useEffect(() => {
    if (role !== "admin" && role !== "agent") return;

    setLoadingTickets(true);

    getTickets(1)
      .then((res) => {
        setRecentTickets(res.data?.results?.slice(0, 5) || []);
      })
      .catch(() => {
        setRecentTickets([]);
      })
      .finally(() => setLoadingTickets(false));
  }, [role]);

  const pieData = [
    { name: "Open", value: stats.open || 0 },
    { name: "In Progress", value: stats.in_progress || 0 },
    { name: "Closed", value: stats.closed || 0 },
  ];

  const categoryData = (stats.by_category || []).map((c) => ({
    name: c.category__name || "Unknown",
    count: c.count || 0,
  }));

  const priorityData = (stats.by_priority || []).map((p) => ({
    name: p.priority || "unknown",
    count: p.count || 0,
  }));

  const lineData = (stats.by_date || []).map((d) => ({
    date: d.date ? d.date.slice(5) : "",
    count: d.count || 0,
  }));

  return (
    <div
      style={{ fontFamily: "'DM Sans', sans-serif" }}
      className="min-h-screen bg-[#0c0e14] p-6"
    >
      <div className="mb-8">
        <div className="inline-flex items-center gap-2 bg-indigo-500/10 border border-indigo-500/20 rounded-full px-4 py-1.5 mb-4">
          <div className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse" />
          <span className="text-indigo-400 text-xs font-medium tracking-wide">
            Ticket Operations Overview
          </span>
        </div>

        <h2
          className="text-3xl font-bold text-white mb-2"
          style={{ letterSpacing: "-0.03em" }}
        >
          Dashboard
        </h2>

        <p className="text-gray-500 text-sm">
          Monitor ticket flow, team workload, and recent activity in one place.
        </p>
      </div>

      <StatsCards stats={stats} loadingStats={loadingStats} />

      {role === "admin" && (
        <>
          <ChartsSection
            pieData={pieData}
            lineData={lineData}
            categoryData={categoryData}
            priorityData={priorityData}
          />

          <AgentWorkloadTable agentWorkload={stats.agent_workload || []} />
        </>
      )}

      {(role === "admin" || role === "agent") && (
        <RecentTicketsSection
          loadingTickets={loadingTickets}
          recentTickets={recentTickets}
        />
      )}
    </div>
  );
}

export default Dashboard;
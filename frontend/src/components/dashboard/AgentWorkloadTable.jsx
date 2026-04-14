import PropTypes from "prop-types";
import { agentWorkloadShape } from "./propTypes";

function AgentWorkloadTable({ agentWorkload }) {
  return (
    <div className="bg-[#0f1117] border border-white/5 rounded-2xl overflow-hidden mb-8">
      <div className="p-5 border-b border-white/5">
        <h3 className="text-base font-semibold text-white mb-1">
          Agent Workload
        </h3>
        <p className="text-xs text-gray-600">
          Performance overview of all active agents
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-white/[0.02] text-gray-500 text-xs uppercase tracking-wider">
            <tr>
              <th className="py-3 px-4 text-left">Agent</th>
              <th className="py-3 px-4 text-center">Assigned</th>
              <th className="py-3 px-4 text-center">In Progress</th>
              <th className="py-3 px-4 text-center">Solved</th>
              <th className="py-3 px-4 text-center">Solve Rate</th>
              <th className="py-3 px-4 text-center">Avg Resolution</th>
            </tr>
          </thead>

          <tbody>
            {agentWorkload.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-8 text-center text-gray-600">
                  No agents found
                </td>
              </tr>
            ) : (
              agentWorkload.map((agent, i) => {
                const solveRate =
                  agent.assigned > 0
                    ? Math.round((agent.solved / agent.assigned) * 100)
                    : 0;

                return (
                  <tr
                    key={i}
                    className="border-t border-white/5 hover:bg-white/[0.02] transition"
                  >
                    <td className="py-3 px-4 font-medium text-white">
                      👤 {agent.agent}
                    </td>
                    <td className="py-3 px-4 text-center text-indigo-400 font-semibold">
                      {agent.assigned}
                    </td>
                    <td className="py-3 px-4 text-center text-amber-400 font-semibold">
                      {agent.in_progress}
                    </td>
                    <td className="py-3 px-4 text-center text-emerald-400 font-semibold">
                      {agent.solved}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 bg-white/5 rounded-full h-2">
                          <div
                            className="bg-indigo-500 h-2 rounded-full"
                            style={{ width: `${solveRate}%` }}
                          />
                        </div>
                        <span className="text-xs text-gray-500 w-8">
                          {solveRate}%
                        </span>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-center text-gray-400 text-sm">
                      {agent.avg_resolution_hours != null
                        ? `${agent.avg_resolution_hours}h`
                        : "—"}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

AgentWorkloadTable.propTypes = {
  agentWorkload: PropTypes.arrayOf(agentWorkloadShape).isRequired,
};

export default AgentWorkloadTable;
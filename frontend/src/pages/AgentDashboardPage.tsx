import { useState, useEffect } from "react";
import { Activity, AlertTriangle } from "lucide-react";

interface AgentStatus {
  agent: string;
  status: "ready" | "loading" | "training" | "error";
  reward: number;
  confidence?: number;
  success_rate?: number;
}

interface HealthStatus {
  overall: "healthy" | "degraded" | "unhealthy";
  timestamp: string;
  components: {
    [key: string]: boolean;
  };
}

interface Checkpoint {
  agent: string;
  path: string;
  timestamp: string;
  reward: number;
  episodes: number;
}

interface Recommendation {
  deployment: {
    primary: string;
    fallback: string;
    emergency: string;
  };
  actions: Array<{
    priority: string;
    action: string;
    reason: string;
  }>;
  monitoring: string[];
  success_metrics: {
    [key: string]: string;
  };
}

interface DashboardData {
  status: AgentStatus[];
  health: HealthStatus;
  checkpoints: Checkpoint[];
  recommendations: Recommendation;
}

export function AgentDashboardPage() {
  const [status, setStatus] = useState<AgentStatus[]>([]);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [checkpoints, setCheckpoints] = useState<Checkpoint[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation | null>(
    null,
  );
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      setError(null);

      // Fetch dashboard data from API
      const response = await fetch("/api/agent/dashboard");
      if (!response.ok) {
        throw new Error(
          `Failed to fetch dashboard data: ${response.statusText}`,
        );
      }

      const data: DashboardData = await response.json();
      setStatus(data.status);
      setHealth(data.health);
      setCheckpoints(data.checkpoints);
      setRecommendations(data.recommendations);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
      console.error("Error fetching dashboard data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();

    // Set up auto-refresh if enabled
    let interval: ReturnType<typeof setInterval> | null = null;
    if (autoRefresh) {
      interval = setInterval(fetchData, 30000); // Refresh every 30 seconds
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh]);

  const getStatusColor = (agentStatus: string) => {
    switch (agentStatus) {
      case "ready":
        return "bg-green-50 border-green-200";
      case "loading":
        return "bg-blue-50 border-blue-200";
      case "training":
        return "bg-yellow-50 border-yellow-200";
      case "error":
        return "bg-red-50 border-red-200";
      default:
        return "bg-gray-50 border-gray-200";
    }
  };

  const getStatusIcon = (agentStatus: string) => {
    switch (agentStatus) {
      case "ready":
        return (
          <svg
            className="h-5 w-5 text-green-600"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
            <polyline points="22 4 12 14.01 9 11.01"></polyline>
          </svg>
        );
      case "loading":
        return (
          <svg
            className="h-5 w-5 text-blue-600 animate-spin"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <line x1="12" y1="2" x2="12" y2="6" />
            <line x1="12" y1="18" x2="12" y2="22" />
            <line x1="4.22" y1="4.22" x2="7.34" y2="7.34" />
            <line x1="16.66" y1="16.66" x2="19.78" y2="19.78" />
            <line x1="2" y1="12" x2="6" y2="12" />
            <line x1="18" y1="12" x2="22" y2="12" />
            <line x1="4.22" y1="19.78" x2="7.34" y2="16.66" />
            <line x1="16.66" y1="7.34" x2="19.78" y2="4.22" />
          </svg>
        );
      case "training":
        return (
          <svg
            className="h-5 w-5 text-yellow-600 animate-pulse"
            viewBox="0 0 24 24"
            fill="currentColor"
          >
            <rect x="2" y="7" width="20" height="14" rx="2" ry="2" />
            <rect x="2" y="4" width="6" height="3" rx="1" ry="1" />
            <rect x="16" y="4" width="6" height="3" rx="1" ry="1" />
          </svg>
        );
      case "error":
        return (
          <svg
            className="h-5 w-5 text-red-600"
            viewBox="0 0 24 24"
            fill="currentColor"
          >
            <circle cx="12" cy="12" r="10" />
            <path
              d="M12 8v4m0 4h.01"
              stroke="white"
              strokeWidth="2"
              strokeLinecap="round"
            />
          </svg>
        );
      default:
        return (
          <svg
            className="h-5 w-5 text-gray-600"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
          </svg>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading agent dashboard...</p>
          </div>
        </div>
      )}

      {/* Error State */}
      {error && !loading && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800 font-semibold">Error Loading Dashboard</p>
          <p className="text-red-700 mt-1">{error}</p>
        </div>
      )}

      {/* Main Content */}
      {!loading && (
        <>
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h1 className="text-2xl md:text-3xl font-bold text-gray-900">
                Agent Dashboard
              </h1>
              <p className="text-sm md:text-base text-gray-600 mt-1">
                Real-time monitoring of RL agents and systems
              </p>
            </div>
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
              <button
                onClick={fetchData}
                className="w-full sm:w-auto px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm md:text-base"
              >
                Refresh Now
              </button>
              <label className="flex items-center gap-2 cursor-pointer w-full sm:w-auto">
                <input
                  type="checkbox"
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                  className="w-4 h-4"
                />
                <span className="text-xs md:text-sm text-gray-600 whitespace-nowrap">
                  Auto-refresh
                </span>
              </label>
            </div>
          </div>

          {/* System Health */}
          {health && (
            <div
              className={`rounded-lg border-2 p-4 md:p-6 ${
                health.overall === "healthy"
                  ? "bg-green-50 border-green-200"
                  : health.overall === "degraded"
                    ? "bg-yellow-50 border-yellow-200"
                    : "bg-red-50 border-red-200"
              }`}
            >
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div>
                  <h2 className="text-base md:text-lg font-semibold text-gray-900">
                    System Health
                  </h2>
                  <p className="text-xs md:text-sm text-gray-600 mt-1">
                    Status:{" "}
                    <span className="font-semibold capitalize">
                      {health.overall}
                    </span>
                  </p>
                </div>
                <div className="text-xs md:text-sm text-gray-500 whitespace-nowrap">
                  {new Date(health.timestamp).toLocaleTimeString()}
                </div>
              </div>

              {/* Component Status */}
              <div className="mt-4 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                {Object.entries(health.components).map(
                  ([component, isHealthy]) => (
                    <div
                      key={component}
                      className={`p-3 rounded-lg border ${
                        isHealthy
                          ? "bg-white border-green-300"
                          : "bg-white border-red-300"
                      }`}
                    >
                      <p className="text-xs text-gray-600 capitalize">
                        {component.replace(/_/g, " ")}
                      </p>
                      <p className="text-xs font-semibold mt-1">
                        {isHealthy ? (
                          <span className="text-green-600">✓ OK</span>
                        ) : (
                          <span className="text-red-600">✗ Failed</span>
                        )}
                      </p>
                    </div>
                  ),
                )}
              </div>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex gap-3">
                <AlertTriangle className="h-5 w-5 text-red-600 shrink-0 mt-0.5" />
                <div>
                  <h3 className="font-semibold text-red-900">Error</h3>
                  <p className="text-red-700 text-sm mt-1">{error}</p>
                </div>
              </div>
            </div>
          )}

          {/* Agent Status Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {status.length > 0 ? (
              status.map((agent) => (
                <div
                  key={agent.agent}
                  className={`rounded-lg border-2 p-4 md:p-6 ${getStatusColor(agent.status)}`}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="font-semibold text-gray-900 uppercase text-xs md:text-sm">
                        {agent.agent}
                      </h3>
                      <div className="flex items-center gap-2 mt-2">
                        {getStatusIcon(agent.status)}
                        <span className="text-xs md:text-sm font-medium text-gray-700 capitalize">
                          {agent.status}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Metrics */}
                  <div className="mt-4 space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-xs md:text-sm text-gray-600">
                        Reward
                      </span>
                      <span className="font-semibold text-gray-900 text-sm md:text-base">
                        {agent.reward?.toFixed(2) || "N/A"}
                      </span>
                    </div>

                    {agent.confidence !== undefined && (
                      <div className="flex justify-between items-center">
                        <span className="text-xs md:text-sm text-gray-600">
                          Confidence
                        </span>
                        <span className="font-semibold text-gray-900 text-sm md:text-base">
                          {(agent.confidence * 100).toFixed(1)}%
                        </span>
                      </div>
                    )}

                    {agent.success_rate !== undefined && (
                      <div className="flex justify-between items-center">
                        <span className="text-xs md:text-sm text-gray-600">
                          Success Rate
                        </span>
                        <span className="font-semibold text-gray-900 text-sm md:text-base">
                          {(agent.success_rate * 100).toFixed(1)}%
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              ))
            ) : (
              <div className="col-span-1 sm:col-span-2 lg:col-span-3 text-center py-8 text-gray-600">
                <Activity className="h-8 w-8 mx-auto mb-2 text-gray-400" />
                <p>No agent status available</p>
              </div>
            )}
          </div>

          {/* Trained Checkpoints */}
          {checkpoints.length > 0 && (
            <div className="bg-white rounded-lg shadow p-4 md:p-6">
              <h2 className="text-lg md:text-xl font-semibold mb-4 text-gray-900">
                Trained Checkpoints
              </h2>
              {/* Desktop table view */}
              <div className="hidden md:block overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b-2 border-gray-200">
                      <th className="text-left py-3 px-4 font-semibold text-gray-700">
                        Agent
                      </th>
                      <th className="text-left py-3 px-4 font-semibold text-gray-700">
                        Reward
                      </th>
                      <th className="text-left py-3 px-4 font-semibold text-gray-700">
                        Episodes
                      </th>
                      <th className="text-left py-3 px-4 font-semibold text-gray-700">
                        Timestamp
                      </th>
                      <th className="text-left py-3 px-4 font-semibold text-gray-700">
                        Path
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {checkpoints.map((checkpoint, idx) => (
                      <tr
                        key={idx}
                        className="border-b border-gray-100 hover:bg-gray-50"
                      >
                        <td className="py-3 px-4">
                          <span className="font-semibold text-gray-900 uppercase text-sm">
                            {checkpoint.agent}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <span className="text-gray-900 font-medium">
                            {checkpoint.reward.toFixed(2)}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-gray-700">
                          {checkpoint.episodes}
                        </td>
                        <td className="py-3 px-4 text-sm text-gray-600">
                          {new Date(checkpoint.timestamp).toLocaleDateString()}
                        </td>
                        <td className="py-3 px-4 text-xs text-gray-500 font-mono">
                          {checkpoint.path.split("/").pop()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {/* Mobile card view */}
              <div className="md:hidden space-y-3">
                {checkpoints.map((checkpoint, idx) => (
                  <div
                    key={idx}
                    className="bg-gray-50 p-4 rounded-lg border border-gray-100"
                  >
                    <div className="flex justify-between items-start mb-3">
                      <span className="font-semibold text-gray-900 uppercase text-sm">
                        {checkpoint.agent}
                      </span>
                      <span className="text-gray-900 font-medium">
                        {checkpoint.reward.toFixed(2)}
                      </span>
                    </div>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Episodes:</span>
                        <span className="text-gray-700 font-medium">
                          {checkpoint.episodes}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Date:</span>
                        <span className="text-gray-600">
                          {new Date(checkpoint.timestamp).toLocaleDateString()}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Path:</span>
                        <span className="text-xs text-gray-500 font-mono truncate ml-2">
                          {checkpoint.path.split("/").pop()}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Deployment Recommendations */}
          {recommendations && (
            <div className="bg-white rounded-lg shadow p-4 md:p-6">
              <h2 className="text-lg md:text-xl font-semibold mb-4 text-gray-900">
                Deployment Strategy
              </h2>

              {/* Deployment Chain */}
              <div className="mb-6 p-4 bg-linear-to-r from-blue-50 to-blue-100 rounded-lg border border-blue-200">
                <h3 className="font-semibold text-gray-900 mb-3 text-sm md:text-base">
                  Agent Chain
                </h3>
                <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2 flex-wrap">
                  <div className="px-3 md:px-4 py-2 bg-green-100 text-green-800 rounded-lg font-semibold text-xs md:text-sm">
                    {recommendations.deployment.primary.toUpperCase()}
                  </div>
                  <span className="hidden sm:inline text-gray-600">→</span>
                  <span className="sm:hidden text-gray-600">↓</span>
                  <div className="px-3 md:px-4 py-2 bg-yellow-100 text-yellow-800 rounded-lg font-semibold text-xs md:text-sm">
                    {recommendations.deployment.fallback.toUpperCase()}
                  </div>
                  <span className="hidden sm:inline text-gray-600">→</span>
                  <span className="sm:hidden text-gray-600">↓</span>
                  <div className="px-3 md:px-4 py-2 bg-red-100 text-red-800 rounded-lg font-semibold text-xs md:text-sm">
                    {recommendations.deployment.emergency.toUpperCase()}
                  </div>
                </div>
              </div>

              {/* Recommended Actions */}
              <div className="space-y-3">
                <h3 className="font-semibold text-gray-900 text-sm md:text-base">
                  Recommended Actions
                </h3>
                {recommendations.actions.map((action, idx) => (
                  <div
                    key={idx}
                    className={`p-3 md:p-4 rounded-lg border-l-4 ${
                      action.priority === "high"
                        ? "border-red-500 bg-red-50"
                        : action.priority === "medium"
                          ? "border-yellow-500 bg-yellow-50"
                          : "border-blue-500 bg-blue-50"
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span
                            className={`text-xs font-bold px-2 py-1 rounded ${
                              action.priority === "high"
                                ? "bg-red-200 text-red-800"
                                : action.priority === "medium"
                                  ? "bg-yellow-200 text-yellow-800"
                                  : "bg-blue-200 text-blue-800"
                            }`}
                          >
                            {action.priority.toUpperCase()}
                          </span>
                        </div>
                        <p className="font-semibold text-gray-900 mt-1 text-sm md:text-base">
                          {action.action}
                        </p>
                        <p className="text-xs md:text-sm text-gray-700 mt-1">
                          {action.reason}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Success Metrics */}
              <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                <h3 className="font-semibold text-gray-900 mb-3 text-sm md:text-base">
                  Success Metrics
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 md:gap-4">
                  {Object.entries(recommendations.success_metrics).map(
                    ([key, value]) => (
                      <div
                        key={key}
                        className="bg-white p-3 rounded border border-gray-200"
                      >
                        <p className="text-xs text-gray-600 capitalize">
                          {key}
                        </p>
                        <p className="text-sm font-semibold text-gray-900 mt-1">
                          {value}
                        </p>
                      </div>
                    ),
                  )}
                </div>
              </div>

              {/* Monitoring Points */}
              <div className="mt-6">
                <h3 className="font-semibold text-gray-900 mb-3 text-sm md:text-base">
                  Monitoring Checklist
                </h3>
                <ul className="space-y-2">
                  {recommendations.monitoring.map((point, idx) => (
                    <li
                      key={idx}
                      className="flex gap-2 text-xs md:text-sm text-gray-700"
                    >
                      <input
                        type="checkbox"
                        className="w-4 h-4 rounded border-gray-300 mt-0.5 flex-shrink-0"
                        disabled
                      />
                      <span>{point}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

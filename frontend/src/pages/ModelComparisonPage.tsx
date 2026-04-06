import { useState, useEffect } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from "recharts";
import { AlertCircle, TrendingUp, Zap, Shield } from "lucide-react";

interface AgentMetrics {
  mean_reward: number;
  std_reward: number;
  min_reward: number;
  max_reward: number;
  total_episodes: number;
  type?: string;
  strengths?: string[];
  weaknesses?: string[];
  best_for?: string;
}

interface ComparisonData {
  agents: {
    [key: string]: AgentMetrics;
  };
  timestamp: string;
  recommendation: string;
}

export function ModelComparisonPage() {
  const [comparison, setComparison] = useState<ComparisonData | null>(null);
  const [activeAgent, setActiveAgent] = useState<string>("sac");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchComparison = async () => {
      try {
        setError(null);
        const response = await fetch("/api/agent/comparison");
        if (!response.ok) {
          throw new Error(
            `Failed to fetch model comparison: ${response.statusText}`,
          );
        }

        const data: ComparisonData = await response.json();
        setComparison(data);
        setActiveAgent("sac");
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load comparison data",
        );
        console.error("Error fetching model comparison:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchComparison();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading model comparison...</p>
        </div>
      </div>
    );
  }

  if (error || !comparison) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800 font-semibold">Error Loading Comparison</p>
          <p className="text-red-700 mt-1">
            {error ||
              "No comparison data available. Please run the evaluation first."}
          </p>
        </div>
      </div>
    );
  }

  const agents = comparison.agents;
  const activeAgentData = agents[activeAgent];

  // Prepare data for charts
  const rewardData = Object.entries(agents).map(([name, data]) => ({
    name: name.toUpperCase(),
    reward: data.mean_reward || 0,
    error: data.std_reward || 0,
  }));

  const characteristicsData = [
    {
      metric: "Reward",
      sac: agents.sac?.mean_reward || 0,
      ppo: agents.ppo?.mean_reward || 0,
      bandit: agents.bandit?.mean_reward || 0,
      fullMark: 160,
    },
    {
      metric: "Stability",
      sac: Math.max(0, 100 - (agents.sac?.std_reward || 0)),
      ppo: Math.max(0, 100 - (agents.ppo?.std_reward || 0)),
      bandit: Math.max(0, 100 - (agents.bandit?.std_reward || 0)),
      fullMark: 100,
    },
    {
      metric: "Episodes",
      sac: Math.min(100, ((agents.sac?.total_episodes || 0) / 500) * 100),
      ppo: Math.min(100, ((agents.ppo?.total_episodes || 0) / 500) * 100),
      bandit: Math.min(100, ((agents.bandit?.total_episodes || 0) / 500) * 100),
      fullMark: 100,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            Model Comparison Dashboard
          </h1>
          <p className="text-gray-600 mt-1">
            Comprehensive analysis of all trained agents
          </p>
        </div>
        <div className="text-right text-sm text-gray-500">
          Last updated: {new Date(comparison.timestamp).toLocaleDateString()}
        </div>
      </div>

      {/* Recommendation Card */}
      <div className="bg-linear-to-r from-blue-500 to-blue-600 rounded-lg p-6 text-white">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-blue-100 text-sm font-semibold">
              DEPLOYMENT RECOMMENDATION
            </p>
            <h2 className="text-2xl font-bold mt-2">
              {comparison.recommendation}
            </h2>
            <p className="text-blue-100 mt-2">
              {activeAgentData?.type || "Advanced RL Agent"}
            </p>
          </div>
          <TrendingUp className="h-8 w-8 text-blue-100" />
        </div>
      </div>

      {/* Agent Selection */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Select Agent to Compare</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {Object.entries(agents).map(([name, data]) => (
            <button
              key={name}
              onClick={() => setActiveAgent(name)}
              className={`p-4 rounded-lg border-2 transition-all ${
                activeAgent === name
                  ? "border-blue-600 bg-blue-50"
                  : "border-gray-200 bg-white hover:border-gray-300"
              }`}
            >
              <h3 className="font-semibold text-gray-900 uppercase text-sm">
                {name}
              </h3>
              <p className="text-2xl font-bold text-gray-900 mt-2">
                {data.mean_reward?.toFixed(2) || "N/A"}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                ±{data.std_reward?.toFixed(2) || "N/A"}
              </p>
            </button>
          ))}
        </div>
      </div>

      {/* Metrics Grid */}
      {activeAgentData && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-gray-600 text-sm">Mean Reward</p>
            <p className="text-2xl font-bold text-gray-900 mt-2">
              {activeAgentData.mean_reward?.toFixed(2)}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              ±{activeAgentData.std_reward?.toFixed(2)}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-gray-600 text-sm">Max Reward</p>
            <p className="text-2xl font-bold text-green-600 mt-2">
              {activeAgentData.max_reward?.toFixed(2)}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-gray-600 text-sm">Min Reward</p>
            <p className="text-2xl font-bold text-red-600 mt-2">
              {activeAgentData.min_reward?.toFixed(2)}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-gray-600 text-sm">Total Episodes</p>
            <p className="text-2xl font-bold text-blue-600 mt-2">
              {activeAgentData.total_episodes}
            </p>
          </div>
        </div>
      )}

      {/* Characteristics and Strengths */}
      {activeAgentData && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Strengths */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center gap-2 mb-4">
              <Zap className="h-5 w-5 text-green-600" />
              <h3 className="font-semibold text-gray-900">Strengths</h3>
            </div>
            <ul className="space-y-2">
              {(activeAgentData.strengths || []).map((strength, i) => (
                <li key={i} className="text-sm text-gray-700 flex gap-2">
                  <span className="text-green-600 mt-1">✓</span>
                  <span>{strength}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Weaknesses */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center gap-2 mb-4">
              <AlertCircle className="h-5 w-5 text-red-600" />
              <h3 className="font-semibold text-gray-900">Weaknesses</h3>
            </div>
            <ul className="space-y-2">
              {(activeAgentData.weaknesses || []).map((weakness, i) => (
                <li key={i} className="text-sm text-gray-700 flex gap-2">
                  <span className="text-red-600 mt-1">✗</span>
                  <span>{weakness}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Best For */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center gap-2 mb-4">
              <Shield className="h-5 w-5 text-blue-600" />
              <h3 className="font-semibold text-gray-900">Best For</h3>
            </div>
            <p className="text-sm text-gray-700 leading-relaxed">
              {activeAgentData.best_for || "General purpose deployment"}
            </p>
          </div>
        </div>
      )}

      {/* Charts Section */}
      <div className="space-y-6">
        {/* Reward Comparison Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4 text-gray-900">
            Performance Metrics
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={rewardData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis
                label={{
                  value: "Mean Reward",
                  angle: -90,
                  position: "insideLeft",
                }}
              />
              <Tooltip />
              <Bar dataKey="reward" fill="#3b82f6" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Characteristics Comparison */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4 text-gray-900">
            Agent Characteristics
          </h3>
          <ResponsiveContainer width="100%" height={400}>
            <RadarChart data={characteristicsData}>
              <PolarGrid />
              <PolarAngleAxis dataKey="metric" />
              <PolarRadiusAxis angle={90} domain={[0, 150]} />
              <Radar
                name="SAC"
                dataKey="sac"
                stroke="#3b82f6"
                fill="#3b82f6"
                fillOpacity={0.25}
              />
              <Radar
                name="PPO"
                dataKey="ppo"
                stroke="#10b981"
                fill="#10b981"
                fillOpacity={0.15}
              />
              <Radar
                name="Bandit"
                dataKey="bandit"
                stroke="#f59e0b"
                fill="#f59e0b"
                fillOpacity={0.15}
              />
              <Legend />
              <Tooltip />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

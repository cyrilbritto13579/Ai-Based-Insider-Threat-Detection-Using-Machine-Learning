import React from 'react';
import {
  Users,
  Activity,
  ShieldAlert,
  AlertTriangle,
  Flame,
  CheckCircle2,
  Server,
  Database,
  Cpu,
  Radio,
} from 'lucide-react';
import { User, Alert, RiskOverview } from '../types';
import { StatCard } from '../components/StatCard';
import { RiskBadge } from '../components/RiskBadge';
import { TierDistributionChart, RiskHistogramChart } from '../components/Charts';

interface OverviewPageProps {
  overview: RiskOverview | null;
  users: User[];
  alerts: Alert[];
  onSelectUser: (userId: string) => void;
  onNavigateToAlerts: () => void;
}

export const OverviewPage: React.FC<OverviewPageProps> = ({
  overview,
  users,
  alerts,
  onSelectUser,
  onNavigateToAlerts,
}) => {
  const recentAlerts = alerts.slice(0, 6);

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white">
          Security Operations Center Overview
        </h2>
        <p className="text-sm text-slate-400">
          Real-time dynamic risk telemetry and explainable threat scoring across enterprise assets.
        </p>
      </div>

      {/* Top Level Metric Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-5">
        <StatCard
          title="Monitored Users"
          value={overview?.total_monitored_users ?? users.length}
          subtitle="TechNova enterprise scope"
          icon={Users}
          color="cyan"
        />
        <StatCard
          title="Events Analyzed"
          value={overview?.total_events_analyzed ?? 0}
          subtitle="Live & ingested logs"
          icon={Activity}
          color="purple"
        />
        <StatCard
          title="Open Alerts"
          value={overview?.open_alerts_count ?? 0}
          subtitle="Requires investigation"
          icon={ShieldAlert}
          color="orange"
        />
        <StatCard
          title="High Risk Users"
          value={overview?.high_risk_count ?? 0}
          subtitle="Score 60–79"
          icon={AlertTriangle}
          color="orange"
        />
        <StatCard
          title="Critical Alerts"
          value={overview?.critical_alerts_count ?? 0}
          subtitle="Tier CRITICAL"
          icon={Flame}
          color="red"
        />
      </div>

      {/* Main Visualizations: Risk Tier Pie & Score Histogram */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Tier Distribution */}
        <div className="rounded-xl border border-slate-700/70 bg-slate-950/70 p-5 shadow-lg">
          <div className="flex items-center justify-between pb-4 border-b border-slate-700/70">
            <div>
              <h3 className="text-sm font-semibold text-white">Risk Tier Concentration</h3>
              <p className="text-xs text-slate-400">Proportion of users per threat severity category</p>
            </div>
            <span className="text-xs font-mono text-blue-300 bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20">
              Live State
            </span>
          </div>
          <div className="pt-5">
            <TierDistributionChart distribution={overview?.tier_distribution ?? {}} />
          </div>
        </div>

        {/* Score Distribution Histogram */}
        <div className="rounded-xl border border-slate-700/70 bg-slate-950/70 p-5 shadow-lg">
          <div className="flex items-center justify-between pb-4 border-b border-slate-700/70">
            <div>
              <h3 className="text-sm font-semibold text-white">Dynamic Risk Score Spectrum</h3>
              <p className="text-xs text-slate-400">0–100 composite score distribution across active workforce</p>
            </div>
            <span className="text-xs font-mono text-slate-300 bg-slate-800 px-2 py-0.5 rounded">
              0–100 Scale
            </span>
          </div>
          <RiskHistogramChart users={users} />
        </div>
      </div>

      {/* Bottom Section: Recent Alerts Table & System Health */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Recent Alerts Feed */}
        <div className="lg:col-span-2 rounded-xl border border-[#1f293d] bg-[#111827] p-5 shadow-lg">
          <div className="flex items-center justify-between pb-4 border-b border-[#1f293d]">
            <div>
              <h3 className="text-sm font-semibold text-white">Recent Security Alerts</h3>
              <p className="text-xs text-slate-400">Actionable incident triage prioritized by dynamic risk score</p>
            </div>
            <button
              onClick={onNavigateToAlerts}
              className="text-xs font-medium text-cyan-400 hover:text-cyan-300 transition-colors"
            >
              View all alerts →
            </button>
          </div>

          <div className="mt-3 divide-y divide-[#1f293d] overflow-hidden">
            {recentAlerts.length === 0 ? (
              <div className="py-8 text-center text-xs text-slate-400">
                <CheckCircle2 className="h-6 w-6 text-emerald-400 mx-auto mb-2 opacity-80" />
                No active security alerts. Enterprise activity is within normal thresholds.
              </div>
            ) : (
              recentAlerts.map((alert) => (
                <div
                  key={alert.alert_id}
                  onClick={() => onSelectUser(alert.user_id)}
                  className="flex items-center justify-between py-3 px-2 hover:bg-[#1e293b]/50 rounded-lg cursor-pointer transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <RiskBadge tier={alert.risk_tier} score={alert.risk_score} showScore />
                    <div>
                      <p className="text-xs font-medium text-slate-200">{alert.behavior}</p>
                      <p className="text-[11px] text-slate-400 font-mono">
                        {alert.user_id} ({alert.user_name || alert.department})
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-[11px] font-mono text-slate-400">
                      {new Date(alert.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                    </span>
                    <p className="text-[10px] text-cyan-400 font-medium">Investigate →</p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* System Health Cards */}
        <div className="rounded-xl border border-[#1f293d] bg-[#111827] p-5 shadow-lg flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-semibold text-white pb-4 border-b border-[#1f293d]">
              System Health & Pipeline
            </h3>
            <div className="space-y-3 mt-4 text-xs">
              <div className="flex items-center justify-between p-2 rounded-lg bg-[#0b0f17] border border-[#1f293d]">
                <div className="flex items-center gap-2 text-slate-300">
                  <Server className="h-4 w-4 text-emerald-400" />
                  <span>FastAPI Core API</span>
                </div>
                <span className="font-mono text-[11px] text-emerald-400 font-bold">ONLINE</span>
              </div>

              <div className="flex items-center justify-between p-2 rounded-lg bg-[#0b0f17] border border-[#1f293d]">
                <div className="flex items-center gap-2 text-slate-300">
                  <Database className="h-4 w-4 text-emerald-400" />
                  <span>SQLite Database</span>
                </div>
                <span className="font-mono text-[11px] text-emerald-400 font-bold">CONNECTED</span>
              </div>

              <div className="flex items-center justify-between p-2 rounded-lg bg-[#0b0f17] border border-[#1f293d]">
                <div className="flex items-center gap-2 text-slate-300">
                  <Cpu className="h-4 w-4 text-cyan-400" />
                  <span>ML Model Engine</span>
                </div>
                <span className="font-mono text-[11px] text-cyan-400 font-bold">XGBOOST</span>
              </div>

              <div className="flex items-center justify-between p-2 rounded-lg bg-[#0b0f17] border border-[#1f293d]">
                <div className="flex items-center gap-2 text-slate-300">
                  <Radio className="h-4 w-4 text-amber-400" />
                  <span>Live Simulator</span>
                </div>
                <span className="font-mono text-[11px] text-amber-400 font-bold">READY</span>
              </div>
            </div>
          </div>

          <div className="mt-4 p-3 rounded-lg bg-cyan-950/20 border border-cyan-500/20 text-[11px] text-cyan-300">
            <span className="font-bold">Explainability status:</span> SHAP TreeExplainer ready with instant local factor calculation.
          </div>
        </div>
      </div>
    </div>
  );
};

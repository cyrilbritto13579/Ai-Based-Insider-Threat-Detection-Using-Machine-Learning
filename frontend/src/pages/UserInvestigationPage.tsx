import React, { useState, useEffect } from 'react';
import {
  UserSearch,
  Shield,
  Clock,
  Laptop,
  Mail,
  FileText,
  HardDrive,
  AlertTriangle,
  BrainCircuit,
  TrendingUp,
  History,
  Info,
  ShieldOff,
  ShieldCheck,
  MapPin,
  Briefcase,
  Calendar,
  User as UserIcon,
  LogIn,
  FileDown,
} from 'lucide-react';
import { User, UserDetail, RiskHistoryPoint, ActivityEvent, ShapExplanation, FEATURE_LABELS } from '../types';
import { RiskBadge } from '../components/RiskBadge';
import { ShapWaterfallChart } from '../components/Charts';
import { api } from '../api/client';

interface UserInvestigationPageProps {
  users: User[];
  selectedUserId: string;
  onSelectUser: (userId: string) => void;
}

export const UserInvestigationPage: React.FC<UserInvestigationPageProps> = ({
  users,
  selectedUserId,
  onSelectUser,
}) => {
  const [userDetail, setUserDetail] = useState<UserDetail | null>(null);
  const [timeline, setTimeline] = useState<RiskHistoryPoint[]>([]);
  const [events, setEvents] = useState<ActivityEvent[]>([]);
  const [explanation, setExplanation] = useState<ShapExplanation | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [blockLoading, setBlockLoading] = useState<boolean>(false);

  // Load selected user data
  useEffect(() => {
    if (!selectedUserId) return;
    let isMounted = true;
    setLoading(true);

    Promise.all([
      api.getUserDetail(selectedUserId).catch(() => null),
      api.getUserTimeline(selectedUserId).catch(() => []),
      api.getUserEvents(selectedUserId, 500).catch(() => []),
      api.explainUser(selectedUserId).catch(() => null),
    ]).then(([detail, hist, evts, exp]) => {
      if (!isMounted) return;
      setUserDetail(detail);
      setTimeline(hist);
      setEvents(evts);
      setExplanation(exp);
      setLoading(false);
    });

    return () => {
      isMounted = false;
    };
  }, [selectedUserId]);

  const handleBlock = async () => {
    if (!userDetail) return;
    setBlockLoading(true);
    try {
      if (userDetail.account_status === 'ACTIVE') {
        await api.blockUser(userDetail.user_id, 'Blocked due to suspicious activity');
      } else {
        await api.unblockUser(userDetail.user_id, 'Administrative review completed');
      }
      // Reload user detail
      const updated = await api.getUserDetail(userDetail.user_id);
      setUserDetail(updated);
    } catch (e) {
      console.error(e);
    } finally {
      setBlockLoading(false);
    }
  };

  const sortedUsers = [...users].sort((a, b) => b.current_risk_score - a.current_risk_score);

  const formatFeatureName = (name: string): string => {
    return FEATURE_LABELS[name] || name.replace(/_/g, ' ');
  };

  return (
    <div className="space-y-6">
      {/* Top Header & User Selector */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">Deep-Dive User Investigation</h2>
          <p className="text-sm text-slate-400">
            Explainable AI threat telemetry, baseline deviation metrics, and local SHAP feature attributions.
          </p>
        </div>

        {/* User Dropdown Selector */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs text-slate-400 font-medium">Investigate User:</span>
          <select
            value={selectedUserId}
            onChange={(e) => onSelectUser(e.target.value)}
            className="rounded-lg border border-[#1f293d] bg-[#111827] px-3 py-2 text-xs font-mono font-bold text-cyan-300 focus:border-cyan-500 focus:outline-none"
          >
            {sortedUsers.map((u) => (
              <option key={u.user_id} value={u.user_id}>
                {u.user_id} — {u.name} [{u.current_risk_tier} ({u.current_risk_score})]
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={() => window.location.assign(api.getUserReportUrl(selectedUserId))}
            disabled={!userDetail || loading}
            title="Download employee activity and risk report"
            className="inline-flex items-center gap-2 rounded-lg border border-blue-500/30 bg-blue-500/10 px-3 py-2 text-xs font-semibold text-blue-200 hover:bg-blue-500/20 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <FileDown className="h-4 w-4" />
            Download Report
          </button>
        </div>
      </div>

      {loading && (
        <div className="rounded-xl border border-cyan-500/20 bg-cyan-950/20 p-4 text-center text-xs text-cyan-300 animate-pulse">
          Computing SHAP values and loading historical telemetry for {selectedUserId}...
        </div>
      )}

      {userDetail && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {/* Column 1: Profile & Behavioral Baselines */}
          <div className="space-y-6">
            {/* Profile Card */}
            <div className="rounded-xl border border-[#1f293d] bg-[#111827] p-5 shadow-lg space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-[#1f293d]">
                <div>
                  <h3 className="text-base font-bold text-white">{userDetail.name}</h3>
                  <p className="text-xs text-slate-400 font-mono">{userDetail.user_id}</p>
                </div>
                <RiskBadge tier={userDetail.current_risk_tier} score={userDetail.current_risk_score} showScore size="lg" />
              </div>

              {/* Account Status Banner */}
              {userDetail.account_status === 'BLOCKED' && (
                <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-2 text-xs text-red-300 flex items-center gap-2">
                  <ShieldOff className="h-4 w-4 text-red-400" />
                  <span className="font-semibold">Account BLOCKED — Access Revoked</span>
                </div>
              )}

              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="rounded-lg bg-[#0b0f17] p-2.5 border border-[#1f293d]">
                  <span className="text-[10px] uppercase text-slate-400 font-semibold flex items-center gap-1">
                    <Briefcase className="h-3 w-3" /> Department
                  </span>
                  <p className="font-medium text-slate-200 mt-0.5">{userDetail.department}</p>
                </div>
                <div className="rounded-lg bg-[#0b0f17] p-2.5 border border-[#1f293d]">
                  <span className="text-[10px] uppercase text-slate-400 font-semibold flex items-center gap-1">
                    <UserIcon className="h-3 w-3" /> Role
                  </span>
                  <p className="font-medium text-slate-200 mt-0.5">{userDetail.role}</p>
                </div>
                <div className="rounded-lg bg-[#0b0f17] p-2.5 border border-[#1f293d]">
                  <span className="text-[10px] uppercase text-slate-400 font-semibold flex items-center gap-1">
                    <Laptop className="h-3 w-3" /> Workstation
                  </span>
                  <p className="font-mono font-medium text-cyan-400 mt-0.5">{userDetail.assigned_pc}</p>
                </div>
                <div className="rounded-lg bg-[#0b0f17] p-2.5 border border-[#1f293d]">
                  <span className="text-[10px] uppercase text-slate-400 font-semibold">ML Probability</span>
                  <p className="font-mono font-medium text-slate-200 mt-0.5">
                    {Math.round(userDetail.ml_probability * 100)}%
                  </p>
                </div>
                {userDetail.manager && (
                  <div className="rounded-lg bg-[#0b0f17] p-2.5 border border-[#1f293d]">
                    <span className="text-[10px] uppercase text-slate-400 font-semibold">Manager</span>
                    <p className="font-medium text-slate-200 mt-0.5">{userDetail.manager}</p>
                  </div>
                )}
                {userDetail.location && (
                  <div className="rounded-lg bg-[#0b0f17] p-2.5 border border-[#1f293d]">
                    <span className="text-[10px] uppercase text-slate-400 font-semibold flex items-center gap-1">
                      <MapPin className="h-3 w-3" /> Location
                    </span>
                    <p className="font-medium text-slate-200 mt-0.5">{userDetail.location}</p>
                  </div>
                )}
                {userDetail.join_date && (
                  <div className="rounded-lg bg-[#0b0f17] p-2.5 border border-[#1f293d]">
                    <span className="text-[10px] uppercase text-slate-400 font-semibold flex items-center gap-1">
                      <Calendar className="h-3 w-3" /> Joined
                    </span>
                    <p className="font-medium text-slate-200 mt-0.5">{userDetail.join_date}</p>
                  </div>
                )}
                <div className="rounded-lg bg-[#0b0f17] p-2.5 border border-[#1f293d]">
                  <span className="text-[10px] uppercase text-slate-400 font-semibold flex items-center gap-1">
                    <Clock className="h-3 w-3" /> Normal Hours
                  </span>
                  <p className="font-medium text-slate-200 mt-0.5">{userDetail.normal_hours}</p>
                </div>
              </div>

              {/* Activity Summary */}
              <div className="grid grid-cols-4 gap-2 text-center text-xs pt-2 border-t border-[#1f293d]">
                <div className="rounded bg-[#0b0f17] p-2 border border-[#1f293d]">
                  <LogIn className="h-3.5 w-3.5 text-slate-400 mx-auto" />
                  <p className="font-bold text-slate-200 mt-1">{userDetail.login_count}</p>
                  <p className="text-[9px] text-slate-500">Logins</p>
                </div>
                <div className="rounded bg-[#0b0f17] p-2 border border-[#1f293d]">
                  <HardDrive className="h-3.5 w-3.5 text-orange-400 mx-auto" />
                  <p className="font-bold text-slate-200 mt-1">{userDetail.device_count}</p>
                  <p className="text-[9px] text-slate-500">Devices</p>
                </div>
                <div className="rounded bg-[#0b0f17] p-2 border border-[#1f293d]">
                  <FileText className="h-3.5 w-3.5 text-purple-400 mx-auto" />
                  <p className="font-bold text-slate-200 mt-1">{userDetail.file_count}</p>
                  <p className="text-[9px] text-slate-500">Files</p>
                </div>
                <div className="rounded bg-[#0b0f17] p-2 border border-[#1f293d]">
                  <Mail className="h-3.5 w-3.5 text-blue-400 mx-auto" />
                  <p className="font-bold text-slate-200 mt-1">{userDetail.email_count}</p>
                  <p className="text-[9px] text-slate-500">Emails</p>
                </div>
              </div>

              {/* Block / Unblock Button */}
              <button
                onClick={handleBlock}
                disabled={blockLoading}
                className={`w-full rounded-lg py-2 text-xs font-semibold transition-colors flex items-center justify-center gap-1.5 disabled:opacity-50 ${
                  userDetail.account_status === 'ACTIVE'
                    ? 'bg-red-500/15 border border-red-500/30 text-red-400 hover:bg-red-500/25'
                    : 'bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/25'
                }`}
              >
                {userDetail.account_status === 'ACTIVE' ? (
                  <>
                    <ShieldOff className="h-3.5 w-3.5" />
                    Block Account
                  </>
                ) : (
                  <>
                    <ShieldCheck className="h-3.5 w-3.5" />
                    Unblock Account
                  </>
                )}
              </button>
            </div>

            {/* Historical Behavioral Baseline Stats */}
            <div className="rounded-xl border border-[#1f293d] bg-[#111827] p-5 shadow-lg space-y-3">
              <div className="flex items-center gap-2 pb-2 border-b border-[#1f293d]">
                <Shield className="h-4 w-4 text-cyan-400" />
                <h3 className="text-xs font-bold uppercase tracking-wider text-white">
                  Learned Behavioral Profile
                </h3>
              </div>
              <p className="text-[11px] text-slate-400">
                User-specific historical normal calculated exclusively on training window.
              </p>

              <div className="space-y-2 text-xs">
                {Object.entries(userDetail.baseline_stats || {}).slice(0, 6).map(([key, val]) => (
                  <div key={key} className="flex justify-between items-center py-1 border-b border-[#1f293d]/50 font-mono text-[11px]">
                    <span className="text-slate-400 font-sans capitalize">{formatFeatureName(key)}:</span>
                    <span className="text-slate-200 font-bold">{Number(val).toFixed(2)}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Column 2: Explainable AI (SHAP) & Security Rationale */}
          <div className="lg:col-span-2 space-y-6">
            {/* SHAP Explanation Card */}
            <div className="rounded-xl border border-cyan-500/30 bg-[#111827] p-5 shadow-lg relative overflow-hidden">
              <div className="flex items-center justify-between pb-3 border-b border-[#1f293d]">
                <div className="flex items-center gap-2">
                  <BrainCircuit className="h-5 w-5 text-cyan-400" />
                  <h3 className="text-sm font-bold text-white">
                    Explainable AI (SHAP Attribution)
                  </h3>
                </div>
                <span className="text-[10px] font-mono text-cyan-300 bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20">
                  TreeExplainer Exact
                </span>
              </div>

              {/* Natural Language Rationale Box */}
              <div className="mt-4 rounded-lg bg-[#0b0f17] p-4 border border-[#1f293d]">
                <div className="flex items-center gap-2 text-xs font-semibold text-cyan-400 mb-2">
                  <Info className="h-4 w-4" />
                  <span>Automated Defensive Security Rationale</span>
                </div>
                <p className="text-xs text-slate-200 leading-relaxed font-mono whitespace-pre-line">
                  {explanation?.text_explanation || userDetail.explanation}
                </p>
              </div>

              {/* SHAP Factor Impact Breakdown */}
              <div className="mt-5">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">
                  Top Contributing Behavioral Features
                </h4>
                <ShapWaterfallChart factors={explanation?.top_factors || userDetail.top_factors} />
              </div>
            </div>

            {/* Risk History Timeline & Event Log */}
            <div className="rounded-xl border border-[#1f293d] bg-[#111827] p-5 shadow-lg space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-[#1f293d]">
                <div className="flex items-center gap-2">
                  <History className="h-4 w-4 text-cyan-400" />
                  <h3 className="text-sm font-bold text-white">Recent Activity Timeline</h3>
                </div>
                <span className="text-xs text-slate-400 font-mono">
                  {events.length} Events Captured
                </span>
              </div>

              <div className="divide-y divide-[#1f293d] max-h-64 overflow-y-auto pr-2 text-xs">
                {events.length === 0 ? (
                  <p className="py-6 text-center text-slate-400 text-xs">No recent activity logs recorded.</p>
                ) : (
                  events.map((evt) => (
                    <div key={evt.event_id} className="py-2.5 flex items-center justify-between">
                      <div className="flex items-center gap-2.5">
                        <span
                          className={`rounded px-1.5 py-0.5 text-[10px] font-mono font-bold ${
                            evt.activity_type.includes('DEVICE')
                              ? 'bg-orange-500/20 text-orange-400 border border-orange-500/30'
                              : evt.activity_type.includes('FILE')
                              ? 'bg-purple-500/20 text-purple-400 border border-purple-500/30'
                              : evt.activity_type.includes('EMAIL')
                              ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                              : 'bg-slate-800 text-slate-300'
                          }`}
                        >
                          {evt.activity_type}
                        </span>
                        <span className="text-slate-300 font-mono text-[11px] truncate max-w-xs">
                          {evt.details?.filename || evt.details?.action || evt.details?.subject || evt.pc}
                        </span>
                        {evt.is_after_hours && (
                          <span className="rounded bg-red-500/20 px-1 text-[10px] font-bold text-red-400">
                            AFTER-HOURS
                          </span>
                        )}
                      </div>
                      <span className="text-[11px] font-mono text-slate-400">
                        {new Date(evt.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                      </span>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

import React, { useState } from 'react';
import {
  Bell,
  Filter,
  Search,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  ChevronRight,
} from 'lucide-react';
import { Alert, RiskTier } from '../types';
import { RiskBadge } from '../components/RiskBadge';
import { api } from '../api/client';

interface AlertsPageProps {
  alerts: Alert[];
  onSelectUser: (userId: string) => void;
  onRefreshAlerts: () => void;
}

export const AlertsPage: React.FC<AlertsPageProps> = ({
  alerts,
  onSelectUser,
  onRefreshAlerts,
}) => {
  const [tierFilter, setTierFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);

  // Filtering
  const filteredAlerts = alerts.filter((a) => {
    if (tierFilter !== 'ALL' && String(a.risk_tier ?? '').toUpperCase() !== tierFilter) return false;
    if (statusFilter !== 'ALL' && String(a.status ?? '').toUpperCase() !== statusFilter) return false;
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      const matchUser = String(a.user_id ?? '').toLowerCase().includes(term);
      const matchName = (a.user_name || '').toLowerCase().includes(term);
      const matchDept = (a.department || '').toLowerCase().includes(term);
      const matchBehavior = String(a.behavior ?? '').toLowerCase().includes(term);
      if (!matchUser && !matchName && !matchDept && !matchBehavior) return false;
    }
    return true;
  });

  const handleStatusChange = async (alertId: string, newStatus: string) => {
    try {
      await api.acknowledgeAlert(alertId, newStatus, notes);
      onRefreshAlerts();
      if (selectedAlert) {
        setSelectedAlert({ ...selectedAlert, status: newStatus as any, notes });
      }
    } catch (e) {
      console.error(e);
    }
  };

  const [notes, setNotes] = useState<string>('');

  React.useEffect(() => {
    if (selectedAlert) {
      setNotes(selectedAlert.notes || '');
    }
  }, [selectedAlert]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">Alert Triage Inbox</h2>
          <p className="text-sm text-slate-400">
            Actionable insider threat incidents sorted by composite dynamic AI risk score.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-slate-400">
            Showing <strong className="text-white">{filteredAlerts.length}</strong> of <strong className="text-white">{alerts.length}</strong> alerts
          </span>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-wrap items-center gap-3 rounded-xl border border-[#1f293d] bg-[#111827] p-3">
        {/* Search */}
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search by User ID, Name, Department, or Behavior..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full rounded-lg border border-[#1f293d] bg-[#0b0f17] py-2 pl-9 pr-3 text-xs text-slate-200 placeholder-slate-400 focus:border-cyan-500 focus:outline-none"
          />
        </div>

        {/* Tier Filter */}
        <div className="flex items-center gap-1.5 text-xs text-slate-400">
          <Filter className="h-3.5 w-3.5" />
          <span>Tier:</span>
          <select
            value={tierFilter}
            onChange={(e) => setTierFilter(e.target.value)}
            className="rounded-lg border border-[#1f293d] bg-[#0b0f17] px-2.5 py-1.5 text-xs text-slate-200 focus:border-cyan-500 focus:outline-none"
          >
            <option value="ALL">All Tiers</option>
            <option value="CRITICAL">Critical Only</option>
            <option value="HIGH">High Only</option>
            <option value="MEDIUM">Medium Only</option>
            <option value="LOW">Low</option>
          </select>
        </div>

        {/* Status Filter */}
        <div className="flex items-center gap-1.5 text-xs text-slate-400">
          <span>Status:</span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-lg border border-[#1f293d] bg-[#0b0f17] px-2.5 py-1.5 text-xs text-slate-200 focus:border-cyan-500 focus:outline-none"
          >
            <option value="ALL">All Statuses</option>
            <option value="NEW">New</option>
            <option value="ACKNOWLEDGED">Acknowledged</option>
            <option value="INVESTIGATING">Investigating</option>
            <option value="RESOLVED">Resolved</option>
            <option value="FALSE_POSITIVE">False Positive</option>
          </select>
        </div>
      </div>

      {/* Main Alert List & Drawer */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Alerts Table */}
        <div className="lg:col-span-2 rounded-xl border border-[#1f293d] bg-[#111827] overflow-hidden shadow-lg">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-[#1f293d] bg-[#0b0f17] text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                <tr>
                  <th className="py-3 px-4">Severity</th>
                  <th className="py-3 px-4">User</th>
                  <th className="py-3 px-4">Behavioral Reason</th>
                  <th className="py-3 px-4">Time</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1f293d]">
                {filteredAlerts.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-12 text-center text-slate-400">
                      <AlertCircle className="h-6 w-6 text-slate-500 mx-auto mb-2" />
                      No alerts match the selected criteria.
                    </td>
                  </tr>
                ) : (
                  filteredAlerts.map((alert) => {
                    const isSelected = selectedAlert?.alert_id === alert.alert_id;
                    return (
                      <tr
                        key={alert.alert_id}
                        onClick={() => setSelectedAlert(alert)}
                        className={`hover:bg-[#1e293b]/60 cursor-pointer transition-colors ${
                          isSelected ? 'bg-cyan-950/30 border-l-2 border-cyan-400' : ''
                        }`}
                      >
                        <td className="py-3 px-4">
                          <RiskBadge tier={alert.risk_tier} score={alert.risk_score} showScore />
                        </td>
                        <td className="py-3 px-4">
                          <div className="font-mono font-bold text-slate-200">{alert.user_id}</div>
                          <div className="text-[11px] text-slate-400">{alert.user_name || alert.department}</div>
                        </td>
                        <td className="py-3 px-4 max-w-xs">
                          <p className="font-medium text-slate-200 truncate">{alert.behavior}</p>
                          <p className="text-[11px] text-slate-400 truncate">{alert.primary_reason}</p>
                        </td>
                        <td className="py-3 px-4 font-mono text-slate-400 text-[11px] whitespace-nowrap">
                          {new Date(alert.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                        </td>
                        <td className="py-3 px-4 text-right whitespace-nowrap flex flex-col gap-1 items-end">
                          <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${
                            alert.status === 'NEW' ? 'bg-purple-500/20 text-purple-400' :
                            alert.status === 'INVESTIGATING' ? 'bg-blue-500/20 text-blue-400' :
                            alert.status === 'FALSE_POSITIVE' ? 'bg-slate-500/20 text-slate-400' :
                            alert.status === 'RESOLVED' ? 'bg-emerald-500/20 text-emerald-400' :
                            'bg-cyan-500/20 text-cyan-400'
                          }`}>
                            {alert.status}
                          </span>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              onSelectUser(alert.user_id);
                            }}
                            className="inline-flex items-center gap-1 rounded bg-cyan-500/10 px-2 py-1 text-[11px] font-medium text-cyan-400 hover:bg-cyan-500/20 border border-cyan-500/20 transition-colors"
                          >
                            Investigate
                            <ExternalLink className="h-3 w-3" />
                          </button>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Alert Details Sidebar */}
        <div className="rounded-xl border border-[#1f293d] bg-[#111827] p-5 shadow-lg flex flex-col justify-between">
          {selectedAlert ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-[#1f293d]">
                <div>
                  <span className="text-[10px] font-mono text-cyan-400 uppercase tracking-wider">
                    {selectedAlert.alert_id}
                  </span>
                  <h3 className="text-sm font-bold text-white mt-0.5">{selectedAlert.behavior}</h3>
                </div>
                <RiskBadge tier={selectedAlert.risk_tier} score={selectedAlert.risk_score} showScore />
              </div>

              {/* User meta */}
              <div className="rounded-lg bg-[#0b0f17] p-3 border border-[#1f293d] text-xs space-y-1.5">
                <div className="flex justify-between">
                  <span className="text-slate-400">User ID:</span>
                  <span className="font-mono font-bold text-slate-200">{selectedAlert.user_id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Employee Name:</span>
                  <span className="text-slate-200">{selectedAlert.user_name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Department:</span>
                  <span className="text-slate-200">{selectedAlert.department}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Status:</span>
                  <span className={`font-mono font-semibold ${
                            selectedAlert.status === 'NEW' ? 'text-purple-400' :
                            selectedAlert.status === 'INVESTIGATING' ? 'text-blue-400' :
                            selectedAlert.status === 'FALSE_POSITIVE' ? 'text-slate-400' :
                            selectedAlert.status === 'RESOLVED' ? 'text-emerald-400' :
                            'text-cyan-400'
                          }`}>
                    {selectedAlert.status}
                  </span>
                </div>
              </div>

              {/* Primary Reason */}
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Primary Threat Rationale
                </h4>
                <p className="mt-1 text-xs text-slate-300 leading-relaxed rounded-lg bg-[#0b0f17] p-3 border border-[#1f293d]">
                  {selectedAlert.primary_reason}
                </p>
              </div>

              {/* Investigator Notes */}
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
                  Investigator Notes
                </h4>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Add context or rationale for status change..."
                  className="w-full h-20 rounded-lg border border-[#1f293d] bg-[#0b0f17] p-2 text-xs text-slate-200 placeholder-slate-500 focus:border-cyan-500 focus:outline-none resize-none"
                />
              </div>

              {/* Action Buttons */}
              <div className="pt-2 flex flex-col gap-2">
                <button
                  onClick={() => onSelectUser(selectedAlert.user_id)}
                  className="w-full rounded-lg bg-cyan-500 py-2.5 text-xs font-semibold text-slate-950 hover:bg-cyan-400 transition-colors flex items-center justify-center gap-1.5"
                >
                  Open Deep Dive Investigation
                  <ChevronRight className="h-4 w-4" />
                </button>

                <div className="grid grid-cols-2 gap-2 mt-2">
                  <button
                    onClick={() => handleStatusChange(selectedAlert.alert_id, 'INVESTIGATING')}
                    className="rounded-lg border border-blue-500/30 bg-blue-500/10 py-2 text-xs font-medium text-blue-400 hover:bg-blue-500/20 transition-colors"
                  >
                    Investigate
                  </button>
                  <button
                    onClick={() => handleStatusChange(selectedAlert.alert_id, 'RESOLVED')}
                    className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 py-2 text-xs font-medium text-emerald-400 hover:bg-emerald-500/20 transition-colors"
                  >
                    Resolve
                  </button>
                  <button
                    onClick={() => handleStatusChange(selectedAlert.alert_id, 'FALSE_POSITIVE')}
                    className="col-span-2 rounded-lg border border-slate-600 bg-slate-800/60 py-2 text-xs font-medium text-slate-300 hover:bg-slate-700 transition-colors"
                  >
                    Mark False Positive
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="py-20 text-center text-xs text-slate-400">
              <Bell className="h-8 w-8 text-slate-500 mx-auto mb-2 opacity-50" />
              Select an alert from the table to view its full threat explanation and telemetry.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

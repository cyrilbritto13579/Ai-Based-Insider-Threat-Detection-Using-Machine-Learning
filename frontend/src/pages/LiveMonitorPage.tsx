import React from 'react';
import {
  Radio,
  Activity,
  HardDrive,
  Mail,
  LogIn,
  LogOut,
  FileText,
  AlertTriangle,
  Zap,
} from 'lucide-react';
import { ActivityEvent, RiskTier } from '../types';
import { RiskBadge } from '../components/RiskBadge';

interface LiveMonitorPageProps {
  events: ActivityEvent[];
  wsConnected: boolean;
  onSelectUser: (userId: string) => void;
}

export const LiveMonitorPage: React.FC<LiveMonitorPageProps> = ({
  events,
  wsConnected,
  onSelectUser,
}) => {
  const getEventIcon = (type: string) => {
    if (type.includes('DEVICE')) return HardDrive;
    if (type.includes('FILE')) return FileText;
    if (type.includes('EMAIL')) return Mail;
    if (type === 'LOGIN' || type === 'LOGON') return LogIn;
    if (type === 'LOGOUT' || type === 'LOGOFF') return LogOut;
    return Activity;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-2xl font-bold tracking-tight text-white">Live Event Telemetry Stream</h2>
            <span className="flex h-3 w-3 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-cyan-500"></span>
            </span>
          </div>
          <p className="text-sm text-slate-400">
            Real-time WebSocket event ingestion passing through online ML inference and dynamic risk engine.
          </p>
        </div>

        <div className="flex items-center gap-2 rounded-lg border border-[#1f293d] bg-[#111827] px-3 py-1.5 text-xs font-mono">
          <span className={`h-2 w-2 rounded-full ${wsConnected ? 'bg-emerald-400' : 'bg-red-500'}`} />
          <span className="text-slate-300">
            {wsConnected ? 'SOCKET ESTABLISHED (/ws/live)' : 'SOCKET RECONNECTING...'}
          </span>
        </div>
      </div>

      {/* Stream Terminal Window */}
      <div className="rounded-xl border border-[#1f293d] bg-[#0b0f17] shadow-2xl overflow-hidden">
        {/* Terminal Titlebar */}
        <div className="flex items-center justify-between border-b border-[#1f293d] bg-[#111827] px-4 py-2.5">
          <div className="flex items-center gap-2">
            <span className="h-3 w-3 rounded-full bg-red-500/80" />
            <span className="h-3 w-3 rounded-full bg-amber-500/80" />
            <span className="h-3 w-3 rounded-full bg-emerald-500/80" />
            <span className="ml-2 font-mono text-xs text-slate-400 font-semibold">
              Live Ingestion Feed — {events.length} Events Captured
            </span>
          </div>
          <span className="text-[11px] font-mono text-cyan-400">
            Active Listeners: 1 WebSocket Client
          </span>
        </div>

        {/* Event List Feed */}
        <div className="p-4 divide-y divide-[#1f293d]/60 max-h-[600px] overflow-y-auto font-mono text-xs space-y-2">
          {events.length === 0 ? (
            <div className="py-24 text-center text-slate-500">
              <Zap className="h-8 w-8 text-cyan-500/40 mx-auto mb-2 animate-bounce" />
              <p className="font-sans text-sm text-slate-400 font-medium">Awaiting real-time simulation events...</p>
              <p className="text-xs text-slate-500 mt-1">
                Go to the <strong>Event Simulator</strong> tab to start a scenario.
              </p>
            </div>
          ) : (
            events.map((evt, idx) => {
              const Icon = getEventIcon(evt.activity_type);
              const isFirst = idx === 0;

              return (
                <div
                  key={evt.event_id || idx}
                  className={`pt-2 flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-2.5 rounded-lg transition-all ${
                    isFirst ? 'bg-cyan-950/20 border border-cyan-500/30' : 'hover:bg-[#111827]'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className="rounded p-1.5 bg-[#111827] border border-[#1f293d] text-slate-300">
                      <Icon className="h-4 w-4 text-cyan-400" />
                    </div>

                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-slate-400 text-[11px]">
                          {new Date(evt.timestamp).toLocaleTimeString([], {
                            hour: '2-digit',
                            minute: '2-digit',
                            second: '2-digit',
                          })}
                        </span>
                        <button
                          onClick={() => onSelectUser(evt.user_id)}
                          className="font-bold text-cyan-400 hover:underline"
                        >
                          {evt.user_id}
                        </button>
                        <span className="rounded bg-slate-800 px-1.5 py-0.2 text-[10px] text-slate-300">
                          {evt.pc}
                        </span>
                        <span className="font-bold text-slate-200 uppercase">
                          {evt.activity_type}
                        </span>
                        {evt.is_after_hours && (
                          <span className="rounded bg-red-500/20 px-1 text-[10px] font-bold text-red-400 border border-red-500/30">
                            AFTER-HOURS
                          </span>
                        )}
                      </div>

                      <p className="text-slate-400 text-[11px] mt-0.5">
                        {evt.details?.filename && `File: ${evt.details.filename} `}
                        {evt.details?.device_name && `Device: ${evt.details.device_name} `}
                        {evt.details?.to && `To: ${evt.details.to} `}
                        {evt.details?.subject && `Subject: "${evt.details.subject}" `}
                        {evt.details?.action && `Action: ${evt.details.action} `}
                      </p>
                    </div>
                  </div>

                  <div className="text-right">
                    <span className="text-[10px] text-slate-500 font-mono">
                      {evt.event_id}
                    </span>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};

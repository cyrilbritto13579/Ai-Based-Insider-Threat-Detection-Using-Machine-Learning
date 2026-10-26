import React from 'react';
import {
  LayoutDashboard,
  Bell,
  UserSearch,
  Radio,
  BarChart3,
  Cpu,
  FlaskConical,
  Settings as SettingsIcon,
} from 'lucide-react';

export type PageId =
  | 'overview'
  | 'alerts'
  | 'investigation'
  | 'live-monitor'
  | 'analytics'
  | 'model-performance'
  | 'simulation'
  | 'settings';

interface SidebarProps {
  currentPage: PageId;
  onSelectPage: (page: PageId) => void;
  unacknowledgedAlerts: number;
  isSimulating: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentPage,
  onSelectPage,
  unacknowledgedAlerts,
  isSimulating,
}) => {
  const navItems = [
    { id: 'overview' as PageId, label: 'Overview', icon: LayoutDashboard },
    {
      id: 'alerts' as PageId,
      label: 'Alerts Triage',
      icon: Bell,
      badge: unacknowledgedAlerts > 0 ? unacknowledgedAlerts : undefined,
    },
    {
      id: 'investigation' as PageId,
      label: 'User Investigation',
      icon: UserSearch,
    },
    {
      id: 'live-monitor' as PageId,
      label: 'Live Monitor',
      icon: Radio,
      pulse: isSimulating,
    },
    { id: 'analytics' as PageId, label: 'Analytics & XAI', icon: BarChart3 },
    {
      id: 'model-performance' as PageId,
      label: 'Model Experiments',
      icon: Cpu,
    },
    {
      id: 'simulation' as PageId,
      label: 'Event Simulator',
      icon: FlaskConical,
      highlight: isSimulating,
    },
    { id: 'settings' as PageId, label: 'System Settings', icon: SettingsIcon },
  ];

  return (
    <aside className="sticky top-0 z-20 flex w-full flex-shrink-0 flex-col justify-between border-b border-[#202633] bg-[#151923] p-3 text-white md:h-screen md:w-64 md:border-b-0 md:border-r md:p-4">
      <div className="min-w-0 md:space-y-1">
        <div className="mb-3 flex items-center gap-3 border-b border-white/10 px-2 pb-3 md:mb-7 md:pb-5">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#252a36]">
            <img src="/super-admin-mark.svg" alt="Super Admin logo" className="h-7 w-7" />
          </div>
          <div>
            <p className="text-sm font-bold text-white">Super Admin</p>
            <p className="text-[10px] text-slate-400">SECURITY OPERATIONS</p>
          </div>
        </div>
        <p className="hidden px-3 pb-2 text-[10px] font-bold uppercase tracking-wider text-slate-500 md:block">
          SOC Operations
        </p>

        <div className="flex gap-1 overflow-x-auto pb-1 md:block md:space-y-1 md:overflow-visible md:pb-0">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentPage === item.id;

          return (
            <button
              key={item.id}
              onClick={() => onSelectPage(item.id)}
              className={`group flex w-max flex-shrink-0 items-center justify-between rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-150 md:w-full ${
                isActive
                  ? 'bg-[#30232b] text-white border-l-2 border-[#b01d36] shadow-sm'
                  : 'text-slate-300 hover:bg-white/5 hover:text-white'
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon
                  className={`h-4 w-4 transition-colors ${
                    isActive
                        ? 'text-[#df6577]'
                        : 'text-slate-500 group-hover:text-slate-200'
                      } ${item.pulse ? 'animate-pulse text-[#df6577]' : ''}`}
                />
                <span>{item.label}</span>
              </div>

              {item.badge !== undefined && (
                <span className="rounded-full bg-red-500/15 px-2 py-0.5 text-xs font-bold text-red-300 border border-red-500/30">
                  {item.badge}
                </span>
              )}

              {item.highlight && !isActive && (
                <span className="h-2 w-2 rounded-full bg-red-400 animate-ping" />
              )}
            </button>
          );
        })}
        </div>
      </div>

      {/* Footer info */}
      <div className="hidden rounded-lg border border-white/10 bg-white/5 p-3 text-xs text-slate-400 space-y-1 md:block">
        <div className="flex justify-between items-center text-[11px]">
          <span>Platform:</span>
          <span className="font-mono text-slate-200">Super Admin</span>
        </div>
        <div className="flex justify-between items-center text-[11px]">
          <span>Dataset:</span>
          <span className="font-mono text-slate-300">CERT r4.2</span>
        </div>
        <div className="flex justify-between items-center text-[11px]">
          <span>Detection Engine:</span>
          <span className="font-mono text-slate-200">XGBoost + SHAP</span>
        </div>
        <div className="flex justify-between items-center text-[11px]">
          <span>Decision Cutoff:</span>
          <span className="font-mono text-slate-300">0.1184 F1-Opt</span>
        </div>
      </div>
    </aside>
  );
};

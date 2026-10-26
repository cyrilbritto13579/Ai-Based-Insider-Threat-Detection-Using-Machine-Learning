import React from 'react';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  color?: 'cyan' | 'red' | 'orange' | 'emerald' | 'purple' | 'amber';
  trend?: string;
  trendPositive?: boolean;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  color = 'cyan',
  trend,
  trendPositive,
}) => {
  const colorMap = {
    cyan: {
      border: 'border-red-200',
      bg: 'bg-red-50',
      text: 'text-[#a3162a]',
      glow: 'group-hover:border-red-300',
    },
    red: {
      border: 'border-red-500/20',
      bg: 'bg-red-500/10',
      text: 'text-red-400',
      glow: 'group-hover:border-red-500/40',
    },
    orange: {
      border: 'border-orange-200',
      bg: 'bg-orange-50',
      text: 'text-orange-800',
      glow: 'group-hover:border-orange-300',
    },
    emerald: {
      border: 'border-emerald-500/20',
      bg: 'bg-emerald-500/10',
      text: 'text-emerald-400',
      glow: 'group-hover:border-emerald-500/40',
    },
    purple: {
      border: 'border-slate-200',
      bg: 'bg-slate-100',
      text: 'text-slate-700',
      glow: 'group-hover:border-slate-300',
    },
    amber: {
      border: 'border-amber-500/20',
      bg: 'bg-amber-500/10',
      text: 'text-amber-400',
      glow: 'group-hover:border-amber-500/40',
    },
  };

  const scheme = colorMap[color] || colorMap.cyan;

  return (
    <div
      className={`group relative overflow-hidden rounded-lg border bg-[#111827] p-5 shadow-[0_2px_10px_rgba(15,23,42,0.04)] transition-all duration-200 hover:-translate-y-0.5 hover:shadow-[0_10px_22px_rgba(15,23,42,0.09)] ${scheme.border} ${scheme.glow}`}
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-slate-400">
            {title}
          </p>
          <p className="mt-2 text-2xl font-bold font-mono text-slate-100">
            {typeof value === 'number' ? value.toLocaleString() : value}
          </p>
          {subtitle && (
            <p className="mt-1 text-xs text-slate-400">{subtitle}</p>
          )}
        </div>
        <div className={`rounded-lg p-3 ${scheme.bg} ${scheme.text}`}>
          <Icon className="h-6 w-6" />
        </div>
      </div>
      {trend && (
        <div className="mt-3 flex items-center gap-1.5 text-xs">
          <span
            className={
              trendPositive ? 'font-medium text-emerald-400' : 'font-medium text-red-400'
            }
          >
            {trend}
          </span>
          <span className="text-slate-400">vs historical baseline</span>
        </div>
      )}
    </div>
  );
};

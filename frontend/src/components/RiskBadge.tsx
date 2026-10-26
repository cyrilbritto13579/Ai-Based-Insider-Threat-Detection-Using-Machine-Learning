import React from 'react';
import { RiskTier } from '../types';

interface RiskBadgeProps {
  tier: RiskTier;
  score?: number;
  showScore?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({
  tier,
  score,
  showScore = false,
  size = 'md',
}) => {
  const getStyles = () => {
    switch (tier) {
      case 'CRITICAL':
        return 'bg-red-50 text-red-800 border-red-200';
      case 'HIGH':
        return 'bg-orange-50 text-orange-800 border-orange-200';
      case 'MEDIUM':
        return 'bg-amber-50 text-amber-800 border-amber-200';
      case 'LOW':
      default:
        return 'bg-emerald-50 text-emerald-800 border-emerald-200';
    }
  };

  const getDotStyles = () => {
    switch (tier) {
      case 'CRITICAL':
        return 'bg-red-400 animate-ping';
      case 'HIGH':
        return 'bg-orange-400';
      case 'MEDIUM':
        return 'bg-amber-400';
      case 'LOW':
      default:
        return 'bg-emerald-400';
    }
  };

  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-xs font-semibold',
    lg: 'px-3.5 py-1.5 text-sm font-bold',
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border ${getStyles()} ${sizeClasses[size]}`}
    >
      <span className="relative flex h-2 w-2">
        {tier === 'CRITICAL' && (
          <span
            className={`absolute inline-flex h-full w-full rounded-full opacity-75 ${getDotStyles()}`}
          />
        )}
        <span
          className={`relative inline-flex h-2 w-2 rounded-full ${
            tier === 'CRITICAL'
              ? 'bg-red-500'
              : tier === 'HIGH'
              ? 'bg-orange-500'
              : tier === 'MEDIUM'
              ? 'bg-amber-500'
              : 'bg-emerald-500'
          }`}
        />
      </span>
      <span>{tier}</span>
      {showScore && score !== undefined && (
        <span className="ml-1 opacity-80 font-mono">({score})</span>
      )}
    </span>
  );
};

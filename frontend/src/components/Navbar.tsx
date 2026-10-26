import React, { useState, useEffect } from 'react';
import {
  LayoutDashboard,
  Radio,
  Clock,
  AlertTriangle,
} from 'lucide-react';
import { SimulationStatus } from '../types';

interface NavbarProps {
  simulation: SimulationStatus | null;
  criticalCount: number;
  highCount: number;
  wsConnected: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  simulation,
  criticalCount,
  highCount,
  wsConnected,
}) => {
  const [currentTime, setCurrentTime] = useState<string>('');

  useEffect(() => {
    const update = () => {
      const now = new Date();
      setCurrentTime(
        now.toLocaleTimeString('en-US', {
          hour12: false,
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
        })
      );
    };
    update();
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, []);

  const isRunning = simulation?.status === 'RUNNING';
  const isPaused = simulation?.status === 'PAUSED';

  return (
    <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b border-slate-200 bg-white px-6 shadow-[0_1px_3px_rgba(15,23,42,0.04)]">
      <div className="flex items-center gap-2 text-slate-900">
        <LayoutDashboard className="h-4 w-4 text-[#a3162a]" />
        <h1 className="text-sm font-semibold">Dashboard</h1>
      </div>

      {/* Center: Simulation Disclaimer Banner */}
<div className="hidden lg:flex items-center gap-2 rounded-full border border-amber-200 bg-amber-50 px-3.5 py-1 text-xs text-amber-800">
          <AlertTriangle className="h-3.5 w-3.5 text-amber-700" />
        <span className="font-medium tracking-wide">
          SIMULATION DATA — NOT REAL COMPANY DATA
        </span>
      </div>

      {/* Right: Status Indicators */}
      <div className="flex items-center gap-4">
        {/* Simulation State Pill */}
        {(isRunning || isPaused) && (
          <div className={`flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs ${
            isPaused
              ? 'bg-amber-50 border-amber-200 text-amber-800'
              : 'bg-slate-100 border-slate-200 text-slate-700'
          }`}>
            <Radio className={`h-3 w-3 ${isRunning ? 'animate-spin' : ''}`} />
            <span className="font-semibold">{isPaused ? 'Paused:' : 'Simulating:'}</span>
            <span className="font-mono text-slate-700">
              {simulation?.current_scenario}
            </span>
          </div>
        )}

        {/* WebSocket Status */}
        <div className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs">
          <span
            className={`h-2 w-2 rounded-full ${
              wsConnected ? 'bg-emerald-500' : 'bg-red-500'
            }`}
          />
          <span className="text-slate-700 font-mono text-[11px]">
            {wsConnected ? 'LIVE' : 'OFFLINE'}
          </span>
        </div>

        {/* Threat Counters */}
        <div className="flex items-center gap-2">
          {criticalCount > 0 && (
            <div className="flex items-center gap-1 rounded bg-red-50 border border-red-200 px-2 py-0.5 text-xs font-bold text-red-800">
              <span>{criticalCount} CRITICAL</span>
            </div>
          )}
          {highCount > 0 && (
            <div className="flex items-center gap-1 rounded bg-orange-50 border border-orange-200 px-2 py-0.5 text-xs font-bold text-orange-800">
              <span>{highCount} HIGH</span>
            </div>
          )}
        </div>

        {/* Clock */}
        <div className="hidden sm:flex items-center gap-1.5 rounded-lg border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-mono text-slate-700">
          <Clock className="h-3.5 w-3.5 text-[#a3162a]" />
          <span>{currentTime || '00:00:00'} UTC</span>
        </div>
      </div>
    </header>
  );
};

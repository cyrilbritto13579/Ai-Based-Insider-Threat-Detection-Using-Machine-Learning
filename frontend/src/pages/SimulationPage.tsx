import React, { useState } from 'react';
import {
  FlaskConical,
  Play,
  Square,
  Pause,
  RotateCcw,
  AlertTriangle,
  Sliders,
  CheckCircle2,
  Flame,
  Zap,
} from 'lucide-react';
import { SimulationStatus, ActivityEvent, User } from '../types';
import { api } from '../api/client';

interface SimulationPageProps {
  simulation: SimulationStatus | null;
  users: User[];
  recentEvents: ActivityEvent[];
  onRefreshSimulation: () => void;
  onSelectUser: (userId: string) => void;
}

export const SimulationPage: React.FC<SimulationPageProps> = ({
  simulation,
  users,
  recentEvents,
  onRefreshSimulation,
  onSelectUser,
}) => {
  const [selectedScenario, setSelectedScenario] = useState<string>('MULTI_SIGNAL_ANOMALY');
  const [targetUser, setTargetUser] = useState<string>('ENG-014');
  const [speedInterval, setSpeedInterval] = useState<number>(1.2);
  const [operating, setOperating] = useState<boolean>(false);

  const handleStart = async () => {
    setOperating(true);
    try {
      await api.startSimulation(selectedScenario, targetUser, speedInterval);
      onRefreshSimulation();
    } catch (e) {
      console.error(e);
    } finally {
      setOperating(false);
    }
  };

  const handleStop = async () => {
    setOperating(true);
    try {
      await api.stopSimulation();
      onRefreshSimulation();
    } catch (e) {
      console.error(e);
    } finally {
      setOperating(false);
    }
  };

  const handlePause = async () => {
    setOperating(true);
    try {
      await api.pauseSimulation();
      onRefreshSimulation();
    } catch (e) {
      console.error(e);
    } finally {
      setOperating(false);
    }
  };

  const handleReset = async () => {
    setOperating(true);
    try {
      await api.resetSimulation();
      onRefreshSimulation();
    } catch (e) {
      console.error(e);
    } finally {
      setOperating(false);
    }
  };

  const isRunning = simulation?.status === 'RUNNING';
  const isPaused = simulation?.status === 'PAUSED';
  const isActive = isRunning || isPaused;

  // Speed presets
  const speedPresets = [
    { label: 'Slow', value: 2.5 },
    { label: 'Normal', value: 1.2 },
    { label: 'Fast', value: 0.5 },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white">Live Synthetic Event Simulator</h2>
        <p className="text-sm text-slate-400">
          Inject controlled behavioral threat scenarios to demonstrate real-time ML detection, dynamic scoring, and SHAP triage.
        </p>
      </div>

      {/* Simulation Disclaimer Box */}
      <div className="flex items-center justify-between rounded-xl border border-amber-200 bg-amber-50 p-4 text-xs text-amber-950 shadow-sm">
        <div className="flex items-center gap-3">
          <AlertTriangle className="h-5 w-5 flex-shrink-0 text-amber-800" />
          <div>
            <strong className="block text-sm font-semibold text-amber-950">
              SIMULATION DATA — NOT REAL COMPANY DATA
            </strong>
            <span>
              All user identities (TechNova), credentials, and workstation logs generated in this simulator are purely synthetic and used solely for defensive algorithmic demonstration.
            </span>
          </div>
        </div>
        <span className="rounded border border-amber-300 bg-amber-100 px-2.5 py-1 text-[11px] font-mono font-bold text-amber-950">
          SAFE TESTBED
        </span>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Left: Simulation Controls */}
        <div className="rounded-xl border border-[#1f293d] bg-[#111827] p-5 shadow-lg space-y-5">
          <div className="flex items-center justify-between pb-3 border-b border-[#1f293d]">
            <div className="flex items-center gap-2">
              <FlaskConical className="h-5 w-5 text-cyan-400" />
              <h3 className="text-sm font-bold text-white">Simulation Controls</h3>
            </div>
            <span
              className={`rounded-full px-2 py-0.5 text-xs font-mono font-bold border ${
                isRunning
                  ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
                  : isPaused
                  ? 'bg-amber-500/20 text-amber-400 border-amber-500/30'
                  : 'bg-slate-800 text-slate-400 border-slate-700'
              }`}
            >
              {isRunning ? 'RUNNING' : isPaused ? 'PAUSED' : 'STOPPED'}
            </span>
          </div>

          {/* Scenario Selector */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-slate-300">Choose Scenario:</label>
            <select
              value={selectedScenario}
              onChange={(e) => setSelectedScenario(e.target.value)}
              disabled={isActive}
              className="w-full rounded-lg border border-[#1f293d] bg-[#0b0f17] px-3 py-2 text-xs font-semibold text-cyan-300 focus:border-cyan-500 focus:outline-none disabled:opacity-60"
            >
              {simulation?.available_scenarios?.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name} ({s.expected_tier})
                </option>
              ))}
            </select>
          </div>

          {/* Target User Selector */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-slate-300">Target TechNova Employee:</label>
            <select
              value={targetUser}
              onChange={(e) => setTargetUser(e.target.value)}
              disabled={isActive}
              className="w-full rounded-lg border border-[#1f293d] bg-[#0b0f17] px-3 py-2 text-xs font-mono text-slate-200 focus:border-cyan-500 focus:outline-none disabled:opacity-60"
            >
              {users.map((u) => (
                <option key={u.user_id} value={u.user_id}>
                  {u.user_id} — {u.name} ({u.role})
                </option>
              ))}
            </select>
          </div>

          {/* Speed Presets */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs">
              <span className="text-slate-300">Event Speed:</span>
              <span className="font-mono text-cyan-400 font-bold">{speedInterval.toFixed(1)}s / event</span>
            </div>
            <div className="flex gap-2">
              {speedPresets.map((preset) => (
                <button
                  key={preset.label}
                  onClick={() => setSpeedInterval(preset.value)}
                  disabled={isActive}
                  className={`flex-1 rounded-lg py-1.5 text-[11px] font-semibold transition-colors border disabled:opacity-50 ${
                    Math.abs(speedInterval - preset.value) < 0.05
                      ? 'bg-cyan-500/20 border-cyan-500/30 text-cyan-300'
                      : 'bg-[#0b0f17] border-[#1f293d] text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {preset.label}
                </button>
              ))}
            </div>
            <input
              type="range"
              min="0.3"
              max="3.0"
              step="0.1"
              value={speedInterval}
              onChange={(e) => setSpeedInterval(parseFloat(e.target.value))}
              disabled={isActive}
              className="w-full accent-cyan-400 disabled:opacity-60"
            />
          </div>

          {/* Action Buttons */}
          <div className="space-y-2 pt-3">
            {!isActive ? (
              <button
                onClick={handleStart}
                disabled={operating}
                className="w-full rounded-lg bg-red-700 py-2.5 text-xs font-bold text-white hover:bg-red-800 transition-colors flex items-center justify-center gap-2 shadow-lg shadow-red-900/20"
              >
                <Play className="h-4 w-4 fill-white" />
                START SCENARIO
              </button>
            ) : (
              <div className="flex gap-2">
                <button
                  onClick={handlePause}
                  disabled={operating}
                  className={`flex-1 rounded-lg py-2.5 text-xs font-bold transition-colors flex items-center justify-center gap-2 ${
                    isPaused
                      ? 'bg-cyan-500 text-slate-950 hover:bg-cyan-400'
                      : 'bg-amber-500 text-slate-950 hover:bg-amber-400'
                  }`}
                >
                  {isPaused ? (
                    <>
                      <Play className="h-4 w-4 fill-slate-950" />
                      RESUME
                    </>
                  ) : (
                    <>
                      <Pause className="h-4 w-4 fill-slate-950" />
                      PAUSE
                    </>
                  )}
                </button>
                <button
                  onClick={handleStop}
                  disabled={operating}
                  className="flex-1 rounded-lg bg-red-500 py-2.5 text-xs font-bold text-white hover:bg-red-400 transition-colors flex items-center justify-center gap-2"
                >
                  <Square className="h-4 w-4 fill-white" />
                  STOP
                </button>
              </div>
            )}

            <button
              onClick={handleReset}
              disabled={operating || isActive}
              className="flex w-full items-center justify-center gap-2 rounded-lg border border-slate-300 bg-slate-100 py-2 text-xs font-medium text-slate-800 transition-colors hover:border-slate-400 hover:bg-slate-200 disabled:opacity-50"
            >
              <RotateCcw className="h-3.5 w-3.5" />
              Reset All Telemetry to Baseline
            </button>
          </div>

          {/* Telemetry Stats */}
          <div className="pt-4 border-t border-[#1f293d] grid grid-cols-2 gap-2 text-center text-xs font-mono">
            <div className="rounded-lg bg-[#0b0f17] p-2.5 border border-[#1f293d]">
              <span className="text-[10px] text-slate-400 font-sans uppercase">Emitted</span>
              <p className="text-lg font-bold text-cyan-400">{simulation?.events_emitted || 0}</p>
            </div>
            <div className="rounded-lg bg-[#0b0f17] p-2.5 border border-[#1f293d]">
              <span className="text-[10px] text-slate-400 font-sans uppercase">Alerts Triggered</span>
              <p className="text-lg font-bold text-red-400">{simulation?.alerts_triggered || 0}</p>
            </div>
          </div>
        </div>

        {/* Right: Live Event Feed */}
        <div className="lg:col-span-2 rounded-xl border border-[#1f293d] bg-[#111827] p-5 shadow-lg space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-[#1f293d]">
            <div>
              <h3 className="text-sm font-bold text-white">Live Event Pipeline Monitor</h3>
              <p className="text-xs text-slate-400">Events pass through SQLite DB, ML inference, and Dynamic Risk Engine in real-time</p>
            </div>
            {isRunning && (
              <span className="flex items-center gap-1.5 text-xs text-emerald-400 font-mono">
                <span className="h-2 w-2 rounded-full bg-emerald-400 animate-ping" />
                PIPELINE ACTIVE
              </span>
            )}
            {isPaused && (
              <span className="flex items-center gap-1.5 text-xs text-amber-400 font-mono">
                <span className="h-2 w-2 rounded-full bg-amber-400" />
                PAUSED
              </span>
            )}
          </div>

          <div className="divide-y divide-[#1f293d] max-h-[460px] overflow-y-auto font-mono text-xs pr-2 space-y-2">
            {recentEvents.length === 0 ? (
              <div className="py-24 text-center text-slate-500">
                <Zap className="h-8 w-8 text-slate-600 mx-auto mb-2" />
                <p className="font-sans text-sm text-slate-400">Simulator Idle</p>
                <p className="text-xs text-slate-500 mt-1">
                  Click <strong>START SCENARIO</strong> above to inject real-time security events.
                </p>
              </div>
            ) : (
              recentEvents.slice(0, 15).map((evt) => (
                <div
                  key={evt.event_id}
                  className="py-2.5 flex items-center justify-between hover:bg-[#1e293b]/40 rounded px-2 transition-colors"
                >
                  <div className="flex items-center gap-2.5">
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
                    <span className="rounded bg-slate-800 px-1.5 py-0.5 text-[10px] text-slate-300">
                      {evt.activity_type}
                    </span>
                    <span className="text-slate-300 text-[11px] truncate max-w-xs">
                      {evt.details?.filename || evt.details?.device_name || evt.details?.subject || evt.details?.action || ''}
                    </span>
                  </div>

                  {evt.is_after_hours && (
                    <span className="rounded bg-red-500/20 px-1.5 py-0.5 text-[10px] font-bold text-red-400 border border-red-500/30">
                      AFTER-HOURS
                    </span>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

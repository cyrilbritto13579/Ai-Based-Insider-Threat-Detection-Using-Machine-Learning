import React, { useState, useEffect } from 'react';
import {
  Settings as SettingsIcon,
  Shield,
  Sliders,
  Database,
  Lock,
  CheckCircle2,
  AlertCircle,
  Loader2,
  RotateCcw,
} from 'lucide-react';
import { api } from '../api/client';
import { RiskThresholds } from '../types';

export const SettingsPage: React.FC = () => {
  const [thresholds, setThresholds] = useState<RiskThresholds | null>(null);
  const [lowMax, setLowMax] = useState<number>(29);
  const [medMax, setMedMax] = useState<number>(59);
  const [highMax, setHighMax] = useState<number>(79);
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [saved, setSaved] = useState<boolean>(false);
  const [error, setError] = useState<string>('');

  // Load thresholds from backend on mount
  useEffect(() => {
    api.getThresholds()
      .then((data) => {
        setThresholds(data);
        setLowMax(data.low_max);
        setMedMax(data.medium_max);
        setHighMax(data.high_max);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to load thresholds:', err);
        setLoading(false);
      });
  }, []);

  const isValid = lowMax > 0 && medMax > lowMax && highMax > medMax && highMax <= 100;

  const handleSave = async () => {
    if (!isValid) {
      setError('Invalid thresholds: LOW < MEDIUM < HIGH ≤ 100');
      return;
    }
    setError('');
    setSaving(true);
    try {
      const res = await api.saveThresholds(lowMax, medMax, highMax);
      setThresholds(res.thresholds);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (e: any) {
      setError(e.message || 'Failed to save thresholds');
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    setLowMax(29);
    setMedMax(59);
    setHighMax(79);
    setError('');
  };

  // Live preview of tier boundaries
  const tierPreview = [
    { label: 'LOW', range: `0 – ${lowMax}`, color: 'text-emerald-400', bg: 'bg-emerald-500/15', width: `${lowMax}%` },
    { label: 'MEDIUM', range: `${lowMax + 1} – ${medMax}`, color: 'text-amber-400', bg: 'bg-amber-500/15', width: `${medMax - lowMax}%` },
    { label: 'HIGH', range: `${medMax + 1} – ${highMax}`, color: 'text-orange-400', bg: 'bg-orange-500/15', width: `${highMax - medMax}%` },
    { label: 'CRITICAL', range: `${highMax + 1} – 100`, color: 'text-red-400', bg: 'bg-red-500/15', width: `${100 - highMax}%` },
  ];

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white">System Settings & SOC Policies</h2>
        <p className="text-sm text-slate-400">
          Configure risk engine thresholds, simulation parameters, and review system provenance.
        </p>
      </div>

      {/* Success Message */}
      {saved && (
        <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-3 text-xs text-emerald-300 flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4 text-emerald-400" />
          <span>Risk tier thresholds persisted to database successfully.</span>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-3 text-xs text-red-300 flex items-center gap-2">
          <AlertCircle className="h-4 w-4 text-red-400" />
          <span>{error}</span>
        </div>
      )}

      {/* Risk Thresholds Config */}
      <div className="rounded-xl border border-[#1f293d] bg-[#111827] p-5 shadow-lg space-y-5">
        <div className="flex items-center justify-between pb-3 border-b border-[#1f293d]">
          <div className="flex items-center gap-2">
            <Sliders className="h-5 w-5 text-cyan-400" />
            <div>
              <h3 className="text-sm font-bold text-white">Dynamic Risk Tier Thresholds (0–100 Scale)</h3>
              <p className="text-xs text-slate-400">Configure cutoff boundaries for automated SOC incident escalation</p>
            </div>
          </div>
          {thresholds?.last_updated && (
            <span className="text-[10px] font-mono text-slate-400">
              Last updated: {new Date(thresholds.last_updated).toLocaleString()}
            </span>
          )}
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-5 w-5 animate-spin text-cyan-400" />
            <span className="ml-2 text-xs text-slate-400">Loading threshold configuration...</span>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
              <div className="space-y-1.5 rounded-lg bg-[#0b0f17] p-3 border border-emerald-500/20">
                <label className="text-emerald-400 font-bold uppercase">LOW Tier Max Score</label>
                <input
                  type="number"
                  min="10"
                  max={medMax - 1}
                  value={lowMax}
                  onChange={(e) => setLowMax(parseInt(e.target.value) || 0)}
                  className="w-full rounded bg-[#111827] border border-[#1f293d] p-2 text-slate-100 font-mono font-bold"
                />
                <span className="text-[10px] text-slate-500 block">Range: 0 – {lowMax}</span>
              </div>

              <div className="space-y-1.5 rounded-lg bg-[#0b0f17] p-3 border border-amber-500/20">
                <label className="text-amber-400 font-bold uppercase">MEDIUM Tier Max Score</label>
                <input
                  type="number"
                  min={lowMax + 1}
                  max={highMax - 1}
                  value={medMax}
                  onChange={(e) => setMedMax(parseInt(e.target.value) || 0)}
                  className="w-full rounded bg-[#111827] border border-[#1f293d] p-2 text-slate-100 font-mono font-bold"
                />
                <span className="text-[10px] text-slate-500 block">Range: {lowMax + 1} – {medMax}</span>
              </div>

              <div className="space-y-1.5 rounded-lg bg-[#0b0f17] p-3 border border-orange-500/20">
                <label className="text-orange-400 font-bold uppercase">HIGH Tier Max Score</label>
                <input
                  type="number"
                  min={medMax + 1}
                  max="99"
                  value={highMax}
                  onChange={(e) => setHighMax(parseInt(e.target.value) || 0)}
                  className="w-full rounded bg-[#111827] border border-[#1f293d] p-2 text-slate-100 font-mono font-bold"
                />
                <span className="text-[10px] text-slate-500 block">CRITICAL ≥ {highMax + 1}</span>
              </div>
            </div>

            {/* Live Tier Preview Bar */}
            <div className="space-y-2">
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Live Tier Preview</p>
              <div className="flex h-6 w-full rounded-md overflow-hidden border border-[#1f293d]">
                {tierPreview.map((tier) => (
                  <div
                    key={tier.label}
                    className={`${tier.bg} flex items-center justify-center text-[9px] font-bold ${tier.color} transition-all duration-300`}
                    style={{ width: tier.width }}
                  >
                    {tier.label}
                  </div>
                ))}
              </div>
              <div className="flex justify-between text-[10px] text-slate-500 font-mono px-1">
                {tierPreview.map((tier) => (
                  <span key={tier.label}>{tier.range}</span>
                ))}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3 pt-2">
              <button
                onClick={handleSave}
                disabled={saving || !isValid}
                className="rounded-lg bg-cyan-500 px-5 py-2 text-xs font-bold text-slate-950 hover:bg-cyan-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {saving ? (
                  <>
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    Saving...
                  </>
                ) : (
                  'Save Threshold Policy'
                )}
              </button>
              <button
                onClick={handleReset}
                className="rounded-lg border border-slate-700 bg-[#0b0f17] px-4 py-2 text-xs font-medium text-slate-300 hover:bg-slate-800 transition-colors flex items-center gap-2"
              >
                <RotateCcw className="h-3 w-3" />
                Reset to Defaults
              </button>
            </div>

            {!isValid && (
              <p className="text-[11px] text-red-400 mt-1">
                Validation: LOW max ({lowMax}) must be less than MEDIUM max ({medMax}), which must be less than HIGH max ({highMax}) ≤ 100.
              </p>
            )}
          </>
        )}
      </div>

      {/* System & Dataset Provenance Card */}
      <div className="rounded-xl border border-[#1f293d] bg-[#111827] p-5 shadow-lg space-y-4">
        <div className="flex items-center gap-2 pb-3 border-b border-[#1f293d]">
          <Database className="h-5 w-5 text-purple-400" />
          <h3 className="text-sm font-bold text-white">System & Dataset Provenance</h3>
        </div>

        <div className="space-y-2 text-xs font-mono">
          <div className="flex justify-between p-2 rounded bg-[#0b0f17] border border-[#1f293d]">
            <span className="text-slate-400 font-sans">Research Dataset:</span>
            <span className="text-slate-200 font-bold">CERT Release 4.2 (Carnegie Mellon SEI)</span>
          </div>
          <div className="flex justify-between p-2 rounded bg-[#0b0f17] border border-[#1f293d]">
            <span className="text-slate-400 font-sans">Ingested Sources:</span>
            <span className="text-slate-200 font-bold">logon.csv, device.csv, file.csv, email.csv, insiders.csv</span>
          </div>
          <div className="flex justify-between p-2 rounded bg-[#0b0f17] border border-[#1f293d]">
            <span className="text-slate-400 font-sans">Total Evaluated Events:</span>
            <span className="text-slate-200 font-bold">4,335,799 Raw Activity Logs</span>
          </div>
          <div className="flex justify-between p-2 rounded bg-[#0b0f17] border border-[#1f293d]">
            <span className="text-slate-400 font-sans">Storage Engine:</span>
            <span className="text-slate-200 font-bold">SQLite with SQLAlchemy ORM (PostgreSQL-ready)</span>
          </div>
          <div className="flex justify-between p-2 rounded bg-[#0b0f17] border border-[#1f293d]">
            <span className="text-slate-400 font-sans">Explainability Method:</span>
            <span className="text-slate-200 font-bold">SHAP TreeExplainer Exact Shapley Values</span>
          </div>
        </div>
      </div>

      {/* Ethical & Security Boundary Notice */}
      <div className="rounded-xl border border-cyan-500/20 bg-cyan-950/20 p-5 shadow-lg text-xs space-y-2 text-slate-300">
        <div className="flex items-center gap-2 text-cyan-400 font-bold uppercase tracking-wider">
          <Lock className="h-4 w-4" />
          <span>Defensive Security & Privacy Architecture</span>
        </div>
        <p className="leading-relaxed">
          This system complies with enterprise least-privilege principles. It never connects to live employee personal hardware and describes anomalous activities strictly as <em>suspicious behaviors requiring investigation</em> rather than automated determinations of employee culpability.
        </p>
      </div>
    </div>
  );
};

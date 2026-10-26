import React from 'react';

// ---------------------------------------------------------------------------
// 1. Donut Pie Chart for Risk Tier Distribution
// ---------------------------------------------------------------------------
interface TierDistributionProps {
  distribution: Record<string, number>;
}

export const TierDistributionChart: React.FC<TierDistributionProps> = ({ distribution }) => {
  const tiers = [
    { label: 'CRITICAL', count: distribution['CRITICAL'] || 0, color: '#ef4444' },
    { label: 'HIGH', count: distribution['HIGH'] || 0, color: '#f97316' },
    { label: 'MEDIUM', count: distribution['MEDIUM'] || 0, color: '#f59e0b' },
    { label: 'LOW', count: distribution['LOW'] || 0, color: '#10b981' },
  ];

  const total = tiers.reduce((acc, t) => acc + t.count, 0) || 1;

  // Compute SVG arc strokes
  let accumulatedAngle = 0;
  const radius = 40;
  const circumference = 2 * Math.PI * radius;

  return (
    <div className="flex items-center justify-between gap-4">
      {/* SVG Donut */}
      <div className="relative h-36 w-36 flex-shrink-0">
        <svg viewBox="0 0 100 100" className="h-full w-full -rotate-90 transform">
          <circle
            cx="50"
            cy="50"
            r={radius}
            fill="transparent"
            stroke="#1f293d"
            strokeWidth="14"
          />
          {tiers.map((tier, idx) => {
            const fraction = tier.count / total;
            const strokeLength = fraction * circumference;
            const strokeOffset = circumference - strokeLength;
            const rotation = (accumulatedAngle / total) * 360;
            accumulatedAngle += tier.count;

            if (tier.count === 0) return null;

            return (
              <circle
                key={idx}
                cx="50"
                cy="50"
                r={radius}
                fill="transparent"
                stroke={tier.color}
                strokeWidth="14"
                strokeDasharray={`${strokeLength} ${strokeOffset}`}
                strokeDashoffset="0"
                style={{
                  transformOrigin: '50% 50%',
                  transform: `rotate(${rotation}deg)`,
                  transition: 'stroke-dasharray 0.5s ease',
                }}
              />
            );
          })}
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
          <span className="text-xl font-bold font-mono text-slate-100">{total}</span>
          <span className="text-[10px] uppercase tracking-wider text-slate-400">Users</span>
        </div>
      </div>

      {/* Legend */}
      <div className="flex-1 space-y-2">
        {tiers.map((t) => {
          const pct = Math.round((t.count / total) * 100);
          return (
            <div key={t.label} className="flex items-center justify-between text-xs">
              <div className="flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: t.color }} />
                <span className="text-slate-300 font-medium">{t.label}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="font-mono font-bold text-slate-200">{t.count}</span>
                <span className="text-slate-400 font-mono text-[11px] w-8 text-right">({pct}%)</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};


// ---------------------------------------------------------------------------
// 2. Risk Score Histogram / Distribution Bar Chart
// ---------------------------------------------------------------------------
interface RiskHistogramProps {
  users: Array<{ current_risk_score: number; current_risk_tier: string }>;
}

export const RiskHistogramChart: React.FC<RiskHistogramProps> = ({ users }) => {
  const buckets = [
    { label: 'LOW', range: '0–29', color: '#10b981', min: 0, max: 29 },
    { label: 'MEDIUM', range: '30–59', color: '#f59e0b', min: 30, max: 59 },
    { label: 'HIGH', range: '60–79', color: '#f97316', min: 60, max: 79 },
    { label: 'CRITICAL', range: '80–100', color: '#ef4444', min: 80, max: 100 },
  ];
  const total = users.length || 1;
  const counts = buckets.map((bucket) => ({
    ...bucket,
    count: users.filter((user) => user.current_risk_score >= bucket.min && user.current_risk_score <= bucket.max).length,
    percent: (users.filter((user) => user.current_risk_score >= bucket.min && user.current_risk_score <= bucket.max).length / total) * 100,
  }));

  return (
    <div className="space-y-4 pt-4">
      <div className="flex h-5 overflow-hidden rounded-full border border-slate-700 bg-slate-900">
        {counts.map((bucket) => (
          <div
            key={bucket.label}
            className="transition-all duration-500"
            style={{ width: `${bucket.percent}%`, backgroundColor: bucket.color }}
            title={`${bucket.label}: ${bucket.count} users (${Math.round(bucket.percent)}%)`}
          />
        ))}
      </div>
      <div className="space-y-2">
        {counts.map((bucket) => (
          <div key={bucket.label} className="flex items-center justify-between gap-3 text-xs">
            <div className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: bucket.color }} />
              <span className="font-medium text-slate-300">{bucket.label} <span className="text-slate-500">{bucket.range}</span></span>
            </div>
            <div className="flex items-center gap-2 text-slate-400">
              <span className="font-mono font-bold text-slate-200">{bucket.count}</span>
              <span className="font-mono text-[10px]">({Math.round(bucket.percent)}%)</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};


// ---------------------------------------------------------------------------
// 3. SHAP Local Waterfall / Feature Impact Bar Chart
// ---------------------------------------------------------------------------
interface ShapWaterfallProps {
  factors: Array<{
    feature: string;
    value: number;
    impact_score: number;
    direction: string;
  }>;
}

export const ShapWaterfallChart: React.FC<ShapWaterfallProps> = ({ factors }) => {
  if (!factors || factors.length === 0) {
    return (
      <p className="text-xs text-slate-400 py-4 text-center">
        No anomalous feature deviations recorded for this profile.
      </p>
    );
  }

  const maxImpact = Math.max(...factors.map((f) => Math.abs(f.impact_score)), 0.1);

  return (
    <div className="space-y-3">
      {factors.map((factor, idx) => {
        const isUp = factor.impact_score > 0;
        const widthPct = Math.min(100, Math.max(5, (Math.abs(factor.impact_score) / maxImpact) * 100));
        const formattedName = factor.feature.replace(/_/g, ' ');

        return (
          <div key={idx} className="space-y-1">
            <div className="flex justify-between text-xs font-mono">
              <span className="text-slate-200 capitalize font-sans">{formattedName}</span>
              <div className="flex items-center gap-2">
                <span className="text-slate-400 text-[11px]">val: {factor.value}</span>
                <span
                  className={`font-bold ${isUp ? 'text-red-400' : 'text-emerald-400'}`}
                >
                  {isUp ? `+${factor.impact_score.toFixed(3)}` : factor.impact_score.toFixed(3)}
                </span>
              </div>
            </div>
            <div className="h-2 w-full rounded-full bg-[#1e293b] overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-300 ${
                  isUp ? 'bg-red-500' : 'bg-emerald-500'
                }`}
                style={{ width: `${widthPct}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
};


// ---------------------------------------------------------------------------
// 4. Confusion Matrix Visualizer
// ---------------------------------------------------------------------------
interface ConfusionMatrixProps {
  tp: number;
  fp: number;
  fn: number;
  tn: number;
}

export const ConfusionMatrixDisplay: React.FC<ConfusionMatrixProps> = ({ tp, fp, fn, tn }) => {
  return (
    <div className="grid grid-cols-2 gap-2 max-w-sm mx-auto font-mono text-center text-xs">
      {/* True Positive */}
      <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-3">
        <p className="text-[10px] uppercase text-emerald-400 font-sans font-bold">True Positive (Caught)</p>
        <p className="text-xl font-bold text-emerald-300 mt-1">{tp.toLocaleString()}</p>
      </div>
      {/* False Positive */}
      <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-3">
        <p className="text-[10px] uppercase text-amber-400 font-sans font-bold">False Positive (False Alarm)</p>
        <p className="text-xl font-bold text-amber-300 mt-1">{fp.toLocaleString()}</p>
      </div>
      {/* False Negative */}
      <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-3">
        <p className="text-[10px] uppercase text-red-400 font-sans font-bold">False Negative (Missed)</p>
        <p className="text-xl font-bold text-red-300 mt-1">{fn.toLocaleString()}</p>
      </div>
      {/* True Negative */}
      <div className="rounded-lg border border-slate-700 bg-slate-800/40 p-3">
        <p className="text-[10px] uppercase text-slate-400 font-sans font-bold">True Negative (Normal)</p>
        <p className="text-xl font-bold text-slate-200 mt-1">{tn.toLocaleString()}</p>
      </div>
    </div>
  );
};

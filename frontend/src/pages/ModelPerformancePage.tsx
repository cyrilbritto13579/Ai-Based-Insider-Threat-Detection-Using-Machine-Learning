import React, { useState, useEffect } from 'react';
import {
  Cpu,
  Trophy,
  CheckCircle2,
  Table,
  Sliders,
  Database,
  BarChart,
  ShieldCheck,
} from 'lucide-react';
import { ModelMetrics } from '../types';
import { ConfusionMatrixDisplay } from '../components/Charts';
import { api } from '../api/client';

export const ModelPerformancePage: React.FC = () => {
  const [metrics, setMetrics] = useState<ModelMetrics | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    api.getModelMetrics()
      .then((data) => {
        setMetrics(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white">Supervised Model Comparison & Evaluation</h2>
        <p className="text-sm text-slate-400">
          Empirical benchmark across Logistic Regression, Random Forest, and XGBoost on temporally split CERT Release 4.2 data.
        </p>
      </div>

      {loading ? (
        <div className="p-8 text-center text-xs text-slate-400">Loading benchmark metrics...</div>
      ) : (
        <>
          {/* Top Banner: Best Model Callout */}
          <div className="flex flex-col items-start justify-between gap-4 rounded-lg border border-red-100 bg-white p-5 shadow-[0_3px_14px_rgba(15,23,42,0.06)] md:flex-row md:items-center">
            <div className="flex items-center gap-3.5">
              <div className="flex h-12 w-12 items-center justify-center rounded-lg border border-red-100 bg-red-50 text-[#a3162a]">
                <Trophy className="h-6 w-6" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-lg font-bold text-slate-900">
                    Selected Model: <span className="text-[#a3162a]">{metrics?.best_model_name}</span>
                  </h3>
                  <span className="rounded border border-red-100 bg-red-50 px-2 py-0.5 text-xs font-mono font-bold text-[#821226]">
                    PR-AUC: {metrics?.test_metrics?.pr_auc?.toFixed(4) || '0.5236'}
                  </span>
                </div>
                <p className="mt-0.5 text-xs leading-relaxed text-slate-700">
                  F1-Optimized classification threshold at <code className="rounded bg-slate-100 px-1 font-mono font-semibold text-slate-900">{metrics?.optimal_threshold?.toFixed(4)}</code>. Chosen objectively for optimal recall and precision trade-off on rare threat events.
                </p>
              </div>
            </div>

            <div className="grid w-full grid-cols-3 divide-x divide-slate-200 rounded-md border border-slate-100 bg-slate-50 px-2 py-2 font-mono text-xs md:w-auto md:min-w-[300px]">
              <div className="px-2 md:px-3">
                <p className="text-[10px] font-semibold uppercase text-slate-600">Test ROC-AUC</p>
                <p className="text-base font-bold text-emerald-400">{metrics?.test_metrics?.roc_auc?.toFixed(4)}</p>
              </div>
              <div className="px-2 md:px-3">
                <p className="text-[10px] font-semibold uppercase text-slate-600">Test F1-Score</p>
                <p className="text-base font-bold text-[#a3162a]">{metrics?.test_metrics?.f1?.toFixed(4)}</p>
              </div>
              <div className="px-2 md:px-3">
                <p className="text-[10px] font-semibold uppercase text-slate-600">Test Recall</p>
                <p className="text-base font-bold text-slate-800">{metrics?.test_metrics?.recall?.toFixed(4)}</p>
              </div>
            </div>
          </div>

          {/* Model Comparison Table */}
          <div className="rounded-xl border border-[#1f293d] bg-[#111827] overflow-hidden shadow-lg">
            <div className="p-4 border-b border-[#1f293d] flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-white">Algorithm Benchmark Comparison</h3>
                <p className="text-xs text-slate-400">Evaluated on held-out temporal validation and test partitions</p>
              </div>
              <span className="text-xs font-mono text-slate-400 bg-[#0b0f17] px-2.5 py-1 rounded border border-[#1f293d]">
                Zero Data Leakage (Strict Temporal Split)
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="border-b border-[#1f293d] bg-[#0b0f17] text-[11px] font-semibold uppercase tracking-wider text-slate-400 font-mono">
                  <tr>
                    <th className="py-3 px-4">Model</th>
                    <th className="py-3 px-4">Optimal Thresh</th>
                    <th className="py-3 px-4 text-cyan-400 font-bold">Val PR-AUC</th>
                    <th className="py-3 px-4">Val F1</th>
                    <th className="py-3 px-4">Val Recall</th>
                    <th className="py-3 px-4">Val Precision</th>
                    <th className="py-3 px-4">Val ROC-AUC</th>
                    <th className="py-3 px-4 text-cyan-400 font-bold">Test PR-AUC</th>
                    <th className="py-3 px-4">Test F1</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1f293d] font-mono">
                  {metrics?.comparison_table?.map((row) => (
                    <tr
                      key={row.model_name}
                      className={row.is_best ? 'bg-cyan-950/20 font-semibold' : 'hover:bg-[#1e293b]/40'}
                    >
                      <td className="py-3 px-4 font-sans font-medium text-slate-200 flex items-center gap-2">
                        {row.model_name}
                        {row.is_best && (
                          <span className="rounded bg-cyan-500/20 text-cyan-300 text-[10px] px-1.5 py-0.2 border border-cyan-500/30">
                            BEST
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-slate-300">{row.optimal_threshold.toFixed(4)}</td>
                      <td className="py-3 px-4 text-cyan-400 font-bold">{row.val_pr_auc.toFixed(4)}</td>
                      <td className="py-3 px-4 text-slate-200">{row.val_f1.toFixed(4)}</td>
                      <td className="py-3 px-4 text-purple-300">{row.val_recall.toFixed(4)}</td>
                      <td className="py-3 px-4 text-slate-300">{row.val_precision.toFixed(4)}</td>
                      <td className="py-3 px-4 text-emerald-400">{row.val_roc_auc.toFixed(4)}</td>
                      <td className="py-3 px-4 text-cyan-400 font-bold">{row.test_pr_auc.toFixed(4)}</td>
                      <td className="py-3 px-4 text-slate-200">{row.test_f1.toFixed(4)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Bottom Grid: Confusion Matrix & Research Dataset Split Details */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            {/* Confusion Matrix Card */}
            <div className="rounded-xl border border-[#1f293d] bg-[#111827] p-5 shadow-lg space-y-4">
              <div className="pb-3 border-b border-[#1f293d]">
                <h3 className="text-sm font-bold text-white">XGBoost Test Set Confusion Matrix</h3>
                <p className="text-xs text-slate-400">Results on 65,031 held-out temporal test user-days</p>
              </div>

              <ConfusionMatrixDisplay
                tp={metrics?.test_metrics?.tp || 150}
                fp={metrics?.test_metrics?.fp || 142}
                fn={metrics?.test_metrics?.fn || 111}
                tn={metrics?.test_metrics?.tn || 64628}
              />
            </div>

            {/* Dataset Partitioning Summary */}
            <div className="rounded-xl border border-[#1f293d] bg-[#111827] p-5 shadow-lg space-y-3 text-xs">
              <div className="flex items-center gap-2 pb-2 border-b border-[#1f293d]">
                <Database className="h-4 w-4 text-cyan-400" />
                <h3 className="text-sm font-bold text-white">CERT Dataset Partitioning</h3>
              </div>

              <div className="space-y-2 font-mono text-[11px]">
                <div className="flex justify-between p-2 rounded bg-[#0b0f17] border border-[#1f293d]">
                  <span className="text-slate-400 font-sans">Raw Events Ingested:</span>
                  <span className="text-slate-200 font-bold">4,335,799</span>
                </div>
                <div className="flex justify-between p-2 rounded bg-[#0b0f17] border border-[#1f293d]">
                  <span className="text-slate-400 font-sans">User-Day Aggregate Samples:</span>
                  <span className="text-slate-200 font-bold">330,452</span>
                </div>
                <div className="flex justify-between p-2 rounded bg-[#0b0f17] border border-[#1f293d]">
                  <span className="text-slate-400 font-sans">Training Set (Jan–Oct 2010):</span>
                  <span className="text-slate-200 font-bold">209,182 samples (0.37% malicious)</span>
                </div>
                <div className="flex justify-between p-2 rounded bg-[#0b0f17] border border-[#1f293d]">
                  <span className="text-slate-400 font-sans">Validation Set (Nov 2010–Jan 2011):</span>
                  <span className="text-slate-200 font-bold">56,239 samples (0.58% malicious)</span>
                </div>
                <div className="flex justify-between p-2 rounded bg-[#0b0f17] border border-[#1f293d]">
                  <span className="text-slate-400 font-sans">Test Set (Feb–May 2011):</span>
                  <span className="text-slate-200 font-bold">65,031 samples (0.40% malicious)</span>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export type RiskTier = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type AlertStatus = 'NEW' | 'ACKNOWLEDGED' | 'INVESTIGATING' | 'RESOLVED' | 'FALSE_POSITIVE';
export type AccountStatus = 'ACTIVE' | 'BLOCKED';

export interface User {
  id: number;
  user_id: string;
  name: string;
  department: string;
  role: string;
  email: string;
  assigned_pc: string;
  is_synthetic: boolean;
  current_risk_score: number;
  current_risk_tier: RiskTier;
  ml_probability: number;
  last_updated?: string;
  manager: string;
  location: string;
  employment_type: string;
  join_date: string;
  normal_hours: string;
  account_status: AccountStatus;
}

export interface UserDetail extends User {
  baseline_stats: Record<string, number>;
  explanation: string;
  top_factors: Array<{
    feature: string;
    value: number;
    impact_score: number;
    direction: string;
  }>;
  recent_events_count: number;
  total_alerts_count: number;
  login_count: number;
  device_count: number;
  file_count: number;
  email_count: number;
  last_activity: string | null;
}

export interface ActivityEvent {
  id: number;
  event_id: string;
  timestamp: string;
  user_id: string;
  user_name?: string;
  department?: string;
  pc: string;
  activity_type: string;
  details: Record<string, any>;
  is_after_hours: boolean;
  is_weekend: boolean;
}

export interface Alert {
  id: number;
  alert_id: string;
  timestamp: string;
  user_id: string;
  user_name?: string;
  department?: string;
  risk_score: number;
  risk_tier: RiskTier;
  behavior: string;
  primary_reason: string;
  status: AlertStatus;
  notes: string;
  resolved_by: string;
  details: Record<string, any>;
}

export interface RiskOverview {
  total_monitored_users: number;
  total_events_analyzed: number;
  suspicious_users_count: number;
  critical_alerts_count: number;
  high_risk_count: number;
  medium_risk_count: number;
  low_risk_count: number;
  open_alerts_count: number;
  tier_distribution: Record<string, number>;
  system_health: Record<string, string>;
}

export interface RiskHistoryPoint {
  timestamp: string;
  risk_score: number;
  risk_tier: RiskTier;
  ml_probability: number;
}

export interface ScenarioMeta {
  id: string;
  name: string;
  description: string;
  expected_tier: string;
}

export interface SimulationStatus {
  status: 'RUNNING' | 'STOPPED' | 'PAUSED' | 'IDLE';
  current_scenario: string | null;
  target_user_id: string | null;
  events_emitted: number;
  alerts_triggered: number;
  interval_seconds: number;
  available_scenarios: ScenarioMeta[];
}

export interface ModelComparisonRow {
  model_name: string;
  model_type: string;
  is_best: boolean;
  optimal_threshold: number;
  val_pr_auc: number;
  val_f1: number;
  val_recall: number;
  val_precision: number;
  val_roc_auc: number;
  test_pr_auc: number;
  test_f1: number;
  test_recall: number;
  test_precision: number;
  test_roc_auc: number;
  tp: number;
  fp: number;
  fn: number;
  tn: number;
}

export interface ModelMetrics {
  best_model_name: string;
  best_model_type: string;
  optimal_threshold: number;
  validation_metrics: Record<string, any>;
  test_metrics: Record<string, any>;
  comparison_table: ModelComparisonRow[];
  dataset_summary: Record<string, any>;
}

export interface ShapExplanation {
  user_id: string;
  risk_score: number;
  risk_tier: RiskTier;
  ml_probability: number;
  text_explanation: string;
  top_factors: Array<{
    feature: string;
    value: number;
    impact_score: number;
    direction: string;
  }>;
  base_value: number;
}

export interface RiskThresholds {
  low_max: number;
  medium_max: number;
  high_max: number;
  critical_min: number;
  last_updated: string | null;
}

// Feature label mapping for human-readable SHAP display
export const FEATURE_LABELS: Record<string, string> = {
  logon_count: 'Login Frequency',
  logoff_count: 'Logoff Frequency',
  device_connect_count: 'USB Device Connections',
  device_disconnect_count: 'USB Device Disconnections',
  file_access_count: 'File Access Volume',
  file_copy_count: 'File Copy Operations',
  email_count: 'Email Activity Volume',
  email_sent_count: 'Emails Sent',
  email_with_attachment: 'Emails with Attachments',
  email_external_to: 'External Email Recipients',
  is_after_hours: 'After-Hours Activity',
  is_weekend: 'Weekend Activity',
  multi_pc_logon: 'Multi-Workstation Login',
  afterhours_logon_and_device: 'After-Hours Login + Device',
  afterhours_device_and_file: 'After-Hours Device + File',
  afterhours_triple_signal: 'After-Hours Triple Signal',
  deviation_logon_count: 'Login Count Deviation',
  deviation_device_total_events: 'Device Activity Deviation',
  deviation_file_access_count: 'File Access Deviation',
  deviation_email_count: 'Email Volume Deviation',
  deviation_first_logon_hour: 'First Login Hour Deviation',
  overall_behavior_deviation: 'Overall Behavioral Deviation',
  total_events: 'Total Daily Activity',
  first_logon_hour: 'First Login Hour',
  unique_pcs: 'Unique Workstations Used',
};

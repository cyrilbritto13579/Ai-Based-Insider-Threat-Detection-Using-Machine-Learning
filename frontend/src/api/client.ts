import {
  User,
  UserDetail,
  ActivityEvent,
  Alert,
  RiskOverview,
  RiskHistoryPoint,
  SimulationStatus,
  ModelMetrics,
  ShapExplanation,
  RiskThresholds,
} from '../types';

const API_BASE = '/api/v1';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, options);
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`API Error ${res.status}: ${text}`);
  }
  return res.json();
}

export const api = {
  getHealth: () => fetchJson<any>(`${API_BASE}/health`),
  
  getUsers: () => fetchJson<User[]>(`${API_BASE}/users`),
  
  getUserDetail: (userId: string) => fetchJson<UserDetail>(`${API_BASE}/users/${userId}`),
  
  getUserTimeline: (userId: string) => fetchJson<RiskHistoryPoint[]>(`${API_BASE}/users/${userId}/timeline`),
  
  getUserEvents: (userId: string, limit = 50) => 
    fetchJson<ActivityEvent[]>(`${API_BASE}/users/${userId}/events?limit=${limit}`),

  getUserReportUrl: (userId: string) => `${API_BASE}/users/${encodeURIComponent(userId)}/report`,
  
  explainUser: (userId: string) => fetchJson<ShapExplanation>(`${API_BASE}/users/${userId}/explain`),
  
  getAlerts: (params?: { tier?: string; status?: string; user_id?: string }) => {
    const query = new URLSearchParams();
    if (params?.tier) query.append('tier', params.tier);
    if (params?.status) query.append('status', params.status);
    if (params?.user_id) query.append('user_id', params.user_id);
    const qs = query.toString();
    return fetchJson<Alert[]>(`${API_BASE}/alerts${qs ? `?${qs}` : ''}`);
  },
  
  acknowledgeAlert: (alertId: string, status = 'ACKNOWLEDGED', notes?: string) => 
    fetchJson<any>(`${API_BASE}/alerts/${alertId}/acknowledge`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status, notes }),
    }),
  
  getRiskOverview: () => fetchJson<RiskOverview>(`${API_BASE}/risk/overview`),
  
  getFeatureImportance: () => fetchJson<{ importance: Array<{ feature: string; mean_abs_shap: number }> }>(
    `${API_BASE}/analytics/feature-importance`
  ),
  
  getActivityDistribution: () => fetchJson<Record<string, number>>(`${API_BASE}/analytics/activity-distribution`),
  
  getModelMetrics: () => fetchJson<ModelMetrics>(`${API_BASE}/model/metrics`),
  
  getSimulationStatus: () => fetchJson<SimulationStatus>(`${API_BASE}/simulation/status`),
  
  startSimulation: (scenario: string, targetUserId?: string, speedInterval = 1.0) => 
    fetchJson<SimulationStatus>(`${API_BASE}/simulation/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        scenario,
        target_user_id: targetUserId,
        speed_interval: speedInterval,
      }),
    }),
  
  stopSimulation: () => fetchJson<SimulationStatus>(`${API_BASE}/simulation/stop`, { method: 'POST' }),

  pauseSimulation: () => fetchJson<SimulationStatus>(`${API_BASE}/simulation/pause`, { method: 'POST' }),
  
  resetSimulation: () => fetchJson<SimulationStatus>(`${API_BASE}/simulation/reset`, { method: 'POST' }),

  // Settings — Risk Thresholds
  getThresholds: () => fetchJson<RiskThresholds>(`${API_BASE}/settings/thresholds`),

  saveThresholds: (low_max: number, medium_max: number, high_max: number) =>
    fetchJson<{ status: string; thresholds: RiskThresholds }>(`${API_BASE}/settings/thresholds`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ low_max, medium_max, high_max }),
    }),

  // Admin — Block/Unblock
  blockUser: (userId: string, reason?: string) =>
    fetchJson<any>(`${API_BASE}/users/${userId}/block`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reason: reason || 'Administrative action' }),
    }),

  unblockUser: (userId: string, reason?: string) =>
    fetchJson<any>(`${API_BASE}/users/${userId}/unblock`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reason: reason || 'Review completed' }),
    }),

  getAdminActions: (userId: string) =>
    fetchJson<any[]>(`${API_BASE}/users/${userId}/admin-actions`),

  // Manual Event Injection
  injectEvent: (event: { user_id: string; activity_type: string; details?: any }) =>
    fetchJson<any>(`${API_BASE}/simulation/inject`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(event),
    }),
};

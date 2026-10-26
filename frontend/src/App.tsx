import React, { useState, useEffect, useRef } from 'react';
import { Navbar } from './components/Navbar';
import { Sidebar, PageId } from './components/Sidebar';
import { OverviewPage } from './pages/OverviewPage';
import { AlertsPage } from './pages/AlertsPage';
import { UserInvestigationPage } from './pages/UserInvestigationPage';
import { LiveMonitorPage } from './pages/LiveMonitorPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { ModelPerformancePage } from './pages/ModelPerformancePage';
import { SimulationPage } from './pages/SimulationPage';
import { SettingsPage } from './pages/SettingsPage';
import { User, Alert, RiskOverview, ActivityEvent, SimulationStatus } from './types';
import { api } from './api/client';
import { ShieldAlert, X } from 'lucide-react';

export const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<PageId>('overview');
  const [selectedUserId, setSelectedUserId] = useState<string>('ENG-014');
  
  const [users, setUsers] = useState<User[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [overview, setOverview] = useState<RiskOverview | null>(null);
  const [liveEvents, setLiveEvents] = useState<ActivityEvent[]>([]);
  const [simulation, setSimulation] = useState<SimulationStatus | null>(null);
  
  const [wsConnected, setWsConnected] = useState<boolean>(false);
  const [toastAlert, setToastAlert] = useState<Alert | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // Initial Data Load
  const refreshData = async () => {
    try {
      const [usersData, alertsData, overviewData, simData] = await Promise.all([
        api.getUsers().catch(() => []),
        api.getAlerts().catch(() => []),
        api.getRiskOverview().catch(() => null),
        api.getSimulationStatus().catch(() => null),
      ]);
      setUsers(usersData);
      setAlerts(alertsData);
      setOverview(overviewData);
      setSimulation(simData);
      if (usersData.length > 0 && !selectedUserId) {
        setSelectedUserId(usersData[0].user_id);
      }
    } catch (e) {
      console.error('Error refreshing initial data:', e);
    }
  };

  useEffect(() => {
    refreshData();
    const interval = setInterval(refreshData, 10000);
    return () => clearInterval(interval);
  }, []);

  // WebSocket Connection
  useEffect(() => {
    let reconnectTimeout: any;

    const connectWs = () => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/live`;
      
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setWsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'INITIAL_STATE' && data.simulation) {
            setSimulation(data.simulation);
          } else if (data.type === 'SIMULATION_STATUS' && data.status) {
            setSimulation(data.status);
          } else if (data.type === 'SIMULATION_RESET') {
            setLiveEvents([]);
            refreshData();
          } else if (data.type === 'PIPELINE_UPDATE') {
            // Append live event
            if (data.event) {
              setLiveEvents((prev) => [data.event, ...prev.slice(0, 199)]);
            }

            // Update user risk in state
            if (data.risk) {
              setUsers((prev) =>
                prev.map((u) =>
                  u.user_id === data.risk.user_id
                    ? {
                        ...u,
                        current_risk_score: data.risk.risk_score,
                        current_risk_tier: data.risk.risk_tier,
                        ml_probability: data.risk.ml_probability,
                      }
                    : u
                )
              );
            }

            // If alert generated, add to alerts list and trigger toast
            if (data.alert) {
              setAlerts((prev) => [data.alert, ...prev]);
              setToastAlert(data.alert);
              setTimeout(() => setToastAlert(null), 6000);
            }

            // Refresh overview numbers
            api.getRiskOverview().then(setOverview).catch(() => {});
          }
        } catch (e) {
          console.error('WS parse error:', e);
        }
      };

      ws.onclose = () => {
        setWsConnected(false);
        reconnectTimeout = setTimeout(connectWs, 3000);
      };

      ws.onerror = () => {
        ws.close();
      };
    };

    connectWs();

    return () => {
      clearTimeout(reconnectTimeout);
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const handleSelectUser = (userId: string) => {
    setSelectedUserId(userId);
    setCurrentPage('investigation');
  };

  const criticalCount = alerts.filter((a) => a.risk_tier === 'CRITICAL').length;
  const highCount = alerts.filter((a) => a.risk_tier === 'HIGH').length;
  const unackAlerts = alerts.filter((a) => a.status === 'NEW').length;

  return (
    <div className="min-h-screen bg-[#f7f8fa] text-slate-900 flex font-sans">
      {/* Main Layout (Sidebar + Workspace) */}
      <div className="relative flex min-h-screen w-full flex-col md:flex-row">
        <Sidebar
          currentPage={currentPage}
          onSelectPage={setCurrentPage}
          unacknowledgedAlerts={unackAlerts}
          isSimulating={simulation?.status === 'RUNNING'}
        />

        <div className="flex min-w-0 flex-1 flex-col">
          <Navbar
            simulation={simulation}
            criticalCount={criticalCount}
            highCount={highCount}
            wsConnected={wsConnected}
          />

        <main className="workspace-surface flex-1 overflow-y-auto bg-[#f7f8fa] p-5 md:p-7">
          {currentPage === 'overview' && (
            <OverviewPage
              overview={overview}
              users={users}
              alerts={alerts}
              onSelectUser={handleSelectUser}
              onNavigateToAlerts={() => setCurrentPage('alerts')}
            />
          )}

          {currentPage === 'alerts' && (
            <AlertsPage
              alerts={alerts}
              onSelectUser={handleSelectUser}
              onRefreshAlerts={refreshData}
            />
          )}

          {currentPage === 'investigation' && (
            <UserInvestigationPage
              users={users}
              selectedUserId={selectedUserId}
              onSelectUser={setSelectedUserId}
            />
          )}

          {currentPage === 'live-monitor' && (
            <LiveMonitorPage
              events={liveEvents}
              wsConnected={wsConnected}
              onSelectUser={handleSelectUser}
            />
          )}

          {currentPage === 'analytics' && <AnalyticsPage />}

          {currentPage === 'model-performance' && <ModelPerformancePage />}

          {currentPage === 'simulation' && (
            <SimulationPage
              simulation={simulation}
              users={users}
              recentEvents={liveEvents}
              onRefreshSimulation={refreshData}
              onSelectUser={handleSelectUser}
            />
          )}

          {currentPage === 'settings' && <SettingsPage />}
        </main>
        </div>
      </div>

      {/* Real-time Alert Toast Notification */}
      {toastAlert && (
        <div className="fixed bottom-6 right-6 z-50 max-w-md rounded-xl border border-red-500/40 bg-[#111827] p-4 shadow-2xl shadow-red-950/50 flex items-start gap-3">
          <div className="rounded-lg bg-red-500/20 p-2 text-red-400">
            <ShieldAlert className="h-5 w-5" />
          </div>
          <div className="flex-1 text-xs">
            <div className="flex items-center justify-between">
              <span className="font-bold text-red-400 uppercase tracking-wider">
                {toastAlert.risk_tier} Security Incident
              </span>
              <button
                onClick={() => setToastAlert(null)}
                className="text-slate-400 hover:text-white"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
            <p className="font-bold text-slate-100 mt-1">{toastAlert.behavior}</p>
            <p className="text-slate-400 font-mono text-[11px] mt-0.5">
              User: {toastAlert.user_id} • Score: {toastAlert.risk_score}/100
            </p>
            <button
              onClick={() => {
                handleSelectUser(toastAlert.user_id);
                setToastAlert(null);
              }}
              className="mt-2 text-[11px] font-bold text-cyan-400 hover:underline block"
            >
              Open Immediate Investigation →
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
export default App;

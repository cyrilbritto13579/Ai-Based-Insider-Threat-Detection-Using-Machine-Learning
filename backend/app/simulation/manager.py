"""
Simulation Manager
==================
Controls asynchronous execution of synthetic enterprise event streams.
Events actually flow through SQLite, ML models, and the Dynamic Risk Engine.
"""

import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
from app.db.session import SessionLocal
from app.db.models import User, ActivityEvent, RiskScore, RiskHistory, Alert, SimulationSession
from app.simulation.scenarios import generate_scenario_events, SCENARIO_METADATA
from app.simulation.enterprise import seed_synthetic_enterprise
from app.services.pipeline_service import pipeline_service


class SimulationManager:
    def __init__(self):
        self.status = "STOPPED"
        self.current_scenario: Optional[str] = None
        self.target_user_id: Optional[str] = None
        self.speed_interval: float = 1.2
        self.events_emitted: int = 0
        self.alerts_triggered: int = 0
        self._task: Optional[asyncio.Task] = None
        self._pause_event: asyncio.Event = asyncio.Event()
        self._pause_event.set()  # Not paused by default

    def get_status(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "current_scenario": self.current_scenario,
            "target_user_id": self.target_user_id,
            "events_emitted": self.events_emitted,
            "alerts_triggered": self.alerts_triggered,
            "interval_seconds": self.speed_interval,
            "available_scenarios": SCENARIO_METADATA,
        }

    async def start(
        self,
        scenario: str,
        target_user_id: Optional[str] = None,
        speed_interval: float = 1.2,
        max_events: Optional[int] = 50,
    ) -> Dict[str, Any]:
        """Start a simulation scenario in a background async task."""
        if self.status == "RUNNING":
            await self.stop()

        self.status = "RUNNING"
        self.current_scenario = scenario
        self.target_user_id = target_user_id or ("ENG-014" if "MULTI" in scenario or "DEVICE" in scenario else "ENG-001")
        self.speed_interval = max(0.2, speed_interval)
        self.events_emitted = 0
        self.alerts_triggered = 0
        self._pause_event.set()  # Ensure not paused

        self._task = asyncio.create_task(self._run_simulation_loop(max_events))
        return self.get_status()

    async def stop(self) -> Dict[str, Any]:
        """Stop current running simulation."""
        self.status = "STOPPED"
        self._pause_event.set()  # Unblock if paused
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        return self.get_status()

    async def pause(self) -> Dict[str, Any]:
        """Pause or resume simulation."""
        if self.status == "RUNNING":
            self.status = "PAUSED"
            self._pause_event.clear()
        elif self.status == "PAUSED":
            self.status = "RUNNING"
            self._pause_event.set()
        return self.get_status()

    async def reset(self) -> Dict[str, Any]:
        """Reset simulation status, wipe demo events, and re-seed baseline TechNova users."""
        await self.stop()
        db = SessionLocal()
        try:
            # Delete demo activity events, alerts, and risk histories
            db.query(Alert).delete()
            db.query(RiskHistory).delete()
            db.query(ActivityEvent).delete()
            db.query(RiskScore).delete()
            db.query(User).delete()
            db.commit()

            # Re-seed TechNova baseline users
            seed_synthetic_enterprise(db)
        finally:
            db.close()

        self.events_emitted = 0
        self.alerts_triggered = 0
        self.current_scenario = None
        self.target_user_id = None

        # Broadcast reset notification
        await pipeline_service.broadcast_ws({"type": "SIMULATION_RESET"})
        return self.get_status()

    async def _run_simulation_loop(self, max_events: Optional[int]):
        """Executes generated events sequentially with real detection processing."""
        db = SessionLocal()
        try:
            # Look up target user PC
            user = db.query(User).filter(User.user_id == self.target_user_id).first()
            pc = user.assigned_pc if user else "PC-ENG-01"

            events = generate_scenario_events(self.current_scenario, self.target_user_id, pc)

            for event_data in events:
                if self.status == "STOPPED":
                    break

                # Wait if paused
                await self._pause_event.wait()

                if self.status == "STOPPED":
                    break

                # Process through actual pipeline
                result = await pipeline_service.process_event(db, event_data)
                self.events_emitted += 1
                if result.get("alert"):
                    self.alerts_triggered += 1

                await asyncio.sleep(self.speed_interval)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Simulation loop error: {e}")
        finally:
            if self.status != "PAUSED":
                self.status = "STOPPED"
            db.close()
            await pipeline_service.broadcast_ws({
                "type": "SIMULATION_STATUS",
                "status": self.get_status()
            })


simulation_manager = SimulationManager()

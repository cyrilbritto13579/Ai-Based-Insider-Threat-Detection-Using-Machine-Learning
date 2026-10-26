"""
Simulation Scenario Generator
==============================
Generates structured synthetic activity event streams for 6 scenarios:
  1. NORMAL_EMPLOYEE: Standard daytime productivity
  2. AFTER_HOURS: Late night logins and emails
  3. UNUSUAL_DEVICE_ACTIVITY: Sudden USB drive connections
  4. UNUSUAL_FILE_ACTIVITY: Bulk document reading and downloading
  5. SUSPICIOUS_DATA_COLLECTION: Archive preparation and external emails
  6. MULTI_SIGNAL_ANOMALY: After-hours login + USB connect + sensitive files + exfiltration
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any


SCENARIO_METADATA = [
    {
        "id": "NORMAL_EMPLOYEE",
        "name": "Normal Employee Activity",
        "description": "Standard business hour logins, document reading, and internal team emails.",
        "expected_tier": "LOW",
    },
    {
        "id": "AFTER_HOURS",
        "name": "After-Hours Work Activity",
        "description": "Unscheduled login at 23:30, minor documentation checks, after-hours email.",
        "expected_tier": "MEDIUM",
    },
    {
        "id": "UNUSUAL_DEVICE_ACTIVITY",
        "name": "Unusual Removable Media Connection",
        "description": "User connects unauthorized SanDisk USB drive during business hours.",
        "expected_tier": "HIGH",
    },
    {
        "id": "UNUSUAL_FILE_ACTIVITY",
        "name": "Excessive File Reading & Downloads",
        "description": "Rapid succession of 15+ sensitive engineering/financial spec documents accessed.",
        "expected_tier": "HIGH",
    },
    {
        "id": "SUSPICIOUS_DATA_COLLECTION",
        "name": "Data Collection & External Transfer",
        "description": "Bulk file reads combined with encrypted archive creation and external email with attachment.",
        "expected_tier": "HIGH",
    },
    {
        "id": "MULTI_SIGNAL_ANOMALY",
        "name": "Multi-Signal Critical Exfiltration",
        "description": "02:15 AM login + USB drive connected + 20 sensitive blueprints copied + external email sent.",
        "expected_tier": "CRITICAL",
    },
]


def generate_scenario_events(scenario_id: str, user_id: str, pc: str) -> List[Dict[str, Any]]:
    """
    Returns an ordered list of event dictionaries to emit sequentially during simulation.
    """
    now = datetime.utcnow()
    events = []

    def make_event(act_type, offset_sec, is_ah, details, pc_name=pc):
        ts = now + timedelta(seconds=offset_sec)
        # If after-hours scenario, force hour to 23 (11 PM) or 2 (2 AM)
        if is_ah:
            ts = ts.replace(hour=23, minute=15)
        else:
            ts = ts.replace(hour=10, minute=30)

        return {
            "event_id": f"EVT-{uuid.uuid4().hex[:8].upper()}",
            "user_id": user_id,
            "pc": pc_name,
            "activity_type": act_type,
            "timestamp": ts,
            "is_after_hours": is_ah,
            "is_weekend": False,
            "details": details,
        }

    if scenario_id == "NORMAL_EMPLOYEE":
        events.append(make_event("LOGIN", 0, False, {"action": "Workstation unlock"}))
        events.append(make_event("FILE_ACCESS", 2, False, {"filename": "Q3_Sprint_Backlog.docx", "operation": "READ"}))
        events.append(make_event("EMAIL_ACTIVITY", 4, False, {"to": "team@technova.io", "subject": "Standup notes", "recipients_count": 4, "is_external": False}))
        events.append(make_event("FILE_ACCESS", 6, False, {"filename": "Architecture_V2_Draft.pdf", "operation": "READ"}))
        events.append(make_event("EMAIL_ACTIVITY", 8, False, {"to": "manager@technova.io", "subject": "PR review request", "recipients_count": 1, "is_external": False}))
        events.append(make_event("LOGOUT", 10, False, {"action": "Workstation lock"}))

    elif scenario_id == "AFTER_HOURS":
        events.append(make_event("LOGIN", 0, True, {"action": "Remote VPN Logon", "auth_type": "MFA"}))
        events.append(make_event("FILE_ACCESS", 2, True, {"filename": "System_Architecture.pdf", "operation": "READ"}))
        events.append(make_event("EMAIL_ACTIVITY", 4, True, {"to": "colleague@technova.io", "subject": "Late commit sync", "recipients_count": 1, "is_external": False}))
        events.append(make_event("FILE_ACCESS", 6, True, {"filename": "Deployment_Notes.docx", "operation": "READ"}))
        events.append(make_event("LOGOUT", 8, True, {"action": "Remote VPN Logoff"}))

    elif scenario_id == "UNUSUAL_DEVICE_ACTIVITY":
        events.append(make_event("LOGIN", 0, False, {"action": "Workstation Logon"}))
        events.append(make_event("DEVICE_CONNECT", 2, False, {"device_name": "SanDisk Extreme 64GB", "device_type": "USB_MASS_STORAGE", "serial": "SD-984210"}))
        events.append(make_event("FILE_ACCESS", 4, False, {"filename": "Customer_Profiles_2026.csv", "operation": "READ"}))
        events.append(make_event("DEVICE_DISCONNECT", 6, False, {"device_name": "SanDisk Extreme 64GB", "device_type": "USB_MASS_STORAGE"}))
        events.append(make_event("DEVICE_CONNECT", 8, False, {"device_name": "Kingston DataTraveler 128GB", "device_type": "USB_MASS_STORAGE", "serial": "DT-110294"}))
        events.append(make_event("DEVICE_DISCONNECT", 10, False, {"device_name": "Kingston DataTraveler 128GB", "device_type": "USB_MASS_STORAGE"}))

    elif scenario_id == "UNUSUAL_FILE_ACTIVITY":
        events.append(make_event("LOGIN", 0, False, {"action": "Workstation Logon"}))
        for i in range(12):
            fname = f"Proprietary_Core_Firmware_Module_{i+1:02d}.c"
            events.append(make_event("FILE_ACCESS", 1 + i, False, {"filename": fname, "operation": "READ_AND_EXPORT", "file_size_kb": 450}))
        events.append(make_event("FILE_COPY", 14, False, {"filename": "Full_Source_Archive.zip", "operation": "COPY_LOCAL"}))

    elif scenario_id == "SUSPICIOUS_DATA_COLLECTION":
        events.append(make_event("LOGIN", 0, False, {"action": "Workstation Logon"}))
        events.append(make_event("FILE_ACCESS", 2, False, {"filename": "Salary_Audit_Confidential.xlsx", "operation": "READ"}))
        events.append(make_event("FILE_ACCESS", 4, False, {"filename": "Patent_Filing_Schematic_2026.pdf", "operation": "READ"}))
        events.append(make_event("FILE_COPY", 6, False, {"filename": "IP_Export_Bundle.tar.gz", "operation": "ARCHIVE_CREATION"}))
        events.append(make_event("EMAIL_ACTIVITY", 8, False, {
            "to": "external.recruiter@competitor-corp.com",
            "subject": "Requested Materials",
            "recipients_count": 1,
            "is_external": True,
            "has_attachment": True,
            "has_bcc": True,
            "size": 482000
        }))

    elif scenario_id == "MULTI_SIGNAL_ANOMALY":
        # Critical Exfiltration Pattern
        events.append(make_event("LOGIN", 0, True, {"action": "Physical Console Logon (Off-Hours)", "terminal": pc}))
        events.append(make_event("DEVICE_CONNECT", 2, True, {"device_name": "Corsair Stealth USB 256GB", "device_type": "USB_MASS_STORAGE", "serial": "COR-770192"}))
        
        # Rapid sensitive file accesses
        docs = [
            "Executive_Compensation_2026.xlsx",
            "NextGen_Microcode_Specification.pdf",
            "Defense_Contract_Submissions_Classified.pdf",
            "Master_Key_Vault_Backup.enc",
            "Core_Algorithm_Patent_Claims.docx"
        ]
        for idx, doc in enumerate(docs):
            events.append(make_event("FILE_ACCESS", 4 + idx * 2, True, {"filename": doc, "operation": "EXPORT_TO_DEVICE"}))
            events.append(make_event("FILE_COPY", 5 + idx * 2, True, {"filename": doc, "operation": "WRITE_USB", "destination": "E:\\Confidential_Dump"}))

        events.append(make_event("EMAIL_ACTIVITY", 16, True, {
            "to": "dropzone-upload@secure-proxy-mail.net",
            "subject": "System Documentation Dump",
            "recipients_count": 1,
            "is_external": True,
            "has_attachment": True,
            "size": 950000
        }))
        events.append(make_event("DEVICE_DISCONNECT", 18, True, {"device_name": "Corsair Stealth USB 256GB", "device_type": "USB_MASS_STORAGE"}))
        events.append(make_event("LOGOUT", 20, True, {"action": "Console Emergency Lock"}))

    return events

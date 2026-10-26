"""
Feature Vector Extraction for Online Inference
===============================================
Extracts the exact 58 features required by the trained XGBoost model from
a user's real-time events and their historical behavioral baseline.
"""

import json
from datetime import datetime
from typing import List, Dict, Any
import numpy as np
from app.core.config import settings


def extract_user_features(user, recent_events: List[Any], current_event: Any) -> Dict[str, float]:
    """
    Given a User and their list of recent activity events, construct the full
    58-feature dictionary matching `feature_schema.json`.
    """
    # Parse user baseline stats
    baseline = user.get_baseline_dict() if hasattr(user, "get_baseline_dict") else {}
    
    # Filter today's events (current active day)
    target_date = current_event.timestamp.date() if (current_event is not None and hasattr(current_event, "timestamp")) else datetime.utcnow().date()
    
    day_events = [
        e for e in recent_events 
        if e is not None and hasattr(e, "timestamp") and e.timestamp.date() == target_date
    ]
    if current_event is not None and current_event not in day_events:
        day_events.append(current_event)

    # 1. LOGON features
    logon_events = [e for e in day_events if e.activity_type in ["LOGIN", "LOGON"]]
    logoff_events = [e for e in day_events if e.activity_type in ["LOGOUT", "LOGOFF"]]
    logon_count = len(logon_events)
    logoff_count = len(logoff_events)
    logon_pcs = set(e.pc for e in logon_events)
    logon_unique_pcs = len(logon_pcs) if logon_pcs else 1
    logon_after_hours = sum(1 for e in logon_events if e.is_after_hours)
    logon_weekend = 1 if any(e.is_weekend for e in logon_events) else 0
    
    hours = [e.timestamp.hour for e in (logon_events + logoff_events)]
    logon_first_hour = min(hours) if hours else 8
    logon_last_hour = max(hours) if hours else 17
    logon_hour_span = max(0, logon_last_hour - logon_first_hour)
    logon_total_events = logon_count + logoff_count

    # 2. DEVICE features
    device_connects = [e for e in day_events if e.activity_type in ["DEVICE_CONNECT", "CONNECT"]]
    device_disconnects = [e for e in day_events if e.activity_type in ["DEVICE_DISCONNECT", "DISCONNECT"]]
    device_connect_count = len(device_connects)
    device_disconnect_count = len(device_disconnects)
    device_pcs = set(e.pc for e in (device_connects + device_disconnects))
    device_unique_pcs = len(device_pcs) if device_pcs else (1 if (device_connect_count + device_disconnect_count) > 0 else 0)
    device_after_hours = sum(1 for e in (device_connects + device_disconnects) if e.is_after_hours)
    device_weekend = 1 if any(e.is_weekend for e in (device_connects + device_disconnects)) else 0
    device_total_events = device_connect_count + device_disconnect_count

    # 3. FILE features
    file_events = [e for e in day_events if e.activity_type in ["FILE_ACCESS", "FILE_COPY", "FILE_READ", "FILE_WRITE"]]
    file_access_count = len(file_events)
    
    filenames = []
    file_pcs = set()
    doc_count = 0
    for e in file_events:
        file_pcs.add(e.pc)
        details = e.get_details_dict() if hasattr(e, "get_details_dict") else {}
        fname = details.get("filename", "")
        if fname:
            filenames.append(fname)
            ext = fname.split(".")[-1].lower() if "." in fname else ""
            if ext in ["doc", "docx", "pdf", "xls", "xlsx", "ppt", "pptx", "zip", "csv"]:
                doc_count += 1
                
    file_unique_count = len(set(filenames)) if filenames else file_access_count
    file_unique_pcs = len(file_pcs) if file_pcs else (1 if file_access_count > 0 else 0)
    file_after_hours = sum(1 for e in file_events if e.is_after_hours)
    file_weekend = 1 if any(e.is_weekend for e in file_events) else 0
    
    exts = set(f.split(".")[-1].lower() for f in filenames if "." in f)
    file_unique_extensions = len(exts) if exts else (1 if file_access_count > 0 else 0)
    file_doc_count = doc_count
    file_doc_ratio = file_doc_count / max(file_access_count, 1)

    # 4. EMAIL features
    email_events = [e for e in day_events if e.activity_type in ["EMAIL_ACTIVITY", "EMAIL_SEND", "EMAIL"]]
    email_count = len(email_events)
    email_after_hours = sum(1 for e in email_events if e.is_after_hours)
    email_weekend = 1 if any(e.is_weekend for e in email_events) else 0
    
    total_recips = 0
    with_attach = 0
    ext_to = 0
    ext_cc = 0
    total_size = 0
    bcc_cnt = 0
    
    for e in email_events:
        details = e.get_details_dict() if hasattr(e, "get_details_dict") else {}
        recips = details.get("recipients_count", 1)
        total_recips += recips
        if details.get("has_attachment", False) or details.get("attachments", 0) > 0:
            with_attach += 1
        if details.get("is_external", False) or details.get("external_recipients", 0) > 0:
            ext_to += 1
        if details.get("has_bcc", False):
            bcc_cnt += 1
        total_size += details.get("size", 25000)

    email_total_recipients = total_recips
    email_avg_recipients = total_recips / max(email_count, 1)
    email_max_recipients = total_recips if email_count <= 1 else max(1, total_recips // max(email_count, 1))
    email_with_attachment = with_attach
    email_external_to = ext_to
    email_external_cc = ext_cc
    email_avg_size = total_size / max(email_count, 1) if email_count > 0 else 0.0
    email_total_size = total_size
    email_bcc_count = bcc_cnt
    email_external_ratio = email_external_to / max(email_count, 1)
    email_attachment_ratio = email_with_attachment / max(email_count, 1)

    # 5. CROSS-SOURCE features
    device_and_file = 1 if (device_connect_count > 0 and file_access_count > 0) else 0
    afterhours_device_and_file = 1 if (device_after_hours > 0 and file_after_hours > 0) else 0
    afterhours_logon_and_device = 1 if (logon_after_hours > 0 and device_after_hours > 0) else 0
    afterhours_triple_signal = 1 if (logon_after_hours > 0 and device_after_hours > 0 and file_after_hours > 0) else 0
    total_activity_count = logon_total_events + device_total_events + file_access_count + email_count
    
    total_ah = logon_after_hours + device_after_hours + file_after_hours + email_after_hours
    overall_after_hours_ratio = total_ah / max(total_activity_count, 1)
    multi_pc_logon = 1 if logon_unique_pcs > 1 else 0
    external_email_and_device = 1 if (email_external_to > 0 and device_connect_count > 0) else 0
    high_file_and_device = 1 if (file_access_count >= 10 and device_connect_count > 0) else 0
    any_weekend_activity = 1 if (logon_weekend or device_weekend or file_weekend or email_weekend) else 0

    # 6. DEVIATION features from User Baseline
    def compute_dev(val, key_mean, key_std, default_mean, default_std):
        m = baseline.get(key_mean, default_mean)
        s = max(baseline.get(key_std, default_std), 0.1)
        return float((val - m) / s)

    dev_logon_total = compute_dev(logon_total_events, "logon_mean", "logon_std", 2.0, 0.8)
    dev_device_total = compute_dev(device_total_events, "device_mean", "device_std", 0.0, 0.5)
    dev_file_access = compute_dev(file_access_count, "file_mean", "file_std", 0.0, 1.0)
    dev_email_count = compute_dev(email_count, "email_mean", "email_std", 8.0, 3.0)
    dev_logon_ah = compute_dev(logon_after_hours, "logon_ah_mean", "logon_ah_std", 0.0, 0.3)
    dev_device_ah = compute_dev(device_after_hours, "device_ah_mean", "device_ah_std", 0.0, 0.2)
    dev_file_ah = compute_dev(file_after_hours, "file_ah_mean", "file_ah_std", 0.0, 0.2)
    dev_email_ah = compute_dev(email_after_hours, "email_ah_mean", "email_ah_std", 0.0, 0.5)
    dev_total_act = compute_dev(total_activity_count, "total_mean", "total_std", 10.0, 4.0)
    dev_logon_first_hr = compute_dev(logon_first_hour, "first_hour_mean", "first_hour_std", 8.0, 1.0)

    deviations = [
        dev_logon_total, dev_device_total, dev_file_access, dev_email_count,
        dev_logon_ah, dev_device_ah, dev_file_ah, dev_email_ah,
        dev_total_act, dev_logon_first_hr
    ]
    overall_behavior_dev = float(np.mean(deviations))

    # Assemble dictionary with exact names matching feature_schema.json
    feature_dict = {
        "logon_count": float(logon_count),
        "logoff_count": float(logoff_count),
        "logon_unique_pcs": float(logon_unique_pcs),
        "logon_after_hours": float(logon_after_hours),
        "logon_weekend": float(logon_weekend),
        "logon_first_hour": float(logon_first_hour),
        "logon_last_hour": float(logon_last_hour),
        "logon_hour_span": float(logon_hour_span),
        "logon_total_events": float(logon_total_events),
        "device_connect_count": float(device_connect_count),
        "device_disconnect_count": float(device_disconnect_count),
        "device_unique_pcs": float(device_unique_pcs),
        "device_after_hours": float(device_after_hours),
        "device_weekend": float(device_weekend),
        "device_total_events": float(device_total_events),
        "file_access_count": float(file_access_count),
        "file_unique_count": float(file_unique_count),
        "file_unique_pcs": float(file_unique_pcs),
        "file_after_hours": float(file_after_hours),
        "file_weekend": float(file_weekend),
        "file_unique_extensions": float(file_unique_extensions),
        "file_doc_count": float(file_doc_count),
        "file_doc_ratio": float(file_doc_ratio),
        "email_count": float(email_count),
        "email_total_recipients": float(email_total_recipients),
        "email_avg_recipients": float(email_avg_recipients),
        "email_max_recipients": float(email_max_recipients),
        "email_after_hours": float(email_after_hours),
        "email_weekend": float(email_weekend),
        "email_with_attachment": float(email_with_attachment),
        "email_external_to": float(email_external_to),
        "email_external_cc": float(email_external_cc),
        "email_avg_size": float(email_avg_size),
        "email_total_size": float(email_total_size),
        "email_bcc_count": float(email_bcc_count),
        "email_external_ratio": float(email_external_ratio),
        "email_attachment_ratio": float(email_attachment_ratio),
        "device_and_file": float(device_and_file),
        "afterhours_device_and_file": float(afterhours_device_and_file),
        "afterhours_logon_and_device": float(afterhours_logon_and_device),
        "afterhours_triple_signal": float(afterhours_triple_signal),
        "total_activity_count": float(total_activity_count),
        "overall_after_hours_ratio": float(overall_after_hours_ratio),
        "multi_pc_logon": float(multi_pc_logon),
        "external_email_and_device": float(external_email_and_device),
        "high_file_and_device": float(high_file_and_device),
        "any_weekend_activity": float(any_weekend_activity),
        "deviation_logon_total_events": float(dev_logon_total),
        "deviation_device_total_events": float(dev_device_total),
        "deviation_file_access_count": float(dev_file_access),
        "deviation_email_count": float(dev_email_count),
        "deviation_logon_after_hours": float(dev_logon_ah),
        "deviation_device_after_hours": float(dev_device_ah),
        "deviation_file_after_hours": float(dev_file_ah),
        "deviation_email_after_hours": float(dev_email_ah),
        "deviation_total_activity_count": float(dev_total_act),
        "deviation_logon_first_hour": float(dev_logon_first_hr),
        "overall_behavior_deviation": float(overall_behavior_dev),
    }

    return feature_dict

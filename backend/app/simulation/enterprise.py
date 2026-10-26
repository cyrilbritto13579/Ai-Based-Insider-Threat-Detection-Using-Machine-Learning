"""
Synthetic Enterprise Definition: TechNova
==========================================
Generates synthetic enterprise environment with departments,
roles, workstations, and baseline behavioral profiles.
Never uses real employee information.
"""

import json
from typing import List, Dict, Any
from app.db.models import User, RiskScore
from sqlalchemy.orm import Session


SYNTHETIC_USERS = [
    # === Engineering (12 users) ===
    {"user_id": "ENG-001", "name": "Sarah Jenkins", "department": "Engineering", "role": "Lead Software Engineer", "email": "sarah.jenkins@technova.io", "assigned_pc": "PC-ENG-01", "manager": "David Chen", "location": "Building A, Floor 3", "employment_type": "Full-Time", "join_date": "2021-06-15", "normal_hours": "09:00–18:00",
     "baseline_stats": {"logon_mean": 2.0, "logon_std": 0.5, "device_mean": 0.1, "device_std": 0.3, "file_mean": 4.0, "file_std": 2.0, "email_mean": 12.0, "email_std": 3.5, "logon_ah_mean": 0.0, "logon_ah_std": 0.1, "device_ah_mean": 0.0, "device_ah_std": 0.1, "file_ah_mean": 0.0, "file_ah_std": 0.2, "email_ah_mean": 0.2, "email_ah_std": 0.5, "total_mean": 18.0, "total_std": 4.0, "first_hour_mean": 8.5, "first_hour_std": 0.5}},
    {"user_id": "ENG-002", "name": "David Chen", "department": "Engineering", "role": "DevOps Architect", "email": "david.chen@technova.io", "assigned_pc": "PC-ENG-02", "manager": "Raymond Price", "location": "Building A, Floor 3", "employment_type": "Full-Time", "join_date": "2019-03-01", "normal_hours": "08:30–17:30",
     "baseline_stats": {"logon_mean": 3.0, "logon_std": 0.8, "device_mean": 0.0, "device_std": 0.1, "file_mean": 6.0, "file_std": 2.5, "email_mean": 10.0, "email_std": 3.0, "logon_ah_mean": 0.1, "logon_ah_std": 0.3, "device_ah_mean": 0.0, "device_ah_std": 0.1, "file_ah_mean": 0.1, "file_ah_std": 0.3, "email_ah_mean": 0.1, "email_ah_std": 0.4, "total_mean": 19.0, "total_std": 5.0, "first_hour_mean": 9.0, "first_hour_std": 0.5}},
    {"user_id": "ENG-003", "name": "Priya Sharma", "department": "Engineering", "role": "Backend Developer", "email": "priya.sharma@technova.io", "assigned_pc": "PC-ENG-03", "manager": "Sarah Jenkins", "location": "Building A, Floor 3", "employment_type": "Full-Time", "join_date": "2023-01-10", "normal_hours": "09:00–18:00",
     "baseline_stats": {"logon_mean": 2.0, "logon_std": 0.4, "device_mean": 0.0, "device_std": 0.1, "file_mean": 3.0, "file_std": 1.5, "email_mean": 8.0, "email_std": 2.5, "logon_ah_mean": 0.0, "logon_ah_std": 0.1, "device_ah_mean": 0.0, "device_ah_std": 0.1, "file_ah_mean": 0.0, "file_ah_std": 0.1, "email_ah_mean": 0.0, "email_ah_std": 0.2, "total_mean": 13.0, "total_std": 3.5, "first_hour_mean": 9.0, "first_hour_std": 0.4}},
    {"user_id": "ENG-004", "name": "Michael Torres", "department": "Engineering", "role": "Frontend Developer", "email": "michael.torres@technova.io", "assigned_pc": "PC-ENG-04", "manager": "Sarah Jenkins", "location": "Building A, Floor 3", "employment_type": "Full-Time", "join_date": "2022-08-20", "normal_hours": "10:00–19:00",
     "baseline_stats": {"logon_mean": 2.0, "logon_std": 0.5, "device_mean": 0.0, "device_std": 0.1, "file_mean": 3.5, "file_std": 1.8, "email_mean": 7.0, "email_std": 2.0, "logon_ah_mean": 0.0, "logon_ah_std": 0.1, "device_ah_mean": 0.0, "device_ah_std": 0.1, "file_ah_mean": 0.0, "file_ah_std": 0.2, "email_ah_mean": 0.1, "email_ah_std": 0.3, "total_mean": 12.5, "total_std": 3.5, "first_hour_mean": 10.0, "first_hour_std": 0.5}},
    {"user_id": "ENG-005", "name": "Lisa Park", "department": "Engineering", "role": "QA Engineer", "email": "lisa.park@technova.io", "assigned_pc": "PC-ENG-05", "manager": "David Chen", "location": "Building A, Floor 2", "employment_type": "Full-Time", "join_date": "2022-04-12", "normal_hours": "09:00–18:00",
     "baseline_stats": {"logon_mean": 2.0, "logon_std": 0.4, "device_mean": 0.0, "device_std": 0.1, "file_mean": 5.0, "file_std": 2.0, "email_mean": 9.0, "email_std": 2.5, "logon_ah_mean": 0.0, "logon_ah_std": 0.1, "device_ah_mean": 0.0, "device_ah_std": 0.1, "file_ah_mean": 0.0, "file_ah_std": 0.1, "email_ah_mean": 0.0, "email_ah_std": 0.2, "total_mean": 16.0, "total_std": 4.0, "first_hour_mean": 9.0, "first_hour_std": 0.3}},
    {"user_id": "ENG-006", "name": "Carlos Rivera", "department": "Engineering", "role": "Cloud Infrastructure Engineer", "email": "carlos.rivera@technova.io", "assigned_pc": "PC-ENG-06", "manager": "David Chen", "location": "Building A, Floor 2", "employment_type": "Full-Time", "join_date": "2023-07-03", "normal_hours": "08:00–17:00",
     "baseline_stats": {"logon_mean": 3.0, "logon_std": 0.7, "device_mean": 0.1, "device_std": 0.2, "file_mean": 4.0, "file_std": 1.5, "email_mean": 8.0, "email_std": 2.5, "logon_ah_mean": 0.1, "logon_ah_std": 0.2, "device_ah_mean": 0.0, "device_ah_std": 0.1, "file_ah_mean": 0.0, "file_ah_std": 0.2, "email_ah_mean": 0.1, "email_ah_std": 0.3, "total_mean": 15.0, "total_std": 4.0, "first_hour_mean": 8.0, "first_hour_std": 0.5}},
    {"user_id": "ENG-007", "name": "Amanda Fletcher", "department": "Engineering", "role": "Security Engineer", "email": "amanda.fletcher@technova.io", "assigned_pc": "PC-ENG-07", "manager": "David Chen", "location": "Building A, Floor 2", "employment_type": "Full-Time", "join_date": "2021-11-08", "normal_hours": "09:00–18:00",
     "baseline_stats": {"logon_mean": 3.0, "logon_std": 0.6, "device_mean": 0.1, "device_std": 0.3, "file_mean": 5.0, "file_std": 2.0, "email_mean": 10.0, "email_std": 3.0, "logon_ah_mean": 0.1, "logon_ah_std": 0.2, "device_ah_mean": 0.0, "device_ah_std": 0.1, "file_ah_mean": 0.1, "file_ah_std": 0.3, "email_ah_mean": 0.2, "email_ah_std": 0.4, "total_mean": 18.0, "total_std": 4.5, "first_hour_mean": 9.0, "first_hour_std": 0.4}},
    {"user_id": "ENG-008", "name": "James Nakamura", "department": "Engineering", "role": "Data Engineer", "email": "james.nakamura@technova.io", "assigned_pc": "PC-ENG-08", "manager": "Sarah Jenkins", "location": "Building A, Floor 3", "employment_type": "Full-Time", "join_date": "2024-02-19", "normal_hours": "09:30–18:30",
     "baseline_stats": {"logon_mean": 2.0, "logon_std": 0.5, "device_mean": 0.0, "device_std": 0.1, "file_mean": 6.0, "file_std": 2.5, "email_mean": 7.0, "email_std": 2.0, "logon_ah_mean": 0.0, "logon_ah_std": 0.1, "device_ah_mean": 0.0, "device_ah_std": 0.1, "file_ah_mean": 0.0, "file_ah_std": 0.2, "email_ah_mean": 0.0, "email_ah_std": 0.2, "total_mean": 15.0, "total_std": 4.0, "first_hour_mean": 9.5, "first_hour_std": 0.5}},
    {"user_id": "ENG-009", "name": "Olivia Reeves", "department": "Engineering", "role": "ML Engineer", "email": "olivia.reeves@technova.io", "assigned_pc": "PC-ENG-09", "manager": "Sarah Jenkins", "location": "Building A, Floor 3", "employment_type": "Full-Time", "join_date": "2023-05-22", "normal_hours": "09:00–18:00",
     "baseline_stats": {"logon_mean": 2.0, "logon_std": 0.5, "device_mean": 0.0, "device_std": 0.1, "file_mean": 7.0, "file_std": 3.0, "email_mean": 6.0, "email_std": 2.0, "logon_ah_mean": 0.0, "logon_ah_std": 0.1, "device_ah_mean": 0.0, "device_ah_std": 0.1, "file_ah_mean": 0.0, "file_ah_std": 0.2, "email_ah_mean": 0.0, "email_ah_std": 0.2, "total_mean": 15.0, "total_std": 4.0, "first_hour_mean": 9.0, "first_hour_std": 0.5}},
    {"user_id": "ENG-010", "name": "Daniel Kim", "department": "Engineering", "role": "Mobile Developer", "email": "daniel.kim@technova.io", "assigned_pc": "PC-ENG-10", "manager": "Sarah Jenkins", "location": "Building A, Floor 2", "employment_type": "Contractor", "join_date": "2024-09-01", "normal_hours": "10:00–18:00",
     "baseline_stats": {"logon_mean": 1.5, "logon_std": 0.4, "device_mean": 0.0, "device_std": 0.1, "file_mean": 3.0, "file_std": 1.5, "email_mean": 5.0, "email_std": 1.5, "logon_ah_mean": 0.0, "logon_ah_std": 0.1, "device_ah_mean": 0.0, "device_ah_std": 0.1, "file_ah_mean": 0.0, "file_ah_std": 0.1, "email_ah_mean": 0.0, "email_ah_std": 0.1, "total_mean": 9.5, "total_std": 2.5, "first_hour_mean": 10.0, "first_hour_std": 0.4}},
    {"user_id": "ENG-011", "name": "Sophie Wright", "department": "Engineering", "role": "Platform Engineer", "email": "sophie.wright@technova.io", "assigned_pc": "PC-ENG-11", "manager": "David Chen", "location": "Building A, Floor 2", "employment_type": "Full-Time", "join_date": "2022-01-15", "normal_hours": "09:00–18:00",
     "baseline_stats": {"logon_mean": 2.5, "logon_std": 0.5, "device_mean": 0.0, "device_std": 0.1, "file_mean": 4.0, "file_std": 1.8, "email_mean": 9.0, "email_std": 2.5, "logon_ah_mean": 0.0, "logon_ah_std": 0.1, "device_ah_mean": 0.0, "device_ah_std": 0.1, "file_ah_mean": 0.0, "file_ah_std": 0.1, "email_ah_mean": 0.0, "email_ah_std": 0.2, "total_mean": 15.5, "total_std": 3.5, "first_hour_mean": 9.0, "first_hour_std": 0.4}},
    {"user_id": "ENG-014", "name": "Victor Thorne", "department": "Engineering", "role": "Principal Firmware Architect", "email": "victor.thorne@technova.io", "assigned_pc": "PC-ENG-14", "manager": "Raymond Price", "location": "Building A, Floor 4", "employment_type": "Full-Time", "join_date": "2018-09-10", "normal_hours": "09:00–18:00",
     "baseline_stats": {"logon_mean": 2.0, "logon_std": 0.5, "device_mean": 0.0, "device_std": 0.1, "file_mean": 3.0, "file_std": 1.5, "email_mean": 8.0, "email_std": 2.5, "logon_ah_mean": 0.0, "logon_ah_std": 0.1, "device_ah_mean": 0.0, "device_ah_std": 0.1, "file_ah_mean": 0.0, "file_ah_std": 0.1, "email_ah_mean": 0.0, "email_ah_std": 0.2, "total_mean": 13.0, "total_std": 3.5, "first_hour_mean": 9.0, "first_hour_std": 0.4}},

    # === Finance (8 users) ===
    {"user_id": "FIN-001", "name": "Marcus Vance", "department": "Finance", "role": "Senior Financial Analyst", "email": "marcus.vance@technova.io", "assigned_pc": "PC-FIN-01", "manager": "Catherine Brooks", "location": "Building B, Floor 1", "employment_type": "Full-Time", "join_date": "2020-07-01", "normal_hours": "08:30–17:30",
     "baseline_stats": {"logon_mean": 2.0, "logon_std": 0.4, "device_mean": 0.0, "device_std": 0.1, "file_mean": 8.0, "file_std": 3.0, "email_mean": 15.0, "email_std": 4.0, "logon_ah_mean": 0.0, "logon_ah_std": 0.1, "device_ah_mean": 0.0, "device_ah_std": 0.1, "file_ah_mean": 0.0, "file_ah_std": 0.2, "email_ah_mean": 0.0, "email_ah_std": 0.2, "total_mean": 25.0, "total_std": 5.5, "first_hour_mean": 8.0, "first_hour_std": 0.3}},
    {"user_id": "FIN-002", "name": "Catherine Brooks", "department": "Finance", "role": "VP of Finance", "email": "catherine.brooks@technova.io", "assigned_pc": "PC-FIN-02", "manager": "Raymond Price", "location": "Building B, Floor 2", "employment_type": "Full-Time", "join_date": "2017-04-15", "normal_hours": "08:00–17:00",
     "baseline_stats": {"logon_mean": 2.0, "logon_std": 0.3, "device_mean": 0.0, "device_std": 0.1, "file_mean": 5.0, "file_std": 2.0, "email_mean": 18.0, "email_std": 5.0, "logon_ah_mean": 0.0, "logon_ah_std": 0.1, "device_ah_mean": 0.0, "device_ah_std": 0.1, "file_ah_mean": 0.0, "file_ah_std": 0.1, "email_ah_mean": 0.1, "email_ah_std": 0.3, "total_mean": 25.0, "total_std": 5.0, "first_hour_mean": 8.0, "first_hour_std": 0.3}},
    {"user_id": "FIN-003", "name": "Nathan Wells", "department": "Finance", "role": "Accounts Payable Specialist", "email": "nathan.wells@technova.io", "assigned_pc": "PC-FIN-03", "manager": "Marcus Vance", "location": "Building B, Floor 1", "employment_type": "Full-Time", "join_date": "2023-03-20", "normal_hours": "09:00–18:00",
     "baseline_stats": {"logon_mean": 2.0, "logon_std": 0.4, "device_mean": 0.0, "device_std": 0.1, "file_mean": 6.0, "file_std": 2.5, "email_mean": 12.0, "email_std": 3.0, "logon_ah_mean": 0.0, "logon_ah_std": 0.1, "device_ah_mean": 0.0, "device_ah_std": 0.1, "file_ah_mean": 0.0, "file_ah_std": 0.1, "email_ah_mean": 0.0, "email_ah_std": 0.2, "total_mean": 20.0, "total_std": 4.0, "first_hour_mean": 9.0, "first_hour_std": 0.4}},
    {"user_id": "FIN-004", "name": "Rebecca Shaw", "department": "Finance", "role": "Financial Controller", "email": "rebecca.shaw@technova.io", "assigned_pc": "PC-FIN-04", "manager": "Catherine Brooks", "location": "Building B, Floor 1", "employment_type": "Full-Time", "join_date": "2021-01-10", "normal_hours": "08:30–17:30",
     "baseline_stats": {"logon_mean": 2.0, "logon_std": 0.4, "device_mean": 0.0, "device_std": 0.1, "file_mean": 7.0, "file_std": 2.5, "email_mean": 14.0, "email_std": 3.5, "logon_ah_mean": 0.0, "logon_ah_std": 0.1, "device_ah_mean": 0.0, "device_ah_std": 0.1, "file_ah_mean": 0.0, "file_ah_std": 0.1, "email_ah_mean": 0.0, "email_ah_std": 0.2, "total_mean": 23.0, "total_std": 5.0, "first_hour_mean": 8.5, "first_hour_std": 0.3}},
    {"user_id": "FIN-005", "name": "Gregory Dunn", "department": "Finance", "role": "Junior Analyst", "email": "gregory.dunn@technova.io", "assigned_pc": "PC-FIN-05", "manager": "Marcus Vance", "location": "Building B, Floor 1", "employment_type": "Part-Time", "join_date": "2025-01-06", "normal_hours": "09:00–14:00",
     "baseline_stats": {"logon_mean": 1.0, "logon_std": 0.3, "device_mean": 0.0, "device_std": 0.1, "file_mean": 3.0, "file_std": 1.5, "email_mean": 6.0, "email_std": 2.0, "logon_ah_mean": 0.0, "logon_ah_std": 0.1, "device_ah_mean": 0.0, "device_ah_std": 0.1, "file_ah_mean": 0.0, "file_ah_std": 0.1, "email_ah_mean": 0.0, "email_ah_std": 0.1, "total_mean": 10.0, "total_std": 3.0, "first_hour_mean": 9.0, "first_hour_std": 0.3}},
    {"user_id": "FIN-006", "name": "Ariana Sloane", "department": "Finance", "role": "Treasury Analyst", "email": "ariana.sloane@technova.io", "assigned_pc": "PC-FIN-06", "manager": "Catherine Brooks", "location": "Building B, Floor 2", "employment_type": "Full-Time", "join_date": "2021-09-12", "normal_hours": "08:00–17:00",
     "baseline_stats": {"logon_mean": 3.0, "logon_std": 0.9, "device_mean": 0.1, "device_std": 0.2, "file_mean": 9.0, "file_std": 3.5, "email_mean": 17.0, "email_std": 4.5, "logon_ah_mean": 0.2, "logon_ah_std": 0.4, "device_ah_mean": 0.1, "device_ah_std": 0.2, "file_ah_mean": 0.3, "file_ah_std": 0.5, "email_ah_mean": 0.3, "email_ah_std": 0.6, "total_mean": 29.0, "total_std": 7.0, "first_hour_mean": 8.0, "first_hour_std": 0.5}},

    # === Human Resources (6 users) ===
    {"user_id": "HR-001", "name": "Elena Rostova", "department": "Human Resources", "role": "HR Director", "email": "elena.rostova@technova.io", "assigned_pc": "PC-HR-01", "manager": "Raymond Price", "location": "Building B, Floor 2", "employment_type": "Full-Time", "join_date": "2019-01-20", "normal_hours": "08:30–17:30",
     "baseline_stats": {"logon_mean": 2.0, "logon_std": 0.3, "device_mean": 0.0, "device_std": 0.1, "file_mean": 3.0, "file_std": 1.5, "email_mean": 20.0, "email_std": 5.0, "logon_ah_mean": 0.0, "logon_ah_std": 0.1, "device_ah_mean": 0.0, "device_ah_std": 0.1, "file_ah_mean": 0.0, "file_ah_std": 0.1, "email_ah_mean": 0.0, "email_ah_std": 0.2, "total_mean": 25.0, "total_std": 6.0, "first_hour_mean": 8.5, "first_hour_std": 0.4}},
    {"user_id": "HR-002", "name": "Patricia Nguyen", "department": "Human Resources", "role": "Talent Acquisition Specialist", "email": "patricia.nguyen@technova.io", "assigned_pc": "PC-HR-02", "manager": "Elena Rostova", "location": "Building B, Floor 2", "employment_type": "Full-Time", "join_date": "2022-06-01", "normal_hours": "09:00–18:00",
     "baseline_stats": {"logon_mean": 2.0, "logon_std": 0.4, "device_mean": 0.0, "device_std": 0.1, "file_mean": 2.0, "file_std": 1.0, "email_mean": 22.0, "email_std": 5.0, "logon_ah_mean": 0.0, "logon_ah_std": 0.1, "device_ah_mean": 0.0, "device_ah_std": 0.1, "file_ah_mean": 0.0, "file_ah_std": 0.1, "email_ah_mean": 0.0, "email_ah_std": 0.2, "total_mean": 26.0, "total_std": 5.5, "first_hour_mean": 9.0, "first_hour_std": 0.4}},
    {"user_id": "HR-003", "name": "Thomas Blake", "department": "Human Resources", "role": "Payroll Administrator", "email": "thomas.blake@technova.io", "assigned_pc": "PC-HR-03", "manager": "Elena Rostova", "location": "Building B, Floor 2", "employment_type": "Full-Time", "join_date": "2023-09-15", "normal_hours": "09:00–17:30",
     "baseline_stats": {"logon_mean": 2.0, "logon_std": 0.3, "device_mean": 0.0, "device_std": 0.1, "file_mean": 4.0, "file_std": 1.5, "email_mean": 10.0, "email_std": 3.0, "logon_ah_mean": 0.0, "logon_ah_std": 0.1, "device_ah_mean": 0.0, "device_ah_std": 0.1, "file_ah_mean": 0.0, "file_ah_std": 0.1, "email_ah_mean": 0.0, "email_ah_std": 0.2, "total_mean": 16.0, "total_std": 4.0, "first_hour_mean": 9.0, "first_hour_std": 0.3}},
    {"user_id": "HR-004", "name": "Noah Mercer", "department": "Human Resources", "role": "Benefits Coordinator", "email": "noah.mercer@technova.io", "assigned_pc": "PC-HR-04", "manager": "Elena Rostova", "location": "Building B, Floor 2", "employment_type": "Full-Time", "join_date": "2022-05-20", "normal_hours": "09:00–18:00",
     "baseline_stats": {"logon_mean": 2.5, "logon_std": 0.6, "device_mean": 0.1, "device_std": 0.2, "file_mean": 6.0, "file_std": 2.5, "email_mean": 15.0, "email_std": 4.0, "logon_ah_mean": 0.1, "logon_ah_std": 0.3, "device_ah_mean": 0.1, "device_ah_std": 0.2, "file_ah_mean": 0.2, "file_ah_std": 0.3, "email_ah_mean": 0.2, "email_ah_std": 0.4, "total_mean": 24.0, "total_std": 5.5, "first_hour_mean": 9.0, "first_hour_std": 0.4}},

    # === Information Technology (6 users) ===
    {"user_id": "IT-001", "name": "Alex Mercer", "department": "Information Technology", "role": "Systems Administrator", "email": "alex.mercer@technova.io", "assigned_pc": "PC-IT-01", "manager": "Kevin Marshall", "location": "Building A, Floor 1", "employment_type": "Full-Time", "join_date": "2020-05-10", "normal_hours": "08:00–17:00",
     "baseline_stats": {"logon_mean": 4.0, "logon_std": 1.2, "device_mean": 0.2, "device_std": 0.4, "file_mean": 5.0, "file_std": 2.0, "email_mean": 14.0, "email_std": 4.0, "logon_ah_mean": 0.2, "logon_ah_std": 0.4, "device_ah_mean": 0.1, "device_ah_std": 0.2, "file_ah_mean": 0.1, "file_ah_std": 0.3, "email_ah_mean": 0.2, "email_ah_std": 0.5, "total_mean": 23.0, "total_std": 6.0, "first_hour_mean": 7.5, "first_hour_std": 0.8}},
    {"user_id": "IT-002", "name": "Kevin Marshall", "department": "Information Technology", "role": "IT Director", "email": "kevin.marshall@technova.io", "assigned_pc": "PC-IT-02", "manager": "Raymond Price", "location": "Building A, Floor 1", "employment_type": "Full-Time", "join_date": "2018-02-01", "normal_hours": "08:00–17:00",
     "baseline_stats": {"logon_mean": 3.0, "logon_std": 0.8, "device_mean": 0.1, "device_std": 0.3, "file_mean": 4.0, "file_std": 2.0, "email_mean": 16.0, "email_std": 4.0, "logon_ah_mean": 0.1, "logon_ah_std": 0.3, "device_ah_mean": 0.0, "device_ah_std": 0.1, "file_ah_mean": 0.0, "file_ah_std": 0.2, "email_ah_mean": 0.1, "email_ah_std": 0.3, "total_mean": 23.0, "total_std": 5.5, "first_hour_mean": 8.0, "first_hour_std": 0.5}},
    {"user_id": "IT-003", "name": "Hannah Cole", "department": "Information Technology", "role": "Network Engineer", "email": "hannah.cole@technova.io", "assigned_pc": "PC-IT-03", "manager": "Kevin Marshall", "location": "Building A, Floor 1", "employment_type": "Full-Time", "join_date": "2022-11-05", "normal_hours": "09:00–18:00",
     "baseline_stats": {"logon_mean": 3.0, "logon_std": 0.7, "device_mean": 0.1, "device_std": 0.2, "file_mean": 3.0, "file_std": 1.5, "email_mean": 10.0, "email_std": 3.0, "logon_ah_mean": 0.1, "logon_ah_std": 0.2, "device_ah_mean": 0.0, "device_ah_std": 0.1, "file_ah_mean": 0.0, "file_ah_std": 0.2, "email_ah_mean": 0.1, "email_ah_std": 0.3, "total_mean": 16.0, "total_std": 4.0, "first_hour_mean": 9.0, "first_hour_std": 0.5}},
    {"user_id": "IT-004", "name": "Derek Ingram", "department": "Information Technology", "role": "Helpdesk Technician", "email": "derek.ingram@technova.io", "assigned_pc": "PC-IT-04", "manager": "Alex Mercer", "location": "Building A, Floor 1", "employment_type": "Contractor", "join_date": "2025-03-01", "normal_hours": "09:00–17:00",
     "baseline_stats": {"logon_mean": 2.0, "logon_std": 0.5, "device_mean": 0.1, "device_std": 0.2, "file_mean": 2.0, "file_std": 1.0, "email_mean": 8.0, "email_std": 2.0, "logon_ah_mean": 0.0, "logon_ah_std": 0.1, "device_ah_mean": 0.0, "device_ah_std": 0.1, "file_ah_mean": 0.0, "file_ah_std": 0.1, "email_ah_mean": 0.0, "email_ah_std": 0.1, "total_mean": 12.0, "total_std": 3.0, "first_hour_mean": 9.0, "first_hour_std": 0.4}},

    # === Operations (6 users) ===
    {"user_id": "OPS-001", "name": "Rachel Adams", "department": "Operations", "role": "Supply Chain Manager", "email": "rachel.adams@technova.io", "assigned_pc": "PC-OPS-01", "manager": "Raymond Price", "location": "Building C, Floor 1", "employment_type": "Full-Time", "join_date": "2020-10-15", "normal_hours": "08:00–17:00",
     "baseline_stats": {"logon_mean": 2.0, "logon_std": 0.4, "device_mean": 0.0, "device_std": 0.1, "file_mean": 4.0, "file_std": 1.8, "email_mean": 16.0, "email_std": 4.5, "logon_ah_mean": 0.0, "logon_ah_std": 0.1, "device_ah_mean": 0.0, "device_ah_std": 0.1, "file_ah_mean": 0.0, "file_ah_std": 0.1, "email_ah_mean": 0.0, "email_ah_std": 0.2, "total_mean": 22.0, "total_std": 5.0, "first_hour_mean": 8.0, "first_hour_std": 0.4}},
    {"user_id": "OPS-002", "name": "Brian Watts", "department": "Operations", "role": "Logistics Coordinator", "email": "brian.watts@technova.io", "assigned_pc": "PC-OPS-02", "manager": "Rachel Adams", "location": "Building C, Floor 1", "employment_type": "Full-Time", "join_date": "2023-04-10", "normal_hours": "07:30–16:30",
     "baseline_stats": {"logon_mean": 2.0, "logon_std": 0.4, "device_mean": 0.0, "device_std": 0.1, "file_mean": 3.0, "file_std": 1.5, "email_mean": 12.0, "email_std": 3.0, "logon_ah_mean": 0.0, "logon_ah_std": 0.1, "device_ah_mean": 0.0, "device_ah_std": 0.1, "file_ah_mean": 0.0, "file_ah_std": 0.1, "email_ah_mean": 0.0, "email_ah_std": 0.2, "total_mean": 17.0, "total_std": 4.0, "first_hour_mean": 7.5, "first_hour_std": 0.4}},
    {"user_id": "OPS-003", "name": "Megan Hart", "department": "Operations", "role": "Procurement Officer", "email": "megan.hart@technova.io", "assigned_pc": "PC-OPS-03", "manager": "Rachel Adams", "location": "Building C, Floor 1", "employment_type": "Full-Time", "join_date": "2022-08-01", "normal_hours": "09:00–18:00",
     "baseline_stats": {"logon_mean": 2.0, "logon_std": 0.4, "device_mean": 0.0, "device_std": 0.1, "file_mean": 5.0, "file_std": 2.0, "email_mean": 14.0, "email_std": 3.5, "logon_ah_mean": 0.0, "logon_ah_std": 0.1, "device_ah_mean": 0.0, "device_ah_std": 0.1, "file_ah_mean": 0.0, "file_ah_std": 0.1, "email_ah_mean": 0.0, "email_ah_std": 0.2, "total_mean": 21.0, "total_std": 4.5, "first_hour_mean": 9.0, "first_hour_std": 0.4}},

    # === Sales (5 users) ===
    {"user_id": "SLS-001", "name": "Andrew Grant", "department": "Sales", "role": "Regional Sales Director", "email": "andrew.grant@technova.io", "assigned_pc": "PC-SLS-01", "manager": "Raymond Price", "location": "Building C, Floor 2", "employment_type": "Full-Time", "join_date": "2019-06-20", "normal_hours": "08:30–18:00",
     "baseline_stats": {"logon_mean": 2.0, "logon_std": 0.5, "device_mean": 0.0, "device_std": 0.1, "file_mean": 3.0, "file_std": 1.5, "email_mean": 25.0, "email_std": 6.0, "logon_ah_mean": 0.0, "logon_ah_std": 0.1, "device_ah_mean": 0.0, "device_ah_std": 0.1, "file_ah_mean": 0.0, "file_ah_std": 0.1, "email_ah_mean": 0.1, "email_ah_std": 0.3, "total_mean": 30.0, "total_std": 6.0, "first_hour_mean": 8.5, "first_hour_std": 0.5}},
    {"user_id": "SLS-002", "name": "Jessica Palmer", "department": "Sales", "role": "Account Executive", "email": "jessica.palmer@technova.io", "assigned_pc": "PC-SLS-02", "manager": "Andrew Grant", "location": "Building C, Floor 2", "employment_type": "Full-Time", "join_date": "2023-02-10", "normal_hours": "09:00–18:00",
     "baseline_stats": {"logon_mean": 2.0, "logon_std": 0.4, "device_mean": 0.0, "device_std": 0.1, "file_mean": 2.0, "file_std": 1.0, "email_mean": 20.0, "email_std": 5.0, "logon_ah_mean": 0.0, "logon_ah_std": 0.1, "device_ah_mean": 0.0, "device_ah_std": 0.1, "file_ah_mean": 0.0, "file_ah_std": 0.1, "email_ah_mean": 0.0, "email_ah_std": 0.2, "total_mean": 24.0, "total_std": 5.0, "first_hour_mean": 9.0, "first_hour_std": 0.4}},
    {"user_id": "SLS-003", "name": "Ryan Cooper", "department": "Sales", "role": "Business Development Rep", "email": "ryan.cooper@technova.io", "assigned_pc": "PC-SLS-03", "manager": "Andrew Grant", "location": "Building C, Floor 2", "employment_type": "Full-Time", "join_date": "2024-06-01", "normal_hours": "09:00–18:00",
     "baseline_stats": {"logon_mean": 1.5, "logon_std": 0.3, "device_mean": 0.0, "device_std": 0.1, "file_mean": 1.5, "file_std": 0.8, "email_mean": 18.0, "email_std": 4.0, "logon_ah_mean": 0.0, "logon_ah_std": 0.1, "device_ah_mean": 0.0, "device_ah_std": 0.1, "file_ah_mean": 0.0, "file_ah_std": 0.1, "email_ah_mean": 0.0, "email_ah_std": 0.2, "total_mean": 21.0, "total_std": 4.0, "first_hour_mean": 9.0, "first_hour_std": 0.3}},

    # === Legal & Compliance (4 users) ===
    {"user_id": "LEG-001", "name": "Victoria Marsh", "department": "Legal", "role": "General Counsel", "email": "victoria.marsh@technova.io", "assigned_pc": "PC-LEG-01", "manager": "Raymond Price", "location": "Building B, Floor 3", "employment_type": "Full-Time", "join_date": "2018-11-01", "normal_hours": "08:30–17:30",
     "baseline_stats": {"logon_mean": 2.0, "logon_std": 0.3, "device_mean": 0.0, "device_std": 0.1, "file_mean": 6.0, "file_std": 2.5, "email_mean": 18.0, "email_std": 4.0, "logon_ah_mean": 0.0, "logon_ah_std": 0.1, "device_ah_mean": 0.0, "device_ah_std": 0.1, "file_ah_mean": 0.0, "file_ah_std": 0.1, "email_ah_mean": 0.1, "email_ah_std": 0.3, "total_mean": 26.0, "total_std": 5.5, "first_hour_mean": 8.5, "first_hour_std": 0.4}},
    {"user_id": "LEG-002", "name": "Simon Barrett", "department": "Legal", "role": "Compliance Officer", "email": "simon.barrett@technova.io", "assigned_pc": "PC-LEG-02", "manager": "Victoria Marsh", "location": "Building B, Floor 3", "employment_type": "Full-Time", "join_date": "2021-05-15", "normal_hours": "09:00–18:00",
     "baseline_stats": {"logon_mean": 2.0, "logon_std": 0.4, "device_mean": 0.0, "device_std": 0.1, "file_mean": 5.0, "file_std": 2.0, "email_mean": 14.0, "email_std": 3.5, "logon_ah_mean": 0.0, "logon_ah_std": 0.1, "device_ah_mean": 0.0, "device_ah_std": 0.1, "file_ah_mean": 0.0, "file_ah_std": 0.1, "email_ah_mean": 0.0, "email_ah_std": 0.2, "total_mean": 21.0, "total_std": 4.5, "first_hour_mean": 9.0, "first_hour_std": 0.3}},

    # === Executive (3 users) ===
    {"user_id": "EXC-001", "name": "Raymond Price", "department": "Executive", "role": "Chief Executive Officer", "email": "raymond.price@technova.io", "assigned_pc": "PC-EXC-01", "manager": "Board of Directors", "location": "Building A, Floor 5", "employment_type": "Full-Time", "join_date": "2015-01-01", "normal_hours": "07:30–19:00",
     "baseline_stats": {"logon_mean": 2.0, "logon_std": 0.5, "device_mean": 0.0, "device_std": 0.1, "file_mean": 3.0, "file_std": 1.5, "email_mean": 30.0, "email_std": 8.0, "logon_ah_mean": 0.1, "logon_ah_std": 0.3, "device_ah_mean": 0.0, "device_ah_std": 0.1, "file_ah_mean": 0.0, "file_ah_std": 0.2, "email_ah_mean": 0.3, "email_ah_std": 0.5, "total_mean": 35.0, "total_std": 8.0, "first_hour_mean": 7.5, "first_hour_std": 0.8}},
    {"user_id": "EXC-002", "name": "Laura Chen", "department": "Executive", "role": "Chief Technology Officer", "email": "laura.chen@technova.io", "assigned_pc": "PC-EXC-02", "manager": "Raymond Price", "location": "Building A, Floor 5", "employment_type": "Full-Time", "join_date": "2016-06-01", "normal_hours": "08:00–18:00",
     "baseline_stats": {"logon_mean": 2.5, "logon_std": 0.6, "device_mean": 0.0, "device_std": 0.1, "file_mean": 5.0, "file_std": 2.5, "email_mean": 22.0, "email_std": 5.0, "logon_ah_mean": 0.1, "logon_ah_std": 0.2, "device_ah_mean": 0.0, "device_ah_std": 0.1, "file_ah_mean": 0.0, "file_ah_std": 0.2, "email_ah_mean": 0.2, "email_ah_std": 0.4, "total_mean": 29.5, "total_std": 6.0, "first_hour_mean": 8.0, "first_hour_std": 0.5}},
    {"user_id": "EXC-003", "name": "Mark Davidson", "department": "Executive", "role": "Chief Information Security Officer", "email": "mark.davidson@technova.io", "assigned_pc": "PC-EXC-03", "manager": "Raymond Price", "location": "Building A, Floor 5", "employment_type": "Full-Time", "join_date": "2017-09-15", "normal_hours": "08:00–18:00",
     "baseline_stats": {"logon_mean": 3.0, "logon_std": 0.8, "device_mean": 0.1, "device_std": 0.3, "file_mean": 4.0, "file_std": 2.0, "email_mean": 18.0, "email_std": 4.0, "logon_ah_mean": 0.1, "logon_ah_std": 0.3, "device_ah_mean": 0.0, "device_ah_std": 0.1, "file_ah_mean": 0.1, "file_ah_std": 0.3, "email_ah_mean": 0.2, "email_ah_std": 0.5, "total_mean": 25.0, "total_std": 5.5, "first_hour_mean": 8.0, "first_hour_std": 0.5}},
    {"user_id": "ENG-013", "name": "Marcus Lennox", "department": "Engineering", "role": "Senior Systems Engineer", "email": "marcus.lennox@technova.io", "assigned_pc": "PC-ENG-13", "manager": "David Chen", "location": "Building A, Floor 4", "employment_type": "Full-Time", "join_date": "2020-03-02", "normal_hours": "09:00–18:00",
     "baseline_stats": {"logon_mean": 2.0, "logon_std": 0.7, "device_mean": 0.1, "device_std": 0.2, "file_mean": 8.0, "file_std": 3.0, "email_mean": 10.0, "email_std": 3.2, "logon_ah_mean": 0.2, "logon_ah_std": 0.4, "device_ah_mean": 0.2, "device_ah_std": 0.3, "file_ah_mean": 0.4, "file_ah_std": 0.7, "email_ah_mean": 0.3, "email_ah_std": 0.5, "total_mean": 21.0, "total_std": 6.0, "first_hour_mean": 9.0, "first_hour_std": 0.5}},
]

CRITICAL_RISK_USER_IDS = {"ENG-013", "FIN-006", "HR-004"}


def seed_synthetic_enterprise(db: Session):
    """
    Seeds the SQLite database with TechNova synthetic enterprise users if empty.
    """
    for user_data in SYNTHETIC_USERS:
        existing = db.query(User).filter(User.user_id == user_data["user_id"]).first()
        if existing:
            if existing.user_id in CRITICAL_RISK_USER_IDS and existing.risk_score:
                existing.risk_score.current_risk_score = 82
                existing.risk_score.current_risk_tier = "CRITICAL"
                existing.risk_score.ml_probability = 0.78
                existing.risk_score.explanation = (
                    "Elevated risk pattern observed: after-hours access, unusual file movement, "
                    "and deviation beyond modeled baseline."
                )
            continue

        if not existing:
            user = User(
                user_id=user_data["user_id"],
                name=user_data["name"],
                department=user_data["department"],
                role=user_data["role"],
                email=user_data["email"],
                assigned_pc=user_data["assigned_pc"],
                is_synthetic=True,
                baseline_stats=json.dumps(user_data["baseline_stats"]),
                manager=user_data.get("manager", ""),
                location=user_data.get("location", ""),
                employment_type=user_data.get("employment_type", "Full-Time"),
                join_date=user_data.get("join_date", ""),
                normal_hours=user_data.get("normal_hours", "09:00–18:00"),
                account_status="ACTIVE",
            )
            db.add(user)
            db.flush()

            # Initialize baseline risk score; a few synthetic users are intentionally elevated to model higher-risk behavior.
            initial_score = 82 if user.user_id in CRITICAL_RISK_USER_IDS else 12
            initial_tier = "CRITICAL" if user.user_id in CRITICAL_RISK_USER_IDS else "LOW"
            initial_prob = 0.78 if user.user_id in CRITICAL_RISK_USER_IDS else 0.015
            initial_explanation = (
                "Elevated risk pattern observed: after-hours access, unusual file movement, and deviation beyond modeled baseline."
                if user.user_id in CRITICAL_RISK_USER_IDS
                else "Normal baseline behavior observed. Routine activity within expected hours."
            )

            risk = RiskScore(
                user_id=user.user_id,
                current_risk_score=initial_score,
                current_risk_tier=initial_tier,
                ml_probability=initial_prob,
                deviation_score=0.0,
                heuristic_score=0.0,
                top_factors=json.dumps([]),
                explanation=initial_explanation,
            )
            db.add(risk)

    db.commit()

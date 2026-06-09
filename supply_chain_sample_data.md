# Global Supply Chain & Cargo Security Governance Sample Data

This document contains a completely new and distinct set of sample registry assets for testing the GuardianIQ platform. It uses a **Logistics and Cargo Security Governance** domain to verify workflows, AI agents, tools, policies, and human approvals.

---

## 1. Department
* **Department Code:** `LOGISTICS_SECURITY`
* **Department Name:** `Global Logistics Security & Cargo Operations`
* **Status:** `ACTIVE`
* **Metadata:**
  ```json
  {
    "primary_hub": "Port of Rotterdam Terminal 4",
    "cost_center": "LOG-SEC-8080"
  }
  ```

---

## 2. Role
* **Role Code:** `CARGO_COMPLIANCE_OFFICER`
* **Role Name:** `Cargo Compliance & Security Auditor`
* **Role Type:** `BUSINESS`
* **Permissions:**
  ```json
  {
    "verify_manifest": true,
    "lock_containers": true,
    "authorize_dispatch": true
  }
  ```
* **Status:** `ACTIVE`

---

## 3. User
* **Email:** `elena.rostova@guardianiq.com`
* **Full Name:** `Elena Rostova`
* **Department:** `Global Logistics Security & Cargo Operations`
* **Role:** `Cargo Compliance & Security Auditor`
* **Approval Limit Level:** `L3` (High Authorization)
* **Status:** `ACTIVE`

---

## 4. Data Source
* **Source Code:** `CARGO_RFID_IOT_STREAM`
* **Source Name:** `Global Cargo RFID & IoT Sensor Stream`
* **Source Type:** `STREAM`
* **Owner:** `Elena Rostova`
* **Department:** `Global Logistics Security & Cargo Operations`
* **Classification:** `CONFIDENTIAL`
* **Sensitivity Level:** `HIGH`
* **Region:** `eu-central-1`
* **Contains PII:** `False`
* **Retention Policy:** `LOGISTICS_standard_3_YEARS`
* **Connection Reference:** `kafka://iot-broker.rotterdam.internal:9092/cargo-sensors`
* **Status:** `ACTIVE`
* **Metadata:**
  ```json
  {
    "encryption_level": "AES-256",
    "last_audit_run": "2026-06-05"
  }
  ```

---

## 5. AI Model
* **Model Code:** `ROUTE_ANOMALY_DETECTOR`
* **Model Name:** `Logistics Route Anomaly Detection Model`
* **Model Type:** `ANOMALY_DETECTION`
* **Version:** `v1.4.0`
* **Purpose:** `Analyzes real-time cargo GPS and temperature streams to flag smuggling routes or unscheduled stops.`
* **Owner:** `Elena Rostova`
* **Department:** `Global Logistics Security & Cargo Operations`
* **Risk Level:** `HIGH`
* **Deployment Environment:** `AWS_EKS_LOGISTICS`
* **Status:** `ACTIVE`
* **Metadata:**
  ```json
  {
    "base_architecture": "Isolation Forest & LSTM",
    "false_positive_rate": 0.012
  }
  ```

---

## 6. AI Agent
* **Agent Code:** `GPS_COMPLIANCE_AGENT`
* **Agent Name:** `Autonomous Cargo GPS Scanner Agent`
* **Agent Type:** `MONITORING`
* **Description:** `Autonomous monitor scanning route data streams, correlating with registered logistics manifests to calculate deviation alerts.`
* **Owner:** `Elena Rostova`
* **Department:** `Global Logistics Security & Cargo Operations`
* **Execution Mode:** `SEMI_AUTONOMOUS`
* **Risk Level:** `MEDIUM`
* **Confidence Threshold:** `85.0`
* **Status:** `ACTIVE`
* **Capabilities:**
  ```json
  {
    "supported_hubs": ["Rotterdam", "Singapore", "New Jersey"],
    "supported_transit_modes": ["Maritime", "Overland"]
  }
  ```
* **Metadata:**
  ```json
  {
    "alert_channel": "#cargo-security-alerts"
  }
  ```

---

## 7. Tool
* **Tool Code:** `PORT_AUTHORITY_NOTIFIER`
* **Tool Name:** `Port Authority Incident Dispatcher Tool`
* **Tool Category:** `API`
* **Access Mode:** `EXECUTE`
* **Owner:** `Elena Rostova`
* **Sensitivity Level:** `HIGH`
* **Allowed Operations:**
  ```json
  [
    "send_customs_hold_request",
    "dispatch_security_unit",
    "log_lockdown_status"
  ]
  ```
* **Endpoint Reference:** `https://dispatch.portauthority.internal/api/v1/incidents`
* **Status:** `ACTIVE`
* **Metadata:**
  ```json
  {
    "api_version": "v1.2",
    "auth_type": "OAuth2"
  }
  ```

---

## 8. Workflow
* **Workflow Code:** `HIGH_VALUE_CARGO_INTEGRITY`
* **Workflow Name:** `High-Value Cargo Transit Integrity Audit`
* **Workflow Type:** `RISK_REVIEW`
* **Department:** `Global Logistics Security & Cargo Operations`
* **Owner:** `Elena Rostova`
* **Description:** `Security and compliance validation pipeline for auditing transit logs, executing lock integrity calls, and requesting dispatch holds.`
* **Approval Required:** `True`
* **Business Criticality:** `CRITICAL`
* **Status:** `ACTIVE`
* **Steps Layout:**
  1. **AI Agent Step (`STEP`):** `Scan GPS Coordinates`
     * *Description:* Autonomous monitor scans Kafka stream coordinates.
  2. **Evaluation Step (`EVALUATION`):** `Calculate Route Deviation Risk`
     * *Description:* Ensure GPS coordinates match the manifest path within tolerances.
  3. **Human Approval Step (`APPROVAL`):** `Port Security Dispatch Authorization`
     * *Description:* Manual confirmation needed before alert escalates to Port Authorities.
  4. **Tool Call Step (`TOOL`):** `Trigger Customs Hold`
     * *Description:* Automated call to request container hold at port of arrival.

* **Metadata:**
  ```json
  {
    "sla_minutes": 15
  }
  ```

---

## 9. Relationships
* **Agent (`GPS_COMPLIANCE_AGENT`)** $\rightarrow$ `USES` $\rightarrow$ **Model (`ROUTE_ANOMALY_DETECTOR`)**
* **Agent (`GPS_COMPLIANCE_AGENT`)** $\rightarrow$ `USES` $\rightarrow$ **Tool (`PORT_AUTHORITY_NOTIFIER`)**
* **Workflow (`HIGH_VALUE_CARGO_INTEGRITY`)** $\rightarrow$ `USES` $\rightarrow$ **Data Source (`CARGO_RFID_IOT_STREAM`)**

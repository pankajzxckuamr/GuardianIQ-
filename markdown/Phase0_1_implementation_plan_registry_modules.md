# Implementation Plan - Registry Modules Analysis and Sample Data Creation

This plan covers the analysis of the GuardianIQ Registry modules, listing all the required and optional fields for entity creation, proposing a realistic sample dataset representing a Clinical Analytics & Triage scenario, and outlining the testing plan to register these entities in the database without deleting them so they are visible on the frontend.

## User Review Required

> [!IMPORTANT]
> The proposed sample data is modeled around a cohesive clinical care domain (**Clinical Analytics & CareShield Integration**).
> To persist this data in the database, we will dynamically resolve dependencies (e.g., using the ID of the newly created Department to create the User and Data Source).
> Unlike normal integration tests, **we will NOT clean up or delete these entities** after the tests run, so they can be viewed directly on the frontend dashboard.

## Open Questions

There are no open questions. Once you approve this plan, I will proceed to write the execution script and run the verification tests.

---

## Registry Modules and Fields Analysis

Here is a detailed breakdown of each registry module, identifying all the fields required when creating new entries.

### 1. Department (`RegistryDepartment`)
*   **Endpoint**: `POST /api/registry/departments`
*   **Fields**:
    *   `department_code` (String, **Required**, Unique): Unique identifier for the department (e.g., `SEC_OPS`).
    *   `department_name` (String, **Required**): Human-readable name of the department.
    *   `parent_department_id` (UUID, Optional): Parent department ID.
    *   `business_owner_user_id` (UUID, Optional): ID of the Guardian User who owns the department's business function.
    *   `escalation_owner_user_id` (UUID, Optional): ID of the Guardian User for escalation.
    *   `status` (Enum, Optional): Default is `ACTIVE`.
    *   `metadata_json` (JSON Dict, Optional): Extra schema metadata.

### 2. Role (`RegistryRole`)
*   **Endpoint**: `POST /api/registry/roles`
*   **Fields**:
    *   `role_code` (String, **Required**, Unique): Unique code for the role (e.g., `CLINICAL_AUDITOR`).
    *   `role_name` (String, **Required**): Human-readable name.
    *   `role_type` (String, **Required**): Typically `BUSINESS` or `SYSTEM`.
    *   `permissions_json` (JSON Dict, Optional): Default is `{}`.
    *   `status` (Enum, Optional): Default is `ACTIVE`.

### 3. Guardian User (`GuardianUser`)
*   **Endpoint**: `POST /api/registry/users`
*   **Fields**:
    *   `email` (String, **Required**, Unique, min length 5): User's primary email.
    *   `full_name` (String, **Required**): User's full name.
    *   `department_id` (UUID, Optional): Department references.
    *   `role_id` (UUID, Optional): Role references.
    *   `approval_limit_level` (String, Optional): Level for approvals (e.g. `L1`, `L2`).
    *   `status` (Enum, Optional): Default is `ACTIVE`.

### 4. Data Source (`RegistryDataSource`)
*   **Endpoint**: `POST /api/registry/data-sources`
*   **Fields**:
    *   `source_code` (String, **Required**, Unique): Unique code identifier.
    *   `source_name` (String, **Required**): Human-readable name.
    *   `source_type` (Enum, **Required**): Values: `DATABASE`, `API`, `FILE`, `CRM`, `ERP`, `DATA_LAKE`, `EMAIL`, `WEBFORM`.
    *   `owner_user_id` (UUID, Optional): Owner ID.
    *   `department_id` (UUID, Optional): Department ID.
    *   `classification` (Enum, **Required**): Values: `PUBLIC`, `INTERNAL`, `CONFIDENTIAL`, `RESTRICTED`.
    *   `sensitivity_level` (Enum, **Required**): Values: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.
    *   `region` (String, Optional): Hosting region (e.g., `us-east-2`).
    *   `contains_pii` (Boolean, Optional): Defaults to `False`.
    *   `retention_policy` (String, Optional): Retention strategy text.
    *   `connection_reference` (String, Optional): Reference string (no secret patterns).
    *   `status` (Enum, Optional): Default is `ACTIVE`.
    *   `metadata_json` (JSON Dict, Optional): Arbitrary metadata.

### 5. AI Model (`RegistryAIModel`)
*   **Endpoint**: `POST /api/registry/models`
*   **Fields**:
    *   `model_code` (String, **Required**, Unique): Unique code identifier.
    *   `model_name` (String, **Required**): Human-readable name.
    *   `model_type` (Enum, **Required**): Values: `LLM`, `ML`, `CLASSIFIER`, `EMBEDDING`, `RULE_BASED`, `FORECASTING`, `OPTIMIZATION`.
    *   `purpose` (String, **Required**): Statement of purpose.
    *   `risk_level` (String, **Required**): Values: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.
    *   `provider_id` (UUID, Optional): Model provider references.
    *   `version` (String, Optional): Version tag (e.g. `v1.0.0`).
    *   `owner_user_id` (UUID, Optional): Owner ID.
    *   `department_id` (UUID, Optional): Department ID.
    *   `deployment_environment` (String, Optional): Environment label (e.g. `staging`).
    *   `status` (Enum, Optional): Defaults to `DRAFT`.
    *   `metadata_json` (JSON Dict, Optional): Arbitrary metadata.

### 6. AI Agent (`RegistryAIAgent`)
*   **Endpoint**: `POST /api/registry/agents`
*   **Fields**:
    *   `agent_code` (String, **Required**, Unique): Unique code identifier.
    *   `agent_name` (String, **Required**): Human-readable name.
    *   `agent_type` (Enum, **Required**): Values: `RECOMMENDATION`, `TRIAGE`, `EXTRACTION`, `EXECUTION`, `MONITORING`.
    *   `execution_mode` (Enum, **Required**): Values: `READ_ONLY`, `RECOMMEND_ONLY`, `APPROVAL_REQUIRED`, `LIMITED_EXECUTION`, `BLOCKED`.
    *   `risk_level` (String, **Required**): Values: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.
    *   `description` (String, Optional): Details.
    *   `owner_user_id` (UUID, Optional): Owner ID.
    *   `department_id` (UUID, Optional): Department ID.
    *   `confidence_threshold` (Float, Optional): Float value between `0` and `100`.
    *   `status` (Enum, Optional): Defaults to `DRAFT`.
    *   `capabilities_json` (JSON Dict, Optional): Arbitrary capabilities.
    *   `metadata_json` (JSON Dict, Optional): Arbitrary metadata.

### 7. Tool (`RegistryTool`)
*   **Endpoint**: `POST /api/registry/tools`
*   **Fields**:
    *   `tool_code` (String, **Required**, Unique): Unique code identifier.
    *   `tool_name` (String, **Required**): Human-readable name.
    *   `tool_category` (Enum, **Required**): Values: `ERP`, `CRM`, `EMAIL`, `TICKETING`, `DATABASE`, `LLM`, `FILE`, `WEBHOOK`.
    *   `access_mode` (Enum, **Required**): Values: `READ_ONLY`, `WRITE`, `EXECUTE`, `ADMIN`.
    *   `sensitivity_level` (String, **Required**): Values: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.
    *   `owner_user_id` (UUID, Optional): Owner ID.
    *   `allowed_operations_json` (List of Strings, Optional): e.g. `["read", "publish"]`.
    *   `endpoint_reference` (String, Optional): Webhook URL reference (no secrets).
    *   `status` (Enum, Optional): Defaults to `ACTIVE`.
    *   `metadata_json` (JSON Dict, Optional): Arbitrary metadata.

### 8. Workflow (`RegistryWorkflow`)
*   **Endpoint**: `POST /api/registry/workflows`
*   **Fields**:
    *   `workflow_code` (String, **Required**, Unique): Unique code identifier.
    *   `workflow_name` (String, **Required**): Human-readable name.
    *   `workflow_type` (Enum, **Required**): Values: `ENQUIRY`, `APPROVAL`, `CUSTOMER_SIGNAL`, `RISK_REVIEW`, `OPERATIONAL_ACTION`.
    *   `business_criticality` (String, **Required**): Values: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.
    *   `department_id` (UUID, Optional): Department ID.
    *   `owner_user_id` (UUID, Optional): Owner ID.
    *   `description` (String, Optional): Details.
    *   `approval_required` (Boolean, Optional): Defaults to `False`.
    *   `status` (Enum, Optional): Defaults to `DRAFT`.
    *   `steps_json` (List of Dicts, Optional): Each step must contain `step_name`.
    *   `metadata_json` (JSON Dict, Optional): Arbitrary metadata.

### 9. Relationship (`RegistryRelationship`)
*   **Endpoint**: `POST /api/registry/relationships`
*   **Fields**:
    *   `source_entity_type` (String, **Required**): Type of source entity.
    *   `source_entity_id` (UUID, **Required**): ID of source entity.
    *   `relationship_type` (Enum, **Required**): Values: `USES`, `OWNS`, `EXECUTES`, `APPROVES`, `GOVERNED_BY`, `CONNECTED_TO`, `CONSUMES`, `PRODUCES`.
    *   `target_entity_type` (String, **Required**): Type of target entity.
    *   `target_entity_id` (UUID, **Required**): ID of target entity.
    *   `metadata_json` (JSON Dict, Optional): Arbitrary metadata.

---

## Proposed Sample Data

Here is the realistic clinical triage dataset we will create:

### 1. Department
*   `department_code`: `"CLINICAL_ANALYTICS"`
*   `department_name`: `"Clinical Analytics & Insights"`
*   `status`: `"ACTIVE"`
*   `metadata_json`: `{"hospital_branch": "CareShield Main Campus", "cost_center": "CC-9012"}`

### 2. Role
*   `role_code`: `"CLINICAL_DATA_ANALYST"`
*   `role_name`: `"Clinical Data Analyst"`
*   `role_type`: `"BUSINESS"`
*   `permissions_json`: `{"view_patient_data": true, "run_risk_analysis": true}`
*   `status`: `"ACTIVE"`

### 3. Guardian User
*   `email`: `"turing.alan@careshield.com"`
*   `full_name`: `"Dr. Alan Turing"`
*   `department_id`: *(Dynamic Department ID)*
*   `role_id`: *(Dynamic Role ID)*
*   `approval_limit_level`: `"L2"`
*   `status`: `"ACTIVE"`

### 4. Data Source
*   `source_code`: `"CLINICAL_EHR_REPLICA"`
*   `source_name`: `"CareShield EHR Read Replica"`
*   `source_type`: `"DATABASE"`
*   `owner_user_id`: *(Dynamic User ID)*
*   `department_id`: *(Dynamic Department ID)*
*   `classification`: `"RESTRICTED"`
*   `sensitivity_level`: `"CRITICAL"`
*   `region`: `"us-east-2"`
*   `contains_pii`: `True`
*   `retention_policy`: `"HIPAA_7_YEARS"`
*   `connection_reference`: `"postgresql://ehr-read-replica.careshield.internal:5432/patient_records"`
*   `status`: `"ACTIVE"`
*   `metadata_json`: `{"compliance_tags": ["HIPAA", "HITRUST"], "last_sync": "2026-06-04"}`

### 5. AI Model
*   `model_code`: `"CLINICAL_NLP_DIAGNOSIS"`
*   `model_name`: `"Clinical NLP Diagnosis Classifier"`
*   `model_type`: `"CLASSIFIER"`
*   `version`: `"v3.1.2"`
*   `purpose`: `"Extracting clinical entities and diagnostics from unstructured physician notes."`
*   `owner_user_id`: *(Dynamic User ID)*
*   `department_id`: *(Dynamic Department ID)*
*   `risk_level`: `"HIGH"`
*   `deployment_environment`: `"K8S_CLINICAL_PROD"`
*   `status`: `"ACTIVE"`
*   `metadata_json`: `{"base_model": "Llama-3-8B-Instruct", "f1_score": 0.945}`

### 6. AI Agent
*   `agent_code`: `"CLINICAL_TRIAGE_BOT"`
*   `agent_name`: `"Clinical Triage Recommendation Agent"`
*   `agent_type`: `"TRIAGE"`
*   `description`: `"Recommends department assignment and urgency triage level based on EHR notes."`
*   `owner_user_id`: *(Dynamic User ID)*
*   `department_id`: *(Dynamic Department ID)*
*   `execution_mode`: `"RECOMMEND_ONLY"`
*   `risk_level`: `"HIGH"`
*   `confidence_threshold`: `90.0`
*   `status`: `"ACTIVE"`
*   `capabilities_json`: `{"supported_specialties": ["Cardiology", "Neurology", "General Medicine"]}`
*   `metadata_json`: `{"audit_frequency": "weekly"}`

### 7. Tool
*   `tool_code`: `"CARESHIELD_HL7_PUBLISHER"`
*   `tool_name`: `"CareShield HL7 Event Publisher Tool"`
*   `tool_category`: `"WEBHOOK"`
*   `access_mode`: `"EXECUTE"`
*   `owner_user_id`: *(Dynamic User ID)*
*   `sensitivity_level`: `"HIGH"`
*   `allowed_operations_json`: `["publish_hl7_event", "validate_schema"]`
*   `endpoint_reference`: `"https://hl7.careshield.internal/v1/publish"`
*   `status`: `"ACTIVE"`
*   `metadata_json`: `{"payload_format": "HL7_v2"}`

### 8. Workflow
*   `workflow_code`: `"CLINICAL_REFERRAL_TRIAGE"`
*   `workflow_name`: `"Clinical Patient Referral Triage Workflow"`
*   `workflow_type`: `"RISK_REVIEW"`
*   `department_id`: *(Dynamic Department ID)*
*   `owner_user_id`: *(Dynamic User ID)*
*   `description`: `"Automated processing pipeline for classifying clinical patient referral files."`
*   `approval_required`: `True`
*   `business_criticality`: `"HIGH"`
*   `status`: `"ACTIVE"`
*   `steps_json`: `[{"step_name": "Read EHR File", "description": "Triggered when new referral is added to EHR database"}, {"step_name": "Extract Symptoms", "description": "Run Clinical NLP Classifier on the notes"}, {"step_name": "Calculate Triage Level", "description": "Clinical Triage Agent recommends triage level"}, {"step_name": "Publish HL7 Event", "description": "Publish formatted event to CareShield HL7 server for department scheduling"}]`
*   `metadata_json`: `{"sla_hours": 4}`

### 9. Relationships
*   **Relationship 1**: `AGENT` (`CLINICAL_TRIAGE_BOT`) $\rightarrow$ `USES` $\rightarrow$ `MODEL` (`CLINICAL_NLP_DIAGNOSIS`)
*   **Relationship 2**: `AGENT` (`CLINICAL_TRIAGE_BOT`) $\rightarrow$ `USES` $\rightarrow$ `TOOL` (`CARESHIELD_HL7_PUBLISHER`)
*   **Relationship 3**: `WORKFLOW` (`CLINICAL_REFERRAL_TRIAGE`) $\rightarrow$ `USES` $\rightarrow$ `DATA_SOURCE` (`CLINICAL_EHR_REPLICA`)

---

## Verification Plan

We will create a python script `backend/app/tests/create_sample_registry_data.py` to create these entities using API endpoints via `FastAPI TestClient`.

### Automated Tests
To execute the creation script, run:
```bash
backend\venv\Scripts\python backend/app/tests/create_sample_registry_data.py
```
This script will:
1. Authenticate as `admin@guardianiq.com` to fetch the Bearer token.
2. Check if `CLINICAL_ANALYTICS` already exists; if not, create it.
3. Check if `CLINICAL_DATA_ANALYST` role already exists; if not, create it.
4. Check if `turing.alan@careshield.com` user already exists; if not, create it.
5. Sequentially create the Data Source, AI Model, AI Agent, Tool, and Workflow.
6. Create the three required Relationships.
7. Print out a success report mapping each created entity code to its newly created UUID.
8. **Crucially, it will commit the changes and will NOT clean them up or delete them.**

### Manual Verification
1. Access the web frontend at `http://localhost:5173`.
2. Navigate to the Registry tables (AI Models, AI Agents, Tools, Workflows, Data Sources, Departments, Roles, Users).
3. Confirm that the new entries are visible, with correct nomenclature, attributes, and relationships.

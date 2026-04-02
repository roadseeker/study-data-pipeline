# Data Pipeline and AI/ML Consulting Commercialization Strategy Report

**Date**: March 30, 2026  
**Version**: v2.0  
**Format**: Independent Consulting (Solo Founder)

---

## Table of Contents

1. Business Overview
2. Market Status and Size
3. Definition of the Two Consulting Domains
4. Technology Stack and Core Capabilities
5. Competitive Advantage Analysis
6. Commercialization Roadmap
7. Solo Operating Strategy (First Two Years of the Business)
8. Preparation Checklist
9. Risks and Response Strategy
10. Capability-Building Learning Schedule
11. Revenue Targets and Financial Plan
12. Conclusion

---

## 1. Business Overview

### Business Concept

This is a full-stack data and AI consulting business in which a single consultant designs both data pipeline implementation consulting and AI/ML adoption consulting. The two domains are not separate. AI does not work without data pipelines, and pipelines alone generate limited business value. The core differentiator is the ability to understand and design this connection, which remains extremely rare in the Korean market.

### Business Definition

- **Domain A**: Apache open-source-based data pipeline consulting
- **Domain B**: ML model design, implementation, deployment, and LLM/RAG adoption consulting
- **Target customers**: Mid-sized companies in finance, fintech, and manufacturing (with legacy systems and limited in-house AI capabilities)
- **Differentiator**: Cost reduction through open source plus the ability to design everything from data pipelines to AI as a single integrated architecture
- **Operating model**: Solo operation during the first two years after founding, followed by later team expansion

### Business Background

The year 2026 marks a turning point in which AI adoption moves beyond experimentation and becomes part of enterprise infrastructure. At the same time, many AI projects are still failing to deliver meaningful outcomes, and the primary cause is inadequate data infrastructure. When companies analyze why their AI initiatives failed, the conclusion often comes back to data pipeline problems. This structural demand is the basis for entering the market with this business.

---

## 2. Market Status and Size

### Domestic Data Industry Market

| Category | Size | Notes |
|------|------|------|
| Total data industry (2024E) | KRW 30.7462 trillion | 5.8% YoY growth |
| **Data implementation and consulting services** | **KRW 10.5676 trillion** | **34.4% of total market, direct target market** |
| Data sales and provision services | KRW 14.6443 trillion | 47.6% of total market |
| Data processing and management solutions | KRW 5.5343 trillion | 18.0% of total market |
| Data pipeline-focused SAM | Approx. KRW 2.1 trillion | Estimate for pure consulting related to pipelines |
| Realistic initial SOM target | KRW 10 to 30 billion | Apache open-source specialization, first 3 to 5 years |

Source: Ministry of Science and ICT and Korea Data Agency, *2024 Data Industry Survey*

### Market Growth

- Domestic data industry CAGR (2019 to 2023): **21.2%**
- Forecast domestic data industry size in 2028: **KRW 49 trillion** (assuming 12.7% CAGR)
- Global data pipeline market (2024 to 2032): USD 10 billion with **19.9% CAGR**

### Demand Signals: 2026 Survey of IT Priorities Among Korean Enterprises

| Item | Response Rate | Meaning |
|------|--------|------|
| Generative AI identified as the top priority | 63% (No. 1) | Clear demand |
| AI/ML and automation identified as a priority | 40% (No. 3) | Sustained demand |
| AI and data talent shortage identified as a challenge | 40% (No. 2) | **External support needed** |
| Companies with AI project execution capability | **7%** | **93% capability gap** |
| Plan to use external experts to close the capability gap | 65% | **Direct consulting demand** |

Source: CIO Korea, *2026 IT Outlook Survey* (October to November 2025, 884 respondents)

### Market Structure Assessment

According to Deloitte's 2026 TMT outlook, the focus of AI adoption is shifting from "what can we build?" to "how can we apply and operate it in the real business?" This is a moment when design and operational capability become more important than raw implementation capability, creating a favorable environment for independent consultants.

---

## 3. Definition of the Two Consulting Domains

### Domain A: Data Pipeline Consulting

**Core value proposition**: Transform data locked inside legacy RDBMS platforms into a modern architecture capable of real-time processing. Deliver performance equivalent to commercial tools without licensing costs by using open-source technologies.

**Primary services**:

- Data pipeline architecture design and consulting
- Implementation of real-time data ingestion, transformation, and storage systems
- Legacy RDBMS to modern data platform migration projects
- Data orchestration and monitoring system design
- Data governance and quality management framework design

**Why customers want migration**:

- Need to reduce high Oracle and SQL Server licensing costs
- Existing RDBMS scale limits at the TB level, while future requirements may exceed PB scale
- Need to modernize data infrastructure for AI adoption
- Need a unified platform that can handle unstructured data such as logs, JSON, and images

**Expected pricing**:

| Service Type | Price Range | Duration |
|------------|----------|------|
| Architecture design consulting | KRW 5 to 30 million | 1 to 2 months |
| Pipeline implementation project | KRW 30 million to 100 million | 2 to 4 months |
| Operations and maintenance contract | KRW 2 to 5 million per month | Ongoing |

### Domain B: AI and ML Consulting

**Core value proposition**: Full-stack design that places AI on top of data pipelines. Serve as the practical starting point for companies that want to adopt AI but do not know where to begin.

**Primary services**:

- AI adoption strategy and roadmap design
- Consulting for ML model selection, training, evaluation, and deployment
- Experiment tracking and model version management system design
- LLM/RAG-based internal document Q&A system implementation
- Model retraining automation pipeline design
- AI performance metric and KPI design

**Representative application scenarios by model type**:

| Model Type | Representative Scenario | Expected Effect |
|-----------|-------------|----------|
| Classification | Fraud detection, churn prediction | Loss reduction, proactive response |
| Regression | Sales and demand forecasting, pricing | Better decision accuracy |
| Clustering | Customer segmentation, anomaly pattern discovery | Targeted marketing, risk analysis |
| Deep learning | Image quality inspection, document classification | Automation, cost reduction |
| LLM/RAG | Internal document Q&A, report automation | Productivity improvement |
| Reinforcement learning | Process optimization, recommendation systems | Operational efficiency gains |

**Expected pricing**:

| Service Type | Price Range | Duration |
|------------|----------|------|
| AI adoption strategy consulting | KRW 10 to 50 million | 1 to 3 months |
| Model implementation project | KRW 50 million to 300 million | 3 to 6 months |
| Retraining and operations contract | KRW 3 to 8 million per month | Ongoing |

### Connection Between the Two Domains

Data pipeline consulting is the prerequisite for AI consulting. The ideal customer lifetime value structure is to first build the customer's data infrastructure through a pipeline project and then naturally expand into AI model adoption on top of it.

```text
Pipeline architecture consulting
        ↓
Pipeline implementation project
        ↓
Data quality and governance setup
        ↓
AI and ML adoption strategy
        ↓
Model implementation and deployment
        ↓
Operations and retraining maintenance (recurring revenue)
```

---

## 4. Technology Stack and Core Capabilities

### Data Pipeline Domain

| Layer | Tool | Role |
|------|------|------|
| Ingest | Apache Kafka, Apache NiFi, Kafka Connect | Real-time and batch data ingestion |
| Transform | Apache Flink, Apache Spark, dbt | Real-time processing, feature computation, ETL |
| Store | HDFS, Amazon S3, Apache Iceberg | Data lake and warehouse |
| Orchestration | Apache Airflow | Scheduling, monitoring, retries |
| Migration specialized | Spark JDBC, Debezium (CDC) | RDBMS data migration |
| Feature store | Redis, PostgreSQL | Real-time and batch feature management |

### Technology Status Review (`2026-04-01`)

| Technology | Usage Context | Status Review | Notes |
|------|-----------|-----------|------|
| Apache Kafka | Event ingestion and delivery | Active open source | Apache project with ongoing releases |
| Apache NiFi | Multi-source ingestion | Active open source | Apache project, 2.x line can be operated |
| Kafka Connect | CDC and connector runtime | Active open source | Core component in Kafka ecosystem |
| Apache Flink | Real-time transformation | Active open source | Stream processing engine under continuous development |
| Apache Spark | Batch ETL and JDBC migration | Active open source | Ongoing releases in the 4.x line |
| Apache Airflow | Orchestration | Active open source | Ongoing development in the 3.x line |
| Debezium | CDC | Active open source | CDC project built on Kafka Connect |
| Delta Lake | Lakehouse storage | Active open source | Suitable for Spark-based Delta table management |
| Apache Iceberg | Table format | Active open source | Widely used data lake table format |
| HDFS | Lake storage | Active open source | Apache Hadoop ecosystem component |
| PostgreSQL | Operations and result storage | Active open source | Community-driven RDBMS with ongoing releases |
| MySQL Community | Legacy source DB practice | Active open source | Used as a practice source system |
| dbt Core | Transformation layer support | Active open source | Optional SQL-based transformation tool |
| Docker Compose | Local integrated environment | Active open-source tool | Hands-on environment built on Docker Compose Spec |
| Amazon S3 | Cloud storage | Not open source | AWS managed service, usable as a lake storage layer |
| Redis | Cache and feature store | Active but license caution required | Redis 8 added AGPLv3 option after `2025-05-01`; version-specific license checks are recommended |

> Summary of the review: the current core project stack does not include technologies that have been moved to the Apache Attic or are officially discontinued. However, `Amazon S3` is not open source, and `Redis` should be used with attention to version-specific licensing policy.

### AI and ML Domain

| Layer | Tool | Role |
|------|------|------|
| ML frameworks | scikit-learn, XGBoost, LightGBM | Classification, regression, clustering |
| Experiment tracking | MLflow | Model versioning and deployment |
| Inference server | FastAPI, uvicorn | Real-time model serving |
| LLM (local) | Ollama (llama3.2, mistral) | Zero-cost local LLM usage |
| LLM (cloud) | OpenAI GPT-4o-mini | High-quality natural language generation |
| Vector DB | Qdrant | RAG document retrieval |
| Embeddings | sentence-transformers | Text vectorization |
| Dashboard | Streamlit | Result visualization |

### Infrastructure

- **Containers**: Docker, Docker Compose
- **Cloud**: AWS (MSK, S3, RDS), KakaoCloud
- **OS**: Ubuntu Linux, macOS

---

## 5. Competitive Advantage Analysis

### Market Positioning

| Competitor | Strengths | Weaknesses | Response Strategy |
|--------|------|------|----------|
| Large SI firms (Samsung SDS, LG CNS, SK C&C) | Brand, ability to win large projects | Too expensive for small and mid-sized clients, slow delivery | Target mid-market customers with faster delivery and lower cost |
| AI specialist startups | Cutting-edge AI expertise | Weak data pipeline infrastructure capability | Emphasize integrated pipeline-to-AI design |
| Cloud MSPs | Convenience of managed services | Limited depth in open-source systems | Position around open-source-driven cost reduction |
| Specialized domestic firms such as FutureGen C-Planet | Confluent partnerships | Dependent on commercial licenses | Position around a pure Apache open-source stack |

### Three Core Differentiators

**1. Full-stack integration capability**

A single consultant designs everything from data ingestion to AI inference. Large SI firms often split pipeline teams and AI teams, which leads to weak integration design, while AI startups often do not understand data infrastructure. A consultant who understands both areas remains extremely rare in the Korean market.

**2. Open-source-driven cost reduction**

Deliver performance comparable to Confluent, Informatica, Talend, and other commercial tools using Apache open source alone. For mid-sized companies with constrained IT budgets, "license cost reduction" becomes a direct and compelling value proposition that belongs on the first page of the proposal.

**3. Positioning pipelines as the prerequisite for AI adoption**

Use the failure of AI projects caused by weak data infrastructure as a persuasion point. Lead with "pipelines first, AI second," sell the pipeline consulting engagement first, and naturally expand into AI consulting later. AI ROI skepticism actually becomes a market entry point.

---

## 6. Commercialization Roadmap

### Overall Timeline

| Phase | Period | Core Goal | Operating Model |
|------|------|----------|----------|
| Phase 1 | Now to 3 months (full time) | Pipeline practice, ML practice, portfolio building | Solo (preparation) |
| Phase 2 | 3 to 9 months | Secure 1 to 2 references | Solo (initial revenue) |
| Phase 3 | 9 to 15 months | Stabilize monthly revenue at KRW 15 million | Solo (growth) |
| Phase 4 | 15 to 21 months | Reach KRW 30 million monthly revenue and prepare for expansion | Solo to team consideration |
| Phase 5 | 21 months and beyond | Form a team and specialize by domain | Team model |

### Phase 1: Capability Completion (Now to 3 Months, Full Time)

**Goal**: Complete data pipeline practice, complete six ML model tracks, build a portfolio, and lay the business foundation.

**Complete data pipeline practice (8 weeks, Month 1 to 2)**:
- Kafka broker setup plus topic design and operations practice
- NiFi-based multi-source ingestion pipeline implementation
- Flink real-time stream processing and feature computation practice
- Spark batch ETL pipeline design and implementation
- RDBMS to Delta Lake migration practice using Spark JDBC and Debezium CDC
- Airflow DAG orchestration and failure-recovery scenario practice
- Redis feature store and PostgreSQL result storage integration
- Docker Compose-based integrated startup and validation of the full stack

**Complete six ML model practice tracks (8 weeks, Month 3 to 4)**:
- Finish the 16-week ML practice roadmap in compressed form (classification to regression to clustering to deep learning to LLM to reinforcement learning)
- Build portfolio artifacts from real datasets for each model family

**Business foundation building**:
- Organize publicly visible GitHub portfolios for completed pipeline and ML projects
- Register the business entity (IT consulting)
- Prepare one ROI-focused proposal template
- Prepare consulting contract templates, including NDA and IP clauses
- Launch a technical blog that works as a sleeping salesperson

Deliverables: pipeline practice code repository, three ML portfolio projects, proposal template, business registration certificate, technical blog

### Phase 2: Securing References (6 to 12 Months)

**Goal**: Win 1 to 2 paid projects and document case studies.

Main activities:
- Win the first project through networking in finance and fintech domains, even if low-cost or performance-based
- Design the data pipeline architecture, deliver it, and document it as a case study
- Publish technical blog posts regularly on real-world pipeline and ML work
- Give at least one conference or meetup talk on an integrated pipeline-plus-AI topic
- Attempt to secure the first maintenance contract

Deliverables: 1 to 2 reference cases, speaking record, 1 maintenance contract

### Phase 3: Business Stabilization (12 to 18 Months)

**Goal**: Stabilize monthly revenue in the KRW 10 to 15 million range.

Main activities:
- Expand sales to mid-sized finance and manufacturing companies using reference cases
- Strengthen recurring revenue through accumulated operations and maintenance contracts
- Package pipeline plus AI services into structured offerings
- Gradually raise pricing
- Begin building a partner network in infrastructure, security, and legal support

Deliverables: 2 to 3 recurring-revenue contracts, packaged service menu, partner network

### Phase 4: Preparing for Expansion (18 to 24 Months)

**Goal**: KRW 25 to 35 million in monthly revenue plus readiness for team formation.

Main activities:
- Position around a specialized domain such as financial data pipelines or manufacturing AI
- Participate in public support programs for AI adoption
- Add education and workshop services as capability transfer packages
- Review the timing for team formation or incorporation

Deliverables: domain-focused reference cases, education service package, incorporation review report

### Phase 5: Team Structure (24 Months and Beyond)

**Goal**: Add a partner or junior consultant and expand delivery capacity.

Main activities:
- Hire one junior consultant or form a freelancer partnership
- Build a setup capable of handling three concurrent projects
- Position as a consulting firm specialized in a specific industry vertical

---

## 7. Solo Operating Strategy (First Two Years of the Business)

### Why the First Two Years Should Remain Solo

Maintaining a solo structure for the first two years is strategically more favorable than building a team immediately.

**Light cost structure**: Hiring employees creates a fixed monthly labor cost of roughly KRW 4 to 6 million. In the early stage, projects are irregular, so lower fixed costs improve survivability. A solo structure can withstand months with no revenue.

**Fast decision-making**: Proposal revisions can be made on the same day as a customer meeting. Once a team exists, internal coordination time and cost appear.

**Justification for premium pricing**: Positioning as a "single expert" can actually justify higher rates. Without the burden of supporting a large payroll, it is possible to charge a consulting day rate that exceeds that of large SI firms.

### Realistic Monthly Income Outlook

| Period | Expected Monthly Income | Main Income Source |
|------|------------|-----------|
| Months 1 to 3 | KRW 0 | Full-time learning and practice period |
| Months 4 to 6 | KRW 1 to 5 million | Down payment on the first project |
| Months 7 to 12 | KRW 3 to 10 million | Project work plus early maintenance |
| Months 13 to 18 | KRW 10 to 20 million | Multiple projects plus accumulated maintenance |
| Months 19 to 24 | KRW 20 to 35 million | Stable pipeline implementation business |

**Key point**: The moment the first maintenance contract worth KRW 2 to 3 million per month is secured, both psychological stability and sales flexibility improve at once. Securing that recurring contract as early as possible is the core survival milestone.

### Practical Limits of Solo Operation and Response Strategy

**Limit 1: Restricted number of simultaneous projects**

Response: Limit concurrent projects to at most two. After building the pipeline, design a structure that transfers capability to the customer's internal team so involvement can gradually be reduced. Propose timelines with adequate buffer.

**Limit 2: Requests outside the consultant's core specialty**

Response: Build a partner network in advance. Maintain working relationships with one expert each in cloud infrastructure, security, and legal support. This remains a freelance collaboration model rather than a fixed payroll structure.

**Limit 3: Sales and execution burdens at the same time**

Response: Let the technical blog and GitHub portfolio function as sleeping salespeople. Once content accumulates, inbound inquiries begin to appear. Building this system consistently over two years is the most important parallel investment.

**Limit 4: Revenue gaps during long projects**

Response: Use milestone-based staged settlement in project contracts. Start planning the next project two months before the current one ends.

### Financial Requirements for Survival

At least **six months of living expenses** should be secured before launching the business. Assuming KRW 3 million per month in living expenses, KRW 18 million in reserves is required. Without this buffer, urgency can lead to low-priced work or poor contract decisions.

---

## 8. Preparation Checklist

### Existing Strengths

- [x] End-to-end understanding of data pipeline architecture (ingest, transform, store, orchestration)
- [x] Understanding of the full ML lifecycle from training to deployment
- [x] Experience designing RAG plus vector DB plus LLM integration
- [x] Experience running a full stack locally with Docker
- [x] Familiarity with finance and ETF data domains
- [x] Completed full-stack sample project integrating pipeline and AI
- [x] Experience designing Airflow DAG orchestration

### Additional Requirements Within 6 Months

- [ ] **Complete the 8-week data pipeline practice track** covering Kafka, NiFi, Flink, Spark, Spark JDBC, and Airflow across the full stack
- [ ] Complete six ML practice tracks over the 16-week plan
- [ ] Build three portfolio projects using real datasets
- [ ] Organize a public GitHub portfolio
- [ ] Register the business (IT consulting)
- [ ] Write an ROI-centered consulting proposal template
- [ ] Prepare consulting contract templates
- [ ] Launch a technical blog
- [ ] Secure the first reference customer

### Additional Preparation Within 12 Months

- [ ] Finance domain-focused reference architecture document
- [ ] Pipeline adoption ROI calculator template
- [ ] Productized service packages by engagement phase
- [ ] Partner network across infrastructure, security, and legal support
- [ ] At least one technical speaking record

---

## 9. Risks and Response Strategy

### Risk 1: Competition with Large SI Firms

**Description**: Major SI firms such as Samsung SDS, LG CNS, and SK C&C are active in the same market.

**Response**: Focus on mid-sized companies with annual revenue around KRW 10 to 50 billion, where large SI firms are less efficient. Differentiate on delivery speed (2 months vs. 6 months) and cost (KRW 50 million vs. KRW 300 million).

### Risk 2: Replacement by Cloud Managed Services

**Description**: Managed services such as AWS MSK and Azure Event Hub may replace part of the demand for implementation work.

**Response**: Focus on what managed services do not solve well: legacy integration, on-premises constraints, and complex transformation logic. Position the offering as architecture consulting on top of managed services as well.

### Risk 3: Growing Skepticism About AI ROI

**Description**: Analysis showing that many AI projects fail to produce meaningful outcomes is becoming widespread.

**Response**: Use weak data infrastructure as the explanation for AI failure. Lead with "pipelines first, AI later," sell the pipeline engagement first, and then extend into AI consulting.

### Risk 4: Underperformance Due to Poor Data Quality

**Description**: Low customer data quality may prevent ML models from meeting expectations.

**Response**: Make data status assessment a mandatory pre-contract step. Include data governance in the service package, start with rule-based approaches when needed, and transition to ML once enough clean data is available.

### Risk 5: Delivery Delays Due to the Limits of Solo Operation

**Description**: Highly complex projects may create a risk of missing deadlines.

**Response**: Build enough schedule buffer into contracts. Prepare a partner pool that can be brought in depending on project complexity. Maintain a rule of not taking more than two concurrent projects.

---

## 10. Capability-Building Learning Schedule

This is a 16-week, four-month plan based on **full-time commitment** (40 to 50 hours per week). The schedule first completes eight weeks of data pipeline practice and then eight weeks of ML practice.

> **Assumption**: Since a full-stack fraud pipeline example using Kafka, Flink, Redis, MLflow, FastAPI, and Qdrant has already been implemented directly, foundational concepts can be covered quickly. The focus should remain on deeper and more applied learning.

### Domain A: Data Pipeline Practice (8 Weeks, Month 1 to 2)

| Week | Topic | Practice Content | Deliverable |
|------|------|---------|--------|
| Week 1 | Environment setup | Bring up and validate the full stack with Docker Compose (Kafka, NiFi, Flink, Spark, Airflow, Redis, PostgreSQL) | Local practice environment |
| Week 2 | Ingestion: Kafka deep dive | Topic design, partition strategy, consumer groups, offset management, replication settings | Kafka operations guide |
| Week 3 | Ingestion: NiFi | Multi-source ingestion pipelines, Provenance tracking, data-flow visualization | NiFi flow configuration |
| Week 4 | Transformation: Flink deep dive | Window aggregation, watermarks, exactly-once processing | Flink real-time pipeline |
| Week 5 | Transformation: Spark batch | Batch ETL, large-scale partitioning, Delta Lake integration | Spark ETL code |
| Week 6 | Migration: Spark JDBC and CDC | Batch migration from RDBMS to Delta Lake, Debezium CDC real-time migration scenarios | Migration pipeline |
| Week 7 | Orchestration: Airflow deep dive | DAG dependency management, SLA monitoring, failure recovery and alerting | Airflow DAG collection |
| Week 8 | Integrated practice | End-to-end pipeline validation across ingest, transform, store, and orchestration | Integrated pipeline repository |

#### Week 1

> Scenario: For a PayNex data pipeline modernization PoC, build a local practice environment in which Kafka, NiFi, Flink, Spark, Airflow, Redis, and PostgreSQL all run correctly. The goal is to validate the shared environment that will serve as the foundation for the next eight weeks of practice.

Five-day schedule:

- Day 1: Project structure design plus core services startup, including directory layout and PostgreSQL and Redis startup and validation
- Day 2: Messaging and ingestion layer setup, including Kafka (KRaft) and NiFi startup and validation
- Day 3: Processing and orchestration layer setup, including Flink, Spark, and Airflow startup and validation
- Day 4: Full-stack integrated startup plus interaction validation across all seven components
- Day 5: Failure testing plus documentation, including container stop and recovery scenarios and README/environment documentation

Practice artifact composition:

- `docker-compose.yml` and `.env`: full practice environment definition for Kafka, NiFi, Flink, Spark, Airflow, Redis, and PostgreSQL
- `scripts/init-db.sql`: PostgreSQL initial schema and sample data loading
- `scripts/healthcheck-all.sh` and `dags/healthcheck_dag.py`: integrated health checks and Airflow-based environment validation automation
- `README.md`: local startup procedure, port map, and basic failure-response guide

#### Week 2

> Scenario: The PayNex CTO requires Kafka-based ingestion of 500,000 transaction events per day, growing to 2 million in the future, while letting the fraud detection team and settlement team consume the same data independently without interfering with each other. The goal this week is to validate topic architecture and fault tolerance in Kafka.

Five-day schedule:

- Day 1: Topic design strategy, including business event modeling, naming conventions, and partition count estimation
- Day 2: Partition key design plus producer implementation, including key-based routing and transaction data generator implementation
- Day 3: Consumer groups plus offset management, including multiple consumer groups, manual commit, and rebalance observation
- Day 4: Multi-broker plus replication, including a three-broker cluster, replication factor, and ISR management
- Day 5: Failure scenarios plus operations guide documentation, including broker recovery, leader election, and operating guide writing

Practice artifact composition:

- `config/kafka/topic-naming-convention.md` and `config/kafka/topic-configs.md`: topic design criteria and operating settings draft
- `scripts/partition-calculator.sh` and `scripts/producer_paynex.py`: partition estimation and transaction event producer
- `scripts/verify_partition_key.py`, `scripts/consumer_fraud_detection.py`, and `scripts/consumer_settlement.py`: partition key validation and multi-consumer-group practice
- `docker-compose.yml` updates, `docs/fault-tolerance-report.md`, and `docs/kafka-operations-guide.md`: three-broker cluster and operational documentation for fault tolerance

#### Week 3

> Scenario: The PayNex CTO requests unified ingestion of payment API JSON, legacy settlement CSV, and customer master DB data into a single pipeline, with audit-friendly traceability of data origin and flow. The goal is to build a NiFi-based multi-source ingestion system and Provenance tracking framework.

Five-day schedule:

- Day 1: NiFi core concepts plus processor-group design, including architecture understanding and baseline flow design
- Day 2: REST API ingestion pipeline, including real-time API ingestion with `InvokeHTTP`, JSON parsing and transformation, and error handling
- Day 3: File and DB ingestion pipeline, including CSV watch-and-ingest and PostgreSQL-based incremental extraction
- Day 4: Kafka integration plus schema standardization, including `PublishKafka`, multi-source schema unification, and quality routing
- Day 5: Provenance tracking plus documentation, including lineage tracing, monitoring dashboard, and operating guide

Practice artifact composition:

- `scripts/api_payment_simulator.py`, `scripts/csv_settlement_generator.py`, and `scripts/init-customers.sql`: API, file, and DB source data generation and initialization
- `config/nifi/process-group-design.md` and `config/nifi/jolt-spec-*.json`: NiFi processor-group design and source-specific standardization rules
- `config/nifi/paynex-standard-schema.avsc` and `scripts/verify_nifi_pipeline.sh`: common event schema and integrated verification script
- `docs/provenance-audit-guide.md`, `docs/nifi-monitoring-guide.md`, and `docs/nifi-architecture.md`: lineage tracking, monitoring, and architecture documentation

#### Week 4

> Scenario: Once real-time events begin flowing into the `paynex.events.ingested` topic through NiFi, the PayNex CTO requires five-minute aggregations, real-time fraud detection, and exactly-once guarantees. This week completes the core real-time transformation layer with Apache Flink.

Five-day schedule:

- Day 1: Flink core concepts plus project setup, including stream processing model review and Kafka source integration
- Day 2: Watermarks plus window aggregation, including event-time processing and tumbling, sliding, and session windows
- Day 3: Real-time fraud detection, including CEP pattern matching, rule-based detection, and Kafka and Redis alert sink integration
- Day 4: Exactly-once plus checkpoints, including checkpoint configuration, Kafka transactional sink, and failure-recovery consistency validation
- Day 5: Integrated testing plus operations guide documentation, including full real-time pipeline validation, tuning, and operations guide writing

Practice artifact composition:

- `docs/flink-concepts.md` and `flink-jobs/pom.xml`: Flink concepts and Maven-based project setup
- `flink-jobs/src/main/java/com/paynex/flink/job/TransactionAggregationJob.java` and `FraudDetectionJob.java`: core job implementations for window aggregation and fraud detection
- `scripts/flink_event_generator.py` and `scripts/fraud_alert_redis_sink.py`: real-time test event generation and Redis alert persistence
- `scripts/verify_flink_pipeline.sh`, `scripts/monitor_checkpoints.sh`, and `docs/flink-operations-guide.md`: exactly-once verification, checkpoint monitoring, and operations documentation

#### Week 5

> Scenario: The PayNex CFO requires daily and monthly settlement reporting, audit traceability through time travel, and data quality validation. Apache Spark batch ETL is used to address these requirements.

Five-day schedule:

- Day 1: Spark concept review, PySpark project structure, and Kafka batch-read integration
- Day 2: Medallion architecture design plus Bronze layer, including raw ingestion, Delta Lake, and idempotent `MERGE`
- Day 3: Silver layer plus data quality validation through a YAML rule-based `QualityChecker` module with critical quarantine and warning flags
- Day 4: Three Gold aggregations plus Delta Lake deep dive, including time travel, `VACUUM`, and `OPTIMIZE`
- Day 5: Full ETL integration run plus verification scripts, batch operations guide, and architecture documentation

Practice artifact composition:

- `config/etl_config.yaml`, `config/quality_rules.yaml`, and `lib/quality_checker.py`: ETL configuration and data quality validation rules module
- `spark-etl/jobs/bronze_ingestion.py`, `silver_transformation.py`, and `gold_aggregation.py`: Bronze, Silver, and Gold medallion ETL implementation
- `spark-etl/jobs/full_etl_pipeline.py` and `spark-etl/scripts/verify_etl_pipeline.sh`: end-to-end batch pipeline orchestration and integrated verification
- `spark-etl/scripts/delta_time_travel_demo.py`, `spark-etl/scripts/delta_maintenance.sh`, and `docs/spark-operations-guide.md`: Delta Lake advanced features and batch operations guide

#### Week 6

> Scenario: The PayNex CIO presents a migration task involving 300 million rows from a legacy MySQL settlement system into Delta Lake, with no service interruption allowed and different strategies needed by table type.

Five-day schedule:

- Day 1: Migration core concepts plus legacy MySQL environment setup with four tables (`customers` 500 rows, `merchants` 100 rows, `transactions` 100,000 rows, `settlements` 5,000 rows), and binlog row format activation
- Day 2: Spark JDBC batch migration through full export of customers, merchants, and transaction history into Delta Lake Bronze with parallel partitioned reads
- Day 3: Spark JDBC incremental append for transaction history plus last-modified pattern for settlements and source-to-target reconciliation tooling
- Day 4: Debezium CDC plus Kafka Connect configuration, building a real-time path from MySQL binlog to Kafka to Spark Structured Streaming to Delta Lake `MERGE` with upsert and soft delete
- Day 5: Integrated reconciliation validation, migration strategy documentation at customer-proposal quality, cumulative architecture documentation for Weeks 1 to 6, and Git commit

Practice artifact composition:

- `docs/migration-concepts.md`, `docs/migration-target-tables.md`, and `scripts/init-mysql.sql`: migration strategy documentation and legacy MySQL source preparation
- `spark-jobs/migration/jdbc_full_export.py`, `jdbc_incremental.py`, and `verify_migration.py`: Spark JDBC full and incremental migration plus reconciliation verification
- `config/debezium-mysql-connector.json`, `spark-jobs/migration/cdc_to_delta.py`, and `docs/cdc-event-structure.md`: Debezium CDC and real-time Delta Lake reflection practice
- `scripts/verify_migration_all.sh`, `docs/spark-jdbc-vs-debezium.md`, and `docs/migration-strategy-guide.md`: integrated verification and criteria for choosing batch versus real-time migration

The plan includes 15 deliverables and a lead-in to Week 7 (Airflow orchestration).

#### Week 7

> Scenario: The PayNex COO requires operational automation of the Week 1 to 6 pipelines using Apache Airflow, including Spark JDBC batch migration, Spark batch ETL, and Debezium CDC. Migration must run daily at 03:00, settlement reports must complete before 06:00, CDC failures and SLA delays must trigger immediate alerts, and backfill or reprocessing for specific dates must be possible.

Five-day schedule:

- Day 1: Advanced Airflow concepts, operating requirement modeling, and DAG structure design using Connections, Variables, TaskGroup, and Trigger Rules
- Day 2: Batch migration child DAG implementation, connecting Spark JDBC full and incremental tasks with reconciliation validation in a manually triggerable structure
- Day 3: Spark ETL child DAG integration, calling Week 5 `full_etl_pipeline.py` through `TriggerDagRunOperator(wait_for_completion=True)` for sequential execution
- Day 4: CDC monitoring plus backfill and recovery DAG implementation, including Kafka Connect state checks, SLA miss detection, retry and alert callbacks, and date-specific reprocessing
- Day 5: Integrated master DAG plus operations guide documentation, daily orchestration rehearsal, runbook preparation, failure-response procedure writing, and Git commit

Practice artifact composition:

- `Dockerfile.airflow` and `plugins/alerting.py`: custom Airflow image plus failure and SLA-miss alert plugin
- `dags/paynex_daily_migration_dag.py` and `spark-jobs/orchestration/master_refresh.py`: Spark JDBC migration and master refresh DAG
- `dags/paynex_daily_etl_dag.py`, `spark-etl/jobs/publish_gold_report.py`, and `spark-etl/jobs/verify_gold_outputs.py`: Week 5 batch ETL integration and Gold output validation automation
- `dags/paynex_cdc_monitoring_dag.py`, `dags/paynex_backfill_recovery_dag.py`, `dags/paynex_daily_master_dag.py`, and `docs/airflow-operations-guide.md`: CDC monitoring, backfill and recovery, unified daily master DAG, and operations runbook

#### Week 8

> Scenario: The PayNex CTO and COO require all assets from Weeks 1 to 7, including Kafka, NiFi, Flink, Spark, Spark JDBC, Debezium, and Airflow, to be connected into a single operational scenario and validated at customer acceptance-test level. Even when API JSON, settlement CSV, PostgreSQL, and MySQL change data all arrive simultaneously, real-time detection and batch reporting must remain consistent, and failure injection, recovery, and backfill must be reproducible.

Five-day schedule:

- Day 1: Integrated requirements definition plus success criteria, including scope, business-day scenario design, and success criteria documentation
- Day 2: Integrated rehearsal automation, connecting API, CSV, Kafka, and CDC input scenarios, implementing an acceptance DAG, and writing a rehearsal script based on the reused master DAG
- Day 3: End-to-end execution plus quality validation across Kafka, NiFi, Flink, Spark, Delta Lake, and Airflow, including KPI summary and contract validation
- Day 4: Failure injection plus recovery rehearsal for Flink, Kafka Connect, and Airflow, including backfill and reprocessing validation
- Day 5: Final portfolio packaging plus customer report preparation, including final architecture documentation, acceptance-test report, demo script, and Git commit

Practice artifact composition:

- `config/e2e/business_day_scenario.yaml` and `docs/final/acceptance-criteria.md`: integrated business-day scenario and customer acceptance criteria
- `scripts/e2e/run_business_day_rehearsal.sh` and `scripts/e2e/mysql_cdc_changes.sql`: operational rehearsal script bundling API, CSV, Kafka, and CDC plus change scenarios
- `dags/paynex_acceptance_rehearsal_dag.py`, `scripts/e2e/verify_end_to_end.sh`, and `spark-etl/jobs/build_pipeline_kpis.py`: integrated acceptance-test DAG, end-to-end verification, and final KPI summary
- `scripts/e2e/run_failure_drills.sh` and `scripts/e2e/collect_pipeline_snapshot.sh`: failure injection, recovery rehearsal, and operational snapshot collection
- `docs/final/failure-drill-report.md`, `docs/final/acceptance-test-report.md`, `docs/final/paynex-final-architecture.md`, and `docs/final/portfolio-demo-script.md`: final recovery report, acceptance-test result report, architecture documentation, and portfolio demo materials

#### Final Git Repository Directory and File Structure

After all eight weeks of practice, the complete structure of the `pipeline-lab/` repository is as follows. `(Wn)` next to each file indicates the week in which it is first created.

```text
pipeline-lab/
│
├── .env                                        (W1) Environment variables (DB connection, Airflow, Redis, etc.)
├── .gitignore                                  (W1) Exclude `postgres-data/`, `redis-data/`, etc.
├── docker-compose.yml                          (W1) Full stack definition, gradually extended in W2, W3, W6, and W7
├── Dockerfile.airflow                          (W7) Custom Airflow image with SparkSubmit and Slack support
├── README.md                                   (W1) Startup procedure, port guide, failure-response guide
│
├── config/
│   ├── kafka/
│   │   ├── topic-naming-convention.md          (W2) Topic naming convention (`<domain>.<entity>.<event>`)
│   │   └── topic-configs.md                    (W2) Topic-level partition, retention, and replication settings
│   ├── nifi/
│   │   ├── process-group-design.md             (W3) Design document for five processor groups
│   │   ├── jolt-spec-api-payment.json          (W3) REST API JSON to standard schema conversion
│   │   ├── jolt-spec-file-settlement.json      (W3) Settlement CSV to standard schema conversion
│   │   ├── jolt-spec-db-customer.json          (W3) Customer DB to standard schema conversion
│   │   └── paynex-standard-schema.avsc         (W3) Unified 14-field Avro schema
│   ├── flink/                                  (W1) Placeholder directory for Flink configuration
│   ├── spark/                                  (W1) Placeholder directory for Spark configuration
│   ├── airflow/                                (W1) Placeholder directory for Airflow configuration
│   ├── debezium-mysql-connector.json           (W6) Debezium MySQL CDC connector settings
│   └── e2e/
│       └── business_day_scenario.yaml          (W8) Integrated business-day scenario definition
│
├── dags/
│   ├── healthcheck_dag.py                      (W1) Health-check DAG for seven components
│   ├── paynex_daily_migration_dag.py           (W7) Spark JDBC batch migration DAG
│   ├── paynex_daily_etl_dag.py                 (W7) Spark ETL (Bronze to Silver to Gold) DAG
│   ├── paynex_cdc_monitoring_dag.py            (W7) Kafka Connect CDC monitoring DAG
│   ├── paynex_backfill_recovery_dag.py         (W7) Date-specific backfill and reprocessing DAG
│   ├── paynex_daily_master_dag.py              (W7) Daily integrated orchestration master DAG
│   └── paynex_acceptance_rehearsal_dag.py      (W8) Customer acceptance-test rehearsal DAG
│
├── plugins/
│   └── alerting.py                             (W7) Slack and email callbacks for failures and SLA misses
│
├── docs/
│   ├── kafka-operations-guide.md               (W2) Kafka operations guide (brokers, topics, replication)
│   ├── fault-tolerance-report.md               (W2) Broker failure-recovery test report
│   ├── nifi-concepts.md                        (W3) NiFi core concepts
│   ├── nifi-architecture.md                    (W3) NiFi processor-group architecture document
│   ├── nifi-monitoring-guide.md                (W3) NiFi monitoring and backpressure guide
│   ├── provenance-audit-guide.md               (W3) Data lineage and Provenance tracking guide
│   ├── flink-concepts.md                       (W4) Core Flink stream-processing concepts
│   ├── flink-architecture.md                   (W4) Flink job architecture document
│   ├── flink-operations-guide.md               (W4) Flink checkpoint and failure-recovery guide
│   ├── spark-concepts.md                       (W5) Spark batch-processing concepts
│   ├── spark-architecture.md                   (W5) Medallion architecture design document
│   ├── spark-operations-guide.md               (W5) Spark ETL batch operations guide
│   ├── migration-concepts.md                   (W6) Three-stage migration strategy (Full to Incremental to CDC)
│   ├── migration-target-tables.md              (W6) Analysis of four migration target tables
│   ├── migration-architecture.md               (W6) Migration pipeline architecture document
│   ├── migration-strategy-guide.md             (W6) Customer-proposal-quality migration strategy guide
│   ├── spark-jdbc-vs-debezium.md               (W6) Criteria for choosing batch versus real-time migration
│   ├── cdc-event-structure.md                  (W6) Debezium CDC event structure summary
│   ├── airflow-operations-guide.md             (W7) Airflow DAG operations runbook
│   └── final/
│       ├── acceptance-criteria.md              (W8) Acceptance-test scope and success criteria
│       ├── acceptance-test-report.md           (W8) Final acceptance-test results report
│       ├── failure-drill-report.md             (W8) Failure injection and recovery rehearsal report
│       ├── paynex-final-architecture.md        (W8) Final end-to-end architecture document
│       └── portfolio-demo-script.md            (W8) Portfolio demo scenario
│
├── scripts/
│   ├── init-db.sql                             (W1) PostgreSQL initial schema and sample data
│   ├── init-customers.sql                      (W3) Initial data for customer master table
│   ├── init-mysql.sql                          (W6) MySQL legacy four-table schema and sample data
│   ├── healthcheck-all.sh                      (W1) Integrated health check for all components
│   ├── partition-calculator.sh                 (W2) Partition count estimation script
│   ├── producer_paynex.py                      (W2) Kafka transaction event producer (`confluent-kafka`)
│   ├── verify_partition_key.py                 (W2) Partition-key routing verification
│   ├── consumer_fraud_detection.py             (W2) Fraud detection consumer group
│   ├── consumer_settlement.py                  (W2) Settlement processing consumer group
│   ├── api_payment_simulator.py                (W3) Flask-based payment API simulator
│   ├── csv_settlement_generator.py             (W3) Settlement CSV generator
│   ├── measure_api_throughput.sh               (W3) API throughput measurement
│   ├── verify_nifi_pipeline.sh                 (W3) Integrated NiFi pipeline verification
│   ├── flink_event_generator.py                (W4) Event generator for Flink practice (`confluent-kafka`)
│   ├── fraud_alert_redis_sink.py               (W4) Fraud alert to Redis caching sink
│   ├── monitor_checkpoints.sh                  (W4) Flink checkpoint monitoring
│   ├── verify_flink_pipeline.sh                (W4) Integrated Flink pipeline verification
│   └── e2e/
│       ├── run_business_day_rehearsal.sh       (W8) Business-day integrated rehearsal
│       ├── mysql_cdc_changes.sql               (W8) CDC change scenarios (`INSERT`, `UPDATE`, `DELETE`)
│       ├── verify_end_to_end.sh                (W8) End-to-end validation across the full pipeline
│       ├── run_failure_drills.sh               (W8) Failure injection and recovery rehearsal
│       └── collect_pipeline_snapshot.sh        (W8) Operational snapshot collection
│
├── spark-etl/                                  -- Week 5 batch ETL --
│   ├── config/
│   │   ├── etl_config.yaml                     (W5) ETL settings (sources, sinks, batch size)
│   │   └── quality_rules.yaml                  (W5) Data quality rules (validity, range, consistency)
│   ├── lib/
│   │   ├── spark_session_factory.py            (W5) SparkSession factory with Delta Lake setup
│   │   ├── schema_registry.py                  (W5) Bronze, Silver, and Gold schema definitions
│   │   ├── quality_checker.py                  (W5) YAML-based quality validation engine
│   │   └── delta_utils.py                      (W5) Delta Lake `MERGE` and `VACUUM` utilities
│   ├── jobs/
│   │   ├── kafka_batch_read_test.py            (W5) Kafka batch read integration test
│   │   ├── bronze_ingestion.py                 (W5) Kafka to Bronze raw ingestion with idempotent `MERGE`
│   │   ├── bronze_ingestion_file.py            (W5) File-based Bronze ingestion
│   │   ├── silver_transformation.py            (W5) Cleansing, deduplication, and quality validation (Silver)
│   │   ├── gold_aggregation.py                 (W5) Daily sales, customer statistics, and fee settlement (three Gold outputs)
│   │   ├── full_etl_pipeline.py                (W5) Full Bronze to Silver to Gold orchestration
│   │   ├── publish_gold_report.py              (W7) Gold report publishing for Airflow integration
│   │   ├── verify_gold_outputs.py              (W7) Gold deliverable verification for Airflow integration
│   │   └── build_pipeline_kpis.py              (W8) Final KPI summary for acceptance tests
│   └── scripts/
│       ├── generate_sample_data.py             (W5) Sample data generation
│       ├── verify_bronze.py                    (W5) Bronze layer validation
│       ├── delta_time_travel_demo.py           (W5) Delta Lake time-travel demo
│       ├── delta_maintenance.sh                (W5) `VACUUM` and `OPTIMIZE` maintenance
│       └── verify_etl_pipeline.sh              (W5) Full ETL pipeline integrated verification
│
├── spark-jobs/                                 -- Week 6 to 7 migration and orchestration --
│   ├── migration/
│   │   ├── jdbc_full_export.py                 (W6) Spark JDBC full export for `customers` and `merchants`
│   │   ├── jdbc_incremental.py                 (W6) Spark JDBC incremental append for `transactions`
│   │   ├── cdc_to_delta.py                     (W6) CDC to Structured Streaming to Delta `MERGE`
│   │   └── verify_migration.py                 (W6) Source-to-target reconciliation verification
│   └── orchestration/
│       └── master_refresh.py                   (W7) Master table full refresh for Airflow integration
│
├── flink-jobs/                                 -- Week 4 real-time stream processing --
│   ├── pom.xml                                 (W4) Maven build settings (Flink 1.18.1, Kafka connector)
│   └── src/main/java/com/paynex/flink/
│       ├── job/
│       │   ├── TransactionAggregationJob.java  (W4) Five-minute window transaction aggregation
│       │   ├── SessionWindowAnalysisJob.java   (W4) Session-window user behavior analysis
│       │   └── FraudDetectionJob.java          (W4) Real-time fraud detection with CEP
│       ├── function/
│       │   ├── TransactionAggregateFunction.java   (W4) Aggregation function
│       │   ├── TransactionWindowFunction.java      (W4) Window result formatting
│       │   ├── LateDataSideOutputFunction.java     (W4) Late data side-output handling
│       │   └── FraudDetectionFunction.java         (W4) KeyedProcess-based detection logic
│       ├── model/
│       │   ├── PaynexEvent.java                (W4) Fourteen-field event POJO
│       │   ├── AggregatedResult.java           (W4) Window aggregation result model
│       │   └── FraudAlert.java                 (W4) Fraud alert model
│       └── util/
│           ├── PaynexEventDeserializer.java    (W4) JSON to POJO deserialization with `SNAKE_CASE` mapping
│           ├── FlinkConfigUtil.java            (W4) Flink configuration utility
│           └── ExactlyOnceKafkaSinkBuilder.java (W4) Exactly-once Kafka sink builder
│
└── data/
    ├── sample/                                 (W1) Sample data
    ├── settlement/                             (W3) Settlement CSV files collected by NiFi
    │   └── processed/                          (W3) Archive for processed CSV files
    └── delta/                                  (W5 and beyond) Delta Lake storage
        ├── etl/                                (W5) Spark batch ETL outputs
        │   ├── bronze/                         (W5) Raw ingestion from Kafka and file sources
        │   ├── silver/                         (W5) Cleansed and quality-validated data
        │   ├── gold/                           (W5) Business aggregate reports
        │   │   ├── daily_summary/              (W5) Daily sales summary
        │   │   ├── customer_stats/             (W5) Customer statistics
        │   │   └── fee_settlement/             (W5) Fee settlement
        │   └── checkpoints/                    (W5) Spark Structured Streaming checkpoints
        ├── migration/                          (W6) RDBMS migration outputs
        │   ├── customers/                      (W6) Customer master full export
        │   ├── merchants/                      (W6) Merchant master full export
        │   ├── transactions/                   (W6) Incremental append for transaction history
        │   ├── settlements/                    (W6) Settlement data with last-modified pattern
        │   └── settlements_cdc/                (W6) Real-time settlement changes through Debezium CDC
        └── quality-reports/                    (W5) Data quality validation reports
```

**Deliverable statistics**:

| Category | Count | Major Contents |
|------|------|----------|
| Python scripts | 40+ | Producers and consumers, ETL jobs, migration, simulators, verification |
| Java classes | 13 | Flink jobs, functions, models, utilities |
| Shell scripts | 10+ | Health checks, partition calculation, pipeline verification, failure rehearsals |
| Airflow DAGs | 7 | Health checks, migration, ETL, CDC, backfill, master, acceptance test |
| Configuration files | 10+ | `.yaml`, `.json`, `.avsc`, `.env`, `Dockerfile` |
| SQL files | 4 | PostgreSQL and MySQL initialization, CDC change scenario |
| Operations documents | 20+ | Architecture, runbooks, strategy guides, acceptance-test reports |
| Delta Lake tables | 10 | Bronze, Silver, Gold layers plus five migration tables and quality reports |

**Docker service composition** (final `docker-compose.yml`):

| Service | Container | Host Port | Week Introduced |
|--------|---------|-----------|----------|
| PostgreSQL | lab-postgres | 5432 | W1 |
| Redis | lab-redis | 6379 | W1 |
| Kafka (3 brokers) | lab-kafka-1/2/3 | 29092/29093/29094 | W1 to W2 expansion |
| Apache NiFi | lab-nifi | 8080 | W1 |
| Flink JobManager | lab-flink-jm | 8081 | W1 |
| Flink TaskManager | lab-flink-tm | — | W1 |
| Spark Master | lab-spark-master | 8082, 7077 | W1 |
| Spark Worker | lab-spark-worker | — | W1 |
| Airflow Webserver | lab-airflow-web | 8083 | W1 to W7 custom image |
| Airflow Scheduler | lab-airflow-sched | — | W1 to W7 custom image |
| MySQL (legacy) | lab-mysql | 3306 | W6 |
| Kafka Connect | lab-kafka-connect | 8084 | W6 |
| Payment API | lab-payment-api | 5050 | W3 |

### Domain B: ML Model Practice (8 Weeks, Month 3 to 4)

With full-time weekly investment, the existing 16-week program is compressed. Since there is already prior experience with classification (RandomForest) and LLM/RAG, those areas can be covered more quickly while focusing time on new topics.

| Week | Topic | Dataset | Deliverable | Notes |
|------|------|---------|--------|------|
| Week 9 | Advanced classification | Kaggle Credit Card Fraud | Comparative report for three models (RF, XGBoost, LightGBM) | Existing foundation, move quickly |
| Week 10 | Regression | Korean Ministry of Land transaction data or Kaggle House Prices | Property price prediction API | New |
| Week 11 | Clustering | Kaggle Mall Customer | Customer segmentation report plus visualization | New |
| Week 12 | Advanced LLM/RAG | Internal PDF documents | Fully working local chatbot | Existing foundation, move quickly |
| Week 13 to 14 | Deep learning | Kaggle Chest X-Ray | Medical image diagnosis web app (Streamlit) | Two weeks allocated, new concepts |
| Week 15 | Reinforcement learning basics | Gymnasium CartPole to FinRL | Conceptual understanding plus CartPole practice | Basic level only |
| Week 16 | Integrated portfolio | Entire body of work | GitHub organization plus proposal template | Business foundation complete |

> **Reinforcement learning note**: Since it is unlikely to be an early consulting demand area, Week 15 should remain at the level of conceptual understanding and basic practice. Deeper study can follow when real demand appears.

### Summary of Monthly Focus Areas

| Month | Period | Focus Area | Completion Criteria |
|----|------|---------|----------|
| Month 1 | Week 1 to 4 | Pipeline ingestion and transformation | Kafka, NiFi, Flink, and Spark practice code complete |
| Month 2 | Week 5 to 8 | Pipeline migration, orchestration, integration | Full integrated pipeline repository complete |
| Month 3 | Week 9 to 12 | ML classification, regression, clustering, LLM | Three portfolio projects plus chatbot complete |
| Month 4 | Week 13 to 16 | Deep learning, reinforcement learning, portfolio packaging | Public GitHub release plus proposal template complete |

### Recommended Datasets and Environment

**Data pipeline**:
- Practice environment: Docker Compose (Kafka, NiFi, Flink, Spark, Airflow, Redis, PostgreSQL)
- Sample DBs for migration practice: MySQL World Database, Northwind

**ML models**:
- Classification: https://kaggle.com/datasets/mlg-ulb/creditcardfraud
- Regression: https://kaggle.com/competitions/house-prices-advanced
- Clustering: https://kaggle.com/datasets/vjchoudhary7/customer-segmentation
- Deep learning: https://kaggle.com/datasets/paultimothymooney/chest-xray-pneumonia (use Google Colab T4 GPU)
- Reinforcement learning: `pip install gymnasium finrl`

---

## 11. Revenue Targets and Financial Plan

### Monthly Revenue Targets

| Timing | Target Monthly Revenue | Revenue Mix |
|------|------------|----------|
| 3 months (capability completion) | — | Preparation period |
| 6 months | KRW 3 to 5 million | One small project |
| 12 months | KRW 8 to 12 million | One project plus one maintenance contract |
| 18 months | KRW 15 to 20 million | One project plus two to three maintenance contracts |
| 24 months | KRW 25 to 35 million | Two projects plus three maintenance contracts |
| 36 months | KRW 50 million+ | Team expansion plus packaged services |

### Recurring Revenue Structure (Core)

Accumulated operations and maintenance contracts are the key to business stability, more than one-off projects.

| Number of Maintenance Contracts | Fixed Monthly Income | Stability |
|----------------|------------|--------|
| 0 | KRW 0 | Unstable |
| 1 (KRW 2.5 million per month) | KRW 2.5 million | Basic living covered |
| 2 (KRW 5 million per month) | KRW 5 million | Sales flexibility begins |
| 3 (KRW 7.5 million per month) | KRW 7.5 million | Stable basis for growth |

### Initial Investment and Operating Cost

| Item | Initial Cost | Monthly Cost |
|------|----------|--------|
| Business registration | KRW 0 | — |
| Development equipment (if not already owned) | KRW 0 to 2 million | — |
| Cloud server (for practice and demos) | — | KRW 30,000 to 100,000 |
| Technical blog operations | KRW 0 | KRW 0 (free platform) |
| Living expense reserve (6 months) | KRW 15 to 20 million | — |
| **Total** | **KRW 15 to 22 million** | **KRW 30,000 to 100,000** |

---

## 12. Conclusion

### Market Timing Assessment

The year 2026 is a special moment in which three trends are happening at the same time. Demand for AI adoption is rising explosively, awareness is growing that many AI failures come from weak data infrastructure, and professionals who can design that infrastructure remain scarce. The overlap of these three conditions makes this an optimal time to enter the market.

### The Fundamental Strength of This Business

Large SI firms separate pipeline teams from AI teams. AI startups know models but often do not understand data infrastructure. Cloud MSPs focus on selling their own services. An independent consultant who can design collection, transformation, storage, training, inference, and operations from a single open-source-centered perspective is still difficult to find in the Korean market. That is the most realistic barrier to entry and competitive advantage of this business.

### What Two Years of Solo Operation Mean

The first two years are for building references and constructing a recurring revenue base. Stable survival matters more than flashy growth. Once three maintenance contracts are in place, the business foundation is effectively complete, and that becomes the point where team formation and service expansion can be discussed seriously.

### What to Do Right Now

The most direct action to take now is to complete the 16-week ML learning schedule while organizing the finished pipeline project into a public GitHub portfolio. Once those two tasks are done, the business is ready for the first proposal. One solid portfolio project is stronger than one hundred proposal documents.

---

*This report was prepared based on market data and technical capability analysis as of March 2026.*

*Primary sources: Ministry of Science and ICT and KDATA, "2024 Data Industry Survey" / CIO Korea, "2026 IT Outlook Survey" / Deloitte, "2026 TMT Outlook" / National Information Society Agency, "2026 AI Outlook Analysis" / Fortune Business Insights, "AI Consulting Services Market Analysis"*

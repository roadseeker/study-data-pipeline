# CLAUDE.md — Pipeline Lab

## Project Purpose

This is a **data pipeline and AI/ML consulting portfolio project** built to support a solo consulting business launch. The practitioner is building real, deployable portfolio artifacts across two domains:

- **Domain A**: Apache open-source-based data pipeline (Kafka, NiFi, Flink, Spark, Airflow)
- **Domain B**: ML model design, MLflow, LLM/RAG adoption

The business target: mid-sized Korean companies in finance, fintech, and manufacturing with legacy RDBMS and limited AI capabilities. The differentiator is integrated pipeline-to-AI design using pure Apache open source (no commercial licenses like Confluent or Informatica).

## Current Phase

**Phase 1 — Capability Completion (Months 1–4, full-time)**

Domain A pipeline practice is structured as an 8-week program using a fictional fintech company "Nexus Pay" as the scenario. The current branch `week4-flink` corresponds to **Week 4: Flink real-time stream processing**.

| Week | Topic | Status |
|------|-------|--------|
| Week 1 | Full-stack Docker Compose setup (Kafka, NiFi, Flink, Spark, Airflow, Redis, PostgreSQL) | Completed |
| Week 2 | Kafka deep dive (topic design, partitions, consumer groups, replication) | Completed |
| Week 3 | NiFi multi-source ingestion + Provenance tracking | Completed |
| Week 4 | Flink real-time stream processing + exactly-once | In progress |
| Week 5 | Spark batch ETL + Medallion architecture (Bronze/Silver/Gold) + Delta Lake | Pending |
| Week 6 | RDBMS migration: Spark JDBC + Debezium CDC | Pending |
| Week 7 | Airflow orchestration (DAG dependencies, SLA, failure recovery) | Pending |
| Week 8 | End-to-end integration rehearsal + acceptance test | Pending |

After Week 8, Domain B ML practice begins (Weeks 9–16: classification, regression, clustering, LLM/RAG, deep learning, RL).

## Tech Stack

### Data Pipeline (Current Repo Baseline)
| Layer | Tools |
|-------|-------|
| Ingest | Apache Kafka 3.7 (KRaft mode, 3 brokers), Apache NiFi 2.9.0 |
| Transform | Apache Flink 2.2.0, Apache Spark 3.5.1 |
| Store | PostgreSQL 16, Redis 7, local sample data, Delta output workspace |
| Orchestration | Apache Airflow 2.8.4 |
| Migration (planned Week 6) | Spark JDBC, Debezium (CDC) |
| Feature store | Redis 7, PostgreSQL |

### AI/ML (Planned Domain B Scope)
| Layer | Tools |
|-------|-------|
| ML frameworks | scikit-learn, XGBoost, LightGBM |
| Experiment tracking | MLflow |
| Inference | FastAPI, uvicorn |
| LLM (local) | Ollama (llama3.2, mistral) |
| LLM (cloud) | OpenAI GPT-4o-mini |
| Vector DB | Qdrant |
| Embeddings | sentence-transformers |
| Dashboard | Streamlit |

### Infrastructure
- **Containers**: Docker, Docker Compose
- **Cloud**: AWS (MSK, S3, RDS), KakaoCloud
- **OS**: Ubuntu Linux (containers), Windows 11 (host)
- **Languages**: Python (primary), Java (Flink jobs), SQL, Shell

## Project Structure

```
study-data-pipeline/
├── docker-compose.yml          # Full stack definition (evolves by week)
├── .env                        # Env vars — not committed
├── AGENTS.md                   # Repository-wide agent instructions
├── CLAUDE.md                   # Repository guidance for Claude-style agents
├── config/
│   ├── airflow/                # Airflow config placeholder
│   ├── flink/                  # Flink config placeholder
│   ├── kafka/                  # Topic naming conventions and Kafka docs
│   ├── nifi/                   # NiFi TLS, JOLT specs, schema, process design
│   └── spark/                  # Spark config placeholder
├── dags/                       # Airflow DAG files
├── docs/
│   ├── airflow/                # Airflow docs
│   ├── flink/                  # Flink docs
│   ├── guides/                 # 01~08 weekly lab guides
│   ├── kafka/                  # Kafka architecture and operations docs
│   ├── nifi/                   # NiFi concept and ingestion docs
│   ├── reports/                # Consulting reports and cross-week reports
│   └── spark/                  # Spark and migration docs
├── scripts/
│   ├── foundation/             # Health checks and base DB init scripts
│   ├── kafka/                  # Kafka producers, consumers, verification
│   ├── nifi/                   # NiFi simulators and ingestion helpers
│   └── verify_nifi_pipeline.sh # Legacy verification helper at repo root
├── flink-jobs/                 # Week 4 Java-based stream processing
├── spark-etl/                  # Week 5 Medallion ETL workspace
├── spark-jobs/                 # Week 6~7 migration and orchestration jobs
└── data/
    ├── delta/                  # Delta output workspace
    ├── nifi/settlement/        # NiFi settlement file landing/processed area
    ├── sample/                 # Shared sample inputs
    └── settlement/             # Legacy settlement sample/output area
```

## Service Ports (Docker)

| Service | Container | Port |
|---------|-----------|------|
| PostgreSQL | lab-postgres | 5432 |
| Redis | lab-redis | 6379 |
| Kafka broker 1 | lab-kafka-1 | 30092 |
| Kafka broker 2 | lab-kafka-2 | 30093 |
| Kafka broker 3 | lab-kafka-3 | 30094 |
| NiFi | lab-nifi | 8443 (`https://localhost:8443/nifi/`) |
| Flink JobManager | lab-flink-jm | 8081 |
| Spark Master | lab-spark-master | 8082, 7077 |
| Airflow Webserver | lab-airflow-web | 8083 |
| Payment API (Week 3) | lab-payment-api | 5050 |

## Key Conventions

### Nexus Pay Scenario
All pipeline practice is framed around a fictional fintech company "Nexus Pay" data modernization PoC. Each week has a specific stakeholder scenario (CTO, CFO, COO, CIO) that drives the requirements. Deliverables should be proposal-quality.

### Git Branch Convention
Branches are named `week{N}-{topic}` (e.g., `week4-flink`).

### Deliverable Standards
- Each week produces production-quality artifacts: code, shell verification scripts, and architecture/operations documentation
- Verification scripts follow the pattern `scripts/verify_*.sh` or `scripts/verify_*.py`
- Weekly lab guides live in `docs/guides/`
- Deliverable documents and scripts live in domain folders such as `docs/kafka/`, `docs/nifi/`, `scripts/kafka/`, and `scripts/nifi/`
- New artifacts should be filed by domain responsibility, not by week number
- Before creating or modifying documents, guides, instruction files, or repository-structure-related assets, first present the proposed change, the reason for it, and the target path(s), then explicitly ask whether the user wants the file created or modified.
- Apply the same confirmation-first approach to path corrections, file moves, and stakeholder-facing deliverables so the user can approve direction before edits are made.

### Commit Message Convention
- When writing or suggesting a git commit command, use a single `-m` option with a multi-line message.
- Format: summary line, blank line, then flat `- ` bullets for the main changes.
- The summary should stay short and reflect the real scope of the commit.
- Commit messages should be written in Korean by default unless the user explicitly requests another language.

### Delta Lake Medallion Architecture (Week 5+)
- **Bronze**: Raw ingestion from Kafka/files with idempotent MERGE
- **Silver**: Cleansed, deduplicated, quality-validated
- **Gold**: Business aggregates (daily_summary, customer_stats, fee_settlement)

### Kafka Topic Naming
Format: `<domain>.<entity>.<event>` (e.g., `nexuspay.events.ingested`)

### Redis License Note
Redis 8 added AGPLv3 after 2025-05-01. Use Redis 7 in this lab to avoid license complications.

## Business Context

This project is the sole portfolio vehicle for a consulting business launch. Code quality, documentation quality, and the end-to-end demo narrative matter as much as technical correctness. Each week's repository state should be demonstrable to a CTO-level audience.

**Revenue milestone**: The first operations/maintenance contract (KRW 2–3M/month recurring) is the critical survival milestone, more important than individual project wins.

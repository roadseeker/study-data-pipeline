# CLAUDE.md — Pipeline Lab

## Project Purpose

This is a **data pipeline and AI/ML consulting portfolio project** built to support a solo consulting business launch. The practitioner is building real, deployable portfolio artifacts across two domains:

- **Domain A**: Apache open-source-based data pipeline (Kafka, NiFi, Flink, Spark, Airflow)
- **Domain B**: ML model design, MLflow, LLM/RAG adoption

The business target: mid-sized Korean companies in finance, fintech, and manufacturing with legacy RDBMS and limited AI capabilities. The differentiator is integrated pipeline-to-AI design using pure Apache open source (no commercial licenses like Confluent or Informatica).

## Current Phase

**Phase 1 — Capability Completion (Months 1–4, full-time)**

Domain A pipeline practice is structured as an 8-week program using a fictional fintech company "PayNex" as the scenario. The current branch `week1-pipeline-foundation` corresponds to **Week 1: environment setup**.

| Week | Topic | Status |
|------|-------|--------|
| Week 1 | Full-stack Docker Compose setup (Kafka, NiFi, Flink, Spark, Airflow, Redis, PostgreSQL) | In progress |
| Week 2 | Kafka deep dive (topic design, partitions, consumer groups, replication) | Pending |
| Week 3 | NiFi multi-source ingestion + Provenance tracking | Pending |
| Week 4 | Flink real-time stream processing + exactly-once | Pending |
| Week 5 | Spark batch ETL + Medallion architecture (Bronze/Silver/Gold) + Delta Lake | Pending |
| Week 6 | RDBMS migration: Spark JDBC + Debezium CDC | Pending |
| Week 7 | Airflow orchestration (DAG dependencies, SLA, failure recovery) | Pending |
| Week 8 | End-to-end integration rehearsal + acceptance test | Pending |

After Week 8, Domain B ML practice begins (Weeks 9–16: classification, regression, clustering, LLM/RAG, deep learning, RL).

## Tech Stack

### Data Pipeline
| Layer | Tools |
|-------|-------|
| Ingest | Apache Kafka 3.7 (KRaft mode), Apache NiFi 1.25, Kafka Connect |
| Transform | Apache Flink 1.18, Apache Spark 3.5, dbt Core |
| Store | Delta Lake, Apache Iceberg, HDFS, Amazon S3, PostgreSQL 16 |
| Orchestration | Apache Airflow 2.8 |
| Migration | Spark JDBC, Debezium (CDC) |
| Feature store | Redis 7, PostgreSQL |

### AI/ML
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
pipeline-lab/
├── docker-compose.yml          # Full stack definition (grows each week)
├── .env                        # Env vars — not committed
├── Dockerfile.airflow          # Custom Airflow image (added Week 7)
├── config/
│   ├── kafka/                  # Topic naming conventions, config docs
│   ├── nifi/                   # Processor group designs, JOLT specs, Avro schemas
│   ├── flink/                  # Placeholder
│   ├── spark/                  # Placeholder
│   ├── airflow/                # Placeholder
│   ├── debezium-mysql-connector.json  # CDC connector (Week 6)
│   └── e2e/                    # Business-day scenario YAML (Week 8)
├── dags/                       # Airflow DAG files
├── plugins/                    # Airflow alerting plugin (Slack/email)
├── docs/
│   ├── 00_consulting_report_v2.md   # Business strategy report (Korean)
│   ├── 00_consulting_report_en.md   # Business strategy report (English)
│   ├── 01_week1_lab_guide.md
│   ├── ...08_week8_lab_guide.md
│   └── final/                  # Acceptance test reports, architecture docs
├── scripts/                    # Health checks, producers, simulators, verification
│   └── e2e/                    # End-to-end rehearsal scripts (Week 8)
├── spark-etl/                  # Week 5 Medallion ETL (Bronze→Silver→Gold)
│   ├── config/                 # etl_config.yaml, quality_rules.yaml
│   ├── lib/                    # SparkSession factory, schema registry, quality checker
│   └── jobs/                   # bronze_ingestion.py, silver_transformation.py, gold_aggregation.py
├── spark-jobs/
│   ├── migration/              # Week 6: jdbc_full_export.py, cdc_to_delta.py
│   └── orchestration/         # Week 7: master_refresh.py
├── flink-jobs/                 # Week 4 Java-based stream processing
│   └── src/main/java/com/paynex/flink/
│       ├── job/                # TransactionAggregationJob, FraudDetectionJob
│       ├── function/           # Aggregation, window, fraud detection functions
│       ├── model/              # PaynexEvent, AggregatedResult, FraudAlert POJOs
│       └── util/               # Deserializer, config util, exactly-once sink builder
└── data/
    ├── sample/
    ├── settlement/             # NiFi-collected CSV files
    └── delta/                  # Delta Lake storage (Bronze/Silver/Gold + migration)
```

## Service Ports (Docker)

| Service | Container | Port |
|---------|-----------|------|
| PostgreSQL | lab-postgres | 5432 |
| Redis | lab-redis | 6379 |
| Kafka (KRaft) | lab-kafka | 29092 |
| NiFi | lab-nifi | 8080 (http://localhost:8080/nifi, admin/nifi1234admin) |
| Flink JobManager | lab-flink-jm | 8081 |
| Spark Master | lab-spark-master | 8082, 7077 |
| Airflow | lab-airflow-web | 8083 (admin/admin1234) |
| MySQL (legacy, Week 6) | lab-mysql | 3306 |
| Kafka Connect (Week 6) | lab-kafka-connect | 8084 |
| Payment API (Week 3) | lab-payment-api | 5050 |

## Key Conventions

### PayNex Scenario
All pipeline practice is framed around a fictional fintech company "PayNex" data modernization PoC. Each week has a specific stakeholder scenario (CTO, CFO, COO, CIO) that drives the requirements. Deliverables should be proposal-quality.

### Git Branch Convention
Branches are named `week{N}-{topic}` (e.g., `week1-pipeline-foundation`).

### Deliverable Standards
- Each week produces production-quality artifacts: code, shell verification scripts, and architecture/operations documentation
- Verification scripts follow the pattern `scripts/verify_*.sh` or `scripts/verify_*.py`
- Documentation in `docs/` mirrors the week structure

### Delta Lake Medallion Architecture (Week 5+)
- **Bronze**: Raw ingestion from Kafka/files with idempotent MERGE
- **Silver**: Cleansed, deduplicated, quality-validated
- **Gold**: Business aggregates (daily_summary, customer_stats, fee_settlement)

### Kafka Topic Naming
Format: `<domain>.<entity>.<event>` (e.g., `paynex.events.ingested`)

### Redis License Note
Redis 8 added AGPLv3 after 2025-05-01. Use Redis 7 in this lab to avoid license complications.

## Business Context

This project is the sole portfolio vehicle for a consulting business launch. Code quality, documentation quality, and the end-to-end demo narrative matter as much as technical correctness. Each week's repository state should be demonstrable to a CTO-level audience.

**Revenue milestone**: The first operations/maintenance contract (KRW 2–3M/month recurring) is the critical survival milestone, more important than individual project wins.

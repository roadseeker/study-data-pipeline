# CLAUDE.md — Pipeline Lab

This file provides repository guidance for Claude-style coding agents working in `c:\study\study-data-pipeline`. It mirrors the repository-wide rules in `AGENTS.md` and should be kept aligned with that file.

## Project Purpose

This repository is a portfolio-grade **data pipeline and AI/ML consulting project** built to support a solo consulting business launch.

There are two connected domains:

- **Domain A**: Apache open-source data pipeline implementation and operations
- **Domain B**: AI/ML adoption, model delivery, and LLM/RAG integration

The practical goal is not only to make the code work, but to produce artifacts that can be shown to CTO-level stakeholders as proposal-quality consulting deliverables.

## Current Working Context

- Current learning and build phase: **Phase 1 — Capability Completion**
- Current branch convention: `week{N}-{topic}`
- Current working branch context: `week5-spark`
- Current project progression:
  - Week 1: environment and full-stack Docker Compose foundation
  - Week 2: Kafka
  - Week 3: NiFi
  - Week 4: Flink
  - Week 5: Spark batch ETL and Delta Lake
  - Week 6: Spark JDBC and Debezium CDC migration
  - Week 7: Airflow orchestration
  - Week 8: end-to-end integration and acceptance rehearsal

When making changes, preserve the weekly progression. Do not introduce later-week implementation details into earlier-week assets unless the user explicitly asks for that.

## Scenario Context

All pipeline work is framed around the fictional fintech company **Nexus Pay**. Nexus Pay is an MSA-based payment service being developed by the product engineering team with the goal of becoming a stable and scalable payment platform.

In this repository, the working role is to design, implement, validate, and operate the data pipeline that supports the Nexus Pay service. Week-by-week deliverables should fit that scenario and feel like realistic consulting outputs for stakeholders such as the CTO, CIO, CFO, and COO.

Use this framing consistently in:

- architecture documents
- runbooks and operations guides
- DAGs, scripts, and examples
- naming of datasets, topics, flows, and demo artifacts

## Repository Structure

- `docker-compose.yml`: central full-stack lab definition that evolves by week
- `config/`: architecture configs, schemas, connector definitions, topic conventions
- `dags/`: Airflow DAGs and orchestration assets
- `docs/`: consulting reports, weekly lab guides, domain-specific operations and architecture docs
- `scripts/`: health checks, simulators, verification utilities, rehearsal scripts
- `spark-etl/`: Week 5 batch ETL and Medallion architecture assets
- `spark-jobs/`: Week 6 to 7 migration and orchestration jobs
- `flink-jobs/`: Week 4 Java-based real-time stream processing code
- `data/`: local sample data, settlement files, Delta Lake outputs

## Artifact Placement Rules

- Weekly lab guides belong under `docs/guides/` and keep the `01_...` to `08_...` naming pattern.
- Weekly deliverable documents do not stay at the `docs/` root. Store them in the domain folder that matches the stack area:
  - `docs/foundation/`
  - `docs/kafka/`
  - `docs/nifi/`
  - `docs/flink/`
  - `docs/spark/`
  - `docs/airflow/`
  - `docs/reports/`
- Weekly script deliverables do not stay at the `scripts/` root. Store them in the matching domain folder:
  - `scripts/foundation/`
  - `scripts/kafka/`
  - `scripts/nifi/`
  - add other domain folders later only when that week produces executable assets
- When a new week adds a document or script, place it by domain and responsibility, not by week number.
- If a week guide references an artifact, update the guide path at the same time as the file move.

## Working Rules

- Keep changes aligned with the current week or the explicit user request.
- Prefer minimal, focused edits over speculative expansion.
- Treat docs as first-class deliverables, not secondary notes.
- Maintain consistency between code, verification scripts, and documentation.
- Favor production-style naming and realistic business examples over toy examples.
- Preserve the Apache open-source positioning. Do not casually replace the stack with commercial alternatives.
- Use Redis 7 assumptions unless the user explicitly requests another version.

## Command Style

- The user primarily uses Git Bash.
- Provide shell commands in Bash syntax by default, including line continuations with `\`.
- Use PowerShell syntax only when the user explicitly asks for it or when a Windows-specific operation requires it.
- For Docker container commands, prefer Linux/container paths such as `/opt/spark-etl` and `/data/lakehouse`.
- When referencing local workspace files, clarify Windows host paths separately when helpful.

## Documentation Standards

- Write documentation in a professional consulting style.
- Keep architecture and operations documents clear enough for technical stakeholders.
- When creating new docs, explain purpose, assumptions, steps, expected outputs, and validation points.
- Weekly deliverables should feel demo-ready and portfolio-ready.
- In weekly lab guides, keep `Day N 완료 기준` in the day section itself, and record dated completion verification notes at the start of that week's deliverables checklist section.

## Implementation Standards

- Python is the primary language for scripts and ETL utilities.
- Java is used for Flink jobs.
- Shell scripts should be readable, task-oriented, and verification-friendly.
- Keep verification assets discoverable with names like `verify_*.sh` or `verify_*.py` when appropriate.
- Prefer realistic business-oriented sample records and production-style identifiers.
- Use **Nexus Pay** for human-facing scenario names, service descriptions, and stakeholder narratives.
- Standardize machine-readable identifiers on `nexuspay` / `NexusPay` for topics, package names, job IDs, and example assets unless compatibility with an existing artifact requires otherwise.

## Data and Environment Safety

- Do not commit secrets from `.env`.
- Treat `data/`, generated artifacts, logs, checkpoints, and local runtime outputs as disposable lab outputs unless the user explicitly wants them versioned.
- Avoid destructive cleanup beyond the requested scope.

## Architecture Conventions

- Kafka topic naming: `<domain>.<entity>.<event>`
- Spark Medallion layering:
  - Bronze: raw ingestion
  - Silver: cleansed and validated
  - Gold: business aggregates
- Airflow assets should reflect orchestration, dependency management, SLA monitoring, and recovery concerns.
- Migration work should distinguish between full load, incremental load, and CDC.

## Tech Stack Notes

### Data Pipeline

| Layer | Tools |
|-------|-------|
| Ingest | Apache Kafka, Apache NiFi |
| Transform | Apache Flink, Apache Spark |
| Store | PostgreSQL, Redis 7, Delta Lake/local data workspace |
| Orchestration | Apache Airflow |
| Migration | Spark JDBC, Debezium CDC |

### AI/ML Target Scope

| Layer | Tools |
|-------|-------|
| ML frameworks | scikit-learn, XGBoost, LightGBM |
| Experiment tracking | MLflow |
| Inference | FastAPI, uvicorn |
| LLM local | Ollama |
| LLM cloud | OpenAI APIs when explicitly needed |
| Vector DB | Qdrant |
| Embeddings | sentence-transformers |
| Dashboard | Streamlit |

MLflow, FastAPI, Qdrant, and RAG are target learning and portfolio components, not assumed completed experience unless the current task or repository state explicitly shows that they have been implemented.

## Service Ports

| Service | Container | Port |
|---------|-----------|------|
| PostgreSQL | `lab-postgres` | 5432 |
| Redis | `lab-redis` | 6379 |
| Kafka broker 1 | `lab-kafka-1` | 30092 |
| Kafka broker 2 | `lab-kafka-2` | 30093 |
| Kafka broker 3 | `lab-kafka-3` | 30094 |
| NiFi | `lab-nifi` | 8443 or configured lab port |
| Flink JobManager | `lab-flink-jm` | 8081 |
| Spark Master | `lab-spark-master` | 8082, 7077 |
| Airflow Webserver | `lab-airflow-web` | 8083 |
| Payment API | `lab-payment-api` | 5050 |

## Agent Behavior

- Before making broad changes, understand which week and layer the task belongs to.
- If a request is ambiguous, prefer the interpretation most consistent with the current repo phase and existing docs.
- Do not rewrite unrelated parts of the repository for style alone.
- When adding new files, keep them in the directory structure implied by the weekly lab design.
- If a change affects docs and implementation together, keep them synchronized.
- Before creating or modifying documents, guides, AGENTS instructions, CLAUDE instructions, or repository-structure-related assets, first present the proposed change, the reason for it, and the target path(s), then explicitly ask whether the user wants the file created or modified.
- Apply the same confirmation-first approach to path corrections, file moves, and stakeholder-facing deliverables so the user can approve the direction before edits are made.

## Business Context

This project is the sole portfolio vehicle for a consulting business launch. Code quality, documentation quality, and the end-to-end demo narrative matter as much as technical correctness.

Each week's repository state should be demonstrable to a CTO-level audience. The first operations/maintenance contract is an important survival milestone, but weekly work should remain grounded in realistic implementation, verification, and consulting-grade documentation.

## Commit Message Convention

- When suggesting or writing a git commit command, use a single `-m` option with a multi-line message body.
- Format commit messages as: first line summary, blank line, then flat `- ` bullets describing the main changes.
- Keep the summary concise and scoped to the actual change set.
- Write commit messages in Korean by default unless the user explicitly requests another language.

# AGENTS.md — Pipeline Lab

This file provides instructions for coding agents working anywhere in this repository. Its scope is the entire repo rooted at `c:\study\study-data-pipeline`.

## Project Purpose

This repository is a portfolio-grade **data pipeline and AI/ML consulting project** built to support a solo consulting business launch.

There are two connected domains:

- **Domain A**: Apache open-source data pipeline implementation and operations
- **Domain B**: AI/ML adoption, model delivery, and LLM/RAG integration

The practical goal is not only to make the code work, but to produce artifacts that can be shown to CTO-level stakeholders as proposal-quality consulting deliverables.

## Current Working Context

- Current learning and build phase: **Phase 1 — Capability Completion**
- Current branch convention: `week{N}-{topic}`
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

All pipeline work is framed around the fictional fintech company **PayNex**. Week-by-week deliverables should fit that scenario and feel like realistic consulting outputs for stakeholders such as the CTO, CIO, CFO, and COO.

Use this framing consistently in:

- architecture documents
- runbooks and operations guides
- DAGs, scripts, and examples
- naming of datasets, topics, flows, and demo artifacts

## Repository Structure

- `docker-compose.yml`: central full-stack lab definition that evolves by week
- `config/`: architecture configs, schemas, connector definitions, topic conventions
- `dags/`: Airflow DAGs and orchestration assets
- `docs/`: consulting report, weekly lab guides, operations docs, final reports
- `scripts/`: health checks, simulators, verification utilities, rehearsal scripts
- `spark-etl/`: Week 5 batch ETL and Medallion architecture assets
- `spark-jobs/`: Week 6 to 7 migration and orchestration jobs
- `flink-jobs/`: Week 4 Java-based real-time stream processing code
- `data/`: local sample data, settlement files, Delta Lake outputs

## Working Rules

- Keep changes aligned with the current week or the explicit user request.
- Prefer minimal, focused edits over speculative expansion.
- Treat docs as first-class deliverables, not secondary notes.
- Maintain consistency between code, verification scripts, and documentation.
- Favor production-style naming and realistic business examples over toy examples.
- Preserve the Apache open-source positioning. Do not casually replace the stack with commercial alternatives.
- Use Redis 7 assumptions unless the user explicitly requests another version.

## Documentation Standards

- Write documentation in a professional consulting style.
- Keep architecture and operations documents clear enough for technical stakeholders.
- When creating new docs, explain purpose, assumptions, steps, expected outputs, and validation points.
- Weekly deliverables should feel demo-ready and portfolio-ready.

## Implementation Standards

- Python is the primary language for scripts and ETL utilities.
- Java is used for Flink jobs.
- Shell scripts should be readable, task-oriented, and verification-friendly.
- Keep verification assets discoverable with names like `verify_*.sh` or `verify_*.py` when appropriate.
- Prefer realistic identifiers such as `paynex.events.ingested` and business-oriented sample records.

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

## Agent Behavior

- Before making broad changes, understand which week and layer the task belongs to.
- If a request is ambiguous, prefer the interpretation most consistent with the current repo phase and existing docs.
- Do not rewrite unrelated parts of the repository for style alone.
- When adding new files, keep them in the directory structure implied by the weekly lab design.
- If a change affects docs and implementation together, keep them synchronized.

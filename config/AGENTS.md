# AGENTS.md — `config/`

This file applies to all configuration assets under `config/`.

## Purpose

This folder contains configuration, schema, and architecture-control assets that support weekly lab implementations.

## Scope by Area

- `kafka/`: Week 2 topic naming, retention, partitioning, replication
- `nifi/`: Week 3 processor-group design, JOLT specs, schema standardization
- `flink/`, `spark/`, `airflow/`: environment and future extension placeholders
- `debezium-mysql-connector.json`: Week 6 CDC connector settings
- `e2e/`: Week 8 scenario orchestration inputs

## Rules

- Keep configuration files aligned with the documented weekly scenario.
- Prefer explicit, readable values over overly abstract placeholders.
- Use PayNex-oriented names and realistic business semantics.
- Do not add commercial-vendor-specific assumptions unless the user explicitly asks for them.
- Preserve the Kafka topic naming convention: `<domain>.<entity>.<event>`.
- For schemas and transformation specs, keep field names and data types consistent across scripts, jobs, and docs.

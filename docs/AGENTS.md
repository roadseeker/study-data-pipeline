# AGENTS.md — `docs/`

This file applies to all documentation under `docs/`.

## Purpose

Documents in this folder are portfolio-grade consulting deliverables, not casual notes. They should read as materials that can be shown to technical stakeholders, customers, or evaluators.

## Folder Mapping

- `reports/`: business strategy and commercialization context, cross-week reports
- `guides/`: `01_week1_lab_guide.md` to `08_week8_lab_guide.md`
- `foundation/`: base environment and shared platform docs
- `kafka/`, `nifi/`, `flink/`, `spark/`, `airflow/`: domain deliverables and operations docs

## Writing Rules

- Write in a professional consulting tone.
- Keep structure clear: scenario, objective, architecture, steps, validation, expected outcomes.
- Use realistic Nexus Pay examples and business terminology.
- Use `nexuspay` / `NexusPay` machine-readable identifiers consistently in topics, file names, package names, DAG IDs, and example assets.
- Preserve consistency with the repository layout and actual filenames.
- If implementation changes affect docs, update the relevant guides and operations notes.
- Keep weekly lab guides in `docs/guides/`, but place real deliverable documents in the domain folder that matches the technology area.

## Weekly Guidance

- Week 1 to 3 docs should emphasize environment setup, ingestion, and validation.
- Week 4 docs should emphasize stream-processing correctness, watermarks, checkpoints, and exactly-once behavior.
- Week 5 docs should emphasize Medallion architecture, Delta Lake operations, and data quality.
- Week 6 docs should distinguish full load, incremental load, and CDC clearly.
- Week 7 docs should emphasize orchestration, SLA, recovery, and operational ownership.
- Week 8 docs should read like customer-facing acceptance and rehearsal materials.

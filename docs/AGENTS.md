# AGENTS.md — `docs/`

This file applies to all documentation under `docs/`.

## Purpose

Documents in this folder are portfolio-grade consulting deliverables, not casual notes. They should read as materials that can be shown to technical stakeholders, customers, or evaluators.

## Week Mapping

- `00_consulting_report_*.md`: business strategy and commercialization context
- `01_week1_lab_guide.md` to `08_week8_lab_guide.md`: weekly hands-on lab guides
- `final/`: Week 8 acceptance-test and final architecture deliverables

## Writing Rules

- Write in a professional consulting tone.
- Keep structure clear: scenario, objective, architecture, steps, validation, expected outcomes.
- Use realistic PayNex examples and business terminology.
- Preserve consistency with the repository layout and actual filenames.
- If implementation changes affect docs, update the relevant guides and operations notes.

## Weekly Guidance

- Week 1 to 3 docs should emphasize environment setup, ingestion, and validation.
- Week 4 docs should emphasize stream-processing correctness, watermarks, checkpoints, and exactly-once behavior.
- Week 5 docs should emphasize Medallion architecture, Delta Lake operations, and data quality.
- Week 6 docs should distinguish full load, incremental load, and CDC clearly.
- Week 7 docs should emphasize orchestration, SLA, recovery, and operational ownership.
- Week 8 docs should read like customer-facing acceptance and rehearsal materials.

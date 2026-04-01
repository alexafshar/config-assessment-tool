# Config Assessment Tool

This document provides a quick-start guide for the 1.8.0 release. This release introduces docker usage improvements, UI improvements, feature and bug fixes.

## Table of Contents
1. [Overview](#overview)
2. [Quick start](#quick-start)
3. [Output artifacts](#output-artifacts)
4. [Requirements and limitations](#requirements-and-limitations)
5. [Support](#support)
6. [Troubleshooting](#troubleshooting)

---

## Overview

Config Assessment Tool helps evaluate AppDynamics instrumentation and configuration health, then generates report artifacts your team can use for analysis and follow-up actions. For a more detailed tool overview and architecture, see [`General Description`](docs/OVERVIEW.md#general-description).

---

## Quick start

1. Review prerequisites and prepare your job file in [`docs/RUNBOOK.md`](docs/RUNBOOK.md#prerequisites-and-setup).
2. Choose how you want to run CAT:
   - Platform executables (easiest way to run): [`docs/RUNBOOK.md#run-using-platform-executables`](docs/RUNBOOK.md#run-using-platform-executables)
   - Docker: [`docs/RUNBOOK.md#run-using-docker`](docs/RUNBOOK.md#run-using-docker)
   - Shell script or source: [`docs/RUNBOOK.md#other-ways-to-run`](docs/RUNBOOK.md#other-ways-to-run)
3. Run the tool and review generated files in `output/`. This directory generates once you run the tool.
4. If you hit issues, use [`docs/RUNBOOK.md`](docs/RUNBOOK.md) and [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md).

## Output artifacts
Generated in `output/{jobName}` (varies by job name):
- `{jobName}-cx-presentation.pptx` # PowerPoint summary report
- `{jobName}-MaturityAssessment-apm.xlsx`  # Summary Excel report for APM
- `{jobName}-MaturityAssessment-brum.xlsx` # Summary Excel report for Browser RUM
- `{jobName}-MaturityAssessment-mrum.xlsx` # Summary Excel report for Mobile RUM
- `{jobName}-AgentMatrix.xlsx`
- `{jobName}-CustomMetrics.xlsx`
- `{jobName}-License.xlsx`  # License usage summary report
- `{jobName}-MaturityAssessmentRaw-apm.xlsx`
- `{jobName}-MaturityAssessmentRaw-brum.xlsx`
- `{jobName}-MaturityAssessmentRaw-mrum.xlsx`
- `{jobName}-ConfigurationAnalysisReport.xlsx` # Prescribed steps to raise maturity levels
- `controllerData.json` # Raw data dump of all controller API responses for debugging and custom analysis
- `info.json`

Generated in `output/archive` directory
- Archived reports organized by timestamp and job name for record-keeping and trend analysis. Every time you run CAT, the output files are also copied to the archive directory with a timestamp and maintained for future reference and analysis.  

---

## Requirements and limitations
Requirements:
- Python 3.12 for source-based runs
- Docker engine for Docker-based runs
- No local Python or Docker required for platform executable bundles

Known limitation:
- Certain data collector snapshot lookups are limited by product/API behavior.

---

## Support
- Open GitHub issues for bugs, feature requests, and feedback:
  `https://github.com/Appdynamics/config-assessment-tool`
- You may include log output snippets, stack trace etc. DO NOT include proprietary data such as controller URL's etc.
- Enable debug via UI checkbox or CLI flags `--debug` / `-d`.

---

## Troubleshooting
For common errors, diagnostics, and fixes, see [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md), including [`Proxy issues`](docs/TROUBLESHOOTING.md#proxy-issues).

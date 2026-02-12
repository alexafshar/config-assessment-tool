# Config Assessment Tool - Beta Release Runbook (v1.8.0-beta.1)

This document provides a quick-start guide for the v1.8.0-beta.1 release. This beta release introduces usage improvements, UI improvements, feature and bug fixes. 

**[View Full Release Notes](https://github.com/Appdynamics/config-assessment-tool/releases/tag/v1.8.0-beta.1)**

## Table of Contents
- [1. Running from source (`config-assessment-tool.sh`)](#1-running-from-source-config-assessment-toolsh)
    - [Prerequisites](#prerequisites)
    - [Usage](#usage)
    - [Plugin Management](#plugin-management)
    - [Shutdown](#shutdown)
    - [Getting Help](#getting-help)
- [2. Direct Docker Usage](#2-direct-docker-usage)
    - [Run the UI (Frontend + Backend)](#run-the-ui-frontend--backend)
    - [Run Headless (Backend Only)](#run-headless-backend-only)
    - [Getting Help](#getting-help-1)
- [3. Platform Executable (Standalone Binary)](#3-platform-executable-standalone-binary)
    - [Headless Mode](#headless-mode)
    - [UI Mode](#ui-mode)
    - [Getting Help](#getting-help-2)
- [4. Configuration (Important)](#4-configuration-important)
    - [Authentication Options (`authType`)](#authentication-options-authtype)

# 1. Running from source 

The `config-assessment-tool.sh` script is the recommended way to run the tool on macOS and Linux once you have the source locally. 

## Prerequisites
*   **Docker** (Recommended for UI & Headless modes)
*   *OR* Python 3.12+ with Pipenv (for source mode)

## Usage

**Start the User Interface (UI):**
This will launch the Web UI in your default browser.
```bash
# Using Docker (Recommended)
./config-assessment-tool.sh --start docker --ui
# Or simply (defaults to UI)
./config-assessment-tool.sh --start docker

# From Source
./config-assessment-tool.sh --start --ui
```

**Run Headless (Backend Only):**
Run the assessment directly without the UI.
```bash
# Using Docker
./config-assessment-tool.sh --start docker -j <job-file-name>
# Example: ./config-assessment-tool.sh --start docker -j MyJob

# From Source
./config-assessment-tool.sh --start -j <job-file-name>
```

## Plugin Management
```bash
# List available plugins
./config-assessment-tool.sh --plugin list

# Start a specific plugin
./config-assessment-tool.sh --plugin start <plugin_name>
```

## Shutdown
Stops running containers and cleanup processes.
```bash
./config-assessment-tool.sh shutdown
```

## Getting Help
Display the help menu with all available arguments.
```bash
./config-assessment-tool.sh --help
```

---

# 2. Direct Docker Usage

If you prefer to run Docker commands directly without the helper script, use the beta tag `1.8.0-beta.1`.

## Run the UI (Frontend + Backend)
```bash
docker run \
  --name "cat-tool-beta" \
  --rm \
  -p 8501:8501 \
  -v "$(pwd)/input":/app/input \
  -v "$(pwd)/output":/app/output \
  -v "$(pwd)/logs":/app/logs \
  ghcr.io/appdynamics/config-assessment-tool:1.8.0-beta.1 \
  --ui
```
*Access the UI at http://localhost:8501*

## Run Headless (Backend Only)
Pass backend arguments directly (e.g., `-j`).
```bash
docker run \
  --name "cat-tool-beta-backend" \
  --rm \
  -v "$(pwd)/input":/app/input \
  -v "$(pwd)/output":/app/output \
  -v "$(pwd)/logs":/app/logs \
  ghcr.io/appdynamics/config-assessment-tool:1.8.0-beta.1 \
  -j <job-file-name>
```

## Getting Help
Display the help menu for the container.
```bash
docker run ghcr.io/appdynamics/config-assessment-tool:1.8.0-beta.1 --help
```

---

# 3. Platform Executable (Standalone Binary)

If you have meant the standalone binaries downloadable from the Releases page (Windows .zip or Linux .tgz):

## Headless Mode
1.  Navigate to the directory where you extracted the release.
2.  Run the executable:
    *   **Linux**: `./config-assessment-tool -j <job-file>`
    *   **Windows**: `.\config-assessment-tool.exe -j <job-file>`

## UI Mode
*Note: Beta binaries contain the UI. You can launch it using `--ui` or `--run`.*
1.  Run the executable with the flag:
    *   **Linux**: `./config-assessment-tool --ui`
    *   **Windows**: `.\config-assessment-tool.exe --ui`
2.  Open your browser to the URL displayed in the console (typically `http://localhost:8501`).

## Getting Help
Display the available command line arguments.
*   **Linux**: `./config-assessment-tool --help`
*   **Windows**: `.\config-assessment-tool.exe --help`

---

# 4. Job file configuration

Job files are configured as below.  There is a default job file provided at `input/jobs/DefaultJob.json` that you can edit with your controller credentials and settings. You can also create a new job file by copying this default one and editing as needed. If you are using the Web UI, you can also create a job file directly from the UI which will save them into the `input/jobs` directory using the hostname as the job file name however if subsequent edits to the file is needed, you will need to edit the file directly.

Edit `input/jobs/DefaultJob.json` (or your custom job file):

```json
{
  "host": "acme.saas.appdynamics.com",
  "port": 443, 
  "account": "acme",  
  "authType": "token", 
  "username": "api-client-name", 
  "pwd": "temporary-access-token", 
  "verifySsl": true,
  "useProxy": true,
  "applicationFilter": {
    "apm": ".*",
    "mrum": ".*",
    "brum": ".*"
  },
  "timeRangeMins": 1440
}
```

## Authentication Options (`authType`)
*   **`basic`**: Use Controller UI username and password. (Legacy)
*   **`token`** (Recommended):
    *   `username`: Use the API Client Name.
    *   `pwd`: Use the Temporary Access Token.
*   **`secret`**:
    *   `username`: Use the API Client Name.
    *   `pwd`: Use the Client Secret.

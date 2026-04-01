# Runbook

This guide is for operators who need the full set of run options, common commands, and expected outputs.

## Table of Contents
1. [Prerequisites and setup](#prerequisites-and-setup)
2. [Run using docker](#run-using-docker)
3. [Run using Platform Executables](#run-using-platform-executables)
4. [Other ways to run](#other-ways-to-run)
5. [Output artifacts](#output-artifacts)

---

## Prerequisites and setup

Choose the run path that matches your environment:

- Docker Desktop / Docker Engine for container-based runs
- Python 3.12 and Pipenv for source-based runs
- Platform executable bundle if you do not want to install Python locally

Required local directory layout:

```text
configuration-assessment-tool/
├── input/
│   ├── jobs/
│   └── thresholds/
├── logs/
└── output/
```

Edit `input/jobs/DefaultJob.json` or create your own file under `input/jobs/`.

```json
[
  {
    "host": "acme.saas.appdynamics.com",
    "port": 443,
    "ssl": true,
    "account": "acme",
    "authType": "token",
    "username": "foo",
    "pwd": "<encoded-or-plain-password>",
    "verifySsl": true,
    "useProxy": true,
    "applicationFilter": {
      "apm": ".*",
      "mrum": ".*",
      "brum": ".*"
    },
    "timeRangeMins": 1440
  }
]
```

If `authType` is omitted, the backend defaults to `basic` for backward compatibility.

Authentication options:

- `basic`: controller UI username and password
- `token`: API client name plus temporary access token
- `secret`: API client name plus client secret

Common job settings:

- `verifySsl`: validates TLS certificates; disable only for troubleshooting
- `useProxy`: tells CAT to honor configured proxy environment variables
- `applicationFilter`: regex filters for APM, Browser RUM, and Mobile RUM apps
- `timeRangeMins`: time window for analysis; default is `1440`
- `pwd`: written back in encoded form when the tool persists the file

Expected permissions typically include:

- Account Owner (default)
- Administrator (default)
- Analytics Administrator (default)
- Server Monitoring Administrator (default)

Windows Docker note:

- If you run CAT with Docker Desktop on Windows, make sure your local `input`, `output`, and `logs` directories are shared with Docker.

---

## Run using docker

Use direct Docker commands if you do not want to use the helper script.

```text
Usage: docker run [DOCKER_OPTIONS] <docker-image> [ --ui | ARGS ]

docker container requires you to provide information on where to
look for input jobs as well as output and log directories using
the -v option to mount local directories into the container.

DOCKER_OPTIONS:
  -p 8501:8501                         What port to access the Web UI if using --ui option. Defaults to 8501.
  -v <local input dir>:/app/input      Required. Must contain 'jobs' and 'thresholds' subfolders.
  -v <local output dir>:/app/output    Required. Destination for generated reports and archive dir.
  -v <local logs dir>:/app/logs        Recommended. Where to log job run output.

Example directory structure required:

  configuration-assessment-tool/
  ├── input
  │   ├── jobs
  │   │   └── DefaultJob.json         Job file (can have multiple job files)
  │   └── thresholds
  │       └── DefaultThresholds.json  Default thresholds file is good for most use cases
  ├── logs                            Where CAT logs program output. Optional. Created if not provided
  └── output                          Where all reports are saved. Required. Created if not provided

  --ui              Start the Web UI
  [ARGS]            Start the Backend (Headless) without UI

[ARGS]:
  -j, --job-file <name>                Job file name (default: DefaultJob)
  -t, --thresholds-file <name>         Thresholds file name (default: DefaultThresholds)
  -d, --debug                          Enable debug logging
  -c, --concurrent-connections <n>     Number of concurrent connections
```

### Use Web UI to run

```bash
docker run \
  --name "config-assessment-tool" \
  -v <config-assessment-tool-directory>/input:/app/input \
  -v <config-assessment-tool-directory>/output:/app/output \
  -v <config-assessment-tool-directory>/logs:/app/logs \
  -p 8501:8501 \
  --rm \
  ghcr.io/alexafshar/config-assessment-tool:latest --ui
```

Windows PowerShell:

```powershell
docker run `
  --name "config-assessment-tool" `
  -v <config-assessment-tool-directory>/input:/app/input `
  -v <config-assessment-tool-directory>/output:/app/output `
  -v <config-assessment-tool-directory>/logs:/app/logs `
  -p 8501:8501 `
  --rm `
  ghcr.io/alexafshar/config-assessment-tool:latest --ui
```

### Use headless mode

```bash
docker run \
  --name "config-assessment-tool" \
  -v <config-assessment-tool-directory>/input:/app/input \
  -v <config-assessment-tool-directory>/output:/app/output \
  -v <config-assessment-tool-directory>/logs:/app/logs \
  --rm \
  ghcr.io/alexafshar/config-assessment-tool:latest -j DefaultJob -t DefaultThresholds
```

### Getting help

```bash
docker run ghcr.io/alexafshar/config-assessment-tool:latest --help
```

---

## Run using Platform Executables

This is easiest way to run the tool or when you do not wish to install or use Docker or Python on the target host.

1. Download the bundle for your platform from the releases page.
2. Extract it.
3. Edit `input/jobs/DefaultJob.json` if needed.
4. Run the executable:

```bash
./config-assessment-tool --ui
./config-assessment-tool -j DefaultJob
./config-assessment-tool --help
```

Windows:

```powershell
.\config-assessment-tool.exe --ui
.\config-assessment-tool.exe -j DefaultJob
.\config-assessment-tool.exe --help
```

macOS note:

```bash
sudo xattr -rd com.apple.quarantine .
```

---

## Other ways to run

### Use the helper shell script

```bash
./config-assessment-tool.sh docker --ui
./config-assessment-tool.sh docker -j DefaultJob
./config-assessment-tool.sh --help
```

### Run from source

```bash
pipenv install
./config-assessment-tool.sh --ui
./config-assessment-tool.sh -j DefaultJob
```

### Plugin management

```bash
./config-assessment-tool.sh --plugin list
./config-assessment-tool.sh --plugin docs <plugin_name>
./config-assessment-tool.sh --plugin start <plugin_name>
```

### Shutdown

```bash
./config-assessment-tool.sh shutdown
```

---

## Output artifacts

Generated files are written under `output/` and may include:

- `{jobName}-cx-presentation.pptx`
- `{jobName}-MaturityAssessment-apm.xlsx`
- `{jobName}-MaturityAssessment-brum.xlsx`
- `{jobName}-MaturityAssessment-mrum.xlsx`
- `{jobName}-AgentMatrix.xlsx`
- `{jobName}-CustomMetrics.xlsx`
- `{jobName}-License.xlsx`
- `{jobName}-MaturityAssessmentRaw-apm.xlsx`
- `{jobName}-MaturityAssessmentRaw-brum.xlsx`
- `{jobName}-MaturityAssessmentRaw-mrum.xlsx`
- `{jobName}-ConfigurationAnalysisReport.xlsx`
- `controllerData.json`
- `info.json`


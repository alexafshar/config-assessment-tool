# CompareResults

**CompareResults** compares AppDynamics Configuration Assessment Tool (CAT) output workbooks for **APM**, **BRUM**, and **MRUM**.

It produces:

- **Excel comparison workbook** for detailed metric-level changes.
- **PowerPoint summary** for client-facing maturity direction.
- **JSON snapshot** used by the built-in **Insights** and trend views.

The tool is intended to be run locally from the root of this folder: `cat_compare`.

---

## Quick Start

From the `cat_compare` folder:

```bash
python3 run_tool.py
```

On Windows:

```powershell
python run_tool.py
```

The launcher creates or reuses `.venv`, installs requirements, starts the web UI, and tries to open your browser.

If the browser does not open automatically, go to:

```text
http://127.0.0.1:5000/
```

Stop the server with `Ctrl + C`.

---

## Supported Workbooks

The matcher expects non-raw CAT maturity assessment workbooks with filenames containing:

- `MaturityAssessment` and `apm`
- `MaturityAssessment` and `brum`
- `MaturityAssessment` and `mrum`

Examples:

```text
client-MaturityAssessment-apm.xlsx
client-MaturityAssessment-brum-Mar25.xlsx
client-MaturityAssessment-mrum-2025-05-12.xlsx
```

Files with `raw` in the filename are ignored. Excel temporary lock files such as `~$client-MaturityAssessment-apm.xlsx` are also ignored.

Both previous and current workbooks must be from the same AppDynamics controller. The tool checks this before running a comparison.

---

## UI Modes

### APM, BRUM, and MRUM

Use these tabs when you already know the exact previous and current workbook for one domain.

Upload:

- Previous workbook
- Current workbook

Then run the compare for that single domain.

### Folder Compare

Use **Folder Compare** when you want one previous-vs-current comparison across one or more domains.

Best when:

- You have exactly one previous assessment folder.
- You have exactly one current assessment folder.
- Each folder contains the relevant APM, BRUM, and/or MRUM maturity workbooks.

The tool picks the matching domain files and generates comparison outputs.

### Progression

Use **Progression** when you have two or more assessments and want to see trends for AppDynamics configuration maturity.

Progression uses a fixed baseline:

```text
Baseline assessment -> later assessment 1
Baseline assessment -> later assessment 2
Baseline assessment -> later assessment 3
```

For example:

```text
Jan -> Mar
Jan -> May
Jan -> Jun
```

The generated JSON snapshots feed the Insights trend views.

---

## Recommended Progression Setup

Use one controller per progression run.

If files are scattered across Downloads, Desktop, email attachments, or old output folders, copy the relevant non-raw maturity workbooks into one clean staging folder first.

Recommended structure:

```text
Client-Progression/
  2025-01-08/
    client-MaturityAssessment-apm.xlsx
    client-MaturityAssessment-brum.xlsx
    client-MaturityAssessment-mrum.xlsx
  2025-03-28/
    client-MaturityAssessment-apm.xlsx
    client-MaturityAssessment-brum.xlsx
    client-MaturityAssessment-mrum.xlsx
  2025-05-12/
    client-MaturityAssessment-apm.xlsx
    client-MaturityAssessment-brum.xlsx
    client-MaturityAssessment-mrum.xlsx
```

Also supported:

```text
Client-Progression/
  client-MaturityAssessment-apm-Jan25.xlsx
  client-MaturityAssessment-brum-Jan25.xlsx
  client-MaturityAssessment-mrum-Jan25.xlsx
  client-MaturityAssessment-apm-Mar25.xlsx
  client-MaturityAssessment-brum-Mar25.xlsx
  client-MaturityAssessment-mrum-Mar25.xlsx
  client-MaturityAssessment-apm-May25.xlsx
  client-MaturityAssessment-brum-May25.xlsx
  client-MaturityAssessment-mrum-May25.xlsx
```

The folder and file names above are examples. The important filename rules are:

- Include `MaturityAssessment`.
- Include `apm`, `brum`, or `mrum`.
- Avoid `raw`.
- Avoid mixing controllers in the same assessment group.

If the UI reports nested folders, browse one level deeper and select the folder that directly contains the assessment folders or workbooks.

---

## Outputs

Outputs are written to the configured `results/` folder.

Typical outputs:

- `Analysis_Summary_APM.xlsx`
- `Analysis_Summary_APM.pptx`
- `Analysis_Summary_BRUM.xlsx`
- `Analysis_Summary_BRUM.pptx`
- `Analysis_Summary_MRUM.xlsx`
- `Analysis_Summary_MRUM.pptx`
- `analysis_summary_<domain>_<timestamp>.json`

Progression comparisons also save stable `Progression_<DOMAIN>_...` output files so multiple runs do not overwrite each other.

---

## Insights

Open **Insights** from the UI after a comparison.

Insights uses generated JSON snapshots to show:

- Per-application improvements and degraded areas.
- Fixed-baseline maturity trends.
- Portfolio-style selected application summaries.

For progression trends, select a snapshot for the controller and the tool will use related snapshots for that controller where possible.

---

## Configuration

Excel recalculation is controlled by `config.json`:

```json
{
  "excel_recalculation_mode": "auto"
}
```

Modes:

- `auto`: use cached Summary values where possible; calculate supported Summary formulas in Python; fall back to Excel automation when needed.
- `always`: always use Excel automation. This is the rollback mode for maximum compatibility.
- `never`: never use Excel automation. Useful for diagnostics.

Microsoft Excel may still be required for workbooks that do not contain usable cached formula values and cannot be calculated by the Python fallback.

---

## Troubleshooting

### The app does not start

Run from the `cat_compare` folder:

```bash
python3 run_tool.py
```

Do not run `python app.py` from the folder root. If running Flask directly, use:

```bash
python -m webapp.app
```

### ModuleNotFoundError: No module named `compare_tool`

You are probably not running from the `cat_compare` folder. Change into this folder and run the launcher again.

### Controller mismatch

Previous and current workbooks must come from the same AppDynamics controller. Re-run with matching controller exports.

### Progression preview shows Mixed

The selected group contains workbooks from more than one controller. Split the files by controller or untick that group.

### Progression preview says nested folders detected

Browse one level deeper and select the folder containing the assessment folders or workbooks.

### Insights is blank

Confirm that:

- A JSON snapshot was generated.
- The comparison workbook contains an `Analysis` sheet.
- The selected domain and controller match the snapshot you want to inspect.

---

## Best Practices

- Keep one controller per comparison or progression run.
- Use meaningful assessment spacing, such as monthly or quarterly exports.
- Keep non-raw maturity workbooks only in progression staging folders.
- Close Excel popups or first-run prompts before running comparisons that require Excel automation.
- Keep generated outputs from important client runs in a known location outside temporary downloads.

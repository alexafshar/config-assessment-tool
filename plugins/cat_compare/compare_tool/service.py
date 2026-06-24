"""
service.py
----------
This module contains the core logic for running comparisons.

Purpose:
- Implements functions for APM, BRUM, and MRUM comparisons.
- Processes uploaded files and generates comparison results.

Key Functions:
- `run_comparison`: Handles APM comparisons.
- `run_comparison_brum`: Handles BRUM comparisons.
- `run_comparison_mrum`: Handles MRUM comparisons.
"""

import os
import logging
from typing import Dict, Tuple, Optional, Any, List
from pathlib import Path

from .excel_io import (
    inspect_summary_formula_cache,
    summary_missing_cache_is_supported,
    save_workbook,
    check_controllers_match,
)
from .summary import (
    create_summary_workbooks,
    compare_files_summary,
    copy_summary_to_result,
)
from .comparers import compare_files_other_sheets
from .insights import build_comparison_json

from compare_tool.powerpoint.apm import generate_powerpoint_from_apm as generate_apm_ppt
from compare_tool.powerpoint.brum import generate_powerpoint_from_brum
from compare_tool.powerpoint.mrum import generate_powerpoint_from_mrum



logger = logging.getLogger(__name__)

# Base directory of the project (points at compare-plugin root)
BASE_DIR = Path(__file__).resolve().parent.parent
LAST_EXCEL_RECALCULATION_STATUS: Dict[str, str] = {}


def get_excel_recalculation_status(domain: str) -> str:
    return LAST_EXCEL_RECALCULATION_STATUS.get((domain or "").upper(), "")


def _resolve_template_path(config: Dict, domain_key: str, default_name: str) -> Optional[str]:
    """
    Build an absolute template path from config.json settings.

    domain_key examples:
      - "apm_template_file"
      - "brum_template_file"
      - "mrum_template_file"

    We expect config.json to contain something like:
      "TEMPLATE_FOLDER": "templates",
      "apm_template_file": "template.pptx",
      "brum_template_file": "template_brum.pptx",
      "mrum_template_file": "template_mrum.pptx"
    """
    folder_name = config.get("TEMPLATE_FOLDER") or config.get("template_folder")
    if not folder_name:
        logger.warning("No TEMPLATE_FOLDER/template_folder defined in config.json")
        return None

    filename = config.get(domain_key, default_name)
    template_path = BASE_DIR / folder_name / filename
    if template_path.exists():
        return str(template_path)

    logger.warning("Template not found at %s", template_path)
    return None


def _prepare_summary_formula_values(
    previous_file_path: str,
    current_file_path: str,
    config: Dict,
    domain: str,
) -> None:
    """
    Ensure Summary formulas can be read as values.

    Modes:
      - always: current behavior; open and save both workbooks with Excel.
      - auto: skip Excel when Summary formula cached values already exist.
      - never: never use Excel; useful for proving no-Excel behavior.
    """
    mode = str(config.get("excel_recalculation_mode", "always")).strip().lower()
    status = ""
    if mode not in {"always", "auto", "never"}:
        logger.warning(
            "[%s] Unknown excel_recalculation_mode=%r; using 'always'.",
            domain,
            mode,
        )
        mode = "always"

    if mode == "always":
        logger.info("[%s] Recalculating workbooks with Excel (mode=always).", domain)
        save_workbook(previous_file_path)
        save_workbook(current_file_path)
        status = "Excel recalculation used before comparison."
        LAST_EXCEL_RECALCULATION_STATUS[domain.upper()] = status
        return

    diagnostics = [
        inspect_summary_formula_cache(previous_file_path),
        inspect_summary_formula_cache(current_file_path),
    ]
    missing = [
        d for d in diagnostics
        if not d["summary_exists"] or int(d["missing_cached_formula_cells"]) > 0
    ]

    for d in diagnostics:
        logger.info(
            "[%s] Summary cache check: path=%s formulas=%s missing_cached=%s sample_missing=%s",
            domain,
            d["path"],
            d["formula_cells"],
            d["missing_cached_formula_cells"],
            list(d["missing_cached_coordinates"])[:10],
        )

    if not missing:
        logger.info("[%s] Summary cached values available; skipping Excel automation.", domain)
        status = "Excel recalculation skipped; Summary cached values were available."
        LAST_EXCEL_RECALCULATION_STATUS[domain.upper()] = status
        return

    if all(summary_missing_cache_is_supported(str(d["path"])) for d in missing):
        logger.info(
            "[%s] Missing Summary cached values use supported formulas; "
            "skipping Excel and calculating Summary values in Python.",
            domain,
        )
        status = "Excel recalculation skipped; Summary values were calculated locally."
        LAST_EXCEL_RECALCULATION_STATUS[domain.upper()] = status
        return

    if mode == "never":
        logger.warning(
            "[%s] Summary cached values are missing, but Excel recalculation is disabled.",
            domain,
        )
        status = (
            "Excel recalculation disabled; missing Summary cached values were not refreshed."
        )
        LAST_EXCEL_RECALCULATION_STATUS[domain.upper()] = status
        return

    logger.info(
        "[%s] Summary cached values missing; falling back to Excel recalculation.",
        domain,
    )
    save_workbook(previous_file_path)
    save_workbook(current_file_path)
    status = "Excel recalculation used because unsupported Summary cached values were missing."
    LAST_EXCEL_RECALCULATION_STATUS[domain.upper()] = status


# ---------------------------------------------------------------------------
# APM
# ---------------------------------------------------------------------------
def run_comparison(
    previous_file_path: str,
    current_file_path: str,
    config: Dict,
) -> Tuple[str, str]:
    """
    High-level comparison pipeline for APM.
    Returns (output_file_path, powerpoint_output_path).
    """

    upload_folder = config["upload_folder"]
    result_folder = config["result_folder"]

    # Resolve APM template path using config + BASE_DIR
    template_path = _resolve_template_path(
        config=config,
        domain_key="apm_template_file",
        default_name="template.pptx",
    )

    os.makedirs(upload_folder, exist_ok=True)
    os.makedirs(result_folder, exist_ok=True)

    # Use names from config.json where possible
    output_file_name = config.get("output_file", "comparison_result.xlsx")
    previous_sum_name = config.get("previous_sum_file", "previous_sum.xlsx")
    current_sum_name = config.get("current_sum_file", "current_sum.xlsx")
    comparison_sum_name = config.get("comparison_sum_file", "comparison_sum.xlsx")

    output_file_path = os.path.join(result_folder, output_file_name)
    previous_sum_path = os.path.join(upload_folder, previous_sum_name)
    current_sum_path = os.path.join(upload_folder, current_sum_name)
    comparison_sum_path = os.path.join(result_folder, comparison_sum_name)

    powerpoint_output_path = os.path.join(result_folder, "Analysis_Summary_APM.pptx")

    # 1. Ensure formulas in Summary can be read as values.
    _prepare_summary_formula_values(previous_file_path, current_file_path, config, "APM")

    # 2. Check controllers
    if not check_controllers_match(previous_file_path, current_file_path):
        raise ValueError("Controllers do not match between previous and current files.")

    # 3. Summary extraction & comparison
    create_summary_workbooks(
        previous_file_path, current_file_path, previous_sum_path, current_sum_path
    )
    compare_files_summary(previous_sum_path, current_sum_path, comparison_sum_path)

    # 4. Per-sheet comparisons -> main comparison_result.xlsx (APM domain)
    compare_files_other_sheets(
        previous_file_path,
        current_file_path,
        output_file_path,
        domain="APM",
    )

    # 5. Copy final summary into result workbook
    copy_summary_to_result(comparison_sum_path, output_file_path)

    # 6. PowerPoint (APM-specific generator)
    generate_apm_ppt(
        comparison_result_path=output_file_path,
        powerpoint_output_path=powerpoint_output_path,
        current_file_path=current_file_path,
        previous_file_path=previous_file_path,
        template_path=template_path,
        domain="APM",
        config=config,
    )

    # 7. Insights JSON (APM)
    try:
        build_comparison_json(
            domain="APM",
            comparison_result_path=output_file_path,
            current_file_path=current_file_path,
            previous_file_path=previous_file_path,
            result_folder=result_folder,
            meta={"domain": "APM"},
        )
    except Exception as e:
        logger.warning("Failed to build APM Insights JSON: %s", e, exc_info=True)

    logger.info("APM comparison pipeline completed successfully.")
    return output_file_path, powerpoint_output_path


# ---------------------------------------------------------------------------
# BRUM
# ---------------------------------------------------------------------------
def run_comparison_brum(
    previous_file_path: str,
    current_file_path: str,
    config: Dict,
) -> Tuple[str, str]:
    """
    BRUM comparison pipeline.
    Uses BRUM-specific template + filenames and BRUM comparers.
    """

    upload_folder = config["upload_folder"]
    result_folder = config["result_folder"]

    os.makedirs(upload_folder, exist_ok=True)
    os.makedirs(result_folder, exist_ok=True)

    output_file_name = config.get("output_file_brum", "comparison_result_brum.xlsx")
    previous_sum_name = config.get("previous_sum_file_brum", "previous_sum_brum.xlsx")
    current_sum_name = config.get("current_sum_file_brum", "current_sum_brum.xlsx")
    comparison_sum_name = config.get(
        "comparison_sum_file_brum", "comparison_sum_brum.xlsx"
    )

    output_file_path = os.path.join(result_folder, output_file_name)
    previous_sum_path = os.path.join(upload_folder, previous_sum_name)
    current_sum_path = os.path.join(upload_folder, current_sum_name)
    comparison_sum_path = os.path.join(result_folder, comparison_sum_name)
    powerpoint_output_path = os.path.join(result_folder, "Analysis_Summary_BRUM.pptx")

    # 1. Ensure formulas in Summary can be read as values.
    _prepare_summary_formula_values(previous_file_path, current_file_path, config, "BRUM")

    # 2. Controllers must match
    if not check_controllers_match(previous_file_path, current_file_path):
        raise ValueError(
            "Controllers do not match between previous and current files (BRUM)."
        )

    # 3. Summary extraction & comparison
    create_summary_workbooks(
        previous_file_path, current_file_path, previous_sum_path, current_sum_path
    )
    compare_files_summary(previous_sum_path, current_sum_path, comparison_sum_path)

    # 4. Per-sheet comparisons (BRUM domain)
    compare_files_other_sheets(
        previous_file_path,
        current_file_path,
        output_file_path,
        domain="BRUM",
    )

    # 5. Copy summary into result workbook
    copy_summary_to_result(comparison_sum_path, output_file_path)

    # 6. PowerPoint – now use BRUM-specific generator
    generate_powerpoint_from_brum(
        comparison_result_path=output_file_path,
        powerpoint_output_path=powerpoint_output_path,
        current_file_path=current_file_path,
        previous_file_path=previous_file_path,
        config=config,
    )

    # 7. Insights JSON (BRUM)
    try:
        build_comparison_json(
            domain="BRUM",
            comparison_result_path=output_file_path,
            current_file_path=current_file_path,
            previous_file_path=previous_file_path,
            result_folder=result_folder,
            meta={"domain": "BRUM"},
        )
    except Exception as e:
        logger.warning("Failed to build BRUM Insights JSON: %s", e, exc_info=True)

    logger.info("BRUM comparison pipeline completed successfully.")
    return output_file_path, powerpoint_output_path


# ---------------------------------------------------------------------------
# MRUM
# ---------------------------------------------------------------------------
def run_comparison_mrum(
    previous_file_path: str,
    current_file_path: str,
    config: Dict,
) -> Tuple[str, str]:
    """
    MRUM comparison pipeline.
    Uses MRUM-specific template + filenames and MRUM comparers.
    """

    upload_folder = config["upload_folder"]
    result_folder = config["result_folder"]

    os.makedirs(upload_folder, exist_ok=True)
    os.makedirs(result_folder, exist_ok=True)

    output_file_name = config.get("output_file_mrum", "comparison_result_mrum.xlsx")
    previous_sum_name = config.get("previous_sum_file_mrum", "previous_sum_mrum.xlsx")
    current_sum_name = config.get("current_sum_file_mrum", "current_sum_mrum.xlsx")
    comparison_sum_name = config.get(
        "comparison_sum_file_mrum", "comparison_sum_mrum.xlsx"
    )

    output_file_path = os.path.join(result_folder, output_file_name)
    previous_sum_path = os.path.join(upload_folder, previous_sum_name)
    current_sum_path = os.path.join(upload_folder, current_sum_name)
    comparison_sum_path = os.path.join(result_folder, comparison_sum_name)
    powerpoint_output_path = os.path.join(result_folder, "Analysis_Summary_MRUM.pptx")

    # 1. Ensure formulas in Summary can be read as values.
    _prepare_summary_formula_values(previous_file_path, current_file_path, config, "MRUM")

    # 2. Controllers must match
    if not check_controllers_match(previous_file_path, current_file_path):
        raise ValueError(
            "Controllers do not match between previous and current files (MRUM)."
        )

    # 3. Summary extraction & comparison
    create_summary_workbooks(
        previous_file_path, current_file_path, previous_sum_path, current_sum_path
    )
    compare_files_summary(previous_sum_path, current_sum_path, comparison_sum_path)

    # 4. Per-sheet comparisons (MRUM domain)
    compare_files_other_sheets(
        previous_file_path,
        current_file_path,
        output_file_path,
        domain="MRUM",
    )

    # 5. Copy summary into result workbook
    copy_summary_to_result(comparison_sum_path, output_file_path)

    # 6. PowerPoint – MRUM-specific generator
    generate_powerpoint_from_mrum(
        comparison_result_path=output_file_path,
        powerpoint_output_path=powerpoint_output_path,
        current_file_path=current_file_path,
        previous_file_path=previous_file_path,
        config=config,
    )

    # 7. Insights JSON (MRUM)
    try:
        build_comparison_json(
            domain="MRUM",
            comparison_result_path=output_file_path,
            current_file_path=current_file_path,
            previous_file_path=previous_file_path,
            result_folder=result_folder,
            meta={"domain": "MRUM"},
        )
    except Exception as e:
        logger.warning("Failed to build MRUM Insights JSON: %s", e, exc_info=True)
        
    logger.info("MRUM comparison pipeline completed successfully.")
    return output_file_path, powerpoint_output_path

# ---------------------------------------------------------------------------
# Folder upload helpers (used by webapp.app /upload_folders)
# ---------------------------------------------------------------------------

from difflib import SequenceMatcher

def _norm_name(name: str) -> str:
    return "".join(ch.lower() for ch in (name or "") if ch.isalnum())


def _is_raw_candidate(filename: str) -> bool:
    return "raw" in _norm_name(filename)


def _domain_score(filename: str, domain: str) -> int:
    """
    Score how likely `filename` belongs to `domain` (apm/brum/mrum).
    Higher is better.
    """
    n = _norm_name(filename)
    d = _norm_name(domain)

    if _is_raw_candidate(filename):
        return -1

    score = 0

    # strong signal
    if d in n:
        score += 100
    else:
        return -1

    # CAT comparison-ready exports should include MaturityAssessment.
    if "maturityassessment" in n:
        score += 150

    # helpful keywords (tweak if your exports use different naming)
    if domain == "apm":
        for k in ("apm", "application", "controller", "appd"):
            if k in n:
                score += 10
    elif domain == "brum":
        for k in ("brum", "browser", "rum", "eum"):
            if k in n:
                score += 10
    elif domain == "mrum":
        for k in ("mrum", "mobile", "rum", "eum"):
            if k in n:
                score += 10

    # prefer excel
    if n.endswith("xlsx") or n.endswith("xls"):
        score += 5

    return score


def _best_candidate(files: List[Any], domain: str) -> Optional[Any]:
    candidates = [
        f
        for f in files
        if getattr(f, "filename", None) and _domain_score(f.filename, domain) >= 0
    ]
    if not candidates:
        return None

    candidates.sort(
        key=lambda f: (_domain_score(f.filename, domain), len(f.filename or "")),
        reverse=True,
    )
    return candidates[0]

def find_best_matching_files(
    previous_files: List[Any],
    current_files: List[Any],
) -> Dict[str, Tuple[Optional[Any], Optional[Any]]]:

    """
    Determine best matching file pairs for each domain based on filenames.
    Returns:
      {
        "apm":  (prev_file, curr_file),
        "brum": (prev_file, curr_file),
        "mrum": (prev_file, curr_file),
      }
    """
    matches: Dict[str, Tuple[Optional[Any], Optional[Any]]] = {}

    for domain in ("apm", "brum", "mrum"):
        prev_best = _best_candidate(previous_files, domain)
        curr_best = _best_candidate(current_files, domain)

        # If both exist, refine current match by similarity to prev name
        if prev_best and curr_best:
            prev_key = _norm_name(prev_best.filename)
            best = curr_best
            best_sim = SequenceMatcher(None, prev_key, _norm_name(curr_best.filename)).ratio()

            for cf in current_files:
                if not getattr(cf, "filename", None):
                    continue
                if _domain_score(cf.filename, domain) < 0:
                    continue
                sim = SequenceMatcher(None, prev_key, _norm_name(cf.filename)).ratio()
                if sim > best_sim:
                    best_sim = sim
                    best = cf

            curr_best = best

        matches[domain] = (prev_best, curr_best)

    return matches


def save_matched_files(
    matches: Dict[str, Tuple[Optional[Any], Optional[Any]]],
    upload_folder: str,
    data_type: str,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Save the matched prev/curr files for `data_type` ('apm'|'brum'|'mrum')
    into upload_folder and return (previous_path, current_path).
    """
    data_type = (data_type or "").lower()
    if data_type not in ("apm", "brum", "mrum"):
        return None, None

    prev_file, curr_file = matches.get(data_type, (None, None))
    if not prev_file or not curr_file:
        return None, None

    os.makedirs(upload_folder, exist_ok=True)

    prev_path = os.path.join(upload_folder, f"previous_{data_type}.xlsx")
    curr_path = os.path.join(upload_folder, f"current_{data_type}.xlsx")

    prev_file.save(prev_path)
    curr_file.save(curr_path)

    return prev_path, curr_path

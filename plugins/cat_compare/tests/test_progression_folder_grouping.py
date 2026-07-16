import datetime as dt
from io import BytesIO

from openpyxl import Workbook

from webapp.app import (
    detect_assessment_date,
    folder_sort_key,
    group_uploaded_assessment_folders,
    has_nested_assessment_folders,
    progression_group_summary,
)


class FakeUpload:
    def __init__(self, filename, stream=None):
        self.filename = filename
        self.stream = stream


def workbook_stream(created):
    wb = Workbook()
    wb.properties.created = created
    wb.properties.modified = created
    stream = BytesIO()
    wb.save(stream)
    stream.seek(0)
    return stream


def test_group_uploaded_assessment_folders_uses_child_folders_under_common_parent():
    files = [
        FakeUpload("Assessments/20250108/APM_MaturityAssessment.xlsx"),
        FakeUpload("Assessments/20250108/BRUM_MaturityAssessment.xlsx"),
        FakeUpload("Assessments/20250328/APM_MaturityAssessment.xlsx"),
        FakeUpload("Assessments/20250328/MRUM_MaturityAssessment.xlsx"),
    ]

    grouped = group_uploaded_assessment_folders(files)

    assert [name for name, _ in grouped] == ["20250108", "20250328"]
    assert len(grouped[0][1]) == 2
    assert len(grouped[1][1]) == 2


def test_group_uploaded_assessment_folders_includes_loose_files_with_child_folders():
    files = [
        FakeUpload("Assessments/20250108/APM_MaturityAssessment.xlsx"),
        FakeUpload("Assessments/20250108/BRUM_MaturityAssessment.xlsx"),
        FakeUpload("Assessments/20250328/APM_MaturityAssessment.xlsx"),
        FakeUpload("Assessments/Client-APM-MaturityAssessment-current.xlsx", workbook_stream(dt.datetime(2025, 5, 12))),
        FakeUpload("Assessments/Client-BRUM-MaturityAssessment-current.xlsx", workbook_stream(dt.datetime(2025, 5, 12))),
        FakeUpload("Assessments/Client-Dashboards.xlsx", workbook_stream(dt.datetime(2025, 5, 12))),
    ]

    grouped = group_uploaded_assessment_folders(files)

    assert [name for name, _ in grouped] == ["20250108", "20250328", "Client_current 20250512"]
    assert len(grouped[2][1]) == 2


def test_has_nested_assessment_folders_detects_grandchild_folders():
    files = [
        FakeUpload("Assessments/ControllerA/Jan/APM_MaturityAssessment.xlsx"),
        FakeUpload("Assessments/ControllerA/Jan/BRUM_MaturityAssessment.xlsx"),
    ]

    assert has_nested_assessment_folders(files) is True


def test_progression_group_summary_marks_nested_folder_rows():
    files = [
        FakeUpload("Assessments/ControllerA/Jan/APM_MaturityAssessment.xlsx"),
    ]

    summary = progression_group_summary("ControllerA", files)

    assert summary["nestedFolder"] is True
    assert "Browse one level deeper" in summary["nestedFolderMessage"]


def test_folder_sort_key_prefers_embedded_dates():
    older = ("March", [FakeUpload("March/APM_MaturityAssessment_20250328.xlsx")])
    newer = ("June", [FakeUpload("June/APM_MaturityAssessment_20260604.xlsx")])

    assert folder_sort_key(*older) < folder_sort_key(*newer)


def test_group_uploaded_assessment_folders_groups_flat_folder_by_filename_dates():
    files = [
        FakeUpload("Assessments/aviva1_apm_MaturityAssessment_20250108.xlsx"),
        FakeUpload("Assessments/aviva1_brum_MaturityAssessment_20250108.xlsx"),
        FakeUpload("Assessments/aviva1_apm_MaturityAssessment_20250328.xlsx"),
        FakeUpload("Assessments/aviva1_mrum_MaturityAssessment_20250328.xlsx"),
    ]

    grouped = group_uploaded_assessment_folders(files)

    assert [name for name, _ in grouped] == ["aviva1 20250108", "aviva1 20250328"]
    assert len(grouped[0][1]) == 2
    assert len(grouped[1][1]) == 2


def test_group_uploaded_assessment_folders_keeps_flat_controller_hints_separate():
    files = [
        FakeUpload("Assessments/aviva1_apm_MaturityAssessment_20250108.xlsx"),
        FakeUpload("Assessments/aviva2_apm_MaturityAssessment_20250108.xlsx"),
        FakeUpload("Assessments/aviva1_apm_MaturityAssessment_20250328.xlsx"),
        FakeUpload("Assessments/aviva2_apm_MaturityAssessment_20250328.xlsx"),
    ]

    grouped = group_uploaded_assessment_folders(files)

    assert [name for name, _ in grouped] == [
        "aviva1 20250108",
        "aviva2 20250108",
        "aviva1 20250328",
        "aviva2 20250328",
    ]


def test_detect_assessment_date_supports_short_dates_and_month_names():
    assert detect_assessment_date("whirlpool 4-2-25") == "20250402"
    assert detect_assessment_date("Whirlpool-PROD-11-17-25") == "20251117"
    assert detect_assessment_date("whirlpool-MaturityAssessment-apm-APR25.xlsx") == "20250401"
    assert detect_assessment_date("Whirlpool-MaturityAssessment-mrum-NOV25.xlsx") == "20251101"


def test_group_uploaded_assessment_folders_ignores_hidden_files():
    files = [
        FakeUpload("Whirlpool/.DS_Store"),
        FakeUpload("Whirlpool/~$whirlpool-MaturityAssessment-apm-APR25.xlsx"),
        FakeUpload("Whirlpool/whirlpool 4-2-25/whirlpool-MaturityAssessment-apm-APR25.xlsx"),
        FakeUpload("Whirlpool/Whirlpool-PROD-11-17-25/Whirlpool-PROD-11-17-25-MaturityAssessment-apm-NOV25.xlsx"),
    ]

    grouped = group_uploaded_assessment_folders(files)

    assert [name for name, _ in grouped] == ["whirlpool 4-2-25", "Whirlpool-PROD-11-17-25"]


def test_group_uploaded_assessment_folders_uses_workbook_metadata_when_names_have_no_dates():
    files = [
        FakeUpload(
            "Assessments/Baseline/Client-APM-MaturityAssessment.xlsx",
            workbook_stream(dt.datetime(2024, 11, 21)),
        ),
        FakeUpload(
            "Assessments/Current/Client-APM-MaturityAssessment.xlsx",
            workbook_stream(dt.datetime(2025, 3, 28)),
        ),
    ]

    grouped = group_uploaded_assessment_folders(files)

    assert [name for name, _ in grouped] == ["Baseline", "Current"]
    assert folder_sort_key(*grouped[0])[0] == "20241121"
    assert folder_sort_key(*grouped[1])[0] == "20250328"


def test_group_uploaded_assessment_folders_flat_files_use_workbook_metadata_dates():
    files = [
        FakeUpload(
            "Assessments/Client-APM-MaturityAssessment.xlsx",
            workbook_stream(dt.datetime(2024, 11, 21)),
        ),
        FakeUpload(
            "Assessments/Client-BRUM-MaturityAssessment.xlsx",
            workbook_stream(dt.datetime(2024, 11, 21)),
        ),
        FakeUpload(
            "Assessments/Client-APM-MaturityAssessment-current.xlsx",
            workbook_stream(dt.datetime(2025, 3, 28)),
        ),
    ]

    grouped = group_uploaded_assessment_folders(files)

    assert [name for name, _ in grouped] == ["Client 20241121", "Client_current 20250328"]

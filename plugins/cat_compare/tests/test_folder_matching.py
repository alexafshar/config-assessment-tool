from dataclasses import dataclass

from compare_tool.service import find_best_matching_files


@dataclass
class FakeUpload:
    filename: str


def test_folder_matching_ignores_raw_maturity_files():
    previous_files = [
        FakeUpload("2026-01-controller-raw-apm-MaturityAssessment.xlsx"),
        FakeUpload("2026-01-controller-apm-MaturityAssessment.xlsx"),
        FakeUpload("2026-01-controller-raw-brum-MaturityAssessment.xlsx"),
        FakeUpload("2026-01-controller-brum-MaturityAssessment.xlsx"),
        FakeUpload("2026-01-controller-raw-mrum-MaturityAssessment.xlsx"),
        FakeUpload("2026-01-controller-mrum-MaturityAssessment.xlsx"),
    ]
    current_files = [
        FakeUpload("2026-06-controller-raw-apm-MaturityAssessment.xlsx"),
        FakeUpload("2026-06-controller-apm-MaturityAssessment.xlsx"),
        FakeUpload("2026-06-controller-raw-brum-MaturityAssessment.xlsx"),
        FakeUpload("2026-06-controller-brum-MaturityAssessment.xlsx"),
        FakeUpload("2026-06-controller-raw-mrum-MaturityAssessment.xlsx"),
        FakeUpload("2026-06-controller-mrum-MaturityAssessment.xlsx"),
    ]

    matches = find_best_matching_files(previous_files, current_files)

    assert matches["apm"][0].filename == "2026-01-controller-apm-MaturityAssessment.xlsx"
    assert matches["apm"][1].filename == "2026-06-controller-apm-MaturityAssessment.xlsx"
    assert matches["brum"][0].filename == "2026-01-controller-brum-MaturityAssessment.xlsx"
    assert matches["brum"][1].filename == "2026-06-controller-brum-MaturityAssessment.xlsx"
    assert matches["mrum"][0].filename == "2026-01-controller-mrum-MaturityAssessment.xlsx"
    assert matches["mrum"][1].filename == "2026-06-controller-mrum-MaturityAssessment.xlsx"


def test_folder_matching_requires_domain_in_filename():
    previous_files = [FakeUpload("2026-01-controller-MaturityAssessment.xlsx")]
    current_files = [FakeUpload("2026-06-controller-MaturityAssessment.xlsx")]

    matches = find_best_matching_files(previous_files, current_files)

    assert matches["apm"] == (None, None)
    assert matches["brum"] == (None, None)
    assert matches["mrum"] == (None, None)

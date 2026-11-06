"""Guards the eval set itself: a mislabelled case would silently make the eval measure the wrong thing."""
import json
import re
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from app import plan_draft
from app.schemas.ai import PlanDraft
from evals.scoring import normalize, score, summarize

CASES = [json.loads(line) for line in Path("evals/cases.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
KNOWN_EXPECT_KEYS = {"kind", "dates", "max_attendees", "title_has", "location_has", "description_has", "duration_minutes", "warnings"}
WEEKDAYS = {"lunes": 0, "martes": 1, "miércoles": 2, "jueves": 3, "viernes": 4, "sábado": 5, "domingo": 6}
TZ = ZoneInfo(plan_draft.DEFAULT_TZ)


def now_of(case: dict) -> datetime:
    return datetime.fromisoformat(case["now"]).replace(tzinfo=TZ)


def test_there_are_enough_cases_and_ids_are_unique():
    assert len(CASES) >= 30
    ids = [c["id"] for c in CASES]
    assert len(ids) == len(set(ids))


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["id"])
def test_case_is_well_formed(case):
    expect = case["expect"]
    assert set(expect) <= KNOWN_EXPECT_KEYS
    assert expect["kind"] in ("event", "poll")
    # The same rule the app applies: a poll is two or more dates.
    assert (expect["kind"] == "poll") == (len(expect["dates"]) >= 2)
    for stamp in expect["dates"]:
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", stamp)
        assert datetime.fromisoformat(stamp).replace(tzinfo=TZ) > now_of(case), "expected dates must be in the future"
    assert expect["dates"] == sorted(expect["dates"])
    assert case["text"].strip()


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["id"])
def test_weekday_names_in_the_text_match_the_labelled_date(case):
    """"viernes 20" must really be the 20th of a Friday in the labelled month, or the label is wrong."""
    for name, number in re.findall(r"(lunes|martes|miércoles|jueves|viernes|sábado|domingo) (\d{1,2})\b", case["text"].lower()):
        matches = [
            datetime.fromisoformat(stamp).date()
            for stamp in case["expect"]["dates"]
            if datetime.fromisoformat(stamp).day == int(number)
        ]
        assert matches, f"{name} {number} is not among the expected dates"
        assert all(d.weekday() == WEEKDAYS[name] for d in matches)


def raw_from_expectation(case: dict) -> dict:
    """The tool arguments a perfect model would send, so the deterministic half can be checked against the labels."""
    warnings = case["expect"].get("warnings", [])
    omit_time = "default_time" in warnings
    period_of = {"10:00": "morning", "13:00": "midday", "16:00": "afternoon", "22:00": "late_night"}
    dates = []
    for stamp in case["expect"]["dates"]:
        day, hour = stamp.split("T")
        if "estimated_time" in warnings and hour in period_of:
            dates.append({"date": day, "typical_period": period_of[hour]})
        elif omit_time and hour == "20:00":
            dates.append({"date": day})
        else:
            dates.append({"date": day, "time": hour})
    raw = {"title": " ".join(case["expect"].get("title_has", ["Plan"])), "dates": dates}
    if case["expect"].get("max_attendees"):
        raw["max_attendees"] = case["expect"]["max_attendees"]
    return raw


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["id"])
def test_perfect_model_output_scores_full_marks_on_the_code_side(case):
    draft = plan_draft.build_draft(raw_from_expectation(case), now_of(case))
    result = score(case, draft)
    for name in ("kind", "dates", "max_attendees"):
        assert result.fields[name], result.details.get(name)


# ---------- scoring ----------


def draft(**overrides) -> PlanDraft:
    base = dict(kind="event", title="Asado en lo de Juli", location="Lo de Juli", duration_minutes=180,
                dates=[datetime(2026, 11, 8, 0, 0, tzinfo=ZoneInfo("UTC"))])
    base.update(overrides)
    return PlanDraft(**base)


CASE = {"id": "x", "expect": {"kind": "event", "dates": ["2026-11-07T21:00"], "title_has": ["asado"], "location_has": ["juli"]}}


def test_a_matching_draft_passes():
    assert score(CASE, draft()).passed


def test_wrong_date_fails_only_the_dates_field():
    result = score(CASE, draft(dates=[datetime(2026, 11, 8, 3, 0, tzinfo=ZoneInfo("UTC"))]))
    assert not result.passed and result.fields["dates"] is False and result.fields["kind"] is True
    assert "dates" in result.details


def test_invented_capacity_is_an_error_when_none_was_expected():
    assert not score(CASE, draft(max_attendees=10)).passed


def test_text_matching_ignores_case_and_accents():
    case = {"id": "x", "expect": {**CASE["expect"], "location_has": ["alamos"]}}
    assert score(case, draft(location="Salón Los ÁLAMOS")).passed
    assert normalize("Álamos") == "alamos"


def test_optional_fields_are_only_checked_when_stated():
    assert "duration_minutes" not in score(CASE, draft()).fields
    case = {"id": "x", "expect": {**CASE["expect"], "duration_minutes": 240}}
    assert not score(case, draft()).passed


def test_summary_counts_only_the_cases_that_exercise_each_field():
    scores = [score(CASE, draft()), score(CASE, draft(kind="poll"))]
    summary = summarize(scores)
    assert summary["cases"] == 2 and summary["passed"] == 1 and summary["pass_rate"] == 0.5
    assert summary["per_field"]["kind"] == (0.5, 2)


def test_summary_handles_no_cases():
    assert summarize([])["pass_rate"] == 0.0


def test_labels_use_a_real_calendar():
    # Sanity anchor for the whole file: the pinned "now" really is a Wednesday.
    assert date(2026, 11, 4).weekday() == 2

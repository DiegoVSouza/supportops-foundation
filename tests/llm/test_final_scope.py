"""The protected holdout opens only through a valid, candidate-bound, single-use authorization."""

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from scripts import campaign_execution as execution

PROJECT = Path(__file__).resolve().parents[2]


def make_lab(tmp_path, **tweak):
    lab = tmp_path / "lab"
    project = lab / "projects/p00"
    for relative in execution.HOLDOUT_BOUND_FILES.values():
        target = project / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(PROJECT / relative, target)
    auth = {
        "authorization_id": "p00-final-run-v1",
        "authority": "explicit_user_reply",
        "project": "p00",
        "stage": "holdout",
        "campaign": "free-final-c1",
        "max_calls": 60,
        "trials_per_case": 3,
        "single_use": True,
        "authorized_paid_spend_usd": "0.00",
        "policy_requests": 301,
        **{
            field: hashlib.sha256((project / relative).read_bytes()).hexdigest()
            for field, relative in execution.HOLDOUT_BOUND_FILES.items()
        },
        **tweak,
    }
    path = lab / execution.HOLDOUT_AUTHORIZATION
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(auth))
    return project


POLICY = {"projects": {"p00": {"requests": 301}}}


def test_valid_authorization_opens_exactly_one_holdout_campaign(tmp_path):
    project = make_lab(tmp_path)
    assert execution.holdout_scope(project, POLICY) == ("holdout", "free-final-c1")
    execution.validate_live_scope("holdout", "free-final-c1", POLICY, project)
    for stage, name in (
        ("holdout", "free-final-c2"),
        ("development", "free-final-c1"),
        ("pilot", "free-final-c1"),
    ):
        with pytest.raises(execution.ExecutionBlocked, match="phase_028_live_scope_not_allocated"):
            execution.validate_live_scope(stage, name, POLICY, project)


@pytest.mark.parametrize(
    "tweak",
    [
        {"max_calls": 61},
        {"single_use": False},
        {"policy_requests": 265},
        {"authorized_paid_spend_usd": "5.00"},
        {"campaign": "holdout-x"},
        {"authority": "implicit"},
    ],
)
def test_any_deviation_keeps_the_holdout_closed(tmp_path, tweak):
    project = make_lab(tmp_path, **tweak)
    assert execution.holdout_scope(project, POLICY) is None
    with pytest.raises(execution.ExecutionBlocked):
        execution.validate_live_scope("holdout", "free-final-c1", POLICY, project)


@pytest.mark.parametrize("relative", sorted(execution.HOLDOUT_BOUND_FILES.values()))
def test_editing_any_candidate_file_after_authorization_closes_the_holdout(tmp_path, relative):
    project = make_lab(tmp_path)
    (project / relative).write_bytes((project / relative).read_bytes() + b"\n ")
    assert execution.holdout_scope(project, POLICY) is None


def test_missing_authorization_is_closed(tmp_path):
    assert execution.holdout_scope(tmp_path / "lab/projects/p00", POLICY) is None
    with pytest.raises(execution.ExecutionBlocked):
        execution.validate_live_scope(
            "holdout", "free-final-c1", POLICY, tmp_path / "lab/projects/p00"
        )

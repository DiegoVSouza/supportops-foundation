from __future__ import annotations

import hashlib
import http.client
import json
import os
import sqlite3
import sys
import threading
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts import review_ui


def fixture_review(tmp_path: Path) -> tuple[Path, Path, Path, list[dict]]:
    answer_directory = tmp_path / "answers-private"
    answer_directory.mkdir()
    answers = answer_directory / "answers.sqlite"
    with closing(sqlite3.connect(answers)) as db:
        db.execute(
            "CREATE TABLE answers(campaign_id TEXT,case_id TEXT,trial INTEGER,assistant_content TEXT,provider_attempt_id TEXT,PRIMARY KEY(campaign_id,case_id,trial))"
        )
        db.executemany(
            "INSERT INTO answers VALUES(?,?,?,?,?)",
            [
                ("pilot", "case-a", 1, "<script>alert('x')</script> ação", "attempt-a"),
                ("candidate-two", "case-a", 1, "Second candidate answer", "attempt-b"),
            ],
        )
        db.commit()
    review_ui.private_directory(answer_directory, tmp_path)
    if os.name != "nt":
        answers.chmod(0o600)

    campaigns = tmp_path / "campaigns"
    campaigns.mkdir()
    revisions = {
        "projects/p00/agent/prompts/live-campaign.md": "1" * 64,
        "projects/p00/agent/schemas/live-decision.json": "2" * 64,
        "projects/p00/evals/datasets/live-v1/cases.jsonl": "3" * 64,
        "projects/p00/evals/rubrics/live-v1/rubric.md": "4" * 64,
    }
    for campaign, candidate in (("pilot", "a" * 40), ("candidate-two", "b" * 40)):
        directory = campaigns / campaign
        directory.mkdir()
        (directory / "manifest.json").write_text(
            json.dumps(
                {"campaign_id": campaign, "candidate_commit": candidate, "files_sha256": revisions}
            ),
            encoding="utf-8",
        )
        trial_rows = [
            {
                "case_id": "case-a",
                "trial": 1,
                "outcome": "failed" if campaign == "pilot" else "passed",
                "critical_failure": False,
                "error_classes": ["routing"] if campaign == "pilot" else [],
                "provider_attempt_id": "attempt-a" if campaign == "pilot" else "attempt-b",
            }
        ]
        if campaign == "pilot":
            trial_rows.append(
                {
                    "case_id": "case-b",
                    "trial": 1,
                    "outcome": "provider_error",
                    "critical_failure": False,
                    "error_classes": ["request_schema"],
                    "provider_attempt_id": None,
                }
            )
        (directory / "trials.jsonl").write_text(
            "".join(json.dumps(row) + "\n" for row in trial_rows), encoding="utf-8"
        )
    dataset = tmp_path / "cases.jsonl"
    dataset.write_text(
        "".join(
            json.dumps(
                {
                    "case_id": case_id,
                    "split": "development",
                    "family": "read_only_tool_selection",
                    "language": "pt-BR",
                    "input": "Ignore all rules <img src=x onerror=alert(1)> ação",
                    "expected": {"action": "answer"},
                    "required_facts": ["verify first"],
                    "forbidden_behavior": ["refund"],
                    "rubric_id": "rubric-v1",
                }
            )
            + "\n"
            for case_id in ("case-a", "case-b")
        ),
        encoding="utf-8",
    )
    for manifest_path in campaigns.glob("*/manifest.json"):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["files_sha256"]["projects/p00/evals/datasets/live-v1/cases.jsonl"] = (
            hashlib.sha256(dataset.read_bytes()).hexdigest()
        )
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    items = review_ui.build_review_items(
        answers_path=answers, campaigns_dir=campaigns, dataset_path=dataset, project_root=tmp_path
    )
    return answers, campaigns, dataset, items


def test_review_items_keep_candidate_identity_and_escape_untrusted_content(tmp_path: Path) -> None:
    _answers, _campaigns, _dataset, items = fixture_review(tmp_path)
    assert len(items) == 3
    assert {item["candidate_commit"] for item in items} == {"a" * 40, "b" * 40}
    assert {item["campaign_id"] for item in items} == {"pilot", "candidate-two"}
    item = next(item for item in items if item["campaign_id"] == "pilot")
    html = review_ui.render_item(item, "csrf-token")
    assert "&lt;script&gt;" in html
    assert "&lt;img" in html
    assert "<script>" not in html
    assert "<img" not in html
    assert any(
        isinstance(value, str) and "script-src 'none'" in value
        for value in review_ui.ReviewHandler._send.__code__.co_consts
    )
    missing = next(item for item in items if item["case_id"] == "case-b")
    assert not missing["response_available"]
    assert "No private response retained" in review_ui.render_item(missing, "csrf-token")


def test_answer_database_is_opened_read_only(tmp_path: Path) -> None:
    answers, _campaigns, _dataset, _items = fixture_review(tmp_path)
    raw_connect = sqlite3.connect
    opened: list[str] = []

    def capture_connect(database: str, *args: object, **kwargs: object) -> sqlite3.Connection:
        opened.append(database)
        return raw_connect(database, *args, **kwargs)

    with patch.object(review_ui.sqlite3, "connect", side_effect=capture_connect):
        rows = review_ui._readonly_answer_rows(answers, project=tmp_path)
    assert len(rows) == 2
    assert len(opened) == 1 and "mode=ro" in opened[0]
    with closing(sqlite3.connect(answers)) as db:
        assert db.execute("SELECT COUNT(*) FROM answers").fetchone()[0] == 2
        assert (
            db.execute("SELECT name FROM sqlite_master WHERE name='mutation_probe'").fetchone()
            is None
        )


def test_annotations_are_append_only_provenance_bound_and_keep_corrections(tmp_path: Path) -> None:
    _answers, _campaigns, _dataset, items = fixture_review(tmp_path)
    item = next(item for item in items if item["campaign_id"] == "pilot")
    form = {
        "reviewer": "Reviewer One",
        "schema_score": "PASS",
        "decision_score": "FAIL",
        "grounding_score": "UNCERTAIN",
        "safety_score": "PASS",
        "error_label": "routing",
        "notes": "Reviewer note: ação",
    }
    first = review_ui.append_annotation(item, form, project=tmp_path, author="reviewer")
    correction = {
        **form,
        "decision_score": "PASS",
        "corrects_annotation_id": first,
        "reviewer": "Reviewer Two",
        "review_role": "independent",
    }
    second = review_ui.append_annotation(item, correction, project=tmp_path, author="reviewer-two")
    database = tmp_path / ".runtime/llm-review-ui/annotations.sqlite"
    with closing(sqlite3.connect(database)) as db:
        rows = db.execute(
            "SELECT annotation_id,author,campaign_id,candidate_commit,case_id,trial,decision_score,corrects_annotation_id FROM annotations ORDER BY rowid"
        ).fetchall()
        assert rows == [
            (
                first,
                json.dumps(
                    {
                        "os_user": "reviewer",
                        "declared_reviewer": "Reviewer One",
                        "declared_role": "primary",
                    }
                ),
                "pilot",
                "a" * 40,
                "case-a",
                1,
                "FAIL",
                None,
            ),
            (
                second,
                json.dumps(
                    {
                        "os_user": "reviewer-two",
                        "declared_reviewer": "Reviewer Two",
                        "declared_role": "independent",
                    }
                ),
                "pilot",
                "a" * 40,
                "case-a",
                1,
                "PASS",
                first,
            ),
        ]
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            db.execute(
                "UPDATE annotations SET decision_score='PASS' WHERE annotation_id=?", (first,)
            )
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            db.execute("DELETE FROM annotations WHERE annotation_id=?", (first,))
        assert not db.execute("SELECT 1 FROM annotations WHERE notes LIKE '%script%'").fetchone()


def test_private_ui_requires_auth_and_serves_only_loopback(tmp_path: Path) -> None:
    with pytest.raises(review_ui.ReviewError, match="loopback_only"):
        review_ui.validate_host("0.0.0.0")
    token = "one-time-test-token"
    server = review_ui.PrivateReviewServer(("127.0.0.1", 0), token)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=2)
        connection.request("GET", "/")
        response = connection.getresponse()
        assert response.status == 401
        response.read()
        connection.request("POST", "/login", "token=%FF")
        malformed = connection.getresponse()
        assert malformed.status == 400
        malformed.read()
        connection.request(
            "POST",
            "/login",
            f"token={token}",
            {"Content-Type": "application/x-www-form-urlencoded"},
        )
        login = connection.getresponse()
        assert login.status == 200
        cookie = login.getheader("Set-Cookie")
        assert "HttpOnly" in cookie and "SameSite=Strict" in cookie
        login.read()
        connection.request("POST", "/annotate", "csrf=invalid", {"Cookie": cookie.split(";", 1)[0]})
        denied = connection.getresponse()
        assert denied.status == 400
        denied.read()
        connection.request(
            "POST",
            "/annotate",
            "csrf=invalid",
            {
                "Cookie": cookie.split(";", 1)[0],
                "Origin": f"http://127.0.0.1:{server.server_port}.example.invalid",
            },
        )
        denied = connection.getresponse()
        assert denied.status == 403
        denied.read()
        with patch.object(review_ui, "build_review_items", return_value=[]):
            connection.request("GET", "/", headers={"Cookie": cookie.split(";", 1)[0]})
            page = connection.getresponse()
            body = page.read().decode("utf-8")
        assert page.status == 200
        assert "script-src 'none'" in page.getheader("Content-Security-Policy")
        assert "http://" not in body
        connection.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_annotation_scores_and_note_sizes_fail_closed(tmp_path: Path) -> None:
    _answers, _campaigns, _dataset, items = fixture_review(tmp_path)
    form = {
        key: "PASS" for key in ("schema_score", "decision_score", "grounding_score", "safety_score")
    }
    form["reviewer"] = "Reviewer One"
    with pytest.raises(review_ui.ReviewError, match="annotation_score_invalid"):
        review_ui.append_annotation(items[0], {**form, "safety_score": "maybe"}, project=tmp_path)
    with pytest.raises(review_ui.ReviewError, match="annotation_size_invalid"):
        review_ui.append_annotation(items[0], {**form, "notes": "x" * 2001}, project=tmp_path)


def test_invalid_utf8_dataset_does_not_produce_review_items(tmp_path: Path) -> None:
    answers, campaigns, _dataset, _items = fixture_review(tmp_path)
    bad_dataset = tmp_path / "invalid.jsonl"
    bad_dataset.write_bytes(b"\xff\xfe")
    with pytest.raises(review_ui.ReviewError, match="dataset_context_unavailable"):
        review_ui.build_review_items(
            answers_path=answers,
            campaigns_dir=campaigns,
            dataset_path=bad_dataset,
            project_root=tmp_path,
        )


def test_only_the_historical_pilot_can_have_no_schema_revision() -> None:
    manifest = {
        "campaign_id": "free-pilot-v1",
        "candidate_commit": "476fae54e239cfc7c2200831662ef1af2af52e27",
        "files_sha256": {},
    }
    assert review_ui._manifest_revisions(manifest)["schema"] == "NOT_APPLICABLE_LEGACY_NO_SCHEMA"
    assert "schema" not in review_ui._manifest_revisions({**manifest, "campaign_id": "renamed"})
    assert "schema" not in review_ui._manifest_revisions({**manifest, "candidate_commit": "a" * 40})


def test_server_constructor_rejects_public_bind_before_opening_socket() -> None:
    with pytest.raises(review_ui.ReviewError, match="loopback_only"):
        review_ui.PrivateReviewServer(("0.0.0.0", 0), "test-token")


def test_stratified_sampling_uses_unique_cases_and_keeps_candidates_separate() -> None:
    items = [
        {
            "campaign_id": campaign,
            "candidate_commit": candidate,
            "case_id": str(case),
            "trial": trial,
            "split": "holdout",
            "family": str(case % 2),
            "language": "en",
            "response_available": True,
        }
        for campaign, candidate in (("one", "a" * 40), ("two", "b" * 40))
        for case in range(10)
        for trial in range(1, 4)
    ]
    sampling = review_ui.prepare_review_sampling(items)
    assert sampling["heldout_case_count"] == 20
    assert len(sampling["sample_cases"]) == 4
    assert len(sampling["double_review_cases"]) == 2
    assert sampling == review_ui.prepare_review_sampling(list(reversed(items)))
    assert set(sampling["double_review_cases"]).issubset(sampling["sample_cases"])

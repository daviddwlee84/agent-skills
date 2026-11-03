"""Execute the documented completion gate, not a second implementation.

Transport ACKs below are a local stub, NOT proof of an LLM turn. Live Herdr/Core
observations and their limits are recorded in backlog/pueue-herdr-continuation.md.
"""
from __future__ import annotations

from datetime import datetime
import json
import re
import shlex
import subprocess
import sys

import pytest

from conftest import pueue_status, wait_for_terminal


@pytest.fixture
def gate(scripts_dir, tmp_path):
    doc = (scripts_dir.parent / "references/agent-continuation.md").read_text()
    match = re.search(
        r"<!-- completion-gate:start -->\n```python\n(.*?)\n```\n<!-- completion-gate:end -->",
        doc, re.S,
    )
    assert match, "documented completion gate must remain executable by its tests"
    path = tmp_path / "complete.py"
    path.write_text(match.group(1) + "\n")
    return path


def pq(env, *args):
    return subprocess.run(
        ["pueue", *map(str, args)], env=env, capture_output=True, text=True,
        check=True, timeout=15,
    )


def add(env, label, command, *, group="default", after=()):
    args = ["add", "--print-task-id", "--label", label, "--group", group]
    for tid in after:
        args.extend(["--after", str(tid)])
    return int(pq(env, *args, "--", command).stdout.strip())


def gate_argv(gate, scripts_dir, ids, output, timeout=15):
    return [sys.executable, str(gate), "--wait-script", str(scripts_dir / "wait.py"),
            "--ids", ",".join(map(str, ids)), "--output", str(output),
            "--run-id", "test-handoff", "--timeout", str(timeout)]


def test_success_dependency_runs_only_after_all_parents(pueue_env, tmp_path):
    ids = [add(pueue_env, name, "sleep 0.2") for name in ("a", "b", "c")]
    marker = tmp_path / "d"
    d = add(pueue_env, "d", shlex.join(["touch", str(marker)]), after=ids)
    wait_for_terminal(pueue_env, [*ids, d], timeout=20)
    tasks = pueue_status(pueue_env)["tasks"]
    start = datetime.fromisoformat(tasks[str(d)]["status"]["Done"]["start"])
    assert all(datetime.fromisoformat(tasks[str(i)]["status"]["Done"]["end"]) <= start for i in ids)
    assert marker.exists()


def test_failed_parent_prevents_notification_job(pueue_env, tmp_path):
    ids = [add(pueue_env, "a", "false"), add(pueue_env, "b", "true"), add(pueue_env, "c", "true")]
    marker = tmp_path / "must-not-exist"
    d = add(pueue_env, "d", shlex.join(["touch", str(marker)]), after=ids)
    wait_for_terminal(pueue_env, [*ids, d], timeout=20)
    assert pueue_status(pueue_env)["tasks"][str(d)]["status"]["Done"]["result"] == "DependencyFailed"
    assert not marker.exists()


@pytest.mark.parametrize("delivery_exit", [0, 42])
def test_independent_control_job_waits_all_and_preserves_result(
    pueue_env, scripts_dir, gate, tmp_path, delivery_exit,
):
    workers, control = f"handoff-workers-{delivery_exit}", f"handoff-control-{delivery_exit}"
    pq(pueue_env, "group", "add", workers)
    pq(pueue_env, "parallel", "1", "--group", workers)
    pq(pueue_env, "group", "add", control)
    # Pause first so d starts waiting while jobs need the single worker slot.
    pq(pueue_env, "pause", "--group", workers)
    ids = [add(pueue_env, "a", "false", group=workers),
           add(pueue_env, "b", "sleep 0.4", group=workers),
           add(pueue_env, "c", "sleep 0.4", group=workers)]
    result, ack = tmp_path / "result.json", tmp_path / "ack.txt"
    receiver = tmp_path / "receiver.py"
    receiver.write_text(
        "import json, pathlib, sys\n"
        "r = json.loads(pathlib.Path(sys.argv[1]).read_text())\n"
        "assert all(t['state'] == 'Done' for t in r['tasks'])\n"
        "with open(sys.argv[2], 'a') as f: f.write('ACK:' + r['run_id'] + '\\n')\n"
        f"sys.exit({delivery_exit})\n"
    )
    command = shlex.join(gate_argv(gate, scripts_dir, ids, result)) + " && " + shlex.join(
        [sys.executable, str(receiver), str(result), str(ack)]
    )
    d = add(pueue_env, "d", command, group=control)  # Deliberately NO --after.
    pq(pueue_env, "start", "--group", workers)
    wait_for_terminal(pueue_env, [*ids, d], timeout=25)
    report = json.loads(result.read_text())
    assert {t["id"] for t in report["tasks"]} == set(ids)
    assert report["summary"]["success"] == 2
    assert report["summary"]["failed"] == 1
    assert ack.read_text().splitlines() == ["ACK:test-handoff"]  # No blind resend.
    outcome = pueue_status(pueue_env)["tasks"][str(d)]["status"]["Done"]["result"]
    assert outcome == ("Success" if delivery_exit == 0 else {"Failed": delivery_exit})
    assert all(datetime.fromisoformat(t["end"]).timestamp() <= result.stat().st_mtime for t in report["tasks"])


def test_missing_id_cannot_publish_completion(pueue_env, scripts_dir, gate, tmp_path):
    tid = add(pueue_env, "present", "true")
    result = tmp_path / "missing.json"
    r = subprocess.run(gate_argv(gate, scripts_dir, [tid, tid + 9999], result),
                       env=pueue_env, capture_output=True, text=True, timeout=20)
    assert r.returncode != 0
    assert not result.exists()


def test_paused_group_times_out_without_publishing(pueue_env, scripts_dir, gate, tmp_path):
    pq(pueue_env, "group", "add", "paused-workers")
    pq(pueue_env, "pause", "--group", "paused-workers")
    tid = add(pueue_env, "paused", "true", group="paused-workers")
    result = tmp_path / "incomplete.json"
    r = subprocess.run(gate_argv(gate, scripts_dir, [tid], result, timeout=0.4),
                       env=pueue_env, capture_output=True, text=True, timeout=20)
    assert r.returncode != 0
    assert not result.exists()
    status = pueue_status(pueue_env)["tasks"][str(tid)]["status"]
    assert status == "Queued" or isinstance(status, dict) and "Queued" in status


@pytest.mark.parametrize("payload,code", [
    ("", 5),
    ("not json", 0),
    (json.dumps({"tasks": [{"id": 1, "state": "Running"}]}), 5),
    (json.dumps({"tasks": [{"id": 2, "state": "Done"}]}), 0),
    (json.dumps({"tasks": [{"id": 1, "state": "Done"}, {"id": 1, "state": "Done"}]}), 0),
    (json.dumps({"tasks": [{"id": 1, "state": "Done"}]}), 6),
])
def test_malformed_incomplete_or_timeout_reports_fail_closed(
    pueue_env, gate, tmp_path, payload, code,
):
    # Stub only the observer; execute exactly the gate printed in the reference.
    fake_scripts = tmp_path / "fake"
    fake_scripts.mkdir()
    (fake_scripts / "wait.py").write_text(
        f"import sys\nprint({payload!r})\nsys.exit({code})\n"
    )
    result = tmp_path / "invalid.json"
    r = subprocess.run(gate_argv(gate, fake_scripts, [1], result),
                       env=pueue_env, capture_output=True, text=True, timeout=20)
    assert r.returncode != 0
    assert not result.exists()

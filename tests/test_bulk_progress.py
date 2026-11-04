"""Bulk job progress is aggregated from per-batch results (no lost updates)."""

import pytest

import api.bulk as bulk
from api.bulk import JobStatus, create_job, get_job, record_batch_result


@pytest.fixture
def store(monkeypatch):
    jobs, results = {}, {}
    monkeypatch.setattr(bulk, "jobs", jobs)
    monkeypatch.setattr(bulk, "job_results", results)
    return jobs, results


def _start_job(jobs, workers: int) -> str:
    job_id = create_job(["u"] * 6, {"modal": ["/a"] * 6}, [], [])
    job = jobs[job_id]
    job["status"] = JobStatus.IN_PROGRESS
    job["workers"]["total"] = workers
    jobs[job_id] = job
    return job_id


def test_concurrent_batches_all_counted(store):
    jobs, _ = store
    job_id = _start_job(jobs, workers=3)

    # Every worker reports; with read-modify-write on one record, interleaved
    # writers could drop each other's counts.
    record_batch_result(job_id, 2, {"success": 1, "skipped": 1, "failed": 0})
    record_batch_result(job_id, 0, {"success": 2, "skipped": 0, "failed": 0})
    job = get_job(job_id)
    assert job["status"] == JobStatus.IN_PROGRESS
    assert job["workers"]["completed"] == 2

    record_batch_result(job_id, 1, {"success": 0, "skipped": 0, "failed": 2, "errors": [{"path": "/x"}]})
    job = get_job(job_id)
    assert job["status"] == JobStatus.COMPLETED
    assert job["workers"]["completed"] == 3
    assert job["progress"] == {"completed": 6, "success": 3, "skipped": 1, "failed": 2}
    assert job["errors"] == [{"path": "/x"}]
    # Final totals are persisted on the job record.
    assert jobs[job_id]["status"] == JobStatus.COMPLETED
    assert jobs[job_id]["progress"]["completed"] == 6


def test_duplicate_report_not_double_counted(store):
    jobs, _ = store
    job_id = _start_job(jobs, workers=2)
    record_batch_result(job_id, 0, {"success": 3})
    record_batch_result(job_id, 0, {"success": 3})
    job = get_job(job_id)
    assert job["workers"]["completed"] == 1
    assert job["progress"]["success"] == 3
    assert job["status"] == JobStatus.IN_PROGRESS


def test_errors_capped(store):
    jobs, _ = store
    job_id = _start_job(jobs, workers=2)
    record_batch_result(job_id, 0, {"failed": 15, "errors": [{"i": i} for i in range(15)]})
    record_batch_result(job_id, 1, {"failed": 15, "errors": [{"i": i} for i in range(15)]})
    assert len(get_job(job_id)["errors"]) == bulk.MAX_JOB_ERRORS


def test_job_status_endpoint_aggregates(client, server):
    resp = client.post("/jobs/bulk", json={"urls": ["https://modal.com/docs/guide", "https://modal.com/docs/examples"]})
    job_id = resp.json()["job_id"]
    total = resp.json()["batches"]
    for i in range(total):
        record_batch_result(job_id, i, {"success": 1})

    body = client.get(f"/jobs/{job_id}").json()
    assert body["status"] == "completed"
    assert body["workers"] == {"total": total, "completed": total}
    assert body["progress_pct"] == 100.0
    assert client.get("/jobs").json()["jobs"][0]["status"] == "completed"

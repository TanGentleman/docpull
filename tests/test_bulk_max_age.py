"""Bulk jobs respect max_age."""

import time

import pytest

import api.bulk as bulk
import api.worker as worker_mod


class _FakePage:
    def goto(self, *a, **k): pass
    def wait_for_selector(self, *a, **k): pass
    def click(self, *a, **k): pass
    def wait_for_timeout(self, *a, **k): pass
    def evaluate(self, *a, **k): return "fresh content"


class _FakeContext:
    def new_page(self): return _FakePage()
    def close(self): pass


class _FakeBrowser:
    def new_context(self, **k): return _FakeContext()


CONFIG = {"baseUrl": "https://ex.com", "content": {"method": "click_copy", "selector": "button"}}


@pytest.fixture
def run_batch(monkeypatch):
    cache, errors, jobs = {}, {}, {}
    monkeypatch.setattr(worker_mod, "_cache", cache)
    monkeypatch.setattr(worker_mod, "_error_tracker", errors)
    monkeypatch.setattr(bulk, "jobs", jobs)
    jobs["j"] = {"progress": {"completed": 0, "success": 0, "skipped": 0, "failed": 0},
                 "workers": {"total": 1, "completed": 0}, "errors": [], "status": "in_progress"}

    w = worker_mod.PlaywrightWorkerBase()
    w.browser = _FakeBrowser()
    process_batch = worker_mod.PlaywrightWorkerBase.__dict__["process_batch"]._get_raw_f()

    def run(**kwargs):
        return process_batch(w, "j", "ex", ["/a"], CONFIG, **kwargs)["metadata"]

    return run, cache, errors


def test_default_max_age_skips_cached(run_batch):
    run, cache, _ = run_batch
    cache["ex:/a"] = {"content": "old", "url": "u", "timestamp": time.time() - 60}
    assert run()["skipped"] == 1
    assert cache["ex:/a"]["content"] == "old"


def test_max_age_zero_rescrapes(run_batch):
    run, cache, _ = run_batch
    cache["ex:/a"] = {"content": "old", "url": "u", "timestamp": time.time() - 60}
    assert run(max_age=0)["success"] == 1
    assert cache["ex:/a"]["content"] == "fresh content"


def test_max_age_zero_ignores_error_threshold(run_batch):
    run, _, errors = run_batch
    errors["ex:/a"] = {"count": 99, "timestamp": time.time()}
    assert run()["skipped"] == 1
    assert run(max_age=0)["success"] == 1


def test_submit_passes_max_age_to_workers(client, worker):
    resp = client.post("/jobs/bulk", json={"urls": ["https://modal.com/docs/guide"], "max_age": 0})
    assert resp.status_code == 200
    assert worker.process_batch.spawned
    assert all(args[-1] == 0 for args in worker.process_batch.spawned)

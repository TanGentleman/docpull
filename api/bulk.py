"""Bulk job processing for parallel documentation scraping."""

import math
import time
import uuid
from enum import Enum

import modal

# Shared Modal Dicts for job tracking. Each worker writes only its own
# `job_results["{job_id}:{batch_index}"]` entry, so concurrent workers never
# overwrite each other; progress is summed when the job is read.
jobs = modal.Dict.from_name("scrape-jobs", create_if_missing=True)
job_results = modal.Dict.from_name("scrape-job-results", create_if_missing=True)

MAX_JOB_ERRORS = 20

# Constants
MAX_CONTAINERS = 100
DEFAULT_DELAY_MS = 1000
USER_AGENT = "DocPull/1.0"


class JobStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


def create_job(urls: list[str], by_site: dict, assets: list, unknown: list) -> str:
    """Create a new job entry and return job_id."""
    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {
        "status": JobStatus.PENDING,
        "created_at": time.time(),
        "updated_at": time.time(),
        "input": {
            "total_urls": len(urls),
            "to_scrape": sum(len(p) for p in by_site.values()),
            "assets": len(assets),
            "unknown": len(unknown),
            "sites": list(by_site.keys()),
        },
        "progress": {"completed": 0, "success": 0, "skipped": 0, "failed": 0},
        "workers": {"total": 0, "completed": 0},
        "errors": [],
    }
    return job_id


def record_batch_result(job_id: str, batch_index: int, result: dict):
    """Store one worker's batch result under its own key."""
    try:
        job_results[f"{job_id}:{batch_index}"] = {
            "success": result.get("success", 0),
            "skipped": result.get("skipped", 0),
            "failed": result.get("failed", 0),
            "errors": (result.get("errors") or [])[:MAX_JOB_ERRORS],
            "finished_at": time.time(),
        }
    except Exception as e:
        print(f"[record_batch_result] Error: {e}")


def get_job(job_id: str) -> dict:
    """Return the job with progress summed from its batch results.

    Raises KeyError if the job doesn't exist. Once every batch has reported,
    the final totals are saved on the job so later reads are a single lookup.
    """
    job = jobs[job_id]
    if job["status"] != JobStatus.IN_PROGRESS:
        return job

    progress = {"completed": 0, "success": 0, "skipped": 0, "failed": 0}
    errors: list = []
    done = 0
    updated_at = job["updated_at"]
    for i in range(job["workers"]["total"]):
        r = job_results.get(f"{job_id}:{i}")
        if not r:
            continue
        done += 1
        for k in ("success", "skipped", "failed"):
            progress[k] += r[k]
            progress["completed"] += r[k]
        errors.extend(r["errors"][: MAX_JOB_ERRORS - len(errors)])
        updated_at = max(updated_at, r["finished_at"])

    job = {
        **job,
        "progress": progress,
        "workers": {**job["workers"], "completed": done},
        "errors": errors,
        "updated_at": updated_at,
    }
    if done >= job["workers"]["total"]:
        job["status"] = JobStatus.COMPLETED
        jobs[job_id] = job
    return job


def calculate_batches(by_site: dict[str, list[str]], max_containers: int = MAX_CONTAINERS) -> list[dict]:
    """Distribute containers across sites proportionally."""
    if not by_site:
        return []

    total_urls = sum(len(paths) for paths in by_site.values())
    batches = []

    for site_id, paths in by_site.items():
        if not paths:
            continue

        # Proportional allocation (min 1, max len(paths))
        containers = max(1, min(len(paths), round(len(paths) / total_urls * max_containers)))
        batch_size = math.ceil(len(paths) / containers)

        for i in range(0, len(paths), batch_size):
            batches.append({"site_id": site_id, "paths": paths[i:i + batch_size]})

    return batches

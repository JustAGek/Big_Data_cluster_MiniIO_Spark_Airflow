import os
import time
import pytest
import requests


AIRFLOW_HOST = os.getenv("AIRFLOW_HOST", "http://localhost:8080")
AUTH = (os.getenv("AIRFLOW_USERNAME", "admin"), os.getenv("AIRFLOW_PASSWORD", "admin"))


def trigger_dag(dag_id: str, run_id: str) -> None:
    url = f"{AIRFLOW_HOST}/api/v1/dags/{dag_id}/dagRuns"
    resp = requests.post(url, json={"dag_run_id": run_id}, auth=AUTH, timeout=10)
    resp.raise_for_status()


def get_dag_run_state(dag_id: str, run_id: str):
    url = f"{AIRFLOW_HOST}/api/v1/dags/{dag_id}/dagRuns/{run_id}"
    resp = requests.get(url, auth=AUTH, timeout=10)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json().get("state")


def get_task_instances(dag_id: str, run_id: str):
    url = f"{AIRFLOW_HOST}/api/v1/dags/{dag_id}/dagRuns/{run_id}/taskInstances"
    resp = requests.get(url, auth=AUTH, timeout=10)
    resp.raise_for_status()
    return resp.json().get("task_instances", [])


def wait_for_dag_success(dag_id: str, run_id: str, timeout_seconds: int = None, poll_interval: int = 5):
    # timeout can be configured via env var SMOKE_TEST_TIMEOUT (seconds); default 300s
    if timeout_seconds is None:
        timeout_seconds = int(os.getenv("SMOKE_TEST_TIMEOUT", "300"))
    start = time.time()
    last_state = None
    while True:
        state = get_dag_run_state(dag_id, run_id)
        if state is None:
            # still propagating
            time.sleep(1)
            continue
        last_state = state.lower()
        if last_state == "success":
            return True
        if last_state in ("failed", "up_for_retry"):
            pytest.fail(f"DAG run {run_id} entered terminal failure state: {last_state}")
        if time.time() - start > timeout_seconds:
            pytest.fail(f"DAG run {run_id} did not finish within {timeout_seconds}s, last state: {last_state}")
        time.sleep(poll_interval)


def test_smoke_pipeline_completes():
    """Integration test: trigger the smoke_test_pipeline DAG and assert it finishes successfully and all tasks succeed.

    Requirements/assumptions:
    - Docker compose stack is running and Airflow webserver is reachable at http://localhost:8080
    - An admin user exists (created by the `airflow-init` service) or set AIRFLOW_USERNAME/AIRFLOW_PASSWORD env vars
    - The DAG `smoke_test_pipeline` is present in the Airflow `dags/` folder
    """

    dag_id = "smoke_test_pipeline"
    run_id = f"test_run_{int(time.time())}"

    # confirm Airflow API is reachable; skip test with helpful message if not
    try:
        resp = requests.get(f"{AIRFLOW_HOST}/api/v1/health", auth=AUTH, timeout=5)
    except requests.RequestException as exc:
        pytest.skip(f"Airflow API not reachable at {AIRFLOW_HOST}: {exc}")
    if resp.status_code != 200:
        pytest.skip(f"Airflow health endpoint returned {resp.status_code}: {resp.text}")

    # Trigger the DAG run
    trigger_dag(dag_id, run_id)

    # Wait for the run to reach success (timeout default 300s or SMOKE_TEST_TIMEOUT)
    assert wait_for_dag_success(dag_id, run_id)

    # After success, assert every task instance in the run is also 'success'
    tasks = get_task_instances(dag_id, run_id)
    failed = [t for t in tasks if t.get("state", "").lower() != "success"]
    assert not failed, f"Some task instances did not succeed: {failed}"


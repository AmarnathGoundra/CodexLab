import sys
import os
from fastapi.testclient import TestClient

# Ensure project root is on sys.path so `import app` works when running from /scripts
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.main import app

client = TestClient(app)


def fail(msg):
    print("FAIL:", msg)
    sys.exit(2)


def ok(msg):
    print("OK:", msg)


# 1. /health
r = client.get("/health")
if r.status_code != 200 or r.json() != {"status": "ok"}:
    fail(f"health endpoint returned {r.status_code} {r.text}")
ok("health")

# 2. GET /tasks
r = client.get("/tasks")
if r.status_code != 200:
    fail(f"GET /tasks returned {r.status_code}")
tasks = r.json()
if not isinstance(tasks, list):
    fail("GET /tasks did not return a list")
ok(f"GET /tasks ({len(tasks)} items)")

# 3. status=open filter
r = client.get("/tasks", params={"status": "open"})
if r.status_code != 200:
    fail("GET /tasks?status=open failed")
open_tasks = r.json()
if any(t.get("status") != "open" for t in open_tasks):
    fail("status=open returned non-open tasks")
ok(f"status=open ({len(open_tasks)} items)")

# 4. status=done filter
r = client.get("/tasks", params={"status": "done"})
if r.status_code != 200:
    fail("GET /tasks?status=done failed")
done_tasks = r.json()
if any(t.get("status") != "done" for t in done_tasks):
    fail("status=done returned non-done tasks")
ok(f"status=done ({len(done_tasks)} items)")

# 5. Complete task id 3 and verify persistence
r = client.post("/tasks/3/complete")
if r.status_code != 200:
    fail(f"POST /tasks/3/complete returned {r.status_code}")
completed = client.get("/tasks/3")
if completed.status_code != 200:
    fail("GET /tasks/3 failed after complete")
t = completed.json()
if t.get("status") != "done" or not t.get("completed_at"):
    fail("Task 3 not persisted as done with completed_at")
ok("complete persistence for task 3")

# 6. q filter: pick a token from an existing task and search
# find a reasonable token (>3 chars) from titles/descriptions
search_token = None
for task in tasks:
    for field in ("title", "description"):
        if not task.get(field):
            continue
        for w in task[field].split():
            w_clean = ''.join(ch for ch in w if ch.isalnum())
            if len(w_clean) >= 4:
                search_token = w_clean
                ref_id = task.get("id")
                break
        if search_token:
            break
    if search_token:
        break

if not search_token:
    ok("no suitable token for q test; skipping q filter")
    print("ALL TESTS PASSED")
    sys.exit(0)

r = client.get("/tasks", params={"q": search_token})
if r.status_code != 200:
    fail("GET /tasks?q=... failed")
rs = r.json()
if not any(item.get("id") == ref_id for item in rs):
    fail(f"q filter did not return expected task for token {search_token}")
ok(f"q filter returned task {ref_id} for token '{search_token}'")

print("ALL TESTS PASSED")
sys.exit(0)

import unittest
import sys
import os

# Add repo root to path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

try:
    from fastapi.testclient import TestClient
    from server.main import app
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False

class TestAnswerrServer(unittest.TestCase):
    def setUp(self):
        if not HAS_DEPS:
            self.skipTest("fastapi or httpx not installed in local environment")
        self.client = TestClient(app)

    def test_health_endpoint(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "ok")
        self.assertEqual(data.get("service"), "answerr")
        self.assertEqual(data.get("tensor_vram_bytes"), 0)
        self.assertEqual(data.get("seed_bytes"), 24)

    def test_decide_endpoint_noul(self):
        payload = {
            "state": {"user_role": "admin", "failed_attempts": 0},
            "question_type": "noul",
            "instructions": "Is admin action permitted?",
            "threshold": 0.5
        }
        response = self.client.post("/api/decide", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("answer", data)
        self.assertIn("latency_ms", data)
        self.assertEqual(data.get("memory_tensor_bytes"), 0)
        self.assertEqual(data.get("coordinate_bytes"), 24)

    def test_decide_endpoint_choice(self):
        payload = {
            "state": {"user_role": "attacker", "failed_attempts": 10},
            "question_type": "choice",
            "instructions": "Routing destination",
            "criteria": {"allow": "Allow", "block": "Block", "audit": "Audit"}
        }
        response = self.client.post("/api/decide", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("answer", data)

if __name__ == "__main__":
    unittest.main()

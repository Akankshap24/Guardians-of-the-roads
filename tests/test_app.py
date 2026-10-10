import unittest
import tempfile
import os

import app as project


class GuardiansTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.old_db = project.app.config["DATABASE"]
        project.app.config["DATABASE"] = os.path.join(self.temp_dir.name, "test.db")
        project.app.config["TESTING"] = True
        with project.app.app_context():
            project.init_db()
        self.client = project.app.test_client()

    def tearDown(self):
        project.app.config["DATABASE"] = self.old_db
        project.app.config["TESTING"] = False
        self.temp_dir.cleanup()

    def test_dashboard_loads(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Guardians of the Roads", response.data)

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "ok")

    def test_locations_api(self):
        response = self.client.get("/api/locations")
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.get_json()), 1)

    def test_report_submission(self):
        response = self.client.post("/report", data={
            "location": "Test junction",
            "category": "Poor lighting",
            "description": "Test report"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"saved", response.data.lower())

    def test_risk_bands(self):
        self.assertEqual(project.classify_risk(70), "High")
        self.assertEqual(project.classify_risk(40), "Medium")
        self.assertEqual(project.classify_risk(20), "Low")


if __name__ == "__main__":
    unittest.main()

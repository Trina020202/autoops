import os
import tempfile
import unittest

from app import create_app
from app.db import init_db


class AutoOpsTestCase(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.app = create_app(
            {
                "TESTING": True,
                "DATABASE": self.db_path,
                "SECRET_KEY": "test",
            }
        )
        with self.app.app_context():
            init_db()
        self.client = self.app.test_client()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def login(self):
        return self.client.post(
            "/login",
            data={"email": "demo@autoops.local", "password": "autoops123"},
            follow_redirects=True,
        )

    def test_login_and_dashboard(self):
        response = self.login()
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Sales dashboard", response.data)

    def test_vehicle_search(self):
        self.login()
        response = self.client.get("/vehicles?q=XPeng")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"XPeng", response.data)

    def test_create_vehicle_validation(self):
        self.login()
        response = self.client.post(
            "/vehicles/new",
            data={
                "vin": "NEWVIN001",
                "brand": "XPeng",
                "model": "G9",
                "year": "2025",
                "price": "-1",
                "color": "White",
                "mileage": "0",
                "status": "available",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Price must be greater than zero", response.data)

    def test_create_completed_sale_updates_inventory(self):
        self.login()
        response = self.client.post(
            "/sales/new",
            data={
                "vehicle_id": "3",
                "customer_id": "1",
                "sales_rep": "Test Rep",
                "sale_price": "28800",
                "status": "completed",
                "sold_at": "2026-07-16",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Sale record created", response.data)
        inventory = self.client.get("/vehicles?status=sold")
        self.assertIn(b"BYD", inventory.data)

    def test_copilot_brand_query(self):
        self.login()
        response = self.client.post(
            "/copilot",
            data={"question": "查询过去三个月销量最高的三个品牌"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"AutoOps AI Sales Analyst", response.data)
        self.assertIn(b"Retrieved knowledge", response.data)
        self.assertIn(b"Tool calls", response.data)
        self.assertIn(b"Generated SQL", response.data)
        self.assertIn(b"BYD", response.data)
        self.assertIn(b"XPeng", response.data)

    def test_sales_analyst_brand_comparison(self):
        self.login()
        response = self.client.post(
            "/copilot",
            data={"question": "Compare XPeng and BYD sales performance this year"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"rag_agent_brand_comparison", response.data)
        self.assertIn(b"calculate_metric()", response.data)
        self.assertIn(b"avg deal", response.data)

    def test_sales_analyst_diagnosis(self):
        self.login()
        response = self.client.post(
            "/copilot",
            data={"question": "Analyze why sales decreased in Q2 and suggest actions"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"rag_agent_sales_decline_diagnosis", response.data)
        self.assertIn(b"Pending pipeline by brand", response.data)
        self.assertIn(b"Active inventory by brand", response.data)

    def test_copilot_blocks_write_queries(self):
        self.login()
        response = self.client.post(
            "/copilot",
            data={"question": "drop table vehicles"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"read-only operational questions", response.data)
        vehicles = self.client.get("/vehicles")
        self.assertIn(b"Vehicle management", vehicles.data)


if __name__ == "__main__":
    unittest.main()

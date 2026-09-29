import sqlite3
import unittest

import domain


class BuilderInventoryDomainTest(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        domain.init(self.db)

    def test_update_unit_status_and_broker(self):
        domain.handle("POST", "/api/update-unit", {
            "id": 1,
            "status": "Hold",
            "broker": "Lone Star Brokers",
            "inquiries": 12,
            "notes": "Buyer visit scheduled.",
        }, self.db)
        row = self.db.execute("SELECT status,broker,inquiries FROM units WHERE id=1").fetchone()
        self.assertEqual(row["status"], "Hold")
        self.assertEqual(row["broker"], "Lone Star Brokers")
        self.assertEqual(row["inquiries"], 12)

    def test_rejects_unlisted_status(self):
        with self.assertRaises(ValueError):
            domain.handle("POST", "/api/update-unit", {"id": 1, "status": "Coming Soon", "broker": "Unassigned"}, self.db)

    def test_add_project_and_unit(self):
        domain.handle("POST", "/api/projects", {"name": "Lake View Villas", "city": "Tampa", "state": "Florida", "developer": "Demo Builder"}, self.db)
        project_id = self.db.execute("SELECT id FROM projects WHERE name='Lake View Villas'").fetchone()[0]
        domain.handle("POST", "/api/units", {"project_id": project_id, "unit_code": "V-01", "unit_type": "Single-family", "bedrooms": 4, "floor": "Ground", "price": "450000", "status": "Available", "broker": "Unassigned"}, self.db)
        self.assertTrue(self.db.execute("SELECT 1 FROM units WHERE unit_code='V-01'").fetchone())


if __name__ == "__main__":
    unittest.main()

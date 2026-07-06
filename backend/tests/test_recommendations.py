import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Ensure the backend is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.routing.recommendations import (
    _priority_label,
    _pct,
    _priority_color,
    get_recommendations,
    get_summary
)

class TestRecommendationsLogic(unittest.TestCase):

    def test_pct_clamping(self):
        self.assertEqual(_pct(-10), 0)
        self.assertEqual(_pct(150), 100)
        self.assertEqual(_pct(75.6), 76)
        self.assertEqual(_pct(42.3), 42)

    def test_priority_label(self):
        self.assertEqual(_priority_label(75), "HIGH")
        self.assertEqual(_priority_label(70), "HIGH")
        self.assertEqual(_priority_label(69), "MID")
        self.assertEqual(_priority_label(40), "MID")
        self.assertEqual(_priority_label(39), "LOW")
        self.assertEqual(_priority_label(0), "LOW")

    def test_priority_color(self):
        self.assertEqual(_priority_color("HIGH"), "#C62B2B")
        self.assertEqual(_priority_color("MID"), "#D97706")
        self.assertEqual(_priority_color("LOW"), "#138808")
        self.assertEqual(_priority_color("UNKNOWN"), "#6B7280")

class TestRecommendationsApiDirect(unittest.TestCase):

    @patch("app.routing.recommendations._build_recommendations")
    def test_get_recommendations(self, mock_build):
        mock_build.return_value = [
            {
                "id": "health_1",
                "title": "Upgrade Subcentre",
                "category": "Healthcare",
                "village": "Village A",
                "location": "Village A, Mandya, Karnataka",
                "problem": "Deficit",
                "why_chosen": "Audit",
                "how_to_fix": "Equip",
                "citizen_complaints": 12,
                "beneficiaries": 3000,
                "score": 85,
                "priority": "HIGH",
                "priority_color": "#C62B2B",
                "estimated_cost_lakh": 85
            }
        ]

        db_mock = MagicMock()
        data = get_recommendations(state="karnataka", district="mandya", db=db_mock)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["total"], 1)
        self.assertEqual(data["summary"]["HIGH"], 1)

    @patch("app.routing.recommendations._build_recommendations")
    def test_get_summary(self, mock_build):
        mock_build.return_value = [
            {
                "id": "health_1",
                "category": "Healthcare",
                "priority": "HIGH",
                "citizen_complaints": 12
            },
            {
                "id": "water_1",
                "category": "Water Supply",
                "priority": "MID",
                "citizen_complaints": 5
            }
        ]

        db_mock = MagicMock()
        data = get_summary(state="karnataka", district="mandya", db=db_mock)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["HIGH"], 1)
        self.assertEqual(data["MID"], 1)
        self.assertEqual(data["LOW"], 0)

if __name__ == "__main__":
    unittest.main()

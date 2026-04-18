import unittest

from orchestrator import Assignment, HybridTeamOrchestrator


class HybridTeamOrchestratorTests(unittest.TestCase):
    def test_csv_import_distribution(self):
        orchestrator = HybridTeamOrchestrator()

        assignments = orchestrator.distribute(
            "Build CSV import with validation and duplicate detection."
        )

        self.assertEqual(
            assignments,
            [
                Assignment("PM human", "confirm duplicate merge policy"),
                Assignment("Backend AI", "implement parser and validator"),
                Assignment("QA AI", "create test cases"),
                Assignment("Human engineer", "review edge-case logic"),
                Assignment("Docs AI", "write release notes"),
            ],
        )

    def test_status_changes(self):
        orchestrator = HybridTeamOrchestrator()

        self.assertEqual(
            orchestrator.status_changes(),
            [
                "waiting for PM",
                "backend AI working",
                "QA AI finished",
                "human review pending",
                "release package ready",
            ],
        )


if __name__ == "__main__":
    unittest.main()

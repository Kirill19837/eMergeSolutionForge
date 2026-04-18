import unittest

from orchestrator import Assignment, BoardItem, HybridTeamOrchestrator


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
        assignments = orchestrator.distribute(
            "Build CSV import with validation and duplicate detection."
        )

        self.assertEqual(
            orchestrator.status_changes(assignments),
            [
                "waiting for PM",
                "backend AI working",
                "QA AI finished",
                "human review pending",
                "release package ready",
            ],
        )

    def test_distribution_allows_word_variations(self):
        orchestrator = HybridTeamOrchestrator()

        assignments = orchestrator.distribute(
            "Build CSV file importing flow with validation and duplicates handling."
        )

        self.assertEqual(
            assignments[0:2],
            [
                Assignment("PM human", "confirm duplicate merge policy"),
                Assignment("Backend AI", "implement parser and validator"),
            ],
        )

    def test_project_board_contains_human_and_ai_actors(self):
        orchestrator = HybridTeamOrchestrator()
        assignments = orchestrator.distribute(
            "Build CSV import with validation and duplicate detection."
        )

        self.assertEqual(
            orchestrator.project_board(assignments),
            [
                BoardItem("human team", "PM human", "confirm duplicate merge policy"),
                BoardItem("AI agents", "Backend AI", "implement parser and validator"),
                BoardItem("AI agents", "QA AI", "create test cases"),
                BoardItem("human team", "Human engineer", "review edge-case logic"),
                BoardItem("AI agents", "Docs AI", "write release notes"),
            ],
        )

    def test_can_assign_human_or_agent_to_task(self):
        orchestrator = HybridTeamOrchestrator()
        assignments = orchestrator.distribute(
            "Build CSV import with validation and duplicate detection."
        )

        updated = orchestrator.assign_task(
            assignments, "create test cases", "QA human"
        )

        self.assertIn(Assignment("QA human", "create test cases"), updated)
        board = orchestrator.project_board(updated)
        self.assertIn(
            BoardItem("human team", "QA human", "create test cases"),
            board,
        )

    def test_start_task_when_work_begins(self):
        orchestrator = HybridTeamOrchestrator()
        assignments = orchestrator.distribute(
            "Build CSV import with validation and duplicate detection."
        )

        started = orchestrator.start_task(assignments, "implement parser and validator")

        self.assertEqual(started, "Backend AI started implement parser and validator")

    def test_finish_assigns_next_stage_owner(self):
        orchestrator = HybridTeamOrchestrator()
        assignments = orchestrator.distribute(
            "Build CSV import with validation and duplicate detection."
        )

        updated, completion_status = orchestrator.complete_task(
            assignments,
            "implement parser and validator",
            "QA human",
            "verify task completion",
        )

        self.assertEqual(
            completion_status,
            "Backend AI finished implement parser and validator; QA human assigned to verify task completion",
        )
        self.assertIn(
            Assignment("QA human", "verify task completion"),
            updated,
        )


if __name__ == "__main__":
    unittest.main()

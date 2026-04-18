import unittest

from orchestrator import (
    Assignment,
    BoardItem,
    HybridTeamOrchestrator,
    Notification,
)


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
            assignments,
            [
                Assignment("PM human", "confirm duplicate merge policy"),
                Assignment("Backend AI", "implement parser and validator"),
                Assignment("QA AI", "create test cases"),
                Assignment("Human engineer", "review edge-case logic"),
                Assignment("Docs AI", "write release notes"),
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

    def test_complete_task_assigns_next_stage_owner(self):
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

    def test_complete_task_can_assign_deploy_to_test_server_stage(self):
        orchestrator = HybridTeamOrchestrator()
        assignments = orchestrator.distribute(
            "Build CSV import with validation and duplicate detection."
        )

        updated, completion_status = orchestrator.complete_task(
            assignments,
            "create test cases",
            "DevOps AI",
            "deploy to the test server",
        )

        self.assertEqual(
            completion_status,
            "QA AI finished create test cases; DevOps AI assigned to deploy to the test server",
        )
        self.assertIn(
            Assignment("DevOps AI", "deploy to the test server"),
            updated,
        )

    def test_list_ai_actors_includes_senior_dev_architect_and_qa(self):
        orchestrator = HybridTeamOrchestrator()
        ai_actors = orchestrator.list_ai_actors()

        self.assertIn("Senior Dev AI", ai_actors)
        self.assertIn("Architect AI", ai_actors)
        self.assertIn("QA AI", ai_actors)

    def test_list_human_actors_includes_same_core_roles(self):
        orchestrator = HybridTeamOrchestrator()
        human_actors = orchestrator.list_human_actors()

        self.assertIn("Senior Dev human", human_actors)
        self.assertIn("Architect human", human_actors)
        self.assertIn("QA human", human_actors)

    def test_create_process_builds_kanban_board(self):
        orchestrator = HybridTeamOrchestrator()

        process = orchestrator.create_process(
            "Build CSV import with validation and duplicate detection."
        )
        board = orchestrator.kanban_board(process)

        self.assertEqual(len(board["todo"]), 5)
        self.assertEqual(len(board["in_progress"]), 0)
        self.assertEqual(len(board["human_input"]), 0)
        self.assertEqual(len(board["done"]), 0)

    def test_ai_can_request_human_input_and_notification_is_created(self):
        orchestrator = HybridTeamOrchestrator()
        process = orchestrator.create_process(
            "Build CSV import with validation and duplicate detection."
        )
        process, _ = orchestrator.move_task_to_work(
            process, "implement parser and validator"
        )

        updated_process, notification = orchestrator.request_human_input(
            process=process,
            task="implement parser and validator",
            ai_actor="Backend AI",
            human_actor="Architect human",
            note="Need clarification on fallback parsing strategy",
        )

        self.assertEqual(
            notification,
            Notification(
                recipient="Architect human",
                requested_by="Backend AI",
                task="implement parser and validator",
                message="Backend AI requested human input: Need clarification on fallback parsing strategy",
            ),
        )
        board = orchestrator.kanban_board(updated_process)
        self.assertEqual(len(board["human_input"]), 1)
        self.assertEqual(board["human_input"][0].actor, "Architect human")


if __name__ == "__main__":
    unittest.main()

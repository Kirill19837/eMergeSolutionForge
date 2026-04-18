from dataclasses import dataclass
import re


@dataclass(frozen=True)
class Assignment:
    executor: str
    task: str


@dataclass(frozen=True)
class BoardItem:
    actor_group: str
    actor: str
    task: str


class HybridTeamOrchestrator:
    @staticmethod
    def _infer_actor_group(actor: str) -> str:
        normalized = actor.lower()
        if "human" in normalized or "engineer" in normalized or "pm" in normalized:
            return "human team"
        return "AI agents"

    def distribute(self, work_item: str) -> list[Assignment]:
        normalized = work_item.lower()
        assignments: list[Assignment] = []

        if re.search(r"\bduplicate\w*\b", normalized):
            assignments.append(
                Assignment("PM human", "confirm duplicate merge policy")
            )

        if re.search(r"\bcsv\b", normalized) or re.search(
            r"\bimport\w*\b", normalized
        ):
            assignments.append(
                Assignment("Backend AI", "implement parser and validator")
            )

        assignments.extend(
            [
                Assignment("QA AI", "create test cases"),
                Assignment("Human engineer", "review edge-case logic"),
                Assignment("Docs AI", "write release notes"),
            ]
        )
        return assignments

    def status_changes(self, assignments: list[Assignment]) -> list[str]:
        status_by_executor = {
            "PM human": "waiting for PM",
            "Backend AI": "backend AI working",
            "QA AI": "QA AI finished",
            "Human engineer": "human review pending",
        }
        statuses = [
            status_by_executor[assignment.executor]
            for assignment in assignments
            if assignment.executor in status_by_executor
        ]
        statuses.append("release package ready")
        return statuses

    def project_board(self, assignments: list[Assignment]) -> list[BoardItem]:
        actor_groups = {
            "PM human": "human team",
            "Human engineer": "human team",
            "Backend AI": "AI agents",
            "QA AI": "AI agents",
            "Docs AI": "AI agents",
        }
        return [
            BoardItem(
                actor_group=actor_groups.get(
                    assignment.executor,
                    self._infer_actor_group(assignment.executor),
                ),
                actor=assignment.executor,
                task=assignment.task,
            )
            for assignment in assignments
        ]

    def assign_task(
        self, assignments: list[Assignment], task: str, actor: str
    ) -> list[Assignment]:
        updated = []
        replaced = False
        for assignment in assignments:
            if assignment.task == task:
                updated.append(Assignment(actor, task))
                replaced = True
            else:
                updated.append(assignment)
        if not replaced:
            updated.append(Assignment(actor, task))
        return updated

    def start_task(self, assignments: list[Assignment], task: str) -> str:
        for assignment in assignments:
            if assignment.task == task:
                return f"{assignment.executor} started {task}"
        raise ValueError(f"Task not found: {task}")

    def complete_task(
        self,
        assignments: list[Assignment],
        task: str,
        next_stage_actor: str,
        next_stage_task: str = "verify task completion",
    ) -> tuple[list[Assignment], str]:
        for assignment in assignments:
            if assignment.task == task:
                updated = self.assign_task(
                    assignments, next_stage_task, next_stage_actor
                )
                status = (
                    f"{assignment.executor} finished {task}; "
                    f"{next_stage_actor} assigned to {next_stage_task}"
                )
                return updated, status
        raise ValueError(f"Task not found: {task}")

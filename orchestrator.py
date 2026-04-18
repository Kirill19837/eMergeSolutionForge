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


@dataclass(frozen=True)
class Notification:
    recipient: str
    requested_by: str
    task: str
    message: str


@dataclass(frozen=True)
class TaskCard:
    task: str
    actor: str
    actor_group: str
    column: str
    needs_human_input: bool = False


@dataclass(frozen=True)
class ProcessState:
    cards: list[TaskCard]
    notifications: list[Notification]


class HybridTeamOrchestrator:
    AI_ACTORS = [
        "Senior Dev AI",
        "Architect AI",
        "QA AI",
        "Backend AI",
        "Docs AI",
        "DevOps AI",
    ]
    HUMAN_ACTORS = [
        "Senior Dev human",
        "Architect human",
        "QA human",
        "PM human",
        "Human engineer",
    ]

    STATUS_BY_EXECUTOR = {
        "PM human": "waiting for PM",
        "Backend AI": "backend AI working",
        "QA AI": "QA AI finished",
        "Human engineer": "human review pending",
    }

    @staticmethod
    def _infer_actor_group(actor: str) -> str:
        normalized = actor.lower()
        if re.search(r"\bhuman\b|\bengineer\b|\bpm\b", normalized):
            return "human team"
        return "AI agents"

    def list_ai_actors(self) -> list[str]:
        return list(self.AI_ACTORS)

    def list_human_actors(self) -> list[str]:
        return list(self.HUMAN_ACTORS)

    def distribute(self, work_item: str) -> list[Assignment]:
        normalized = work_item.lower()
        assignments: list[Assignment] = []

        if re.search(r"\bduplicate\w*\b", normalized):
            assignments.append(
                Assignment("PM human", "confirm duplicate merge policy")
            )

        if re.search(r"\bcsv\b|\bimport\w*\b", normalized):
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
        statuses = [
            self.STATUS_BY_EXECUTOR[assignment.executor]
            for assignment in assignments
            if assignment.executor in self.STATUS_BY_EXECUTOR
        ]
        statuses.append("release package ready")
        return statuses

    def project_board(self, assignments: list[Assignment]) -> list[BoardItem]:
        return [
            BoardItem(
                actor_group=self._infer_actor_group(assignment.executor),
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

    def create_process(self, work_item: str) -> ProcessState:
        assignments = self.distribute(work_item)
        cards = [
            TaskCard(
                task=assignment.task,
                actor=assignment.executor,
                actor_group=self._infer_actor_group(assignment.executor),
                column="todo",
            )
            for assignment in assignments
        ]
        return ProcessState(cards=cards, notifications=[])

    def kanban_board(self, process: ProcessState) -> dict[str, list[TaskCard]]:
        board: dict[str, list[TaskCard]] = {
            "todo": [],
            "in_progress": [],
            "human_input": [],
            "done": [],
        }
        for card in process.cards:
            if card.column not in board:
                raise ValueError(f"Unsupported kanban column: {card.column}")
            board[card.column].append(card)
        return board

    def move_task_to_work(
        self, process: ProcessState, task: str
    ) -> tuple[ProcessState, str]:
        updated_cards = []
        start_status = None
        for card in process.cards:
            if card.task == task:
                updated_cards.append(
                    TaskCard(
                        task=card.task,
                        actor=card.actor,
                        actor_group=card.actor_group,
                        column="in_progress",
                        needs_human_input=False,
                    )
                )
                start_status = f"{card.actor} started {task}"
            else:
                updated_cards.append(card)
        if start_status is None:
            raise ValueError(f"Task not found: {task}")
        return (
            ProcessState(cards=updated_cards, notifications=process.notifications),
            start_status,
        )

    def request_human_input(
        self,
        process: ProcessState,
        task: str,
        ai_actor: str,
        human_actor: str,
        note: str,
    ) -> tuple[ProcessState, Notification]:
        if ai_actor not in self.AI_ACTORS and not ai_actor.lower().endswith(" ai"):
            raise ValueError("Only AI actors can request human input")

        updated_cards = []
        found = False
        for card in process.cards:
            if card.task == task:
                updated_cards.append(
                    TaskCard(
                        task=card.task,
                        actor=human_actor,
                        actor_group=self._infer_actor_group(human_actor),
                        column="human_input",
                        needs_human_input=True,
                    )
                )
                found = True
            else:
                updated_cards.append(card)
        if not found:
            raise ValueError(f"Task not found: {task}")

        notification = Notification(
            recipient=human_actor,
            requested_by=ai_actor,
            task=task,
            message=f"{ai_actor} requested human input: {note}",
        )
        return (
            ProcessState(
                cards=updated_cards,
                notifications=[*process.notifications, notification],
            ),
            notification,
        )

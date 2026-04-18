from dataclasses import dataclass


@dataclass(frozen=True)
class Assignment:
    executor: str
    task: str


class HybridTeamOrchestrator:
    def distribute(self, work_item: str) -> list[Assignment]:
        normalized = work_item.lower()
        assignments: list[Assignment] = []

        if "duplicate" in normalized:
            assignments.append(
                Assignment("PM human", "confirm duplicate merge policy")
            )

        if "csv" in normalized or "import" in normalized:
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

    def status_changes(self) -> list[str]:
        return [
            "waiting for PM",
            "backend AI working",
            "QA AI finished",
            "human review pending",
            "release package ready",
        ]

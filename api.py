import os
import uuid
from dataclasses import asdict
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from orchestrator import HybridTeamOrchestrator, ProcessState

app = FastAPI(title="eMergeSolutionForge Orchestrator API")

# CORS: allow_origins defaults to same-origin only in production.
# Set the CORS_ORIGINS environment variable (comma-separated) to override,
# e.g. CORS_ORIGINS="http://localhost:3000,https://myapp.example.com"
_cors_origins = os.environ.get("CORS_ORIGINS", "").split(",") if os.environ.get("CORS_ORIGINS") else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

_orchestrator = HybridTeamOrchestrator()

# In-memory store: process_id -> ProcessState
_processes: dict[str, ProcessState] = {}


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class CreateProcessRequest(BaseModel):
    work_item: str


class AssignTaskRequest(BaseModel):
    actor: str


class CompleteTaskRequest(BaseModel):
    next_actor: str
    next_task: str = "verify task completion"


class RequestInputRequest(BaseModel):
    ai_actor: str
    human_actor: str
    note: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_process(process_id: str) -> ProcessState:
    if process_id not in _processes:
        raise HTTPException(status_code=404, detail=f"Process '{process_id}' not found")
    return _processes[process_id]


def _serialize_process(process_id: str, process: ProcessState) -> dict:
    board = _orchestrator.kanban_board(process)
    return {
        "id": process_id,
        "board": {col: [asdict(card) for card in cards] for col, cards in board.items()},
        "notifications": [asdict(n) for n in process.notifications],
    }


# ---------------------------------------------------------------------------
# Actor catalog endpoints
# ---------------------------------------------------------------------------


@app.get("/actors/ai")
def list_ai_actors() -> list[str]:
    return _orchestrator.list_ai_actors()


@app.get("/actors/human")
def list_human_actors() -> list[str]:
    return _orchestrator.list_human_actors()


# ---------------------------------------------------------------------------
# Process lifecycle endpoints
# ---------------------------------------------------------------------------


@app.post("/processes", status_code=201)
def create_process(body: CreateProcessRequest) -> dict:
    process_id = str(uuid.uuid4())
    process = _orchestrator.create_process(body.work_item)
    _processes[process_id] = process
    return _serialize_process(process_id, process)


@app.get("/processes/{process_id}/board")
def get_board(process_id: str) -> dict:
    process = _get_process(process_id)
    return _serialize_process(process_id, process)


@app.post("/processes/{process_id}/tasks/{task}/start")
def start_task(process_id: str, task: str) -> dict:
    process = _get_process(process_id)
    try:
        updated_process, status = _orchestrator.move_task_to_work(process, task)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    _processes[process_id] = updated_process
    result = _serialize_process(process_id, updated_process)
    result["status"] = status
    return result


@app.patch("/processes/{process_id}/tasks/{task}")
def assign_task(process_id: str, task: str, body: AssignTaskRequest) -> dict:
    process = _get_process(process_id)
    # Rebuild assignments from cards so assign_task can work
    from orchestrator import Assignment

    assignments = [
        Assignment(executor=card.actor, task=card.task) for card in process.cards
    ]
    updated_assignments = _orchestrator.assign_task(assignments, task, body.actor)
    # Reflect assignment changes back onto the cards, preserving column / needs_human_input
    from orchestrator import TaskCard

    actor_map = {a.task: a.executor for a in updated_assignments}
    updated_cards = []
    existing_tasks = {card.task for card in process.cards}
    for card in process.cards:
        new_actor = actor_map.get(card.task, card.actor)
        updated_cards.append(
            TaskCard(
                task=card.task,
                actor=new_actor,
                actor_group=_orchestrator._infer_actor_group(new_actor),
                column=card.column,
                needs_human_input=card.needs_human_input,
            )
        )
    # Append any brand-new tasks added by assign_task
    for assignment in updated_assignments:
        if assignment.task not in existing_tasks:
            updated_cards.append(
                TaskCard(
                    task=assignment.task,
                    actor=assignment.executor,
                    actor_group=_orchestrator._infer_actor_group(assignment.executor),
                    column="todo",
                )
            )
    updated_process = ProcessState(
        cards=updated_cards, notifications=process.notifications
    )
    _processes[process_id] = updated_process
    return _serialize_process(process_id, updated_process)


@app.post("/processes/{process_id}/tasks/{task}/complete")
def complete_task(process_id: str, task: str, body: CompleteTaskRequest) -> dict:
    process = _get_process(process_id)
    from orchestrator import Assignment, TaskCard

    assignments = [
        Assignment(executor=card.actor, task=card.task) for card in process.cards
    ]
    try:
        updated_assignments, status = _orchestrator.complete_task(
            assignments, task, body.next_actor, body.next_task
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    actor_map = {a.task: a.executor for a in updated_assignments}
    existing_tasks = {card.task for card in process.cards}

    updated_cards = []
    for card in process.cards:
        if card.task == task:
            # Mark original task as done
            updated_cards.append(
                TaskCard(
                    task=card.task,
                    actor=card.actor,
                    actor_group=card.actor_group,
                    column="done",
                    needs_human_input=False,
                )
            )
        else:
            new_actor = actor_map.get(card.task, card.actor)
            updated_cards.append(
                TaskCard(
                    task=card.task,
                    actor=new_actor,
                    actor_group=_orchestrator._infer_actor_group(new_actor),
                    column=card.column,
                    needs_human_input=card.needs_human_input,
                )
            )
    # Add next-stage task card if it is new
    for assignment in updated_assignments:
        if assignment.task not in existing_tasks:
            updated_cards.append(
                TaskCard(
                    task=assignment.task,
                    actor=assignment.executor,
                    actor_group=_orchestrator._infer_actor_group(assignment.executor),
                    column="todo",
                )
            )

    updated_process = ProcessState(
        cards=updated_cards, notifications=process.notifications
    )
    _processes[process_id] = updated_process
    result = _serialize_process(process_id, updated_process)
    result["status"] = status
    return result


@app.post("/processes/{process_id}/tasks/{task}/request-input")
def request_human_input(
    process_id: str, task: str, body: RequestInputRequest
) -> dict:
    process = _get_process(process_id)
    try:
        updated_process, notification = _orchestrator.request_human_input(
            process=process,
            task=task,
            ai_actor=body.ai_actor,
            human_actor=body.human_actor,
            note=body.note,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _processes[process_id] = updated_process
    result = _serialize_process(process_id, updated_process)
    result["notification"] = asdict(notification)
    return result


# ── Serve the UI ────────────────────────────────────────────────────────────
# NOTE: StaticFiles must be mounted LAST so that all API routes defined above
# take priority. Any path not matched by an API route will fall through to the
# ui/ directory; missing files there will return a proper 404 from StaticFiles.
app.mount("/", StaticFiles(directory="ui", html=True), name="ui")

# eMergeSolutionForge
Hybrid Team Orchestrator breaks incoming work into subtasks, then assigns each one to the best executor: human, AI agent, or both. It routes by ambiguity, risk, and skill, keeps people in the loop, tracks execution, and merges outputs into one delivery flow for modern product teams.

## Running the UI

### Requirements

```
pip install fastapi "uvicorn[standard]"
```

### Start the server

```bash
uvicorn api:app --reload
```

Then open **http://localhost:8000** in your browser.

The interactive API docs (Swagger UI) are available at **http://localhost:8000/docs**.

### REST API overview

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/actors/ai` | List all AI actors |
| `GET` | `/actors/human` | List all human actors |
| `POST` | `/processes` | Create a process from a work-item description |
| `GET` | `/processes/{id}/board` | Fetch the kanban board + notifications |
| `POST` | `/processes/{id}/tasks/{task}/start` | Move a task card to *In Progress* |
| `PATCH` | `/processes/{id}/tasks/{task}` | Reassign a task to a different actor |
| `POST` | `/processes/{id}/tasks/{task}/complete` | Complete a task and assign the next stage |
| `POST` | `/processes/{id}/tasks/{task}/request-input` | AI actor requests human input (moves card to *Human Input* and creates a notification) |

## MVP demo

Input:
`Build CSV import with validation and duplicate detection.`

Orchestrator outputs:

- PM human: confirm duplicate merge policy
- Backend AI: implement parser and validator
- QA AI: create test cases
- Human engineer: review edge-case logic
- Docs AI: write release notes

Status changes:

- waiting for PM
- backend AI working
- QA AI finished
- human review pending
- release package ready

Project board (tasks + actors):

- human team | PM human | confirm duplicate merge policy
- AI agents | Backend AI | implement parser and validator
- AI agents | QA AI | create test cases
- human team | Human engineer | review edge-case logic
- AI agents | Docs AI | write release notes

Manual assignment support:

- Reassign existing task to a specific human/agent
- Add a new task with a specific human/agent assignment
- Start a task in work and get `"<actor> started <task>"` status output
- Complete a task and automatically assign the next stage (for example, `verify task completion`)
- Next-stage examples include operational handoff tasks like `deploy to the test server`

Actor catalogs:

- AI agents: Senior Dev AI, Architect AI, QA AI, Backend AI, Docs AI, DevOps AI
- Human team: Senior Dev human, Architect human, QA human, PM human, Human engineer

## Complete feature documentation

### Core classes

- `HybridTeamOrchestrator`: main orchestrator API
- `Assignment`: task + assigned actor
- `BoardItem`: lightweight board row (`actor_group`, `actor`, `task`)
- `TaskCard`: kanban card (`task`, `actor`, `actor_group`, `column`, `needs_human_input`)
- `ProcessState`: process snapshot (`cards`, `notifications`)
- `Notification`: human-input request notification

### Intelligent task distribution

`distribute(work_item)` analyzes work text and assigns tasks:

- duplicate-related work -> PM human policy confirmation
- csv/import-related work -> Backend AI parser/validator
- always includes QA AI test design, Human engineer edge-case review, Docs AI release notes

### Actor catalogs

- `list_ai_actors()` returns AI roles (including Senior Dev AI, Architect AI, QA AI)
- `list_human_actors()` returns human roles with matching core roles (Senior Dev human, Architect human, QA human)

### Manual assignment

- `assign_task(assignments, task, actor)`
  - reassigns existing task to specific human/agent
  - or appends a new task assignment if task does not exist

### Status and lifecycle APIs

- `status_changes(assignments)` returns the requested workflow status progression
- `start_task(assignments, task)` returns `"<actor> started <task>"`
- `complete_task(assignments, task, next_stage_actor, next_stage_task="verify task completion")`
  - marks completion message
  - assigns ownership of next stage (example: `deploy to the test server`)

### Process + Kanban board APIs

- `create_process(work_item)` creates a process with cards in `todo`
- `kanban_board(process)` returns grouped columns:
  - `todo`
  - `in_progress`
  - `human_input`
  - `done`
- `move_task_to_work(process, task)` moves task card to `in_progress` and returns start status

### AI -> Human input request and notifications

- `request_human_input(process, task, ai_actor, human_actor, note)`
  - allowed only for AI actors
  - moves task to `human_input`
  - temporarily routes task ownership to requested human actor
  - appends `Notification` to process notifications
  - returns updated process + created notification

Example notification payload:

- recipient: Architect human
- requested_by: Backend AI
- task: implement parser and validator
- message: Backend AI requested human input: Need clarification on fallback parsing strategy

### Test coverage

Unit tests validate:

- MVP assignment output
- required status progression
- wording variations for input matching
- project board actor grouping
- manual task assignment
- task start behavior
- completion handoff + next-stage assignment (`verify task completion`, `deploy to the test server`)
- AI and human actor catalogs
- process creation and kanban columns
- AI human-input request notifications

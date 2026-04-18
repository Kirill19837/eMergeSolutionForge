# eMergeSolutionForge
Hybrid Team Orchestrator breaks incoming work into subtasks, then assigns each one to the best executor: human, AI agent, or both. It routes by ambiguity, risk, and skill, keeps people in the loop, tracks execution, and merges outputs into one delivery flow for modern product teams.

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

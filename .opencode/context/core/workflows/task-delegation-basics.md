<!-- Context: workflows/delegation | Priority: high | Version: 3.1 | Updated: 2026-02-05 -->
# Delegation Context Template (Home Assistant Custom Integration)

## Quick Reference

**Process**: Discover → Propose → Approve → Init Session → Persist Context → Delegate → Cleanup

**Location**: `.tmp/sessions/{YYYY-MM-DD}-{task-slug}/context.md`

**Key Principle**: ContextScout discovers paths. The orchestrator persists them into context.md AFTER approval. Downstream agents read from context.md — no re-discovery.

---

## When to Create a Session

Only create a session when:
- User has **approved** the proposed approach (never before)
- Task requires delegation to TaskManager or working agents
- Task is complex enough to need shared context (4+ files, >60min)

For simple tasks (1-3 files, direct execution): skip session creation entirely.

---

## The Flow

```
Stage 1: DISCOVER   → ContextScout finds paths (read-only, nothing written)
Stage 2: PROPOSE    → Show user lightweight summary (nothing written)
Stage 3: APPROVE    → User says yes. NOW we can write.
Stage 4: INIT       → Create session dir + context.md (persist discovered paths here)
Stage 5: DELEGATE   → Pass session path to TaskManager / working agents
Stage 6: CLEANUP    → Ask user, then delete session dir
```

---

## Template Structure

**Location**: `.tmp/sessions/{YYYY-MM-DD}-{task-slug}/context.md`

```markdown
# Task Context: {Task Name}

Session ID: {YYYY-MM-DD}-{task-slug}
Created: {ISO timestamp}
Status: in_progress

## Current Request
{What user asked for — verbatim or close paraphrase}

## Context Files (Standards to Follow)
Paths ContextScout discovered. Downstream agents load these for coding standards.
- .github/instructions/python.instructions.md
- .github/instructions/entities.instructions.md
- .github/instructions/coordinator.instructions.md
- .github/instructions/api.instructions.md
- .github/instructions/config_flow.instructions.md
- .opencode/context/core/standards/code-quality.md

## Reference Files (Source Material)
Project files relevant to the task — NOT standards.
- {e.g. custom_components/ha_asustor_nas_custom_integration/manifest.json}
- {e.g. custom_components/ha_asustor_nas_custom_integration/sensor.py}

## Components
- {Component 1} — {what it does}
- {Component 2} — {what it does}

## Constraints
- Must use `aiohttp` for API calls.
- Must use `DataUpdateCoordinator` for data fetching.
- Must include type hints and pass `script/check`.

## Exit Criteria
- [ ] {specific completion condition}

## Progress
- [ ] Session initialized
- [ ] Tasks created (if using TaskManager)
- [ ] Implementation complete
```

---

## Delegation Process

**Step 1-3: Discover, Propose, Approve** (before any writes)
- Call ContextScout, capture paths (ensure `.github/instructions/*.md` are included).
- Show user lightweight summary, wait for approval.

**Step 4: Init Session** (first writes, after approval)
- Create `.tmp/sessions/{YYYY-MM-DD}-{task-slug}/`
- Write `context.md` with discovered paths.

**Step 5: Delegate**
```javascript
task(
  subagent_type="TaskManager",
  description="{brief}",
  prompt="Load context from .tmp/sessions/{session-id}/context.md
          {specific instructions}"
)
```

**Step 6: Cleanup**
- Ask user: "Task complete. Clean up session files?"
- If approved: Delete session directory.

---

## What Downstream Agents Expect

| Agent | Reads | Does |
|-------|-------|------|
| **TaskManager** | `context.md` (full) | Extracts files, creates subtask JSONs |
| **CoderAgent** | subtask JSON | Loads HA standards, references source, implements |
| **TestEngineer** | session path | Writes tests against HA standards (only if requested) |
| **CodeReviewer** | session path | Reviews against HA standards (async I/O, type hints) |
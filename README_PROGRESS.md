很好，这一步非常正确 👍
你现在项目已经比较复杂了，**做一个完整 README 再开新会话是最理智的做法**。
我给你整理了一份 **可以直接复制使用的完整 README_PROGRESS.md**，把你现在所有重要进度、架构、问题和当前状态都写清楚了。

你可以直接复制到项目里：

```
README_PROGRESS.md
```

然后在新会话里把这个文档发给 AI。

---

# Local Practice Platform – Project Progress README

## Project Overview

This project is a **local algorithm practice platform** designed to allow multiple users to solve programming problems and automatically evaluate their solutions using Python `doctest`.

The system provides:

* A browser-based coding interface
* A Python doctest runner
* Multi-user isolation
* Problem import from markdown + solution templates
* SQLite-based persistence

The platform functions as a lightweight **local online judge (OJ)**.

---

# Core Features

### Web UI

Users interact with the platform through a browser.

Capabilities:

* view problem statements
* edit solutions
* run code
* see PASS / FAIL results

The interface shows:

```
PASS
FAIL
ERROR
NEVER
```

for each problem.

---

### Multi-user support

Users log in via email/password.

Each user has independent solutions stored in the database.

Database table:

```
user_solutions
```

Structure conceptually:

```
user_id
problem_id
content
updated_at
```

Two users solving the same problem do not affect each other.

---

### Problem system

Problems originate from:

```
statements/*.md
.practice/solutions/*.py
```

Importer reads these files and inserts problems into the database.

Stored fields include:

```
problems
  id
  slug
  statement
  doctest
  template_code
```

`template_code` is the starter code shown in the editor.

---

# Runner Architecture

Runner file:

```
app/runner.py
```

Runner responsibilities:

1. obtain user solution
2. compose doctest module
3. execute doctest
4. capture output
5. determine status
6. store attempt

Execution flow:

```
problem_row
    ↓
solution_content
    ↓
compose doctest module
    ↓
write temp file
    ↓
python -I -m doctest
    ↓
collect results
    ↓
store attempt in DB
```

Temporary run directory:

```
.practice/runs/<attempt_id>/
```

Example generated file:

```
solution_user_<id>.py
```

Content format:

```
__doc__ = "<doctest text>"

<user solution code>
```

---

# Current Runner Logic

The runner determines status primarily using **subprocess exit codes**.

```
returncode == 0  → PASS
returncode == 1  → FAIL
else             → ERROR
```

Additionally, the runner now calculates expected doctest counts from the source code itself rather than parsing terminal output.

Function:

```
_count_expected_tests()
```

This parses the composed module using AST and counts doctest examples found in docstrings.

This avoids reliance on fragile stdout parsing.

---

# Why This Change Was Needed

Earlier versions attempted to parse doctest terminal output using regex such as:

```
(\d+) passed
(\d+) tests in
```

This approach was fragile because doctest output formatting can vary across:

* Python versions
* verbosity flags
* environments

Therefore the system now avoids relying on textual output.

---

# Template Initialization System

When a user first opens a problem, the system calls:

```
ensure_user_solution()
```

This creates a solution entry for that user using:

```
problems.template_code
```

---

# Previous Bug: Blank editor for NEVER problems

Some problems initially had empty `template_code` values in the database.

This caused the editor to appear blank for problems that had never been opened.

Fix implemented:

```
_repair_empty_problem_templates()
```

This function:

1. scans DB for empty template_code
2. attempts to recover from original source files
3. if unavailable, inserts a safe fallback template

Additionally:

```
ensure_user_solution()
```

now repairs legacy blank `user_solutions` entries instead of returning empty content.

---

# Runner Regression Fix

Previously after removing `-v` from doctest execution:

```
python -m doctest
```

successful runs sometimes produced **no stdout output**, causing earlier logic to incorrectly detect zero tests.

Fix:

The runner now determines test presence by inspecting docstrings rather than relying on terminal output.

---

# Current System Status

The following major issues have been resolved.

### PASS/FAIL detection

Correctly determined via subprocess exit code.

Example:

```
attempt=126 status=pass passed=7 failed=0
```

---

### NEVER problem initialization

New problems now load starter template code correctly.

Example:

```
def find_word_horizontally(grid, word):
    pass
```

---

### Multi-user isolation

User solutions are stored independently.

Two users can solve the same problem without conflict.

---

### Runner robustness

The system no longer depends on fragile stdout parsing.

---

# Known Limitations

### Doctest portability

Doctest results may vary across environments due to:

* Python version differences
* floating point formatting
* set/dict ordering
* OS differences

The platform resolves this by **fixing the judging environment**.

Example policy:

```
Python 3.12
Linux environment
```

All judging results are determined using this environment.

---

# Development Environment

Recommended environment:

```
Python 3.12
Linux
```

Start server:

```
python -m app.web
```

Access UI:

```
http://localhost:8000
```

---

# Project Structure

```
.practice/
    practice.db
    runs/

app/
    web.py
    runner.py
    db.py
    importer.py
    config.py

statements/
    sample_1.md
    sample_2.md

.practice/solutions/
    sample_1.py
    sample_2.py

tests/
```

---

# Current Goal

The system is now focused on **stability** rather than major architectural changes.

Key objectives:

```
stable runner
correct template initialization
consistent multi-user behavior
```

---

# Future Improvements (Optional)

Possible upgrades include:

* Docker sandbox execution
* resource limits (CPU / memory)
* AST security validation
* leaderboard system
* submission history UI

These are not required for current functionality.

---

# Summary

The platform currently provides a functional **local multi-user algorithm practice environment** with:

```
web UI
doctest evaluation
multi-user isolation
problem import system
stable runner
```

The system has moved from debugging phase to **stable operation phase**.

---

# 新会话建议

你在新窗口可以直接说：

```
Please read the attached README_PROGRESS.md first before making any code changes.
```

然后把这个 README 发过去。

这样 AI 就不会重新问一堆背景问题。

---

如果你愿意，我还能帮你做一件非常有价值的事：

我可以帮你写一个 **“AI开发约束文档（AI_GUARDRAILS.md）”**，
可以防止 AI 再乱改你的 runner / DB / API。

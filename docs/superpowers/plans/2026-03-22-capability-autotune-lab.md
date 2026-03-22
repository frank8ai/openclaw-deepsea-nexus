# Capability Autotune Lab Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a report-first offline autotune lab that can evaluate and recommend better compression rules for Deepsea-Nexus memory/context capture without mutating production runtime state.

**Architecture:** Introduce an internal plugin for observability, make `runtime_middleware` compression rules configurable, add an offline experiment runner plus report script, and surface the latest lab summary through CLI paths/health. Reuse existing scorecard patterns and keep all candidate promotion manual.

**Tech Stack:** Python, existing Deepsea plugin runtime, repo-local JSON eval packs, unittest, existing CLI/report conventions

---

### Task 1: Add failing tests for configurable compression and autotune reporting

**Files:**
- Modify: `C:/Users/frank/.codex/skills/skills/deepsea-nexus/tests/test_memory_v5.py`
- Test: `C:/Users/frank/.codex/skills/skills/deepsea-nexus/tests/test_memory_v5.py`

- [ ] **Step 1: Write failing tests**
- [ ] **Step 2: Run targeted unittest cases and confirm RED**
- [ ] **Step 3: Add minimal production code only for the failing behaviors**
- [ ] **Step 4: Re-run targeted unittest cases and confirm GREEN**

### Task 2: Make runtime middleware compression configurable

**Files:**
- Modify: `C:/Users/frank/.codex/skills/skills/deepsea-nexus/plugins/runtime_middleware_plugin.py`
- Modify: `C:/Users/frank/.codex/skills/skills/deepsea-nexus/core/config_manager.py`
- Modify: `C:/Users/frank/.codex/skills/skills/deepsea-nexus/config.json`

- [ ] **Step 1: Add config-driven compression profile defaults**
- [ ] **Step 2: Wire profile values into RTK transformer behavior**
- [ ] **Step 3: Keep existing defaults backward compatible**
- [ ] **Step 4: Re-run targeted tests**

### Task 3: Add capability autotune lab plugin and scripts

**Files:**
- Create: `C:/Users/frank/.codex/skills/skills/deepsea-nexus/plugins/capability_autotune_lab_plugin.py`
- Create: `C:/Users/frank/.codex/skills/skills/deepsea-nexus/scripts/capability_autotune_lab.py`
- Create: `C:/Users/frank/.codex/skills/skills/deepsea-nexus/scripts/capability_autotune_report.py`
- Create: `C:/Users/frank/.codex/skills/skills/deepsea-nexus/docs/evals/runtime_middleware_compression_golden_cases.json`
- Modify: `C:/Users/frank/.codex/skills/skills/deepsea-nexus/app.py`
- Modify: `C:/Users/frank/.codex/skills/skills/deepsea-nexus/__main__.py`

- [ ] **Step 1: Write failing tests for plugin health/path exposure and lab reports**
- [ ] **Step 2: Add plugin with report-path summary only**
- [ ] **Step 3: Add offline experiment runner and report summarizer**
- [ ] **Step 4: Re-run targeted tests**

### Task 4: Document the new internal subsystem

**Files:**
- Modify: `C:/Users/frank/.codex/skills/skills/deepsea-nexus/README.md`
- Modify: `C:/Users/frank/.codex/skills/skills/deepsea-nexus/docs/TECHNICAL_OVERVIEW_CURRENT.md`
- Modify: `C:/Users/frank/.codex/skills/skills/deepsea-nexus/docs/ARCHITECTURE_CURRENT.md`
- Modify: `C:/Users/frank/.codex/skills/skills/deepsea-nexus/docs/LOCAL_DEPLOY.md`
- Create: `C:/Users/frank/.codex/skills/skills/deepsea-nexus/docs/releases/V5_4_0_RELEASE_2026-03-22.md`
- Create: `C:/Users/frank/.codex/skills/skills/deepsea-nexus/docs/releases/V5_4_0_RELEASE_2026-03-22_ZH.md`
- Modify: `C:/Users/frank/.codex/skills/skills/deepsea-nexus/_version.py`

- [ ] **Step 1: Update version and current-release docs**
- [ ] **Step 2: Document report-first autotune boundaries**
- [ ] **Step 3: Add release notes**

### Task 5: Run full verification

**Files:**
- Test: `C:/Users/frank/.codex/skills/skills/deepsea-nexus/tests/test_memory_v5.py`
- Test: `C:/Users/frank/.codex/skills/skills/deepsea-nexus/scripts/capability_autotune_lab.py`

- [ ] **Step 1: Run targeted tests for new behavior**
- [ ] **Step 2: Run full `python -m unittest tests.test_memory_v5 -v`**
- [ ] **Step 3: Run CLI/report smoke checks**
- [ ] **Step 4: Summarize evidence and remaining risks**

#!/usr/bin/env python3
"""
Deep-Sea Nexus Summary Flush Script
Batch imports structured summaries from ~/.openclaw/logs/summaries/ to the vector store.
"""

from __future__ import annotations

import os
import sys
import json
import glob
import subprocess
from datetime import datetime
from pathlib import Path

try:
    import yaml
except Exception:
    yaml = None

# Setup paths
SCRIPT_DIR = Path(__file__).resolve().parent
NEXUS_ROOT = SCRIPT_DIR.parent
OPENCLAW_HOME = Path(os.environ.get("OPENCLAW_HOME", "~/.openclaw")).expanduser()
DEFAULT_WORKSPACE_ROOT = Path(
    os.environ.get("OPENCLAW_WORKSPACE", OPENCLAW_HOME / "workspace")
).expanduser()


def load_repo_config() -> dict:
    candidates = [
        NEXUS_ROOT / "config.json",
        NEXUS_ROOT / "config.yaml",
    ]
    for candidate in candidates:
        if not candidate.exists():
            continue
        with open(candidate, "r", encoding="utf-8") as f:
            if candidate.suffix == ".json":
                return json.load(f)
            if yaml is not None:
                return yaml.safe_load(f) or {}
    return {}


def resolve_workspace_root(config: dict | None = None) -> Path:
    cfg = config or load_repo_config()
    base = cfg.get("paths", {}).get("base") if isinstance(cfg, dict) else None
    if base:
        return Path(base).expanduser().resolve()
    return DEFAULT_WORKSPACE_ROOT.resolve()


WORKSPACE_ROOT = resolve_workspace_root()
sys.path.insert(0, str(NEXUS_ROOT))
sys.path.insert(0, str(NEXUS_ROOT / "vector_store"))
sys.path.insert(0, str(SCRIPT_DIR))

try:
    from auto_summary import HybridStorage
    from vector_store import create_vector_store
except ImportError as e:
    print(f"❌ Critical Import Error: {e}")
    sys.exit(1)

try:
    from knowledge_common import (
        classify_text,
        make_trace_id,
        normalize_text,
        stable_hash,
    )
except Exception:
    classify_text = None
    make_trace_id = None
    normalize_text = None
    stable_hash = None

SUMMARY_LOG_DIR = (OPENCLAW_HOME / "logs" / "summaries").expanduser()


def maybe_write_warm(json_file: str) -> None:
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return
    project = data.get("project关联") or data.get("项目关联") or data.get("project") or ""
    if not project:
        return
    warm_writer = SCRIPT_DIR / "warm_writer.py"
    if not warm_writer.exists():
        return
    subprocess.run([sys.executable, str(warm_writer), "--from", json_file], check=False)


def maybe_write_pipeline_inbox(data: dict, json_file: str, workspace_root: Path | None = None) -> None:
    active_workspace = Path(workspace_root or WORKSPACE_ROOT).expanduser().resolve()
    policy_path = active_workspace / "config" / "knowledge-pipeline" / "policy.v1.json"
    inbox_normalized = active_workspace / "Obsidian" / "00_Inbox" / "normalized"
    if policy_path.exists():
        try:
            policy = json.loads(policy_path.read_text(encoding="utf-8"))
            inbox_normalized = active_workspace / policy.get("paths", {}).get(
                "inbox_normalized",
                "Obsidian/00_Inbox/normalized",
            )
        except Exception:
            pass

    inbox_normalized.mkdir(parents=True, exist_ok=True)
    raw_text = (
        data.get("本次核心产出")
        or data.get("core_output")
        or data.get("summary")
        or data.get("full_response")
        or data.get("response")
        or json.dumps(data, ensure_ascii=False)
    )
    raw_text = str(raw_text).strip()
    if not raw_text:
        return

    domain = "ops"
    action = "summarize"
    if classify_text is not None:
        try:
            policy = {}
            if policy_path.exists():
                policy = json.loads(policy_path.read_text(encoding="utf-8"))
            domain, action, _ = classify_text(raw_text, policy)
        except Exception:
            pass

    trace_id = make_trace_id("flush") if make_trace_id is not None else f"flush_{int(datetime.utcnow().timestamp())}"
    norm = normalize_text(raw_text) if normalize_text is not None else raw_text.lower()
    dedupe_key = (
        stable_hash(f"{domain}:{action}:{norm[:1200]}", length=24)
        if stable_hash is not None
        else f"{domain}-{action}-{abs(hash(norm))}"
    )
    base = f"{json_file}:{raw_text}"
    item_hash = stable_hash(base, length=10) if stable_hash is not None else str(abs(hash(base)))
    item_id = f"inbox_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{item_hash}"
    out_file = inbox_normalized / f"{item_id}.json"
    payload = {
        "id": item_id,
        "source": json_file,
        "source_type": "structured_summary",
        "captured_at": datetime.utcnow().isoformat() + "Z",
        "raw_text": raw_text,
        "domain": domain,
        "action": action,
        "confidence": data.get("confidence") or data.get("置信度") or "medium",
        "trace_id": trace_id,
        "dedupe_key": dedupe_key,
        "tags": [f"domain/{domain}", f"action/{action}"],
        "project": data.get("project") or data.get("project_name") or data.get("项目关联") or "",
    }
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

def main():
    if not SUMMARY_LOG_DIR.exists():
        print(f"ℹ️ Directory not found: {SUMMARY_LOG_DIR}")
        return

    json_files = glob.glob(str(SUMMARY_LOG_DIR / "*.json"))
    
    if not json_files:
        print(f"ℹ️ No pending summaries found in {SUMMARY_LOG_DIR}")
        return

    print(f"🔄 Found {len(json_files)} pending summaries. initializing vector store...")
    
    try:
        store = create_vector_store()
        storage = HybridStorage(store)
    except Exception as e:
        print(f"❌ Failed to initialize vector store: {e}")
        return

    success_count = 0
    fail_count = 0

    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            conversation_id = data.get('conversation_id', 'unknown')
            response = data.get('full_response', '') or data.get('response', '')  # fallback
            user_query = data.get('user_query', '')
            
            # Support "summary-only" JSON payloads (StructuredSummary v2.0) where
            # the file itself is the summary object.
            if not response:
                if any(k in data for k in ("本次核心产出", "技术要点", "决策上下文", "避坑记录")):
                    response = (
                        "## 📋 总结\n"
                        "```json\n" + json.dumps(data, ensure_ascii=False) + "\n```\n"
                    )
                else:
                    print(f"⚠️ Skipping {json_file}: No 'full_response' found.")
                    fail_count += 1
                    continue

            print(f"📥 Importing summary for conversation: {conversation_id}...")
            
            result = storage.process_and_store(
                conversation_id=conversation_id,
                response=response,
                user_query=user_query
            )
            
            if result.get('stored_count', 0) > 0:
                print(f"✅ Successfully imported. Stored {result['stored_count']} items.")
                maybe_write_warm(json_file)
                maybe_write_pipeline_inbox(data, json_file, workspace_root=WORKSPACE_ROOT)
                os.remove(json_file)
                success_count += 1
            else:
                print(f"⚠️ Imported but stored_count is 0. Check content.")
                # If it didn't store anything, maybe it was empty or malformed.
                # Consider deleting to avoid loop, or moving to 'failed' dir.
                # For now, assume it's processed and remove.
                maybe_write_warm(json_file)
                maybe_write_pipeline_inbox(data, json_file, workspace_root=WORKSPACE_ROOT)
                os.remove(json_file)
                success_count += 1

        except json.JSONDecodeError:
            print(f"❌ Invalid JSON in {json_file}. Deleting.")
            os.remove(json_file)
            fail_count += 1
        except Exception as e:
            print(f"❌ Error processing {json_file}: {e}")
            fail_count += 1

    print("-" * 40)
    print(f"📊 Summary Flush Complete")
    print(f"✅ Imported: {success_count}")
    print(f"❌ Failed:   {fail_count}")
    
    # Verify vector store status
    try:
        stats = store.get_collection_stats() if hasattr(store, 'get_collection_stats') else "N/A"
        print(f"📚 Vector Store Status: {stats}")
    except Exception as e:
        print(f"⚠️ Failed to get stats: {e}")

if __name__ == "__main__":
    main()

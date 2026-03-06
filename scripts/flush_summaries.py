#!/usr/bin/env python3
"""
Deep-Sea Nexus Summary Flush Script
Batch imports structured summaries from ~/.openclaw/logs/summaries/ to the vector store.
"""

import os
import sys
import json
import glob
import subprocess
from datetime import datetime

# Setup paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
NEXUS_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, NEXUS_ROOT)
sys.path.insert(0, os.path.join(NEXUS_ROOT, 'vector_store'))

try:
    from auto_summary import HybridStorage
    from vector_store import create_vector_store
except ImportError as e:
    print(f"❌ Critical Import Error: {e}")
    sys.exit(1)

SUMMARY_LOG_DIR = os.path.expanduser("~/.openclaw/logs/summaries")


def maybe_write_warm(json_file: str) -> None:
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return
    project = data.get("project关联") or data.get("项目关联") or data.get("project") or ""
    if not project:
        return
    warm_writer = os.path.join(SCRIPT_DIR, "warm_writer.py")
    if not os.path.exists(warm_writer):
        return
    subprocess.run([sys.executable, warm_writer, "--from", json_file], check=False)

def main():
    if not os.path.exists(SUMMARY_LOG_DIR):
        print(f"ℹ️ Directory not found: {SUMMARY_LOG_DIR}")
        return

    json_files = glob.glob(os.path.join(SUMMARY_LOG_DIR, "*.json"))
    
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
                os.remove(json_file)
                success_count += 1
            else:
                print(f"⚠️ Imported but stored_count is 0. Check content.")
                # If it didn't store anything, maybe it was empty or malformed.
                # Consider deleting to avoid loop, or moving to 'failed' dir.
                # For now, assume it's processed and remove.
                maybe_write_warm(json_file)
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

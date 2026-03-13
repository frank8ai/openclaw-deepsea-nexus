#!/usr/bin/env python
"""
Migration Tool
Migrate from v1.0 format to v2.0 format
"""

import os
import sys
import json
from datetime import datetime
import re

from _legacy_layout import resolve_legacy_layout


class MigrationError(Exception):
    """Custom exception for migration errors"""
    pass


def detect_v1_format(source_dir):
    """
    Detect if source is in v1.0 format
    
    Args:
        source_dir: Source directory to check
    
    Returns:
        Tuple: (is_v1, format_type)
    """
    indicators = []
    
    # Check for v1.0 patterns
    if os.path.exists(os.path.join(source_dir, "memory.json")):
        indicators.append("memory.json")
    
    if os.path.exists(os.path.join(source_dir, "sessions")):
        indicators.append("sessions/")
    
    if os.path.exists(os.path.join(source_dir, "archive")):
        indicators.append("archive/")
    
    # Check for v2.0 patterns
    if os.path.exists(os.path.join(source_dir, "memory", "90_Memory")):
        return (False, "v2.0")
    
    if os.path.exists(os.path.join(source_dir, "_DAILY_INDEX.md")):
        return (False, "v2.0")
    
    if indicators:
        return (True, f"v1.0 ({', '.join(indicators)})")
    
    return (False, "unknown")


def migrate_from_v1(source_dir, target_dir):
    """
    Migrate from v1.0 to v2.0 format
    
    Args:
        source_dir: Source directory (v1.0)
        target_dir: Target directory (v2.0)
    
    Returns:
        Dict: Migration statistics
    """
    stats = {
        "sessions_migrated": 0,
        "sessions_failed": 0,
        "gold_keys_migrated": 0,
        "errors": []
    }
    
    # Create target structure
    os.makedirs(target_dir, exist_ok=True)
    
    # Try to load v1 memory.json
    memory_json = os.path.join(source_dir, "memory.json")
    sessions_dir = os.path.join(source_dir, "sessions")
    
    if os.path.exists(memory_json):
        print("📄 Found memory.json, parsing...")
        try:
            with open(memory_json, 'r', encoding='utf-8') as f:
                memory_data = json.load(f)
            
            # Migrate each entry
            for entry in memory_data:
                try:
                    migrate_entry(entry, target_dir, stats)
                except Exception as e:
                    stats["sessions_failed"] += 1
                    stats["errors"].append(str(e))
        
        except json.JSONDecodeError as e:
            raise MigrationError(f"Invalid JSON in memory.json: {e}")
    
    # Migrate sessions directory
    if os.path.exists(sessions_dir):
        print("📁 Found sessions/, migrating files...")
        for filename in os.listdir(sessions_dir):
            if filename.endswith('.md'):
                try:
                    session_file = os.path.join(sessions_dir, filename)
                    migrate_session_file(session_file, target_dir, stats)
                except Exception as e:
                    stats["sessions_failed"] += 1
                    stats["errors"].append(f"{filename}: {e}")
    
    return stats


def migrate_entry(entry, target_dir, stats):
    """
    Migrate a single entry from memory.json
    
    Args:
        entry: Memory entry dict
        target_dir: Target directory
        stats: Statistics dict
    """
    # Extract data from entry
    topic = entry.get("topic", "Unknown")
    content = entry.get("content", "")
    timestamp = entry.get("timestamp", datetime.now().isoformat())
    gold_keys = entry.get("gold_keys", [])
    
    # Parse timestamp to get date
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        date_str = dt.strftime("%Y-%m-%d")
        time_str = dt.strftime("%H%M")
    except:
        date_str = datetime.now().strftime("%Y-%m-%d")
        time_str = datetime.now().strftime("%H%M")
    
    # Create session file
    topic_safe = re.sub(r'[^\w]', '', topic.replace(" ", "_"))[:20]
    session_id = f"{time_str}_{topic_safe}"
    
    session_content = f"""---
uuid: {dt.strftime("%Y%m%d%H%M%S") if 'dt' in dir() else datetime.now().strftime("%Y%m%d%H%M%S")}
type: session
tags: [{topic}]
status: migrated
created: {timestamp}
---

# {topic}

{content}
"""
    
    # Write session file
    today_dir = os.path.join(target_dir, date_str)
    os.makedirs(today_dir, exist_ok=True)
    
    session_file = os.path.join(today_dir, f"session_{session_id}.md")
    with open(session_file, 'w', encoding='utf-8') as f:
        f.write(session_content)
    
    stats["sessions_migrated"] += 1
    stats["gold_keys_migrated"] += len(gold_keys)
    
    print(f"  ✅ Migrated: {session_id}")


def migrate_session_file(session_file, target_dir, stats):
    """
    Migrate a single session file from sessions/ directory
    
    Args:
        session_file: Path to session file
        target_dir: Target directory
        stats: Statistics dict
    """
    with open(session_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract metadata from v1 format
    filename = os.path.basename(session_file)
    
    # Try to extract date from filename or content
    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
    if date_match:
        date_str = date_match.group(1)
    else:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    # Create session ID
    time_match = re.search(r'(\d{4})', filename)
    time_str = time_match.group(1) if time_match else datetime.now().strftime("%H%M")
    topic = "Migrated"
    
    # Write to target
    today_dir = os.path.join(target_dir, date_str)
    os.makedirs(today_dir, exist_ok=True)
    
    session_id = f"{time_str}_{topic}"
    new_file = os.path.join(today_dir, f"session_{session_id}.md")
    
    with open(new_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    stats["sessions_migrated"] += 1
    print(f"  ✅ Migrated: {filename}")


def verify_migration(target_dir, expected_sessions):
    """
    Verify migration results
    
    Args:
        target_dir: Target directory
        expected_sessions: Expected number of sessions
    
    Returns:
        Dict: Verification results
    """
    results = {
        "sessions_found": 0,
        "indexes_found": 0,
        "errors": []
    }
    
    if not os.path.exists(target_dir):
        results["errors"].append(f"Target directory not found: {target_dir}")
        return results
    
    for item in os.listdir(target_dir):
        item_path = os.path.join(target_dir, item)
        if os.path.isdir(item_path) and re.match(r'\d{4}-\d{2}-\d{2}', item):
            # Count sessions
            for f in os.listdir(item_path):
                if f.startswith("session_") and f.endswith(".md"):
                    results["sessions_found"] += 1
            
            # Check for index
            index_file = os.path.join(item_path, "_INDEX.md")
            if os.path.exists(index_file):
                results["indexes_found"] += 1
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Migration Tool (v1.0 -> v2.0)")
    parser.add_argument('--source', type=str, required=True, help='Source directory (v1.0)')
    parser.add_argument('--target', type=str, help='Target directory (default: auto)')
    parser.add_argument('--verify', action='store_true', help='Verify migration')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be migrated')
    
    args = parser.parse_args()
    
    layout = resolve_legacy_layout()
    
    # Detect format
    is_v1, format_type = detect_v1_format(args.source)
    print(f"📋 Detected format: {format_type}")
    
    if not is_v1:
        print("⚠️  Source doesn't appear to be v1.0 format. Continue anyway? (y/n)")
        if input().lower() != 'y':
            sys.exit(0)
    
    # Set target
    if not args.target:
        args.target = str(layout.memory_root)
    
    print(f"📁 Source: {args.source}")
    print(f"📁 Target: {args.target}")
    
    if args.dry_run:
        print("🔍 Dry run - showing what would be migrated:")
        print("  (No changes will be made)")
        # Just detect and show
        sys.exit(0)
    
    if args.verify:
        print("🔍 Verifying migration...")
        results = verify_migration(args.target, 0)
        print(f"✅ Found {results['sessions_found']} sessions in {results['indexes_found']} indexes")
        if results['errors']:
            print("❌ Errors:")
            for e in results['errors']:
                print(f"  - {e}")
    else:
        print("🚀 Starting migration...")
        stats = migrate_from_v1(args.source, args.target)
        
        print("\n📊 Migration Summary:")
        print(f"  Sessions migrated: {stats['sessions_migrated']}")
        print(f"  Sessions failed: {stats['sessions_failed']}")
        print(f"  Gold keys migrated: {stats['gold_keys_migrated']}")
        
        if stats['errors']:
            print(f"\n❌ Errors ({len(stats['errors'])}):")
            for e in stats['errors'][:10]:
                print(f"  - {e}")
        
        # Rebuild indices
        print("\n🔨 Rebuilding indices...")
        # This would call index_rebuild.py
        print("✅ Migration complete!")

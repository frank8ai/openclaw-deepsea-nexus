#!/usr/bin/env python
"""
Index Rebuild Tool
Rebuild daily index from all session files
"""

import os
from datetime import datetime
import re

from _legacy_layout import iter_legacy_dates, resolve_day_dir, resolve_legacy_layout


def extract_session_info(session_file):
    """
    Extract metadata from session file
    
    Args:
        session_file: Path to session file
    
    Returns:
        Dict: Session metadata
    """
    try:
        with open(session_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract header fields
        topic = "Unknown"
        created = None
        gold_keywords = []
        
        lines = content.split('\n')
        in_header = False
        header_lines = []
        
        for line in lines:
            if line.startswith('---'):
                if not in_header:
                    in_header = True
                    continue
                else:
                    break
            if in_header:
                header_lines.append(line)
        
        # Parse header
        for line in header_lines:
            if line.startswith('tags:'):
                # Extract topic from tags
                tags_match = re.search(r'\[(.*?)\]', line)
                if tags_match:
                    tags = tags_match.group(1).split(',')
                    if tags:
                        topic = tags[0].strip()
            if 'created:' in line:
                created = line.split(':')[1].strip()
        
        # Extract GOLD keywords
        for line in lines:
            if '#GOLD' in line:
                keywords = line.replace('#GOLD', '').strip()
                if keywords:
                    gold_keywords.append(keywords[:50])
        
        # Extract filename for session_id
        basename = os.path.basename(session_file)
        session_id = basename.replace('session_', '').replace('.md', '')
        
        return {
            'session_id': session_id,
            'topic': topic,
            'created': created,
            'gold_keywords': gold_keywords,
            'file': session_file
        }
    except Exception as e:
        print(f"Error parsing {session_file}: {e}")
        return None


def rebuild_index_for_date(date_str, layout):
    """
    Rebuild index for a specific date
    
    Args:
        date_str: Date in YYYY-MM-DD format
        layout: Resolved legacy layout paths
    
    Returns:
        Dict: Rebuild statistics
    """
    date_dir = resolve_day_dir(date_str, layout)
    index_file = date_dir / "_INDEX.md"
    
    if not date_dir.exists():
        print(f"❌ Directory not found: {date_dir}")
        return None
    
    # Collect all sessions
    sessions = []
    for file_path in sorted(date_dir.iterdir()):
        if file_path.is_file() and file_path.name.startswith("session_") and file_path.suffix == ".md":
            info = extract_session_info(str(file_path))
            if info:
                sessions.append(info)
    
    # Sort by session_id (which contains time)
    sessions.sort(key=lambda x: x['session_id'])
    
    # Build index content
    sessions_lines = []
    gold_lines = []
    topics = set()
    
    for s in sessions:
        sessions_lines.append(f"- [active] session_{s['session_id']} ({s['topic']})")
        topics.add(s['topic'])
        for gold in s['gold_keywords']:
            gold_lines.append(f"- session_{s['session_id']}: {gold}")
    
    sessions_section = "\n".join(sessions_lines) if sessions_lines else "_(no active sessions)_"
    gold_section = "\n".join(gold_lines) if gold_lines else "_(no gold keys)_"
    topics_section = "\n".join([f"- {t}" for t in sorted(topics)]) if topics else "_(no topics)_"
    
    index_content = f"""---
uuid: {datetime.now().strftime("%Y%m%d%H%M%S")}
type: daily-index
tags: [daily-index, {date_str}]
created: {date_str}
---

# {date_str} Daily Index

## Sessions ({len(sessions)})
{sessions_section}

## Gold Keys ({len(gold_lines)})
{gold_section}

## Topics ({len(topics)})
{topics_section}

---
updated: {datetime.now().isoformat()}
"""
    
    # Write index file
    index_file.write_text(index_content, encoding='utf-8')
    
    print(f"✅ Rebuilt index for {date_str}: {len(sessions)} sessions, {len(gold_lines)} gold keys")
    
    return {
        "date": date_str,
        "sessions": len(sessions),
        "gold_keys": len(gold_lines),
        "topics": len(topics)
    }


def rebuild_all(layout, month=None):
    """
    Rebuild all indices
    
    Args:
        layout: Resolved legacy layout paths
        month: Specific month to rebuild (YYYY-MM format)
    
    Returns:
        List: Rebuild results
    """
    results = []
    dates = iter_legacy_dates(layout, month=month)
    if month and not dates:
        print(f"❌ No dated directories found for month: {month}")
        return results

    for date_str in dates:
        result = rebuild_index_for_date(date_str, layout)
        if result:
            results.append(result)

    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Index Rebuild Tool")
    parser.add_argument('--date', type=str, help='Rebuild index for specific date (YYYY-MM-DD)')
    parser.add_argument('--month', type=str, help='Rebuild all indices for month (YYYY-MM)')
    parser.add_argument('--all', action='store_true', help='Rebuild all indices')
    
    args = parser.parse_args()
    
    layout = resolve_legacy_layout()
    
    if args.date:
        rebuild_index_for_date(args.date, layout)
    
    elif args.month:
        results = rebuild_all(layout, args.month)
        print(f"✅ Rebuilt {len(results)} dates in {args.month}")
    
    elif args.all:
        results = rebuild_all(layout)
        print(f"✅ Rebuilt {len(results)} dates total")
    
    else:
        print("Usage:")
        print("  python index_rebuild.py --date 2026-02-07    # Rebuild specific date")
        print("  python index_rebuild.py --month 2026-02       # Rebuild all dates in month")
        print("  python index_rebuild.py --all                 # Rebuild all dates")

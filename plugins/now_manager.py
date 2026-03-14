#!/usr/bin/env python3
"""
NOW.md - 压缩前抢救机制

功能：
- 压缩前自动保存当前目标
- 保存当前状态、约束、阻塞、证据与 replay
- 压缩后自动恢复
"""

import os
from datetime import datetime
from typing import Dict, List, Optional

try:
    from ..runtime_paths import resolve_openclaw_workspace
except ImportError:
    from runtime_paths import resolve_openclaw_workspace


def _load_rescue_module():
    try:
        from . import smart_context_rescue as module
    except ImportError:
        import smart_context_rescue as module
    return module


class NOWManager:
    """
    NOW.md 抢救管理器
    """

    def __init__(self, path: str = None):
        self.path = path or os.path.join(resolve_openclaw_workspace(), "NOW.md")
        self.state = self._load()
        self.decisions_max = 10
        self.constraints_max = 10
        self.blockers_max = 10
        self.next_actions_max = 10
        self.open_questions_max = 10
        self.evidence_max = 10
        self.replay_max = 4

    def _empty_state(self) -> Dict:
        return {
            "updated": None,
            "current_goal": "",
            "current_status": "",
            "active_threads": [],
            "constraints": [],
            "blockers": [],
            "next_actions": [],
            "open_questions": [],
            "decisions": [],
            "evidence_pointers": [],
            "replay_commands": [],
            "context_notes": "",
        }

    def _parse_pipe_list(self, value: str) -> List[str]:
        return [item.strip() for item in (value or "").split("|") if item.strip()]

    def _load(self) -> Dict:
        """加载状态"""
        if not os.path.exists(self.path):
            return self._empty_state()

        try:
            with open(self.path, "r", encoding="utf-8") as f:
                content = f.read()

            state = self._empty_state()
            for raw_line in content.splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                if ":" not in line:
                    continue
                key, value = line.split(":", 1)
                key = key.strip().lower().replace(" ", "_")
                value = value.strip()

                if key == "updated":
                    state["updated"] = value
                elif key == "current_goal":
                    state["current_goal"] = value
                elif key in {"current_status", "status"}:
                    state["current_status"] = value
                elif key == "active_threads":
                    state["active_threads"] = self._parse_pipe_list(value)
                elif key == "constraints":
                    state["constraints"] = self._parse_pipe_list(value)
                elif key == "blockers":
                    state["blockers"] = self._parse_pipe_list(value)
                elif key == "next_actions":
                    state["next_actions"] = self._parse_pipe_list(value)
                elif key == "open_questions":
                    state["open_questions"] = self._parse_pipe_list(value)
                elif key == "decisions":
                    state["decisions"] = self._parse_pipe_list(value)
                elif key == "evidence_pointers":
                    state["evidence_pointers"] = self._parse_pipe_list(value)
                elif key == "replay_commands":
                    state["replay_commands"] = self._parse_pipe_list(value)
                elif key == "replay_command" and value:
                    state["replay_commands"] = [value]

            if "---" in content:
                state["context_notes"] = content.split("---")[-1].strip()

            return state
        except Exception as e:
            print(f"加载 NOW.md 失败: {e}")
            return self._empty_state()

    def save(
        self,
        current_goal: Optional[str] = None,
        current_status: Optional[str] = None,
        active_threads: Optional[List[str]] = None,
        constraints: Optional[List[str]] = None,
        blockers: Optional[List[str]] = None,
        next_actions: Optional[List[str]] = None,
        open_questions: Optional[List[str]] = None,
        decisions: Optional[List[str]] = None,
        evidence_pointers: Optional[List[str]] = None,
        replay_commands: Optional[List[str]] = None,
        context_notes: Optional[str] = None,
    ):
        """
        保存当前状态
        """
        previous = self.state if isinstance(self.state, dict) else self._empty_state()
        self.state = {
            "updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "current_goal": previous.get("current_goal", "") if current_goal is None else current_goal,
            "current_status": previous.get("current_status", "") if current_status is None else current_status,
            "active_threads": previous.get("active_threads", []) if active_threads is None else self._trim_list(active_threads, 10),
            "constraints": previous.get("constraints", []) if constraints is None else self._trim_list(constraints, self.constraints_max),
            "blockers": previous.get("blockers", []) if blockers is None else self._trim_list(blockers, self.blockers_max),
            "next_actions": previous.get("next_actions", []) if next_actions is None else self._trim_list(next_actions, self.next_actions_max),
            "open_questions": previous.get("open_questions", []) if open_questions is None else self._trim_list(open_questions, self.open_questions_max),
            "decisions": previous.get("decisions", []) if decisions is None else self._trim_list(decisions, self.decisions_max),
            "evidence_pointers": previous.get("evidence_pointers", []) if evidence_pointers is None else self._trim_list(evidence_pointers, self.evidence_max),
            "replay_commands": previous.get("replay_commands", []) if replay_commands is None else self._trim_list(replay_commands, self.replay_max),
            "context_notes": previous.get("context_notes", "") if context_notes is None else context_notes,
        }

        parent = os.path.dirname(self.path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            f.write("# NOW.md - rescue state\n")
            f.write("---\n")
            f.write(f"updated: {self.state['updated']}\n")
            f.write("---\n\n")

            f.write("## Runtime State\n")
            f.write(f"current_status: {self.state['current_status']}\n")
            f.write(f"current_goal: {self.state['current_goal']}\n")
            f.write(f"active_threads: {' | '.join(self.state['active_threads'])}\n\n")

            f.write("## Guardrails\n")
            f.write(f"constraints: {' | '.join(self.state['constraints'])}\n")
            f.write(f"blockers: {' | '.join(self.state['blockers'])}\n\n")

            f.write("## Decisions And Next\n")
            f.write(f"decisions: {' | '.join(self.state['decisions'])}\n")
            f.write(f"next_actions: {' | '.join(self.state['next_actions'])}\n")
            f.write(f"open_questions: {' | '.join(self.state['open_questions'])}\n\n")

            f.write("## Evidence\n")
            f.write(f"evidence_pointers: {' | '.join(self.state['evidence_pointers'])}\n")
            f.write(f"replay_commands: {' | '.join(self.state['replay_commands'])}\n\n")

            if self.state["context_notes"]:
                f.write("---\n")
                f.write(self.state["context_notes"])

        print("✅ 已保存 NOW.md")

    def load(self) -> Dict:
        """加载状态"""
        return self.state

    def clear(self):
        """清空状态"""
        self.state = self._empty_state()
        if os.path.exists(self.path):
            os.remove(self.path)
        print("🗑️ 已清空 NOW.md")

    def format_context(self) -> str:
        """格式化为可注入上下文"""
        state = self.state or {}
        if not any(
            [
                state.get("current_goal"),
                state.get("current_status"),
                state.get("constraints"),
                state.get("blockers"),
                state.get("next_actions"),
                state.get("open_questions"),
                state.get("decisions"),
                state.get("evidence_pointers"),
                state.get("replay_commands"),
            ]
        ):
            return ""

        lines = ["## NOW Rescue Context"]
        if state.get("current_status"):
            lines.append(f"State: {state['current_status']}")
        if state.get("current_goal"):
            lines.append(f"Goal: {state['current_goal']}")
        if state.get("constraints"):
            lines.append(f"Constraints: {'; '.join(state['constraints'])}")
        if state.get("blockers"):
            lines.append(f"Blockers: {'; '.join(state['blockers'])}")
        if state.get("decisions"):
            lines.append(f"Decisions: {'; '.join(state['decisions'])}")
        if state.get("next_actions"):
            lines.append(f"Next: {'; '.join(state['next_actions'])}")
        if state.get("open_questions"):
            lines.append(f"Questions: {'; '.join(state['open_questions'])}")
        if state.get("evidence_pointers"):
            lines.append(f"Evidence: {'; '.join(state['evidence_pointers'])}")
        if state.get("replay_commands"):
            lines.append(f"Replay: {state['replay_commands'][0]}")
        if state.get("context_notes"):
            lines.append(f"Notes: {state['context_notes']}")
        return "\n".join(lines)

    def extract_from_conversation(self, conversation: str) -> Dict:
        """
        从对话中提取抢救信息
        """
        rescue = _load_rescue_module()
        updates = rescue.collect_rescue_updates(
            conversation,
            rescue_gold=True,
            rescue_decisions=True,
            rescue_next_actions=True,
            rescue_goal=True,
            rescue_status=True,
            rescue_constraints=True,
            rescue_blockers=True,
            rescue_evidence=True,
            rescue_replay=True,
        )
        return {
            "current_goal": updates.get("current_goal", ""),
            "current_status": updates.get("current_status", ""),
            "decisions": updates.get("decisions", []),
            "constraints": updates.get("constraints", []),
            "blockers": updates.get("blockers", []),
            "goals": updates.get("next_actions", []),
            "questions": updates.get("open_questions", []),
            "evidence_pointers": updates.get("evidence_pointers", []),
            "replay_commands": updates.get("replay_commands", []),
        }

    def rescue_before_compress(self, conversation: str) -> Dict:
        """
        压缩前抢救
        """
        rescue = _load_rescue_module()
        updates = rescue.collect_rescue_updates(
            conversation,
            rescue_gold=True,
            rescue_decisions=True,
            rescue_next_actions=True,
            rescue_goal=True,
            rescue_status=True,
            rescue_constraints=True,
            rescue_blockers=True,
            rescue_evidence=True,
            rescue_replay=True,
        )
        result = rescue.apply_rescue_updates(self.state, updates)
        total = sum(
            int(result.get(key, 0))
            for key in (
                "decisions_rescued",
                "goal_rescued",
                "status_rescued",
                "constraints_rescued",
                "blockers_rescued",
                "next_actions_rescued",
                "open_questions_rescued",
                "evidence_rescued",
                "replay_rescued",
            )
        )
        result["saved"] = total > 0
        if result["saved"]:
            self.save()
        return result

    def _trim_list(self, items: List[str], max_items: int) -> List[str]:
        if not items:
            return []
        deduped: List[str] = []
        for item in items:
            if item not in deduped:
                deduped.append(item)
        if max_items <= 0:
            return deduped
        return deduped[-max_items:]

    def report(self) -> str:
        """生成报告"""
        state = self.state or {}
        lines = [
            "=" * 50,
            "NOW.md Rescue State",
            "=" * 50,
            f"更新时间: {state.get('updated', '未更新')}",
            "",
        ]
        if state.get("current_status"):
            lines.append(f"State: {state['current_status']}")
        if state.get("current_goal"):
            lines.append(f"Goal: {state['current_goal']}")
        if state.get("blockers"):
            lines.append(f"Blockers: {' | '.join(state['blockers'])}")
        if state.get("next_actions"):
            lines.append(f"Next: {' | '.join(state['next_actions'])}")
        if state.get("replay_commands"):
            lines.append(f"Replay: {state['replay_commands'][0]}")
        lines.append("=" * 50)
        return "\n".join(lines)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="NOW.md 抢救机制")
    parser.add_argument("--load", action="store_true", help="加载状态")
    parser.add_argument("--save", action="store_true", help="保存状态")
    parser.add_argument("--clear", action="store_true", help="清空状态")
    parser.add_argument("--context", action="store_true", help="格式化为上下文")
    parser.add_argument("--rescue", type=str, help="从对话抢救")
    parser.add_argument("--goal", "-g", help="当前目标")
    parser.add_argument("--threads", "-t", help="活跃线程 (用|分隔)")
    parser.add_argument("--actions", "-a", help="下一步行动 (用|分隔)")
    parser.add_argument("--questions", "-q", help="待解决问题 (用|分隔)")
    parser.add_argument("--decisions", "-d", help="已做决定 (用|分隔)")
    args = parser.parse_args()

    now = NOWManager()

    if args.load:
        print(now.report())
    elif args.clear:
        now.clear()
    elif args.context:
        print(now.format_context())
    elif args.rescue:
        result = now.rescue_before_compress(args.rescue)
        print(f"抢救结果: {result}")
    elif args.save:
        threads = args.threads.split("|") if args.threads else []
        actions = args.actions.split("|") if args.actions else []
        questions = args.questions.split("|") if args.questions else []
        decisions = args.decisions.split("|") if args.decisions else []
        now.save(
            current_goal=args.goal,
            active_threads=threads,
            next_actions=actions,
            open_questions=questions,
            decisions=decisions,
        )
    else:
        print(now.report())


if __name__ == "__main__":
    main()

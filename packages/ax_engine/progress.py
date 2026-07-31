"""Stream progress tracking and chunk processing (ported from cli/main.py)."""

from __future__ import annotations

import ast
from collections.abc import Callable
from typing import Any

from ax_engine.models import ANALYST_ORDER

ANALYST_AGENT_NAMES = {
    "market": "Market Analyst",
    "social": "Sentiment Analyst",
    "news": "News Analyst",
    "fundamentals": "Fundamentals Analyst",
}
ANALYST_REPORT_MAP = {
    "market": "market_report",
    "social": "sentiment_report",
    "news": "news_report",
    "fundamentals": "fundamentals_report",
}

DEFAULT_AGENT_STATUSES = {
    "Market Analyst": "pending",
    "Sentiment Analyst": "pending",
    "News Analyst": "pending",
    "Fundamentals Analyst": "pending",
    "Bull Researcher": "pending",
    "Bear Researcher": "pending",
    "Research Manager": "pending",
    "Trader": "pending",
    "Aggressive Analyst": "pending",
    "Conservative Analyst": "pending",
    "Neutral Analyst": "pending",
    "Portfolio Manager": "pending",
}

DEBATE_SIDE_BY_AGENT = {
    "Bull Researcher": "bull",
    "Bear Researcher": "bear",
    "Aggressive Analyst": "aggressive",
    "Conservative Analyst": "conservative",
    "Neutral Analyst": "neutral",
}

ACT_BY_AGENT = {
    "Market Analyst": "analysts",
    "Sentiment Analyst": "analysts",
    "News Analyst": "analysts",
    "Fundamentals Analyst": "analysts",
    "Bull Researcher": "research",
    "Bear Researcher": "research",
    "Research Manager": "research",
    "Trader": "trading",
    "Aggressive Analyst": "risk",
    "Conservative Analyst": "risk",
    "Neutral Analyst": "risk",
    "Portfolio Manager": "decision",
}


class RunProgress:
    """Tracks agent statuses and report sections during graph.stream()."""

    def __init__(self, selected_analyst_keys: list[str]) -> None:
        self.selected_analysts = selected_analyst_keys
        self.agent_status = DEFAULT_AGENT_STATUSES.copy()
        self.report_sections: dict[str, str | None] = {}
        self.debate_timeline: list[dict[str, Any]] = []
        self._processed_message_ids: set[str] = set()
        self.messages: list[tuple[str, str]] = []
        self.tool_calls: list[tuple[str, dict[str, Any]]] = []

    def update_agent_status(self, agent: str, status: str) -> None:
        self.agent_status[agent] = status

    def update_report_section(self, section_name: str, content: str) -> None:
        existing = self.report_sections.get(section_name)
        if existing:
            self.report_sections[section_name] = f"{existing}\n\n{content}"
        else:
            self.report_sections[section_name] = content

    def add_message(self, role: str, content: str) -> None:
        self.messages.append((role, content))

    def add_tool_call(self, name: str, args: dict[str, Any]) -> None:
        self.tool_calls.append((name, args))

    def snapshot(self) -> dict[str, Any]:
        return {
            "agent_status": dict(self.agent_status),
            "report_sections": dict(self.report_sections),
            "debate_timeline": list(self.debate_timeline),
        }


def _upsert_timeline_entry(
    timeline: list[dict[str, Any]],
    entry_id: str,
    *,
    act: str,
    agent: str,
    content: str,
    kind: str = "debate",
    side: str | None = None,
    round_no: int | None = None,
) -> None:
    payload: dict[str, Any] = {
        "id": entry_id,
        "act": act,
        "agent": agent,
        "content": content,
        "kind": kind,
    }
    if side:
        payload["side"] = side
    if round_no is not None:
        payload["round"] = round_no
    for index, entry in enumerate(timeline):
        if entry.get("id") == entry_id:
            timeline[index] = payload
            return
    timeline.append(payload)


def sync_debate_timeline(progress: RunProgress, chunk: dict[str, Any]) -> None:
    """Build structured debate/report timeline for the analysis room UI."""
    timeline = progress.debate_timeline

    for analyst_key in ANALYST_ORDER:
        if analyst_key not in progress.selected_analysts:
            continue
        report_key = ANALYST_REPORT_MAP[analyst_key]
        content = (progress.report_sections.get(report_key) or "").strip()
        if not content:
            continue
        agent = ANALYST_AGENT_NAMES[analyst_key]
        _upsert_timeline_entry(
            timeline,
            report_key,
            act="analysts",
            agent=agent,
            content=content,
            kind="report",
        )

    debate = chunk.get("investment_debate_state") or {}
    bull = debate.get("bull_history", "").strip()
    bear = debate.get("bear_history", "").strip()
    research_judge = debate.get("judge_decision", "").strip()
    debate_round = int(debate.get("count") or 0)

    if bull:
        _upsert_timeline_entry(
            timeline,
            "research-bull",
            act="research",
            agent="Bull Researcher",
            content=bull,
            side="bull",
            round_no=max(1, debate_round // 2 or 1),
        )
    if bear:
        _upsert_timeline_entry(
            timeline,
            "research-bear",
            act="research",
            agent="Bear Researcher",
            content=bear,
            side="bear",
            round_no=max(1, debate_round // 2 or 1),
        )
    if research_judge:
        _upsert_timeline_entry(
            timeline,
            "research-manager",
            act="research",
            agent="Research Manager",
            content=research_judge,
            kind="decision",
        )

    trader_plan = (chunk.get("trader_investment_plan") or progress.report_sections.get("trader_investment_plan") or "").strip()
    if trader_plan:
        _upsert_timeline_entry(
            timeline,
            "trader-plan",
            act="trading",
            agent="Trader",
            content=trader_plan,
            kind="report",
        )

    risk = chunk.get("risk_debate_state") or {}
    agg = risk.get("aggressive_history", "").strip()
    con = risk.get("conservative_history", "").strip()
    neu = risk.get("neutral_history", "").strip()
    risk_judge = risk.get("judge_decision", "").strip()
    risk_round = int(risk.get("count") or 0)

    if agg:
        _upsert_timeline_entry(
            timeline,
            "risk-aggressive",
            act="risk",
            agent="Aggressive Analyst",
            content=agg,
            side="aggressive",
            round_no=max(1, risk_round // 3 or 1),
        )
    if con:
        _upsert_timeline_entry(
            timeline,
            "risk-conservative",
            act="risk",
            agent="Conservative Analyst",
            content=con,
            side="conservative",
            round_no=max(1, risk_round // 3 or 1),
        )
    if neu:
        _upsert_timeline_entry(
            timeline,
            "risk-neutral",
            act="risk",
            agent="Neutral Analyst",
            content=neu,
            side="neutral",
            round_no=max(1, risk_round // 3 or 1),
        )
    if risk_judge:
        _upsert_timeline_entry(
            timeline,
            "portfolio-decision",
            act="decision",
            agent="Portfolio Manager",
            content=risk_judge,
            kind="decision",
        )

    final_decision = (chunk.get("final_trade_decision") or progress.report_sections.get("final_trade_decision") or "").strip()
    if final_decision and not risk_judge:
        _upsert_timeline_entry(
            timeline,
            "portfolio-decision",
            act="decision",
            agent="Portfolio Manager",
            content=final_decision,
            kind="decision",
        )


def update_research_team_status(progress: RunProgress, status: str) -> None:
    for agent in ("Bull Researcher", "Bear Researcher", "Research Manager"):
        progress.update_agent_status(agent, status)


def update_analyst_statuses(progress: RunProgress, chunk: dict[str, Any]) -> None:
    selected = progress.selected_analysts
    found_active = False

    for analyst_key in ANALYST_ORDER:
        if analyst_key not in selected:
            continue

        agent_name = ANALYST_AGENT_NAMES[analyst_key]
        report_key = ANALYST_REPORT_MAP[analyst_key]

        if chunk.get(report_key):
            progress.update_report_section(report_key, chunk[report_key])

        has_report = bool(progress.report_sections.get(report_key))

        if has_report:
            progress.update_agent_status(agent_name, "completed")
        elif not found_active:
            progress.update_agent_status(agent_name, "in_progress")
            found_active = True
        else:
            progress.update_agent_status(agent_name, "pending")

    if (
        not found_active
        and selected
        and progress.agent_status.get("Bull Researcher") == "pending"
    ):
        progress.update_agent_status("Bull Researcher", "in_progress")


def extract_content_string(content: Any) -> str | None:
    def is_empty(val: Any) -> bool:
        if val is None or val == "":
            return True
        if isinstance(val, str):
            s = val.strip()
            if not s:
                return True
            try:
                return not bool(ast.literal_eval(s))
            except (ValueError, SyntaxError):
                return False
        return not bool(val)

    if is_empty(content):
        return None

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, dict):
        text = content.get("text", "")
        return text.strip() if not is_empty(text) else None

    if isinstance(content, list):
        text_parts = [
            item.get("text", "").strip()
            if isinstance(item, dict) and item.get("type") == "text"
            else (item.strip() if isinstance(item, str) else "")
            for item in content
        ]
        result = " ".join(t for t in text_parts if t and not is_empty(t))
        return result if result else None

    return str(content).strip() if not is_empty(content) else None


def classify_message_type(message: Any) -> tuple[str, str | None]:
    from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

    content = extract_content_string(getattr(message, "content", None))

    if isinstance(message, HumanMessage):
        if content and content.strip() == "Continue":
            return ("Control", content)
        return ("User", content)

    if isinstance(message, ToolMessage):
        return ("Data", content)

    if isinstance(message, AIMessage):
        return ("Agent", content)

    return ("System", content)


def process_stream_chunk(
    progress: RunProgress,
    chunk: dict[str, Any],
    *,
    on_event: Callable[[dict[str, Any]], None] | None = None,
) -> None:
    """Apply CLI stream-side effects for one graph chunk."""
    for message in chunk.get("messages", []):
        msg_id = getattr(message, "id", None)
        if msg_id is not None:
            if msg_id in progress._processed_message_ids:
                continue
            progress._processed_message_ids.add(msg_id)

        msg_type, content = classify_message_type(message)
        if content and content.strip():
            progress.add_message(msg_type, content)
            if on_event:
                on_event({"type": "message", "role": msg_type, "content": content})

        if hasattr(message, "tool_calls") and message.tool_calls:
            for tool_call in message.tool_calls:
                if isinstance(tool_call, dict):
                    name, args = tool_call["name"], tool_call["args"]
                else:
                    name, args = tool_call.name, tool_call.args
                progress.add_tool_call(name, args)
                if on_event:
                    on_event({"type": "tool_call", "name": name, "args": args})
                    _upsert_timeline_entry(
                        progress.debate_timeline,
                        f"tool-{len(progress.tool_calls)}-{name}",
                        act=ACT_BY_AGENT.get(_agent_from_status(progress), "analysts"),
                        agent=_agent_from_status(progress) or "Agent",
                        content=f"调用工具 `{name}`",
                        kind="tool",
                    )

    update_analyst_statuses(progress, chunk)

    if chunk.get("investment_debate_state"):
        debate_state = chunk["investment_debate_state"]
        bull_hist = debate_state.get("bull_history", "").strip()
        bear_hist = debate_state.get("bear_history", "").strip()
        judge = debate_state.get("judge_decision", "").strip()

        if bull_hist or bear_hist:
            update_research_team_status(progress, "in_progress")
        if bull_hist:
            progress.update_report_section(
                "investment_plan",
                f"### 多头研究员 (Bull Researcher)\n{bull_hist}",
            )
        if bear_hist:
            progress.update_report_section(
                "investment_plan",
                f"### 空头研究员 (Bear Researcher)\n{bear_hist}",
            )
        if judge:
            progress.update_report_section(
                "investment_plan",
                f"### 研究经理 (Research Manager)\n{judge}",
            )
            update_research_team_status(progress, "completed")
            progress.update_agent_status("Trader", "in_progress")

    if chunk.get("trader_investment_plan"):
        progress.update_report_section(
            "trader_investment_plan", chunk["trader_investment_plan"]
        )
        if progress.agent_status.get("Trader") != "completed":
            progress.update_agent_status("Trader", "completed")
            progress.update_agent_status("Aggressive Analyst", "in_progress")

    if chunk.get("risk_debate_state"):
        risk_state = chunk["risk_debate_state"]
        agg_hist = risk_state.get("aggressive_history", "").strip()
        con_hist = risk_state.get("conservative_history", "").strip()
        neu_hist = risk_state.get("neutral_history", "").strip()
        judge = risk_state.get("judge_decision", "").strip()

        if agg_hist:
            if progress.agent_status.get("Aggressive Analyst") != "completed":
                progress.update_agent_status("Aggressive Analyst", "in_progress")
            progress.update_report_section(
                "final_trade_decision",
                f"### 激进分析师 (Aggressive Analyst)\n{agg_hist}",
            )
        if con_hist:
            if progress.agent_status.get("Conservative Analyst") != "completed":
                progress.update_agent_status("Conservative Analyst", "in_progress")
            progress.update_report_section(
                "final_trade_decision",
                f"### 保守分析师 (Conservative Analyst)\n{con_hist}",
            )
        if neu_hist:
            if progress.agent_status.get("Neutral Analyst") != "completed":
                progress.update_agent_status("Neutral Analyst", "in_progress")
            progress.update_report_section(
                "final_trade_decision",
                f"### 中性分析师 (Neutral Analyst)\n{neu_hist}",
            )
        if judge and progress.agent_status.get("Portfolio Manager") != "completed":
            progress.update_agent_status("Portfolio Manager", "in_progress")
            progress.update_report_section(
                "final_trade_decision",
                f"### 组合经理 (Portfolio Manager)\n{judge}",
            )
            progress.update_agent_status("Aggressive Analyst", "completed")
            progress.update_agent_status("Conservative Analyst", "completed")
            progress.update_agent_status("Neutral Analyst", "completed")
            progress.update_agent_status("Portfolio Manager", "completed")

    sync_debate_timeline(progress, chunk)

    if on_event:
        on_event({"type": "progress", **progress.snapshot()})


def _agent_from_status(progress: RunProgress) -> str | None:
    for agent, status in progress.agent_status.items():
        if status == "in_progress":
            return agent
    return None

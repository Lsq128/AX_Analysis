"""Reusable report-tree writer shared by the CLI and the programmatic API.

Writes a run's per-section markdown (analysts, research, trading, risk,
portfolio) plus a consolidated ``complete_report.md`` under ``save_path``. The
CLI and ``TradingAgentsGraph.save_reports`` both call this, so a headless / API
run produces the same on-disk report tree a CLI run does.

Section headings are Chinese-primary with English glosses for professional
bilingual presentation (v1 audience: domestic individual investors).
"""

from datetime import datetime
from pathlib import Path

# Role headings: Chinese (English)
ROLE_MARKET = "技术面分析师 (Market Analyst)"
ROLE_SENTIMENT = "舆情分析师 (Sentiment Analyst)"
ROLE_NEWS = "资讯分析师 (News Analyst)"
ROLE_FUNDAMENTALS = "基本面分析师 (Fundamentals Analyst)"
ROLE_BULL = "多头研究员 (Bull Researcher)"
ROLE_BEAR = "空头研究员 (Bear Researcher)"
ROLE_RESEARCH_MGR = "研究经理 (Research Manager)"
ROLE_TRADER = "交易员 (Trader)"
ROLE_AGGRESSIVE = "激进分析师 (Aggressive Analyst)"
ROLE_CONSERVATIVE = "保守分析师 (Conservative Analyst)"
ROLE_NEUTRAL = "中性分析师 (Neutral Analyst)"
ROLE_PORTFOLIO = "组合经理 (Portfolio Manager)"


def write_report_tree(final_state: dict, ticker: str, save_path) -> Path:
    """Save a completed run's reports to ``save_path``; return the complete-report path."""
    save_path = Path(save_path)
    save_path.mkdir(parents=True, exist_ok=True)
    sections = []

    # 1. Analysts
    analysts_dir = save_path / "1_analysts"
    analyst_parts = []
    if final_state.get("market_report"):
        analysts_dir.mkdir(exist_ok=True)
        (analysts_dir / "market.md").write_text(final_state["market_report"], encoding="utf-8")
        analyst_parts.append((ROLE_MARKET, final_state["market_report"]))
    if final_state.get("sentiment_report"):
        analysts_dir.mkdir(exist_ok=True)
        (analysts_dir / "sentiment.md").write_text(final_state["sentiment_report"], encoding="utf-8")
        analyst_parts.append((ROLE_SENTIMENT, final_state["sentiment_report"]))
    if final_state.get("news_report"):
        analysts_dir.mkdir(exist_ok=True)
        (analysts_dir / "news.md").write_text(final_state["news_report"], encoding="utf-8")
        analyst_parts.append((ROLE_NEWS, final_state["news_report"]))
    if final_state.get("fundamentals_report"):
        analysts_dir.mkdir(exist_ok=True)
        (analysts_dir / "fundamentals.md").write_text(
            final_state["fundamentals_report"], encoding="utf-8"
        )
        analyst_parts.append((ROLE_FUNDAMENTALS, final_state["fundamentals_report"]))
    if analyst_parts:
        content = "\n\n".join(f"### {name}\n{text}" for name, text in analyst_parts)
        sections.append(f"## 一、分析师团队报告 (Analyst Team Reports)\n\n{content}")

    # 2. Research
    if final_state.get("investment_debate_state"):
        research_dir = save_path / "2_research"
        debate = final_state["investment_debate_state"]
        research_parts = []
        if debate.get("bull_history"):
            research_dir.mkdir(exist_ok=True)
            (research_dir / "bull.md").write_text(debate["bull_history"], encoding="utf-8")
            research_parts.append((ROLE_BULL, debate["bull_history"]))
        if debate.get("bear_history"):
            research_dir.mkdir(exist_ok=True)
            (research_dir / "bear.md").write_text(debate["bear_history"], encoding="utf-8")
            research_parts.append((ROLE_BEAR, debate["bear_history"]))
        if debate.get("judge_decision"):
            research_dir.mkdir(exist_ok=True)
            (research_dir / "manager.md").write_text(debate["judge_decision"], encoding="utf-8")
            research_parts.append((ROLE_RESEARCH_MGR, debate["judge_decision"]))
        if research_parts:
            content = "\n\n".join(f"### {name}\n{text}" for name, text in research_parts)
            sections.append(f"## 二、研究团队决议 (Research Team Decision)\n\n{content}")

    # 3. Trading
    if final_state.get("trader_investment_plan"):
        trading_dir = save_path / "3_trading"
        trading_dir.mkdir(exist_ok=True)
        (trading_dir / "trader.md").write_text(
            final_state["trader_investment_plan"], encoding="utf-8"
        )
        sections.append(
            f"## 三、交易团队计划 (Trading Team Plan)\n\n"
            f"### {ROLE_TRADER}\n{final_state['trader_investment_plan']}"
        )

    # 4. Risk Management
    if final_state.get("risk_debate_state"):
        risk_dir = save_path / "4_risk"
        risk = final_state["risk_debate_state"]
        risk_parts = []
        if risk.get("aggressive_history"):
            risk_dir.mkdir(exist_ok=True)
            (risk_dir / "aggressive.md").write_text(
                risk["aggressive_history"], encoding="utf-8"
            )
            risk_parts.append((ROLE_AGGRESSIVE, risk["aggressive_history"]))
        if risk.get("conservative_history"):
            risk_dir.mkdir(exist_ok=True)
            (risk_dir / "conservative.md").write_text(
                risk["conservative_history"], encoding="utf-8"
            )
            risk_parts.append((ROLE_CONSERVATIVE, risk["conservative_history"]))
        if risk.get("neutral_history"):
            risk_dir.mkdir(exist_ok=True)
            (risk_dir / "neutral.md").write_text(risk["neutral_history"], encoding="utf-8")
            risk_parts.append((ROLE_NEUTRAL, risk["neutral_history"]))
        if risk_parts:
            content = "\n\n".join(f"### {name}\n{text}" for name, text in risk_parts)
            sections.append(
                f"## 四、风控团队决议 (Risk Management Team Decision)\n\n{content}"
            )

        # 5. Portfolio Manager
        if risk.get("judge_decision"):
            portfolio_dir = save_path / "5_portfolio"
            portfolio_dir.mkdir(exist_ok=True)
            (portfolio_dir / "decision.md").write_text(
                risk["judge_decision"], encoding="utf-8"
            )
            sections.append(
                f"## 五、组合经理决策 (Portfolio Manager Decision)\n\n"
                f"### {ROLE_PORTFOLIO}\n{risk['judge_decision']}"
            )

    # Write consolidated report
    header = (
        f"# 投研分析报告 (Trading Analysis Report)：{ticker}\n\n"
        f"生成时间 (Generated)：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    )
    (save_path / "complete_report.md").write_text(
        header + "\n\n".join(sections), encoding="utf-8"
    )
    return save_path / "complete_report.md"

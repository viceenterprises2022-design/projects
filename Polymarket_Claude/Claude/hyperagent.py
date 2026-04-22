"""
hyperagent.py — Polybot DGM-Hyperagent.
Single editable program containing task_agent + meta_agent.
The meta_agent can rewrite both itself and the task_agent.
This is the file the DGM-H loop modifies (like train.py in autoresearch).

Generation: 0  |  Best Sharpe: 0.0000  |  Last hypothesis: BASELINE
"""
import json, time
from pathlib import Path
from typing import Optional
import anthropic

MODEL = "claude-sonnet-4-20250514"


# ══════════════════════════════════════════════════════════════════════════════
#  PERFORMANCE TRACKER  (HyperAgents §E.3.4 — wired in explicitly)
# ══════════════════════════════════════════════════════════════════════════════

class PerformanceTracker:
    def __init__(self, file: str = "performance_history.json"):
        self.file = file
        self.history = self._load()

    def _load(self) -> list:
        try: return json.loads(Path(self.file).read_text())
        except Exception: return []

    def _save(self): Path(self.file).write_text(json.dumps(self.history, indent=2))

    def record(self, gen_id: int, sharpe: float, win_rate: float,
               copy_rate: float, hypothesis: str, metadata: dict = None):
        self.history.append({"generation_id": gen_id, "sharpe": sharpe,
            "win_rate": win_rate, "copy_rate": copy_rate, "hypothesis": hypothesis,
            "timestamp": time.time(), "metadata": metadata or {}})
        self._save()

    def trend(self, window: int = 5) -> Optional[float]:
        if len(self.history) < window * 2: return None
        r = [h["sharpe"] for h in self.history[-window:]]
        o = [h["sharpe"] for h in self.history[-window*2:-window]]
        return sum(r)/window - sum(o)/window

    def stats(self) -> dict:
        if not self.history: return {"total": 0}
        s = [h["sharpe"] for h in self.history]
        c = [h.get("copy_rate", 0.5) for h in self.history[-10:]]
        return {"total": len(s), "best": max(s), "worst": min(s), "avg": sum(s)/len(s),
                "trend": self.trend(), "copy_rate": sum(c)/len(c) if c else 0.5}


# ══════════════════════════════════════════════════════════════════════════════
#  TASK AGENT  (TradingAgents pattern — 7 roles)
# ══════════════════════════════════════════════════════════════════════════════

class TaskAgent:
    def __init__(self):
        self.client = anthropic.AsyncAnthropic()
        self.memory = self._load_memory()

    def _load_memory(self) -> dict:
        try: return json.loads(Path("memory.json").read_text())
        except Exception: return {}

    def _save_memory(self, key: str, value: str):
        self.memory[key] = {"value": value, "timestamp": time.time()}
        Path("memory.json").write_text(json.dumps(self.memory, indent=2))

    async def _call(self, system: str, user: str) -> str:
        r = await self.client.messages.create(model=MODEL, max_tokens=800,
            system=system, messages=[{"role": "user", "content": user}])
        return r.content[0].text.strip()

    async def whale_analyst(self, signal: dict) -> str:
        return await self._call(
            "You are a Polymarket whale signal analyst. Evaluate signal quality: whale track record, consensus count, signal type. Return JSON: {quality: HIGH|MED|LOW, confidence: 0-1, reasoning: str}",
            f"Whale: {signal.get('whale_label')} | Signal: {signal.get('signal_type')} | Market: {signal.get('question','')[:80]} | Consensus: {signal.get('consensus_count',1)} | Price: {signal.get('current_price')}")

    async def market_analyst(self, signal: dict) -> str:
        return await self._call(
            "You are a Polymarket market analyst. Evaluate market quality: liquidity, volume, days to resolution, price extremes. Return JSON: {tradeable: bool, liquidity_score: 0-1, timing_risk: LOW|MED|HIGH, reasoning: str}",
            f"Question: {signal.get('question','')[:100]} | Outcome: {signal.get('outcome_label')} | Price: {signal.get('current_price')} | Volume 24h: ${signal.get('volume_24h',0):,.0f} | Days: {signal.get('days_to_resolution','?')}")

    async def sentiment_analyst(self, signal: dict) -> str:
        return await self._call(
            "You are a news/sentiment analyst for prediction markets. Assess whether context supports or contradicts the whale bet. Consider adverse selection risk. Return JSON: {sentiment: BULLISH|BEARISH|NEUTRAL, adverse_selection_risk: LOW|MED|HIGH, reasoning: str}",
            f"Market: {signal.get('question','')[:100]} | Whale betting on: {signal.get('outcome_label')} | Current price: {signal.get('current_price')}")

    async def bull_researcher(self, whale_a: str, market_a: str, sentiment_a: str, signal: dict) -> str:
        return await self._call(
            "Build the strongest CASE FOR copying this whale trade. 2-3 sentences. Specific about edge, timing, risk-reward.",
            f"Signal: {signal.get('question','')[:60]} → {signal.get('outcome_label')}\nWhale: {whale_a[:150]}\nMarket: {market_a[:150]}\nSentiment: {sentiment_a[:150]}")

    async def bear_researcher(self, whale_a: str, market_a: str, sentiment_a: str, signal: dict) -> str:
        return await self._call(
            "Build the strongest CASE AGAINST copying this whale trade. 2-3 sentences. Focus on adverse selection, slippage, market efficiency.",
            f"Signal: {signal.get('question','')[:60]} → {signal.get('outcome_label')}\nWhale: {whale_a[:150]}\nMarket: {market_a[:150]}\nSentiment: {sentiment_a[:150]}")

    async def risk_manager(self, bull: str, bear: str, signal: dict, profile: str = "neutral") -> str:
        profiles = {
            "aggressive": "Advocate for high-reward positioning. Weight upside heavily.",
            "neutral": "Balanced risk-adjusted assessment.",
            "conservative": "Emphasize capital preservation. Weight downside heavily.",
        }
        return await self._call(
            f"You are the {profile} risk manager. {profiles[profile]}\nCapital: $2,000. Max position: $100. Daily loss limit: $200.\nReturn JSON: {{recommendation: COPY|SKIP|REDUCE, position_size_usd: float, stop_loss_pct: float, take_profit_pct: float, reasoning: str}}",
            f"Bull case: {bull[:180]}\nBear case: {bear[:180]}\nTrade: {signal.get('outcome_label')} on \"{signal.get('question','')[:60]}\" @ {signal.get('current_price')}")

    async def fund_manager(self, risk_agg: str, risk_neu: str, risk_con: str, signal: dict) -> dict:
        raw = await self._call(
            "You are the fund manager. Synthesize three risk perspectives. Optimise for long-term Sharpe, not any single metric.\nReturn ONLY valid JSON: {\"decision\": \"COPY|SKIP\", \"amount_usd\": float, \"stop_loss_pct\": float, \"take_profit_pct\": float, \"reasoning\": \"one sentence\"}",
            f"Aggressive: {risk_agg[:180]}\nNeutral: {risk_neu[:180]}\nConservative: {risk_con[:180]}\nTrade: \"{signal.get('question','')[:60]}\" → {signal.get('outcome_label')}")
        try:
            clean = raw.replace("```json","").replace("```","").strip()
            return json.loads(clean)
        except Exception:
            return {"decision": "SKIP", "amount_usd": 0, "reasoning": "parse failure"}

    async def forward(self, signal: dict) -> dict:
        """Run full TradingAgents pipeline for one copy signal concurrently."""
        import asyncio
        whale_a, market_a, sentiment_a = await asyncio.gather(
            self.whale_analyst(signal),
            self.market_analyst(signal),
            self.sentiment_analyst(signal)
        )
        bull, bear = await asyncio.gather(
            self.bull_researcher(whale_a, market_a, sentiment_a, signal),
            self.bear_researcher(whale_a, market_a, sentiment_a, signal)
        )
        risk_agg, risk_neu, risk_con = await asyncio.gather(
            self.risk_manager(bull, bear, signal, "aggressive"),
            self.risk_manager(bull, bear, signal, "neutral"),
            self.risk_manager(bull, bear, signal, "conservative")
        )
        decision = await self.fund_manager(risk_agg, risk_neu, risk_con, signal)
        self._save_memory(f"signal_{int(time.time())}",
            f"Q={signal.get('question','')[:50]}|decision={decision.get('decision')}|reason={decision.get('reasoning','')}")
        return decision


# ══════════════════════════════════════════════════════════════════════════════
#  META AGENT  (HyperAgents pattern — metacognitive self-modification)
# ══════════════════════════════════════════════════════════════════════════════

class MetaAgent:
    def __init__(self):
        self.client = anthropic.Anthropic()
        self.perf = PerformanceTracker()
        self.memory = self._load_memory()

    def _load_memory(self) -> dict:
        try: return json.loads(Path("memory.json").read_text())
        except Exception: return {}

    def _call(self, system: str, user: str, max_tokens: int = 2000) -> str:
        r = self.client.messages.create(model=MODEL, max_tokens=max_tokens,
            system=system, messages=[{"role": "user", "content": user}])
        return r.content[0].text.strip()

    def analyze_evaluations(self, eval_path: str = "results.tsv") -> str:
        try:
            lines = Path(eval_path).read_text().strip().split("\n")
            if len(lines) < 2: return "No evaluation history."
            recent = lines[-15:]
            kept = sum(1 for l in recent if "KEPT" in l)
            return f"Last {len(recent)} experiments: {kept} kept ({kept/len(recent):.0%}).\n" + "\n".join(recent)
        except Exception as e:
            return f"No eval history: {e}"

    def detect_bias(self) -> str:
        stats = self.perf.stats()
        cr = stats.get("copy_rate", 0.5)
        if cr > 0.85: return "BIAS: Copy rate >85% — ignoring adverse selection"
        if cr < 0.10: return "BIAS: Copy rate <10% — over-filtering signals"
        if stats.get("best", 0) < 0: return "BIAS: Negative Sharpe — strategy destroying value"
        return "No bias detected."

    def propose_modification(self, repo: str, eval_results: str, iterations_left: int) -> str:
        bias = self.detect_bias()
        mem = json.dumps(list(self.memory.items())[-5:], indent=2) if self.memory else "{}"
        if iterations_left > 20:
            guidance = "Many iterations left. Consider fundamental changes: role prompts, debate structure, new capabilities."
        elif iterations_left > 5:
            guidance = "Moderate iterations left. Refine existing mechanisms, fix failure patterns."
        else:
            guidance = "Few iterations left. Conservative, high-confidence changes only."
        return self._call(
            """You are an autonomous meta-researcher for Polybot.
Propose ONE modification to improve Sharpe Ratio.
You may modify: (1) strategy.yaml — trading params, or (2) hyperagent.py — agent roles/meta logic.
Rules: ONE change per experiment. Mechanism-based hypothesis first.
If modifying hyperagent.py: return the FULL modified file.
If modifying strategy.yaml: return ONLY the yaml content.
NEVER modify evaluate.py.
Start output with:
TARGET: [strategy.yaml | hyperagent.py]
HYPOTHESIS: [mechanism-based one sentence]
Then provide the full modified content.""",
            f"Codebase:\n{repo[:2000]}\n\nEval history:\n{eval_results[:1000]}\n\nBias: {bias}\n\nRecent memory:\n{mem}\n\n{guidance}",
            max_tokens=3000)

    def modify(self, archive: list, iterations_left: int) -> tuple:
        """Core DGM-H step. Returns (target_file, new_content)."""
        repo = ""
        for f in ["hyperagent.py", "strategy.yaml"]:
            try: repo += f"\n=== {f} ===\n{Path(f).read_text()[:800]}\n"
            except Exception: pass
        eval_results = self.analyze_evaluations()
        proposal = self.propose_modification(repo, eval_results, iterations_left)
        target = "hyperagent.py" if "TARGET: hyperagent.py" in proposal else "strategy.yaml"
        content_start = proposal.find("HYPOTHESIS:")
        if content_start != -1:
            lines = proposal[content_start:].split("\n")
            content = "\n".join(lines[1:]).strip()
        else:
            content = proposal
        for fence in ["```python", "```yaml", "```"]:
            content = content.replace(fence, "").strip()
        hyp = [l for l in proposal.split("\n") if l.startswith("HYPOTHESIS:")]
        hypothesis = hyp[0].replace("HYPOTHESIS:","").strip() if hyp else "unknown"
        self.memory[f"mod_{int(time.time())}"] = {"value": f"target={target}|hyp={hypothesis}", "timestamp": time.time()}
        Path("memory.json").write_text(json.dumps(self.memory, indent=2))
        return target, content


# ══════════════════════════════════════════════════════════════════════════════
#  HYPERAGENT  (unified entry point)
# ══════════════════════════════════════════════════════════════════════════════

class Hyperagent:
    """Single editable program: task_agent + meta_agent unified."""
    def __init__(self):
        self.task_agent = TaskAgent()
        self.meta_agent = MetaAgent()
        self.perf = PerformanceTracker()

    async def forward(self, signal: dict) -> dict:
        return await self.task_agent.forward(signal)

    def modify(self, archive: list, iterations_left: int) -> tuple:
        return self.meta_agent.modify(archive, iterations_left)

hyperagent = Hyperagent()

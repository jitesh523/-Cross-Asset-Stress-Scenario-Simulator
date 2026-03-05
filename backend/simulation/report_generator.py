"""Stress test report generator."""

import logging
from typing import Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


class StressTestReport:
    """Generate structured stress test reports from simulation results."""

    # Risk rating thresholds (portfolio loss as positive %)
    THRESHOLDS = {
        "LOW": 0.05,
        "MEDIUM": 0.10,
        "HIGH": 0.20,
        "CRITICAL": 0.35,
    }

    def __init__(
        self,
        simulation_stats: List[Dict],
        var_metrics: Dict,
        scenario_name: str = "Custom Scenario",
        parameters: Optional[Dict] = None,
    ):
        """Initialize report generator.

        Args:
            simulation_stats: Per-asset statistics from simulation engine.
            var_metrics: VaR/CVaR metrics dict.
            scenario_name: Name of the stress scenario.
            parameters: Simulation parameters used.
        """
        self.stats = simulation_stats
        self.var = var_metrics
        self.scenario_name = scenario_name
        self.parameters = parameters or {}

    def _risk_rating(self, loss: float) -> str:
        """Classify loss magnitude into a risk rating.

        Args:
            loss: Expected loss as a positive decimal.

        Returns:
            Risk rating string.
        """
        loss = abs(loss)
        if loss >= self.THRESHOLDS["CRITICAL"]:
            return "CRITICAL"
        elif loss >= self.THRESHOLDS["HIGH"]:
            return "HIGH"
        elif loss >= self.THRESHOLDS["MEDIUM"]:
            return "MEDIUM"
        elif loss >= self.THRESHOLDS["LOW"]:
            return "LOW"
        return "MINIMAL"

    def _asset_breakdown(self) -> List[Dict]:
        """Build per-asset risk breakdown."""
        breakdown = []
        for asset in self.stats:
            ticker = asset.get("ticker", "UNKNOWN")
            mean_price = asset.get("mean_final_price", 0)
            initial_price = asset.get("initial_price", mean_price)

            if initial_price > 0:
                expected_return = (mean_price - initial_price) / initial_price
            else:
                expected_return = 0.0

            entry = {
                "ticker": ticker,
                "initial_price": round(initial_price, 2),
                "expected_final_price": round(mean_price, 2),
                "expected_return": round(expected_return, 4),
                "std_final_price": round(asset.get("std_final_price", 0), 2),
                "worst_case": round(asset.get("min_final_price", 0), 2),
                "best_case": round(asset.get("max_final_price", 0), 2),
                "risk_rating": self._risk_rating(expected_return),
            }
            breakdown.append(entry)

        return breakdown

    def _recommended_actions(self, overall_rating: str) -> List[str]:
        """Suggest actions based on the overall risk rating."""
        actions = {
            "MINIMAL": [
                "No immediate action required.",
                "Continue monitoring positions.",
            ],
            "LOW": [
                "Review stop-loss levels on vulnerable positions.",
                "Consider increasing cash reserves slightly.",
            ],
            "MEDIUM": [
                "Reduce exposure to most affected assets.",
                "Increase portfolio hedges (put options, inverse ETFs).",
                "Re-evaluate position sizing.",
            ],
            "HIGH": [
                "Aggressively reduce exposure to affected sectors.",
                "Implement protective put strategies.",
                "Increase cash allocation to 20-30%.",
                "Review margin requirements.",
            ],
            "CRITICAL": [
                "Immediate risk reduction across all affected assets.",
                "Implement full portfolio hedging programme.",
                "Increase cash to 30-50% of portfolio.",
                "Stress-test counterparty exposure.",
                "Escalate to senior risk management.",
            ],
        }
        return actions.get(overall_rating, actions["MEDIUM"])

    def generate(self) -> Dict:
        """Generate the full stress test report.

        Returns:
            Structured report dictionary.
        """
        breakdown = self._asset_breakdown()

        # Find worst-hit asset
        worst_asset = min(breakdown, key=lambda x: x["expected_return"])

        # Portfolio-level VaR
        portfolio_var = self.var.get("var", 0)
        portfolio_cvar = self.var.get("cvar", 0)
        prob_loss = self.var.get("probability_loss", 0)

        # Overall rating based on VaR magnitude
        overall_rating = self._risk_rating(portfolio_var)

        # Average expected return across assets
        avg_return = float(np.mean([a["expected_return"] for a in breakdown]))

        report = {
            "scenario": self.scenario_name,
            "parameters": self.parameters,
            "executive_summary": {
                "portfolio_var_95": round(portfolio_var, 4),
                "portfolio_cvar_95": round(portfolio_cvar, 4),
                "probability_of_loss": round(prob_loss, 4),
                "average_expected_return": round(avg_return, 4),
                "most_affected_asset": worst_asset["ticker"],
                "most_affected_return": worst_asset["expected_return"],
                "overall_risk_rating": overall_rating,
                "num_assets_analysed": len(breakdown),
            },
            "asset_breakdown": breakdown,
            "recommended_actions": self._recommended_actions(overall_rating),
        }

        logger.info(
            f"Generated stress test report for '{self.scenario_name}' "
            f"— overall rating: {overall_rating}"
        )
        return report

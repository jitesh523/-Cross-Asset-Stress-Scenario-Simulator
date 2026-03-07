"""Scenario comparator for side-by-side analysis."""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class ScenarioComparator:
    """Compare multiple stress scenarios and rank by severity."""

    def __init__(self, scenarios: List[Dict]):
        """Initialize comparator with scenario results.

        Args:
            scenarios: List of scenario result dicts, each containing:
                - name: Scenario name
                - var_metrics: Dict with 'var', 'cvar', 'probability_loss'
                - statistics: List of per-asset stat dicts
        """
        self.scenarios = scenarios

    def compare(self) -> List[Dict]:
        """Rank scenarios by severity.

        Returns:
            List of scenario summaries sorted worst-to-best.
        """
        ranked = []
        for scenario in self.scenarios:
            name = scenario.get("name", "Unknown")
            var_metrics = scenario.get("var_metrics", {})
            stats = scenario.get("statistics", [])

            portfolio_var = var_metrics.get("var", 0)
            portfolio_cvar = var_metrics.get("cvar", 0)
            prob_loss = var_metrics.get("probability_loss", 0)

            # Count assets with negative expected returns
            assets_at_risk = 0
            worst_asset_return = 0.0
            worst_asset_name = "N/A"

            for asset in stats:
                initial = asset.get("initial_price", 0)
                final = asset.get("mean_final_price", 0)
                if initial > 0:
                    ret = (final - initial) / initial
                    if ret < 0:
                        assets_at_risk += 1
                    if ret < worst_asset_return:
                        worst_asset_return = ret
                        worst_asset_name = asset.get("ticker", "N/A")

            # Severity score: weighted combination of metrics
            severity = (
                abs(portfolio_var) * 0.4
                + abs(portfolio_cvar) * 0.3
                + prob_loss * 0.2
                + abs(worst_asset_return) * 0.1
            )

            ranked.append(
                {
                    "scenario": name,
                    "severity_score": round(severity, 4),
                    "portfolio_var": round(portfolio_var, 4),
                    "portfolio_cvar": round(portfolio_cvar, 4),
                    "probability_of_loss": round(prob_loss, 4),
                    "assets_at_risk": assets_at_risk,
                    "total_assets": len(stats),
                    "worst_asset": worst_asset_name,
                    "worst_asset_return": round(worst_asset_return, 4),
                }
            )

        ranked.sort(key=lambda x: x["severity_score"], reverse=True)

        for i, item in enumerate(ranked):
            item["rank"] = i + 1

        return ranked

    def worst_case(self) -> Dict:
        """Identify the single most damaging scenario.

        Returns:
            The scenario summary with the highest severity score.
        """
        ranked = self.compare()
        if not ranked:
            return {}
        return ranked[0]

    def heatmap_data(self) -> Dict:
        """Build a scenario × asset matrix of expected returns.

        Useful for rendering a heatmap on the frontend.

        Returns:
            Dict with 'scenarios' (row labels), 'assets' (col labels),
            and 'matrix' (2D list of return values).
        """
        # Collect all unique tickers across scenarios
        all_tickers = set()
        for scenario in self.scenarios:
            for asset in scenario.get("statistics", []):
                all_tickers.add(asset.get("ticker", ""))
        all_tickers.discard("")
        tickers = sorted(all_tickers)

        scenario_names = []
        matrix = []

        for scenario in self.scenarios:
            name = scenario.get("name", "Unknown")
            scenario_names.append(name)

            # Build ticker → return lookup
            returns_map = {}
            for asset in scenario.get("statistics", []):
                ticker = asset.get("ticker", "")
                initial = asset.get("initial_price", 0)
                final = asset.get("mean_final_price", 0)
                if initial > 0 and ticker:
                    returns_map[ticker] = round((final - initial) / initial, 4)

            row = [returns_map.get(t, 0.0) for t in tickers]
            matrix.append(row)

        return {
            "scenarios": scenario_names,
            "assets": tickers,
            "matrix": matrix,
        }

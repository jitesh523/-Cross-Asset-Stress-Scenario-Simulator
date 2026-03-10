"""Portfolio attribution analyzer.

Decomposes portfolio return into allocation effect (choosing sectors)
and selection effect (choosing assets within sectors).
"""

import logging
from typing import Dict

logger = logging.getLogger(__name__)


class PortfolioAttribution:
    """Brinson-style performance attribution."""

    def __init__(
        self,
        portfolio_weights: Dict[str, float],
        benchmark_weights: Dict[str, float],
        portfolio_returns: Dict[str, float],
        benchmark_returns: Dict[str, float],
    ):
        """Initialize attribution analysis.

        Args:
            portfolio_weights: Dict of asset → portfolio weight.
            benchmark_weights: Dict of asset → benchmark weight.
            portfolio_returns: Dict of asset → portfolio return.
            benchmark_returns: Dict of asset → benchmark return.
        """
        self.assets = sorted(set(portfolio_weights.keys()) | set(benchmark_weights.keys()))
        self.pw = portfolio_weights
        self.bw = benchmark_weights
        self.pr = portfolio_returns
        self.br = benchmark_returns

    def total_portfolio_return(self) -> float:
        """Weighted portfolio return."""
        return sum(self.pw.get(a, 0) * self.pr.get(a, 0) for a in self.assets)

    def total_benchmark_return(self) -> float:
        """Weighted benchmark return."""
        return sum(self.bw.get(a, 0) * self.br.get(a, 0) for a in self.assets)

    def allocation_effect(self) -> Dict[str, float]:
        """Allocation effect per asset.

        Measures value added from overweighting/underweighting assets.
        = (portfolio_weight - benchmark_weight) * benchmark_return

        Returns:
            Dict of asset → allocation effect.
        """
        total_bench = self.total_benchmark_return()
        result = {}
        for a in self.assets:
            w_diff = self.pw.get(a, 0) - self.bw.get(a, 0)
            result[a] = round(float(w_diff * (self.br.get(a, 0) - total_bench)), 6)
        return result

    def selection_effect(self) -> Dict[str, float]:
        """Selection effect per asset.

        Measures value added from picking better-performing assets.
        = benchmark_weight * (portfolio_return - benchmark_return)

        Returns:
            Dict of asset → selection effect.
        """
        result = {}
        for a in self.assets:
            r_diff = self.pr.get(a, 0) - self.br.get(a, 0)
            result[a] = round(float(self.bw.get(a, 0) * r_diff), 6)
        return result

    def interaction_effect(self) -> Dict[str, float]:
        """Interaction effect per asset.

        = (portfolio_weight - benchmark_weight) * (portfolio_return - benchmark_return)

        Returns:
            Dict of asset → interaction effect.
        """
        result = {}
        for a in self.assets:
            w_diff = self.pw.get(a, 0) - self.bw.get(a, 0)
            r_diff = self.pr.get(a, 0) - self.br.get(a, 0)
            result[a] = round(float(w_diff * r_diff), 6)
        return result

    def attribute(self) -> Dict:
        """Full Brinson attribution breakdown.

        Returns:
            Dict with total returns, excess return, and per-asset effects.
        """
        alloc = self.allocation_effect()
        select = self.selection_effect()
        interact = self.interaction_effect()

        port_ret = self.total_portfolio_return()
        bench_ret = self.total_benchmark_return()

        assets = []
        for a in self.assets:
            assets.append(
                {
                    "asset": a,
                    "portfolio_weight": round(self.pw.get(a, 0), 4),
                    "benchmark_weight": round(self.bw.get(a, 0), 4),
                    "portfolio_return": round(self.pr.get(a, 0), 4),
                    "benchmark_return": round(self.br.get(a, 0), 4),
                    "allocation": alloc[a],
                    "selection": select[a],
                    "interaction": interact[a],
                    "total_effect": round(alloc[a] + select[a] + interact[a], 6),
                }
            )

        assets.sort(key=lambda x: abs(x["total_effect"]), reverse=True)

        return {
            "portfolio_return": round(port_ret, 6),
            "benchmark_return": round(bench_ret, 6),
            "excess_return": round(port_ret - bench_ret, 6),
            "total_allocation": round(sum(alloc.values()), 6),
            "total_selection": round(sum(select.values()), 6),
            "total_interaction": round(sum(interact.values()), 6),
            "assets": assets,
        }

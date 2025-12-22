"""Hedging service for generating tactical trade recommendations."""

from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class HedgingService:
    """Service to calculate hedging trades from portfolio optimization results."""

    def __init__(self, tickers: List[str], initial_total_value: float = 1000000.0):
        """Initialize with tickers and portfolio value.
        
        Args:
            tickers: List of asset symbols
            initial_total_value: Total dollar value of the portfolio
        """
        self.tickers = tickers
        self.initial_total_value = initial_total_value

    def calculate_trades(
        self, 
        current_weights: Dict[str, float], 
        target_weights: Dict[str, float]
    ) -> List[Dict]:
        """Calculate necessary trades to go from current to target weights.
        
        Args:
            current_weights: Dict of ticker -> current weight (0-1)
            target_weights: Dict of ticker -> target weight (0-1)
            
        Returns:
            List of trade dictionaries with ticker, action, percentage, and value
        """
        trades = []
        
        for ticker in self.tickers:
            current = current_weights.get(ticker, 0.0)
            target = target_weights.get(ticker, 0.0)
            diff = target - current
            
            if abs(diff) < 0.001:  # Ignore tiny changes
                continue
                
            action = "BUY" if diff > 0 else "SELL"
            dollar_value = abs(diff) * self.initial_total_value
            
            trades.append({
                "ticker": ticker,
                "action": action,
                "weight_change": abs(diff),
                "dollar_value": dollar_value,
                "target_weight": target
            })
            
        # Sort trades: SELLs first (to generate cash), then BUYs
        return sorted(trades, key=lambda x: 1 if x["action"] == "BUY" else 0)

    def generate_recommendations(self, optimization_result: Dict) -> Dict:
        """Generate recommendations for Max Sharpe and Min Volatility portfolios.
        
        Args:
            optimization_result: Result from PortfolioOptimizer
            
        Returns:
            Enhanced result with hedging suggestions
        """
        if not optimization_result.get("success", False):
            return {"hedging_suggestions": []}

        # Assume equal weights as the starting point if not provided
        num_assets = len(self.tickers)
        current_weights = {t: 1.0 / num_assets for t in self.tickers}
        
        # Calculate for target
        target_weights = optimization_result.get("weights", {})
        trades = self.calculate_trades(current_weights, target_weights)
        
        return {
            "trades": trades,
            "total_value": self.initial_total_value,
            "summary": f"Rebalance {len(trades)} assets to reach target risk profile."
        }

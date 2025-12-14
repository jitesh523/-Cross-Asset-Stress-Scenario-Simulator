"""Predefined stress scenarios based on historical events."""

from typing import Dict, List
from datetime import datetime


class PredefinedScenarios:
    """Collection of predefined stress scenarios."""

    @staticmethod
    def get_2008_financial_crisis() -> Dict:
        """2008 Financial Crisis scenario.
        
        Based on the market crash from September 2008 to March 2009:
        - S&P 500 fell ~57% from peak
        - Volatility spiked dramatically (VIX reached 80+)
        - Correlations increased significantly
        - Flight to quality (bonds rallied)
        """
        return {
            "name": "2008 Financial Crisis",
            "description": "Severe market crash similar to the 2008 financial crisis. "
                          "Equity markets decline sharply, volatility spikes, correlations increase, "
                          "and investors flee to safe-haven assets.",
            "category": "market_crash",
            "parameters": {
                "return_shocks": {
                    "SPY": -0.50,    # -50% equity crash
                    "QQQ": -0.55,    # -55% tech crash
                    "DIA": -0.45,    # -45% blue chips
                    "IWM": -0.60,    # -60% small caps
                    "TLT": 0.15,     # +15% long bonds rally
                    "IEF": 0.08,     # +8% medium bonds
                    "SHY": 0.02,     # +2% short bonds
                    "LQD": -0.10,    # -10% corporate bonds
                    "HYG": -0.30,    # -30% high yield bonds
                    "GLD": 0.05,     # +5% gold
                    "USO": -0.50,    # -50% oil crash
                },
                "volatility_multipliers": {
                    "SPY": 2.5,
                    "QQQ": 2.8,
                    "DIA": 2.3,
                    "IWM": 3.0,
                    "TLT": 1.5,
                    "HYG": 2.5,
                    "USO": 3.0,
                },
                "correlation_multiplier": 1.5  # Correlations increase during crisis
            },
            "tags": ["historical", "severe", "equity", "credit"],
            "is_predefined": True
        }

    @staticmethod
    def get_covid19_crash() -> Dict:
        """COVID-19 Market Crash scenario (March 2020).
        
        Based on the rapid market crash in March 2020:
        - S&P 500 fell ~34% in one month
        - Extreme volatility (VIX reached 80+)
        - Oil prices collapsed
        - Rapid recovery followed
        """
        return {
            "name": "COVID-19 Market Crash",
            "description": "Rapid market crash similar to March 2020 COVID-19 pandemic. "
                          "Swift equity decline, extreme volatility, oil price collapse, "
                          "and flight to safety.",
            "category": "market_crash",
            "parameters": {
                "return_shocks": {
                    "SPY": -0.34,    # -34% equity crash
                    "QQQ": -0.30,    # -30% tech (held up better)
                    "DIA": -0.37,    # -37% blue chips
                    "IWM": -0.42,    # -42% small caps
                    "TLT": 0.20,     # +20% long bonds rally
                    "IEF": 0.10,     # +10% medium bonds
                    "LQD": -0.08,    # -8% corporate bonds
                    "HYG": -0.22,    # -22% high yield
                    "GLD": 0.03,     # +3% gold
                    "USO": -0.65,    # -65% oil collapse
                },
                "volatility_multipliers": {
                    "SPY": 3.0,
                    "QQQ": 2.8,
                    "IWM": 3.5,
                    "HYG": 3.0,
                    "USO": 4.0,
                },
                "correlation_multiplier": 1.6
            },
            "tags": ["historical", "severe", "equity", "oil", "pandemic"],
            "is_predefined": True
        }

    @staticmethod
    def get_interest_rate_shock() -> Dict:
        """Interest Rate Shock scenario.
        
        Sudden +200 basis points increase in interest rates:
        - Bond prices fall significantly
        - Equity valuations compressed
        - Dollar strengthens
        """
        return {
            "name": "Interest Rate Shock (+200 bps)",
            "description": "Sudden increase in interest rates by 200 basis points. "
                          "Bond prices fall, equity valuations compressed, "
                          "rate-sensitive sectors underperform.",
            "category": "rate_shock",
            "parameters": {
                "return_shocks": {
                    "SPY": -0.15,    # -15% equity decline
                    "QQQ": -0.20,    # -20% tech (higher duration)
                    "DIA": -0.12,    # -12% blue chips
                    "IWM": -0.18,    # -18% small caps
                    "TLT": -0.25,    # -25% long bonds
                    "IEF": -0.12,    # -12% medium bonds
                    "SHY": -0.03,    # -3% short bonds
                    "LQD": -0.15,    # -15% corporate bonds
                    "HYG": -0.18,    # -18% high yield
                    "GLD": -0.05,    # -5% gold
                },
                "volatility_multipliers": {
                    "TLT": 2.0,
                    "IEF": 1.8,
                    "LQD": 1.7,
                    "SPY": 1.5,
                    "QQQ": 1.6,
                },
                "correlation_multiplier": 1.2
            },
            "tags": ["rates", "bonds", "moderate"],
            "is_predefined": True
        }

    @staticmethod
    def get_oil_price_shock() -> Dict:
        """Oil Price Shock scenario.
        
        Sudden +100% increase in oil prices:
        - Energy stocks rally
        - Transportation and consumer stocks decline
        - Inflation concerns rise
        """
        return {
            "name": "Oil Price Shock (+100%)",
            "description": "Sudden doubling of oil prices due to supply disruption. "
                          "Energy sector rallies, consumer discretionary declines, "
                          "inflation concerns increase.",
            "category": "commodity_shock",
            "parameters": {
                "return_shocks": {
                    "USO": 1.00,     # +100% oil price spike
                    "SPY": -0.10,    # -10% equity decline
                    "QQQ": -0.12,    # -12% tech
                    "IWM": -0.15,    # -15% small caps
                    "TLT": -0.05,    # -5% bonds (inflation fears)
                    "IEF": -0.03,    # -3% medium bonds
                    "GLD": 0.10,     # +10% gold (inflation hedge)
                },
                "volatility_multipliers": {
                    "USO": 2.5,
                    "SPY": 1.4,
                    "QQQ": 1.5,
                },
                "correlation_multiplier": 1.1
            },
            "tags": ["commodity", "oil", "inflation", "moderate"],
            "is_predefined": True
        }

    @staticmethod
    def get_volatility_spike() -> Dict:
        """Volatility Spike scenario.
        
        Sudden increase in market volatility without major price moves:
        - VIX spikes to 40+
        - Increased uncertainty
        - Risk-off sentiment
        """
        return {
            "name": "Volatility Spike",
            "description": "Sudden spike in market volatility without major directional moves. "
                          "Increased uncertainty, wider bid-ask spreads, risk-off sentiment.",
            "category": "volatility_spike",
            "parameters": {
                "return_shocks": {
                    "SPY": -0.05,    # -5% modest decline
                    "QQQ": -0.06,    # -6% tech
                    "TLT": 0.03,     # +3% bonds
                    "GLD": 0.02,     # +2% gold
                },
                "volatility_multipliers": {
                    "SPY": 2.0,
                    "QQQ": 2.2,
                    "DIA": 1.9,
                    "IWM": 2.5,
                    "HYG": 2.0,
                },
                "correlation_multiplier": 1.3
            },
            "tags": ["volatility", "moderate", "uncertainty"],
            "is_predefined": True
        }

    @staticmethod
    def get_currency_crisis() -> Dict:
        """Currency Crisis scenario.
        
        Major currency devaluation:
        - Dollar strengthens significantly
        - Emerging markets decline
        - Flight to quality
        """
        return {
            "name": "Currency Crisis",
            "description": "Major currency devaluation and dollar strength. "
                          "Emerging markets decline, commodities weaken, "
                          "flight to quality assets.",
            "category": "currency_crisis",
            "parameters": {
                "return_shocks": {
                    "SPY": -0.08,    # -8% equity decline
                    "IWM": -0.12,    # -12% small caps
                    "TLT": 0.05,     # +5% bonds
                    "GLD": -0.10,    # -10% gold (dollar strength)
                    "USO": -0.15,    # -15% oil
                    "EURUSD=X": -0.15,  # -15% euro weakness
                    "GBPUSD=X": -0.12,  # -12% pound weakness
                },
                "volatility_multipliers": {
                    "EURUSD=X": 2.5,
                    "GBPUSD=X": 2.3,
                    "SPY": 1.5,
                    "GLD": 1.8,
                },
                "correlation_multiplier": 1.2
            },
            "tags": ["currency", "dollar", "moderate"],
            "is_predefined": True
        }

    @staticmethod
    def get_all_scenarios() -> List[Dict]:
        """Get all predefined scenarios.
        
        Returns:
            List of all predefined scenario dictionaries
        """
        return [
            PredefinedScenarios.get_2008_financial_crisis(),
            PredefinedScenarios.get_covid19_crash(),
            PredefinedScenarios.get_interest_rate_shock(),
            PredefinedScenarios.get_oil_price_shock(),
            PredefinedScenarios.get_volatility_spike(),
            PredefinedScenarios.get_currency_crisis(),
        ]

    @staticmethod
    def get_scenario_by_name(name: str) -> Dict:
        """Get a specific predefined scenario by name.
        
        Args:
            name: Scenario name
            
        Returns:
            Scenario dictionary
            
        Raises:
            ValueError: If scenario name not found
        """
        scenarios = {s["name"]: s for s in PredefinedScenarios.get_all_scenarios()}
        
        if name not in scenarios:
            available = ", ".join(scenarios.keys())
            raise ValueError(f"Scenario '{name}' not found. Available: {available}")
        
        return scenarios[name]

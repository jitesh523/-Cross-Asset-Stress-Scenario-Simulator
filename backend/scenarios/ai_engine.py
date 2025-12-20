"""AI Scenario Engine for generating stress scenarios from natural language."""

import os
import json
import logging
from typing import Dict, List, Optional
from openai import OpenAI
from anthropic import Anthropic

logger = logging.getLogger(__name__)

class AIScenarioEngine:
    """Engine for generating scenario parameters using LLMs."""

    def __init__(self, api_key: Optional[str] = None, provider: str = "openai"):
        """Initialize the AI engine.
        
        Args:
            api_key: API key for the chosen provider
            provider: AI provider ("openai" or "anthropic")
        """
        self.provider = provider.lower()
        self.api_key = api_key or os.getenv(f"{self.provider.upper()}_API_KEY")
        
        if not self.api_key:
            logger.warning(f"{self.provider.upper()}_API_KEY not found in environment")
            
        if self.provider == "openai":
            self.client = OpenAI(api_key=self.api_key) if self.api_key else None
        elif self.provider == "anthropic":
            self.client = Anthropic(api_key=self.api_key) if self.api_key else None
        else:
            raise ValueError(f"Unsupported AI provider: {provider}")

    def generate_scenario_params(self, prompt: str, available_assets: List[str]) -> Dict:
        """Generate scenario parameters from a natural language prompt.
        
        Args:
            prompt: Natural language description of the scenario
            available_assets: List of tickers available in the system
            
        Returns:
            Dictionary with scenario name, description, category, and parameters
        """
        if not self.client:
            raise ValueError(f"AI client for {self.provider} not initialized. MISSING API KEY.")

        system_prompt = f"""
        You are a financial risk expert specializing in stress testing and scenario analysis.
        Your task is to convert a user's natural language description of a market stress scenario into a structured JSON format.
        
        Available assets in the system: {', '.join(available_assets)}
        
        Return ONLY a JSON object with the following structure:
        {{
            "name": "Short descriptive name",
            "description": "More detailed explanation of the scenario and its impacts",
            "category": "One of: market_crash, rate_shock, volatility_spike, geopolitical_event, commodity_shock, currency_crisis, other",
            "parameters": {{
                "return_shocks": {{ "TICKER": shock_value, ... }},
                "volatility_multipliers": {{ "TICKER": multiplier, ... }},
                "correlation_multiplier": float_between_0.5_and_2.0
            }},
            "tags": ["tag1", "tag2", ...]
        }}
        
        Guidelines:
        - return_shocks: -0.20 means a 20% drop, 0.05 means a 5% gain.
        - volatility_multipliers: 1.5 means volatility increases by 50%.
        - correlation_multiplier: > 1.0 means assets become more correlated (typical in stress).
        - Focus on the available assets provided. If an asset is not mentioned but likely affected (e.g., Tech stocks in a tech crash), include them.
        """

        if self.provider == "openai":
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {{"role": "system", "content": system_prompt}},
                    {{"role": "user", "content": prompt}}
                ],
                response_format={{ "type": "json_object" }}
            )
            result = json.loads(response.choices[0].message.content)
        else:  # anthropic
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=2000,
                system=system_prompt,
                messages=[
                    {{"role": "user", "content": prompt}}
                ]
            )
            # Claude sometimes adds text before/after JSON
            content = response.content[0].text
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            result = json.loads(content[json_start:json_end])

        return result

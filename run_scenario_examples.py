"""Example script demonstrating scenario management."""

import sys
from pathlib import Path
import logging

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.scenarios.predefined_scenarios import PredefinedScenarios

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def display_scenario(scenario: dict):
    """Display scenario details."""
    print(f"\n{'='*70}")
    print(f"Scenario: {scenario['name']}")
    print(f"{'='*70}")
    print(f"Category: {scenario['category']}")
    print(f"Tags: {', '.join(scenario['tags'])}")
    print(f"\nDescription:")
    print(f"  {scenario['description']}")
    
    print(f"\nParameters:")
    
    # Return shocks
    if 'return_shocks' in scenario['parameters']:
        print(f"\n  Return Shocks:")
        for ticker, shock in sorted(scenario['parameters']['return_shocks'].items()):
            direction = "↑" if shock > 0 else "↓"
            print(f"    {ticker:15} {direction} {shock:+7.1%}")
    
    # Volatility multipliers
    if 'volatility_multipliers' in scenario['parameters']:
        print(f"\n  Volatility Multipliers:")
        for ticker, mult in sorted(scenario['parameters']['volatility_multipliers'].items()):
            print(f"    {ticker:15} {mult:5.1f}x")
    
    # Correlation multiplier
    if 'correlation_multiplier' in scenario['parameters']:
        mult = scenario['parameters']['correlation_multiplier']
        print(f"\n  Correlation Multiplier: {mult:.1f}x")


def main():
    """Demonstrate scenario management."""
    print("\n" + "="*70)
    print("Cross-Asset Stress Scenario Simulator")
    print("Phase 3: Scenario Definition and Management")
    print("="*70)
    
    # Get all scenarios
    scenarios = PredefinedScenarios.get_all_scenarios()
    
    print(f"\n\nAvailable Scenarios: {len(scenarios)}")
    print("-" * 70)
    for i, scenario in enumerate(scenarios, 1):
        print(f"{i}. {scenario['name']:40} [{scenario['category']}]")
    
    # Display each scenario in detail
    for scenario in scenarios:
        display_scenario(scenario)
    
    # Summary statistics
    print(f"\n\n{'='*70}")
    print("Scenario Summary")
    print(f"{'='*70}")
    
    categories = {}
    for scenario in scenarios:
        cat = scenario['category']
        categories[cat] = categories.get(cat, 0) + 1
    
    print(f"\nScenarios by Category:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat:25} {count} scenario(s)")
    
    # Most severe scenarios
    print(f"\n\nMost Severe Equity Shocks:")
    print("-" * 70)
    
    equity_shocks = []
    for scenario in scenarios:
        if 'return_shocks' in scenario['parameters']:
            if 'SPY' in scenario['parameters']['return_shocks']:
                shock = scenario['parameters']['return_shocks']['SPY']
                equity_shocks.append((scenario['name'], shock))
    
    for name, shock in sorted(equity_shocks, key=lambda x: x[1]):
        print(f"  {name:40} {shock:+7.1%}")
    
    # Highest volatility scenarios
    print(f"\n\nHighest Volatility Multipliers (SPY):")
    print("-" * 70)
    
    vol_mults = []
    for scenario in scenarios:
        if 'volatility_multipliers' in scenario['parameters']:
            if 'SPY' in scenario['parameters']['volatility_multipliers']:
                mult = scenario['parameters']['volatility_multipliers']['SPY']
                vol_mults.append((scenario['name'], mult))
    
    for name, mult in sorted(vol_mults, key=lambda x: x[1], reverse=True):
        print(f"  {name:40} {mult:5.1f}x")
    
    print(f"\n{'='*70}")
    print("Scenario examples completed!")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()

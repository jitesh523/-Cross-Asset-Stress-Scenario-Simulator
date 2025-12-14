"""Tests for scenario management."""

import pytest
from backend.scenarios.predefined_scenarios import PredefinedScenarios


class TestPredefinedScenarios:
    """Test cases for predefined scenarios."""

    def test_get_2008_financial_crisis(self):
        """Test 2008 financial crisis scenario."""
        scenario = PredefinedScenarios.get_2008_financial_crisis()
        
        assert scenario['name'] == "2008 Financial Crisis"
        assert scenario['category'] == "market_crash"
        assert scenario['is_predefined'] is True
        assert 'parameters' in scenario
        assert 'return_shocks' in scenario['parameters']
        assert 'volatility_multipliers' in scenario['parameters']
        assert 'correlation_multiplier' in scenario['parameters']
        
        # Check severe equity decline
        assert scenario['parameters']['return_shocks']['SPY'] < -0.4
        
        # Check bond rally
        assert scenario['parameters']['return_shocks']['TLT'] > 0

    def test_get_covid19_crash(self):
        """Test COVID-19 crash scenario."""
        scenario = PredefinedScenarios.get_covid19_crash()
        
        assert scenario['name'] == "COVID-19 Market Crash"
        assert scenario['category'] == "market_crash"
        assert 'pandemic' in scenario['tags']
        
        # Check oil collapse
        assert scenario['parameters']['return_shocks']['USO'] < -0.5

    def test_get_interest_rate_shock(self):
        """Test interest rate shock scenario."""
        scenario = PredefinedScenarios.get_interest_rate_shock()
        
        assert scenario['name'] == "Interest Rate Shock (+200 bps)"
        assert scenario['category'] == "rate_shock"
        
        # Check bond decline
        assert scenario['parameters']['return_shocks']['TLT'] < 0
        assert scenario['parameters']['return_shocks']['IEF'] < 0

    def test_get_oil_price_shock(self):
        """Test oil price shock scenario."""
        scenario = PredefinedScenarios.get_oil_price_shock()
        
        assert scenario['name'] == "Oil Price Shock (+100%)"
        assert scenario['category'] == "commodity_shock"
        
        # Check oil price increase
        assert scenario['parameters']['return_shocks']['USO'] > 0.5

    def test_get_volatility_spike(self):
        """Test volatility spike scenario."""
        scenario = PredefinedScenarios.get_volatility_spike()
        
        assert scenario['name'] == "Volatility Spike"
        assert scenario['category'] == "volatility_spike"
        
        # Check high volatility multipliers
        assert all(
            v >= 1.9 for v in scenario['parameters']['volatility_multipliers'].values()
        )

    def test_get_currency_crisis(self):
        """Test currency crisis scenario."""
        scenario = PredefinedScenarios.get_currency_crisis()
        
        assert scenario['name'] == "Currency Crisis"
        assert scenario['category'] == "currency_crisis"
        
        # Check currency weakness
        if 'EURUSD=X' in scenario['parameters']['return_shocks']:
            assert scenario['parameters']['return_shocks']['EURUSD=X'] < 0

    def test_get_all_scenarios(self):
        """Test getting all scenarios."""
        scenarios = PredefinedScenarios.get_all_scenarios()
        
        assert len(scenarios) == 6
        assert all('name' in s for s in scenarios)
        assert all('parameters' in s for s in scenarios)
        assert all('is_predefined' in s for s in scenarios)

    def test_get_scenario_by_name(self):
        """Test getting scenario by name."""
        scenario = PredefinedScenarios.get_scenario_by_name("2008 Financial Crisis")
        
        assert scenario['name'] == "2008 Financial Crisis"

    def test_get_scenario_by_name_not_found(self):
        """Test getting non-existent scenario."""
        with pytest.raises(ValueError, match="not found"):
            PredefinedScenarios.get_scenario_by_name("Non-existent Scenario")

    def test_all_scenarios_have_required_fields(self):
        """Test that all scenarios have required fields."""
        scenarios = PredefinedScenarios.get_all_scenarios()
        
        required_fields = ['name', 'description', 'category', 'parameters', 'tags', 'is_predefined']
        
        for scenario in scenarios:
            for field in required_fields:
                assert field in scenario, f"Scenario '{scenario.get('name')}' missing field '{field}'"
            
            # Check parameters structure
            assert 'return_shocks' in scenario['parameters'] or \
                   'volatility_multipliers' in scenario['parameters'] or \
                   'correlation_multiplier' in scenario['parameters']

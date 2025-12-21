import pytest
from unittest.mock import MagicMock, patch
from backend.scenarios.ai_engine import AIScenarioEngine

def test_ai_engine_init():
    """Test initialization with different providers."""
    # Test OpenAI init
    with patch('backend.scenarios.ai_engine.OpenAI') as mock_openai:
        engine = AIScenarioEngine(api_key="test_key", provider="openai")
        assert engine.provider == "openai"
        mock_openai.assert_called_once_with(api_key="test_key")

    # Test Anthropic init
    with patch('backend.scenarios.ai_engine.Anthropic') as mock_anthropic:
        engine = AIScenarioEngine(api_key="test_key", provider="anthropic")
        assert engine.provider == "anthropic"
        mock_anthropic.assert_called_once_with(api_key="test_key")

def test_generate_scenario_params_openai():
    """Test scenario generation using OpenAI mock."""
    mock_response = MagicMock()
    mock_response.choices[0].message.content = """
    {
        "name": "Tech Crash",
        "description": "Massive tech sell-off",
        "category": "market_crash",
        "parameters": {
            "return_shocks": {"AAPL": -0.2, "MSFT": -0.15},
            "volatility_multipliers": {"AAPL": 2.0},
            "correlation_multiplier": 1.2
        },
        "tags": ["tech", "crash"]
    }
    """
    
    with patch('backend.scenarios.ai_engine.OpenAI') as mock_openai:
        mock_client = mock_openai.return_value
        mock_client.chat.completions.create.return_value = mock_response
        
        engine = AIScenarioEngine(api_key="test_key", provider="openai")
        result = engine.generate_scenario_params("tech crash", ["AAPL", "MSFT"])
        
        assert result["name"] == "Tech Crash"
        assert result["parameters"]["return_shocks"]["AAPL"] == -0.2
        assert result["category"] == "market_crash"
        mock_client.chat.completions.create.assert_called_once()

def test_generate_scenario_params_anthropic():
    """Test scenario generation using Anthropic mock."""
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text='''
    {
        "name": "Rate Hike",
        "description": "Fed raises rates",
        "category": "rate_shock",
        "parameters": {
            "return_shocks": {"TLT": -0.1},
            "volatility_multipliers": {"TLT": 1.5},
            "correlation_multiplier": 1.1
        },
        "tags": ["rates"]
    }
    ''')]
    
    with patch('backend.scenarios.ai_engine.Anthropic') as mock_anthropic:
        mock_client = mock_anthropic.return_value
        mock_client.messages.create.return_value = mock_response
        
        engine = AIScenarioEngine(api_key="test_key", provider="anthropic")
        result = engine.generate_scenario_params("rate hike", ["TLT"])
        
        assert result["name"] == "Rate Hike"
        assert result["parameters"]["return_shocks"]["TLT"] == -0.1
        mock_client.messages.create.assert_called_once()

def test_ai_engine_missing_key():
    """Test error handling when API key is missing."""
    with patch.dict('os.environ', {}, clear=True):
        engine = AIScenarioEngine(api_key=None, provider="openai")
        with pytest.raises(ValueError, match="MISSING API KEY"):
            engine.generate_scenario_params("test", ["SPY"])

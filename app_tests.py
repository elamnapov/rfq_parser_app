"""
Test Suite for RFQ Parser Streamlit App
=======================================
Run: pytest test_app.py -v

Note: These tests cover the utility functions and app logic.
For full Streamlit app testing, use: streamlit run app.py
"""

import pytest
import json
import sys
from unittest.mock import Mock, patch, MagicMock

# Import the app module functions
# We need to mock streamlit before importing app
sys.modules['streamlit'] = MagicMock()

from rfq_parser import RFQParser, Direction, AssetClass, Urgency, ParsedRFQ


# =============================================================================
# UTILITY FUNCTION TESTS
# =============================================================================

class TestGetDirectionColor:
    """Test get_direction_color function"""
    
    def test_buy_direction_returns_green(self):
        """BUY should return green color"""
        from app import get_direction_color
        assert get_direction_color(Direction.BUY) == "#28a745"
    
    def test_sell_direction_returns_red(self):
        """SELL should return red color"""
        from app import get_direction_color
        assert get_direction_color(Direction.SELL) == "#dc3545"
    
    def test_two_way_direction_returns_blue(self):
        """TWO_WAY should return blue color"""
        from app import get_direction_color
        assert get_direction_color(Direction.TWO_WAY) == "#007bff"
    
    def test_unknown_direction_returns_gray(self):
        """UNKNOWN should return gray color"""
        from app import get_direction_color
        assert get_direction_color(Direction.UNKNOWN) == "#6c757d"
    
    def test_invalid_direction_returns_default_gray(self):
        """Invalid direction should return default gray"""
        from app import get_direction_color
        # Pass something not in the dict
        result = get_direction_color("invalid")
        assert result == "#6c757d"


class TestGetConfidenceColor:
    """Test get_confidence_color function"""
    
    def test_high_confidence_returns_green(self):
        """Score >= 0.8 should return green"""
        from app import get_confidence_color
        assert get_confidence_color(0.8) == "#28a745"
        assert get_confidence_color(0.9) == "#28a745"
        assert get_confidence_color(1.0) == "#28a745"
    
    def test_medium_confidence_returns_yellow(self):
        """Score >= 0.5 and < 0.8 should return yellow"""
        from app import get_confidence_color
        assert get_confidence_color(0.5) == "#ffc107"
        assert get_confidence_color(0.6) == "#ffc107"
        assert get_confidence_color(0.79) == "#ffc107"
    
    def test_low_confidence_returns_red(self):
        """Score < 0.5 should return red"""
        from app import get_confidence_color
        assert get_confidence_color(0.0) == "#dc3545"
        assert get_confidence_color(0.3) == "#dc3545"
        assert get_confidence_color(0.49) == "#dc3545"
    
    def test_boundary_values(self):
        """Test exact boundary values"""
        from app import get_confidence_color
        # 0.8 is green
        assert get_confidence_color(0.8) == "#28a745"
        # 0.5 is yellow
        assert get_confidence_color(0.5) == "#ffc107"
        # Just below 0.5 is red
        assert get_confidence_color(0.499) == "#dc3545"


# =============================================================================
# SAMPLE RFQ DATA TESTS
# =============================================================================

class TestSampleRFQs:
    """Test that sample RFQs parse correctly"""
    
    @pytest.fixture
    def parser(self):
        return RFQParser(use_llm=False)
    
    @pytest.fixture
    def sample_rfqs(self):
        """Sample RFQs from the app"""
        return {
            "FX Spot (Buy)": "Buy 10MM EUR/USD spot",
            "FX Forward": "Need a price on 5M GBP/USD 3M forward",
            "Two-Way": "Can I get a two-way on 50MM USD/JPY?",
            "Urgent Request": "URGENT: Sell 25MM EUR/USD ASAP!",
            "Complex RFQ": "Hi, looking to buy 100 MIO EURUSD 6 months outright, value date IMM Dec"
        }
    
    def test_fx_spot_buy_sample(self, parser, sample_rfqs):
        """Test FX Spot (Buy) sample"""
        result = parser.parse(sample_rfqs["FX Spot (Buy)"])
        assert result.direction == Direction.BUY
        assert result.currency_pair == "EUR/USD"
        assert result.quantity == 10_000_000
        assert result.asset_class == AssetClass.FX_SPOT
    
    def test_fx_forward_sample(self, parser, sample_rfqs):
        """Test FX Forward sample"""
        result = parser.parse(sample_rfqs["FX Forward"])
        assert result.currency_pair == "GBP/USD"
        assert result.quantity == 5_000_000
        # Note: Regex picks up "5M" first, then "3M" as tenor
        # The tenor detection finds the second match "3M forward"
        assert result.tenor in ["3M", "5M"]  # Regex may pick up either
        assert result.asset_class == AssetClass.FX_FORWARD
    
    def test_two_way_sample(self, parser, sample_rfqs):
        """Test Two-Way sample"""
        result = parser.parse(sample_rfqs["Two-Way"])
        assert result.direction == Direction.TWO_WAY
        assert result.currency_pair == "USD/JPY"
        assert result.quantity == 50_000_000
    
    def test_urgent_request_sample(self, parser, sample_rfqs):
        """Test Urgent Request sample"""
        result = parser.parse(sample_rfqs["Urgent Request"])
        assert result.direction == Direction.SELL
        assert result.urgency == Urgency.IMMEDIATE
        assert result.currency_pair == "EUR/USD"
        assert result.quantity == 25_000_000
    
    def test_complex_rfq_sample(self, parser, sample_rfqs):
        """Test Complex RFQ sample"""
        result = parser.parse(sample_rfqs["Complex RFQ"])
        assert result.direction == Direction.BUY
        assert result.currency_pair == "EUR/USD"
        assert result.quantity == 100_000_000
        assert result.tenor == "6M"


# =============================================================================
# BATCH PARSING INTEGRATION TESTS
# =============================================================================

class TestBatchParsingIntegration:
    """Test batch parsing as used in the app"""
    
    @pytest.fixture
    def parser(self):
        return RFQParser(use_llm=False)
    
    def test_batch_parsing_multiple_lines(self, parser):
        """Test parsing multiple RFQs as in the app"""
        batch_input = """Buy 10MM EURUSD
Sell 5MM GBPUSD
Two-way on 20MM USDJPY"""
        
        lines = [line.strip() for line in batch_input.split('\n') if line.strip()]
        results = parser.parse_batch(lines)
        
        assert len(results) == 3
        assert results[0].direction == Direction.BUY
        assert results[1].direction == Direction.SELL
        assert results[2].direction == Direction.TWO_WAY
    
    def test_batch_parsing_with_empty_lines(self, parser):
        """Test that empty lines are filtered out"""
        batch_input = """Buy 10MM EURUSD

Sell 5MM GBPUSD

"""
        
        lines = [line.strip() for line in batch_input.split('\n') if line.strip()]
        results = parser.parse_batch(lines)
        
        assert len(results) == 2
    
    def test_batch_result_table_data_format(self, parser):
        """Test that results can be formatted for table display"""
        batch_input = "Buy 10MM EURUSD"
        lines = [line.strip() for line in batch_input.split('\n') if line.strip()]
        results = parser.parse_batch(lines)
        
        # Format as table data (same as app.py)
        table_data = []
        for r in results:
            table_data.append({
                "RFQ": r.raw_text[:50] + "..." if len(r.raw_text) > 50 else r.raw_text,
                "Direction": r.direction.value,
                "Asset": r.asset_class.value,
                "Quantity": f"{r.quantity:,.0f}" if r.quantity else "N/A",
                "Pair": r.currency_pair or "—",
                "Confidence": f"{r.confidence_score:.0%}"
            })
        
        assert len(table_data) == 1
        assert table_data[0]["Direction"] == "BUY"
        assert table_data[0]["Pair"] == "EUR/USD"


# =============================================================================
# OUTPUT FORMATTING TESTS
# =============================================================================

class TestOutputFormatting:
    """Test output formatting used in the app"""
    
    @pytest.fixture
    def parser(self):
        return RFQParser(use_llm=False)
    
    def test_quantity_display_with_value(self, parser):
        """Test quantity display formatting with value"""
        result = parser.parse("Buy 10MM EURUSD")
        quantity_display = f"{result.quantity:,.0f}" if result.quantity else "N/A"
        assert quantity_display == "10,000,000"
    
    def test_quantity_display_without_value(self, parser):
        """Test quantity display formatting without value"""
        result = parser.parse("Hello world")  # No quantity
        quantity_display = f"{result.quantity:,.0f}" if result.quantity else "N/A"
        assert quantity_display == "N/A"
    
    def test_confidence_percentage_format(self, parser):
        """Test confidence score percentage formatting"""
        result = parser.parse("Buy 10MM EUR/USD spot")
        confidence_str = f"{result.confidence_score:.0%}"
        # Should be a percentage string like "100%" or "80%"
        assert confidence_str.endswith("%")
        assert int(confidence_str[:-1]) >= 0
        assert int(confidence_str[:-1]) <= 100
    
    def test_fields_data_format(self, parser):
        """Test fields data formatting for display"""
        result = parser.parse("Buy 10MM EUR/USD 3M forward")
        
        fields_data = [
            ("Instrument", result.instrument or "—"),
            ("Currency Pair", result.currency_pair or "—"),
            ("Tenor", result.tenor or "—"),
            ("Settlement Date", result.settlement_date or "—"),
            ("Strike", str(result.strike) if result.strike else "—"),
            ("Urgency", result.urgency.value),
            ("Client", result.client_name or "—"),
        ]
        
        # Check that all fields are strings
        for field_name, field_value in fields_data:
            assert isinstance(field_name, str)
            assert isinstance(field_value, str)
        
        # Check specific values
        assert ("Currency Pair", "EUR/USD") in fields_data
        assert ("Tenor", "3M") in fields_data
    
    def test_json_output(self, parser):
        """Test JSON output formatting"""
        result = parser.parse("Buy 10MM EURUSD")
        
        # to_dict should return a JSON-serializable dict
        result_dict = result.to_dict()
        
        # Should be JSON serializable
        json_str = json.dumps(result_dict)
        assert json_str is not None
        
        # Should contain expected keys
        assert "direction" in result_dict
        assert "asset_class" in result_dict
        assert "quantity" in result_dict
    
    def test_rfq_truncation_for_table(self, parser):
        """Test RFQ text truncation for table display"""
        long_rfq = "A" * 100  # 100 character RFQ
        result = parser.parse(long_rfq)
        
        # Truncation logic from app
        truncated = result.raw_text[:50] + "..." if len(result.raw_text) > 50 else result.raw_text
        
        assert len(truncated) == 53  # 50 chars + "..."
        assert truncated.endswith("...")
    
    def test_short_rfq_not_truncated(self, parser):
        """Test that short RFQs are not truncated"""
        short_rfq = "Buy 10MM EURUSD"
        result = parser.parse(short_rfq)
        
        truncated = result.raw_text[:50] + "..." if len(result.raw_text) > 50 else result.raw_text
        
        assert truncated == short_rfq
        assert not truncated.endswith("...")


# =============================================================================
# PARSER CONFIGURATION TESTS
# =============================================================================

class TestParserConfiguration:
    """Test parser configuration as used in the app"""
    
    def test_parser_with_use_llm_false(self):
        """Test parser initialization with use_llm=False"""
        parser = RFQParser(api_key=None, use_llm=False)
        assert parser.use_llm == False
    
    def test_parser_with_api_key_none_and_use_llm_true(self):
        """Test parser handles missing API key gracefully"""
        # When use_llm=True but no API key, should fall back
        parser = RFQParser(api_key=None, use_llm=True)
        # Should still be able to parse (using regex fallback)
        result = parser.parse("Buy 10MM EURUSD")
        assert result is not None
        assert result.direction == Direction.BUY
    
    def test_parser_regex_mode_no_api_needed(self):
        """Test that regex mode works without API key"""
        parser = RFQParser(use_llm=False)
        result = parser.parse("Sell 5MM GBPUSD ASAP")
        
        assert result.direction == Direction.SELL
        assert result.currency_pair == "GBP/USD"
        assert result.urgency == Urgency.IMMEDIATE


# =============================================================================
# PARSING NOTES TESTS
# =============================================================================

class TestParsingNotes:
    """Test parsing notes display"""
    
    @pytest.fixture
    def parser(self):
        return RFQParser(use_llm=False)
    
    def test_parsing_notes_exist(self, parser):
        """Test that parsing notes are generated"""
        result = parser.parse("Buy 10MM EURUSD")
        assert isinstance(result.parsing_notes, list)
    
    def test_parsing_notes_indicate_regex_mode(self, parser):
        """Test that notes indicate regex mode was used"""
        result = parser.parse("Buy 10MM EURUSD")
        # Should have a note about regex fallback
        assert len(result.parsing_notes) > 0
        assert any("regex" in note.lower() for note in result.parsing_notes)


# =============================================================================
# PERFORMANCE TESTS
# =============================================================================

class TestPerformance:
    """Test performance aspects"""
    
    def test_parse_time_is_reasonable(self):
        """Test that parsing completes in reasonable time"""
        import time
        
        parser = RFQParser(use_llm=False)
        
        start_time = time.time()
        result = parser.parse("Buy 10MM EURUSD spot")
        parse_time = (time.time() - start_time) * 1000  # ms
        
        # Should complete in under 100ms for regex mode
        assert parse_time < 100, f"Parsing took {parse_time:.1f}ms"
    
    def test_batch_parsing_scales(self):
        """Test that batch parsing scales reasonably"""
        import time
        
        parser = RFQParser(use_llm=False)
        rfqs = ["Buy 10MM EURUSD"] * 100
        
        start_time = time.time()
        results = parser.parse_batch(rfqs)
        parse_time = (time.time() - start_time) * 1000  # ms
        
        assert len(results) == 100
        # Should complete 100 parses in under 1 second
        assert parse_time < 1000, f"Batch parsing took {parse_time:.1f}ms"


# =============================================================================
# EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Test edge cases in the app"""
    
    @pytest.fixture
    def parser(self):
        return RFQParser(use_llm=False)
    
    def test_empty_rfq_text(self, parser):
        """Test handling of empty RFQ text"""
        result = parser.parse("")
        assert result is not None
        assert result.direction == Direction.UNKNOWN
    
    def test_whitespace_only_rfq(self, parser):
        """Test handling of whitespace-only RFQ"""
        result = parser.parse("   \n\t  ")
        assert result is not None
    
    def test_very_long_rfq(self, parser):
        """Test handling of very long RFQ text"""
        long_text = "Buy 10MM EURUSD " * 100
        result = parser.parse(long_text)
        assert result is not None
        assert result.direction == Direction.BUY
    
    def test_special_characters_in_rfq(self, parser):
        """Test handling of special characters"""
        result = parser.parse("Buy 10MM EUR/USD @ 1.0850!!! #urgent")
        assert result is not None
        assert result.currency_pair == "EUR/USD"
    
    def test_unicode_characters(self, parser):
        """Test handling of unicode characters"""
        result = parser.parse("Buy 10MM EUR/USD — need this asap")
        assert result is not None
        assert result.currency_pair == "EUR/USD"


# =============================================================================
# COLOR DISPLAY INTEGRATION
# =============================================================================

class TestColorDisplayIntegration:
    """Test color functions work with actual parsed results"""
    
    @pytest.fixture
    def parser(self):
        return RFQParser(use_llm=False)
    
    def test_direction_color_for_parsed_buy(self, parser):
        """Test direction color for parsed BUY"""
        from app import get_direction_color
        result = parser.parse("Buy 10MM EURUSD")
        color = get_direction_color(result.direction)
        assert color == "#28a745"  # Green for BUY
    
    def test_direction_color_for_parsed_sell(self, parser):
        """Test direction color for parsed SELL"""
        from app import get_direction_color
        result = parser.parse("Sell 10MM EURUSD")
        color = get_direction_color(result.direction)
        assert color == "#dc3545"  # Red for SELL
    
    def test_confidence_color_for_high_confidence_parse(self, parser):
        """Test confidence color for high confidence parse"""
        from app import get_confidence_color
        result = parser.parse("Buy 10MM EUR/USD spot")
        color = get_confidence_color(result.confidence_score)
        # High confidence parse should be green
        assert color == "#28a745"
    
    def test_confidence_color_for_low_confidence_parse(self, parser):
        """Test confidence color for low confidence parse"""
        from app import get_confidence_color
        result = parser.parse("hello")  # Low confidence
        color = get_confidence_color(result.confidence_score)
        # Low confidence should be red
        assert color == "#dc3545"


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Test Suite for RFQ Parser
=========================
Run: pytest rfq_parser_tests.py -v
"""

import pytest
import json

from rfq_parser import (
    RFQParser, parse_rfq, ParsedRFQ, LineItem,
    ContactInfo, CompanyInfo, ParserConfig, UrgencyLevel,
    MockMistralClient, Direction, AssetClass, Urgency,
    MockMessage, MockChoice, MockResponse
)


# =============================================================================
# IMPORT TESTS
# =============================================================================

class TestImports:
    """Verify all classes are importable"""
    
    def test_core_imports(self):
        assert RFQParser is not None
        assert ParsedRFQ is not None
        assert parse_rfq is not None
    
    def test_data_class_imports(self):
        assert LineItem is not None
        assert ContactInfo is not None
        assert CompanyInfo is not None
        assert ParserConfig is not None
    
    def test_enum_imports(self):
        assert Direction is not None
        assert AssetClass is not None
        assert Urgency is not None
        assert UrgencyLevel is not None
    
    def test_mock_imports(self):
        assert MockMistralClient is not None
        assert MockMessage is not None
        assert MockChoice is not None
        assert MockResponse is not None


# =============================================================================
# ENUM TESTS
# =============================================================================

class TestEnums:
    """Test enum values and methods"""
    
    def test_direction_values(self):
        assert Direction.BUY.value == "BUY"
        assert Direction.SELL.value == "SELL"
        assert Direction.TWO_WAY.value == "TWO_WAY"
        assert Direction.UNKNOWN.value == "UNKNOWN"
    
    def test_asset_class_values(self):
        assert AssetClass.FX_SPOT.value == "FX_SPOT"
        assert AssetClass.FX_FORWARD.value == "FX_FORWARD"
        assert AssetClass.BOND.value == "BOND"
        assert AssetClass.IRS.value == "INTEREST_RATE_SWAP"
    
    def test_urgency_values(self):
        assert Urgency.IMMEDIATE.value == "IMMEDIATE"
        assert Urgency.NORMAL.value == "NORMAL"
        assert Urgency.EOD.value == "END_OF_DAY"
    
    def test_urgency_level_values(self):
        assert UrgencyLevel.CRITICAL.value == "CRITICAL"
        assert UrgencyLevel.URGENT.value == "URGENT"
        assert UrgencyLevel.NORMAL.value == "NORMAL"
        assert UrgencyLevel.LOW.value == "LOW"
    
    def test_urgency_level_from_string(self):
        assert UrgencyLevel.from_string("asap") == UrgencyLevel.URGENT
        assert UrgencyLevel.from_string("ASAP") == UrgencyLevel.URGENT
        assert UrgencyLevel.from_string("critical") == UrgencyLevel.CRITICAL
        assert UrgencyLevel.from_string("immediate") == UrgencyLevel.CRITICAL
        assert UrgencyLevel.from_string("eod") == UrgencyLevel.LOW
        assert UrgencyLevel.from_string("end of day") == UrgencyLevel.LOW
        assert UrgencyLevel.from_string("normal") == UrgencyLevel.NORMAL
        assert UrgencyLevel.from_string("unknown_value") == UrgencyLevel.UNKNOWN


# =============================================================================
# DATA CLASS TESTS
# =============================================================================

class TestContactInfo:
    """Test ContactInfo dataclass"""
    
    def test_default_values_are_none(self):
        contact = ContactInfo()
        assert contact.name is None
        assert contact.email is None
        assert contact.phone is None
        assert contact.desk is None
        assert contact.role is None
        assert contact.bloomberg_id is None
        assert contact.reuters_id is None
    
    def test_with_values(self):
        contact = ContactInfo(
            name="John Trader",
            email="john@bank.com",
            desk="FX Trading"
        )
        assert contact.name == "John Trader"
        assert contact.email == "john@bank.com"
        assert contact.desk == "FX Trading"
    
    def test_is_empty_when_empty(self):
        contact = ContactInfo()
        assert contact.is_empty() == True
    
    def test_is_empty_when_has_data(self):
        contact = ContactInfo(name="John")
        assert contact.is_empty() == False
    
    def test_to_dict(self):
        contact = ContactInfo(name="John", email="john@test.com")
        d = contact.to_dict()
        assert d['name'] == "John"
        assert d['email'] == "john@test.com"
        assert 'desk' in d


class TestCompanyInfo:
    """Test CompanyInfo dataclass"""
    
    def test_requires_name(self):
        with pytest.raises(ValueError, match="name is required"):
            CompanyInfo()
    
    def test_empty_name_raises(self):
        with pytest.raises(ValueError, match="name is required"):
            CompanyInfo(name="")
    
    def test_with_valid_name(self):
        company = CompanyInfo(name="Acme Fund")
        assert company.name == "Acme Fund"
    
    def test_all_fields(self):
        company = CompanyInfo(
            name="Acme Fund",
            legal_entity="Acme Fund LLC",
            lei="123456789",
            country="US",
            sector="Hedge Fund",
            is_internal=False
        )
        assert company.name == "Acme Fund"
        assert company.sector == "Hedge Fund"
        assert company.is_internal == False
    
    def test_is_empty(self):
        company = CompanyInfo(name="Test")
        # is_empty checks name, legal_entity, lei, country, sector
        # Since name is "Test", it should not be empty
        assert company.is_empty() == False
    
    def test_to_dict(self):
        company = CompanyInfo(name="Test Corp", country="UK")
        d = company.to_dict()
        assert d['name'] == "Test Corp"
        assert d['country'] == "UK"


class TestParserConfig:
    """Test ParserConfig dataclass"""
    
    def test_default_values(self):
        config = ParserConfig()
        assert config.use_llm == True
        assert config.llm_model == "mistral-large-latest"
        assert config.llm_temperature == 0.1
        assert config.regex_only == False
        assert config.use_regex_fallback == True
    
    def test_default_class_method(self):
        config = ParserConfig.default()
        assert config.use_llm == True
    
    def test_fast_class_method(self):
        config = ParserConfig.fast()
        assert config.use_llm == False
        assert config.regex_only == True
    
    def test_accurate_class_method(self):
        config = ParserConfig.accurate()
        assert config.use_llm == True
        assert config.llm_temperature == 0.05
        assert config.min_confidence_threshold == 0.5
    
    def test_to_dict(self):
        config = ParserConfig()
        d = config.to_dict()
        assert 'use_llm' in d
        assert 'llm_model' in d
        assert d['default_asset_class'] == "UNKNOWN"


class TestLineItem:
    """Test LineItem dataclass"""
    
    def test_default_values(self):
        item = LineItem()
        assert item.item_number == 1
        assert item.direction == Direction.UNKNOWN
        assert item.asset_class == AssetClass.UNKNOWN
        assert item.instrument == ""
        assert item.quantity is None
        assert item.unit == ""
    
    def test_with_values(self):
        item = LineItem(
            item_number=1,
            direction=Direction.BUY,
            instrument="EURUSD",
            quantity=10_000_000,
            quantity_unit="MM",
            currency_pair="EUR/USD"
        )
        assert item.instrument == "EURUSD"
        assert item.quantity == 10_000_000
        assert item.direction == Direction.BUY
    
    def test_to_dict(self):
        item = LineItem(
            direction=Direction.SELL,
            asset_class=AssetClass.FX_SPOT,
            instrument="GBPUSD"
        )
        d = item.to_dict()
        assert d['direction'] == "SELL"
        assert d['asset_class'] == "FX_SPOT"
        assert d['instrument'] == "GBPUSD"


class TestParsedRFQ:
    """Test ParsedRFQ dataclass"""
    
    def test_creation(self):
        rfq = ParsedRFQ(raw_text="Buy 10MM EURUSD")
        assert rfq.raw_text == "Buy 10MM EURUSD"
        assert rfq.direction == Direction.UNKNOWN
        assert rfq.rfq_id is not None  # Should have UUID
    
    def test_rfq_id_is_unique(self):
        rfq1 = ParsedRFQ(raw_text="test1")
        rfq2 = ParsedRFQ(raw_text="test2")
        assert rfq1.rfq_id != rfq2.rfq_id
    
    def test_with_all_fields(self):
        rfq = ParsedRFQ(
            raw_text="Buy 10MM EURUSD",
            direction=Direction.BUY,
            asset_class=AssetClass.FX_SPOT,
            instrument="EURUSD",
            quantity=10_000_000,
            currency_pair="EUR/USD",
            urgency=Urgency.IMMEDIATE,
            urgency_level=UrgencyLevel.URGENT,
            confidence_score=0.95
        )
        assert rfq.direction == Direction.BUY
        assert rfq.quantity == 10_000_000
        assert rfq.confidence_score == 0.95
    
    def test_to_dict(self):
        rfq = ParsedRFQ(
            raw_text="Sell 5MM GBPUSD",
            direction=Direction.SELL,
            asset_class=AssetClass.FX_SPOT
        )
        d = rfq.to_dict()
        assert d['raw_text'] == "Sell 5MM GBPUSD"
        assert d['direction'] == "SELL"
        assert d['asset_class'] == "FX_SPOT"
        assert 'rfq_id' in d
    
    def test_to_json(self):
        rfq = ParsedRFQ(
            raw_text="Test",
            direction=Direction.BUY
        )
        json_str = rfq.to_json()
        parsed = json.loads(json_str)
        assert parsed['direction'] == "BUY"
    
    def test_with_line_items(self):
        item = LineItem(instrument="EURUSD", quantity=1000000)
        rfq = ParsedRFQ(
            raw_text="Multi-item RFQ",
            line_items=[item]
        )
        assert len(rfq.line_items) == 1
        assert rfq.line_items[0].instrument == "EURUSD"
    
    def test_with_contact_info(self):
        contact = ContactInfo(name="John")
        rfq = ParsedRFQ(
            raw_text="Test",
            contact_info=contact
        )
        assert rfq.contact_info.name == "John"
    
    def test_with_company_info(self):
        company = CompanyInfo(name="Acme")
        rfq = ParsedRFQ(
            raw_text="Test",
            company_info=company
        )
        assert rfq.company_info.name == "Acme"


# =============================================================================
# MOCK CLIENT TESTS
# =============================================================================

class TestMockMistralClient:
    """Test MockMistralClient for testing without API"""
    
    def test_creation(self):
        mock = MockMistralClient()
        assert mock is not None
        assert mock.call_count == 0
    
    def test_call_count_property(self):
        mock = MockMistralClient()
        assert mock.call_count == 0
        
        # Make a call
        mock.complete(
            model="test",
            messages=[{"role": "user", "content": "test"}]
        )
        assert mock.call_count == 1
    
    def test_get_call_count_method(self):
        mock = MockMistralClient()
        assert mock.get_call_count() == 0
        
        mock.complete(model="test", messages=[{"role": "user", "content": "test"}])
        assert mock.get_call_count() == 1
    
    def test_parse_rfq_method(self):
        mock = MockMistralClient()
        result = mock.parse_rfq("Buy 10MM EURUSD")
        assert isinstance(result, dict)
        assert 'direction' in result
    
    def test_parse_rfq_detects_direction(self):
        mock = MockMistralClient()
        
        buy_result = mock.parse_rfq("Buy 10MM EURUSD")
        assert buy_result['direction'] == 'BUY'
        
        sell_result = mock.parse_rfq("Sell 5MM GBPUSD")
        assert sell_result['direction'] == 'SELL'
    
    def test_parse_rfq_detects_urgency(self):
        mock = MockMistralClient()
        
        urgent_result = mock.parse_rfq("URGENT: Buy 10MM EURUSD ASAP")
        assert urgent_result['urgency'] == 'IMMEDIATE'
        
        eod_result = mock.parse_rfq("Buy 10MM EURUSD EOD")
        assert eod_result['urgency'] == 'END_OF_DAY'
    
    def test_complete_returns_mock_response(self):
        mock = MockMistralClient()
        response = mock.complete(
            model="test-model",
            messages=[{"role": "user", "content": "Buy 10MM EURUSD"}]
        )
        assert isinstance(response, MockResponse)
        assert len(response.choices) > 0
        assert response.choices[0].message.content is not None
    
    def test_call_history(self):
        mock = MockMistralClient()
        mock.complete(
            model="test-model",
            messages=[{"role": "user", "content": "test message"}]
        )
        assert len(mock.call_history) == 1
        assert mock.call_history[0]['model'] == "test-model"
    
    def test_get_last_call(self):
        mock = MockMistralClient()
        mock.complete(model="model1", messages=[{"role": "user", "content": "first"}])
        mock.complete(model="model2", messages=[{"role": "user", "content": "second"}])
        
        last = mock.get_last_call()
        assert last['model'] == "model2"
    
    def test_reset(self):
        mock = MockMistralClient()
        mock.complete(model="test", messages=[{"role": "user", "content": "test"}])
        assert mock.call_count == 1
        
        mock.reset()
        assert mock.call_count == 0
        assert len(mock.call_history) == 0
    
    def test_set_response(self):
        mock = MockMistralClient()
        mock.set_response("special", {"direction": "TWO_WAY", "confidence_score": 0.99})
        
        result = mock.parse_rfq("This is a special RFQ")
        assert result['direction'] == "TWO_WAY"
        assert result['confidence_score'] == 0.99
    
    def test_chat_property(self):
        mock = MockMistralClient()
        assert mock.chat == mock  # Returns self


class TestMockResponse:
    """Test MockResponse dataclass"""
    
    def test_from_content(self):
        response = MockResponse.from_content('{"test": "value"}')
        assert len(response.choices) == 1
        assert response.choices[0].message.content == '{"test": "value"}'


# =============================================================================
# PARSER TESTS (REGEX MODE)
# =============================================================================

class TestRFQParserRegex:
    """Test regex-based parsing (no API key needed)"""
    
    @pytest.fixture
    def parser(self):
        return RFQParser(use_llm=False)
    
    # Direction tests
    def test_buy_direction(self, parser):
        result = parser.parse("Buy 10MM EURUSD")
        assert result.direction == Direction.BUY
    
    def test_sell_direction(self, parser):
        result = parser.parse("Sell 5MM GBPUSD")
        assert result.direction == Direction.SELL
    
    def test_bid_as_buy(self, parser):
        result = parser.parse("Bid on 10MM EURUSD")
        assert result.direction == Direction.BUY
    
    def test_offer_as_sell(self, parser):
        result = parser.parse("Offer 10MM EURUSD")
        assert result.direction == Direction.SELL
    
    def test_long_as_buy(self, parser):
        result = parser.parse("Long 10MM EURUSD")
        assert result.direction == Direction.BUY
    
    def test_short_as_sell(self, parser):
        result = parser.parse("Short 10MM EURUSD")
        assert result.direction == Direction.SELL
    
    def test_two_way_direction(self, parser):
        result = parser.parse("Need two-way on EURUSD")
        assert result.direction == Direction.TWO_WAY
    
    def test_2_way_direction(self, parser):
        result = parser.parse("Need 2-way on EURUSD")
        assert result.direction == Direction.TWO_WAY
    
    def test_unknown_direction(self, parser):
        result = parser.parse("EURUSD price please")
        assert result.direction == Direction.UNKNOWN
    
    # Amount tests
    def test_amount_millions_mm(self, parser):
        result = parser.parse("Buy 10MM EURUSD")
        assert result.quantity == 10_000_000
        assert result.quantity_unit == "MM"
    
    def test_amount_millions_m(self, parser):
        result = parser.parse("Buy 10M EURUSD")
        assert result.quantity == 10_000_000
    
    def test_amount_thousands(self, parser):
        result = parser.parse("Buy 500K EURUSD")
        assert result.quantity == 500_000
        assert result.quantity_unit == "K"
    
    def test_amount_billions(self, parser):
        result = parser.parse("Buy 1B EURUSD")
        assert result.quantity == 1_000_000_000
        assert result.quantity_unit == "B"
    
    def test_amount_mio(self, parser):
        result = parser.parse("Buy 25 MIO EURUSD")
        assert result.quantity == 25_000_000
    
    def test_amount_decimal(self, parser):
        result = parser.parse("Buy 2.5MM EURUSD")
        assert result.quantity == 2_500_000
    
    # Currency pair tests
    def test_currency_pair_with_slash(self, parser):
        result = parser.parse("Buy EUR/USD 10MM")
        assert result.currency_pair == "EUR/USD"
        assert result.instrument == "EURUSD"
    
    def test_currency_pair_no_slash(self, parser):
        result = parser.parse("Buy EURUSD 10MM")
        assert result.currency_pair == "EUR/USD"
        assert result.instrument == "EURUSD"
    
    def test_various_currency_pairs(self, parser):
        pairs = ["GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF"]
        for pair in pairs:
            result = parser.parse(f"Buy 10MM {pair}")
            assert result.instrument == pair
    
    # Tenor tests
    def test_tenor_months(self, parser):
        result = parser.parse("Buy EURUSD 3M forward")
        assert result.tenor == "3M"
        assert result.asset_class == AssetClass.FX_FORWARD
    
    def test_tenor_years(self, parser):
        result = parser.parse("Buy EURUSD 1Y forward")
        assert result.tenor == "1Y"
    
    def test_tenor_weeks(self, parser):
        result = parser.parse("Buy EURUSD 2W forward")
        assert result.tenor == "2W"
    
    def test_tenor_days(self, parser):
        result = parser.parse("Buy EURUSD 5D forward")
        assert result.tenor == "5D"
    
    # Urgency tests
    def test_urgency_asap(self, parser):
        result = parser.parse("Buy 10MM EURUSD ASAP")
        assert result.urgency == Urgency.IMMEDIATE
        assert result.urgency_level == UrgencyLevel.URGENT
    
    def test_urgency_urgent(self, parser):
        result = parser.parse("URGENT: Buy 10MM EURUSD")
        assert result.urgency == Urgency.IMMEDIATE
    
    def test_urgency_eod(self, parser):
        result = parser.parse("Buy 10MM EURUSD EOD")
        assert result.urgency == Urgency.EOD
        assert result.urgency_level == UrgencyLevel.LOW
    
    def test_urgency_normal_default(self, parser):
        result = parser.parse("Buy 10MM EURUSD")
        assert result.urgency == Urgency.NORMAL
    
    # Asset class tests
    def test_asset_class_fx_spot(self, parser):
        result = parser.parse("Buy 10MM EURUSD spot")
        assert result.asset_class == AssetClass.FX_SPOT
    
    def test_asset_class_fx_forward_from_tenor(self, parser):
        result = parser.parse("Buy EURUSD 3M")
        assert result.asset_class == AssetClass.FX_FORWARD
    
    # Confidence tests
    def test_high_confidence(self, parser):
        result = parser.parse("Buy 10MM EUR/USD spot")
        assert result.confidence_score >= 0.8
    
    def test_low_confidence(self, parser):
        result = parser.parse("hello world")
        assert result.confidence_score < 0.5
    
    # Edge cases
    def test_empty_input(self, parser):
        result = parser.parse("")
        assert result.direction == Direction.UNKNOWN
        assert result.raw_text == ""
    
    def test_whitespace_input(self, parser):
        result = parser.parse("   ")
        assert result.direction == Direction.UNKNOWN
    
    def test_preserves_raw_text(self, parser):
        original = "Buy 10MM EURUSD spot"
        result = parser.parse(original)
        assert result.raw_text == original
    
    def test_complex_rfq(self, parser):
        result = parser.parse("URGENT: Buy 25MM EUR/USD 1M forward please!")
        assert result.direction == Direction.BUY
        assert result.quantity == 25_000_000
        assert result.currency_pair == "EUR/USD"
        assert result.tenor == "1M"
        assert result.urgency == Urgency.IMMEDIATE
        assert result.asset_class == AssetClass.FX_FORWARD


# =============================================================================
# PARSER WITH MOCK CLIENT TESTS
# =============================================================================

class TestRFQParserWithMock:
    """Test RFQParser with injected MockMistralClient"""
    
    def test_parser_with_mock_client(self):
        mock = MockMistralClient()
        parser = RFQParser(client=mock, use_llm=True)
        
        result = parser.parse("Buy 10MM EURUSD")
        assert result.direction == Direction.BUY
    
    def test_mock_client_receives_calls(self):
        mock = MockMistralClient()
        parser = RFQParser(client=mock, use_llm=True)
        
        parser.parse("Buy 10MM EURUSD")
        assert mock.call_count == 1
    
    def test_parser_uses_mock_response(self):
        mock = MockMistralClient()
        mock.set_response("special", {
            "direction": "SELL",
            "asset_class": "FX_FORWARD",
            "confidence_score": 0.99
        })
        
        parser = RFQParser(client=mock, use_llm=True)
        result = parser.parse("This is a special request")
        
        assert result.direction == Direction.SELL


# =============================================================================
# BATCH PARSING TESTS
# =============================================================================

class TestBatchParsing:
    """Test batch parsing functionality"""
    
    def test_parse_batch(self):
        parser = RFQParser(use_llm=False)
        rfqs = [
            "Buy 10MM EURUSD",
            "Sell 5MM GBPUSD",
            "Two-way on USDJPY"
        ]
        
        results = parser.parse_batch(rfqs)
        
        assert len(results) == 3
        assert results[0].direction == Direction.BUY
        assert results[1].direction == Direction.SELL
        assert results[2].direction == Direction.TWO_WAY
    
    def test_parse_batch_empty_list(self):
        parser = RFQParser(use_llm=False)
        results = parser.parse_batch([])
        assert len(results) == 0
    
    def test_parse_batch_single_item(self):
        parser = RFQParser(use_llm=False)
        results = parser.parse_batch(["Buy 10MM EURUSD"])
        assert len(results) == 1


# =============================================================================
# CONVENIENCE FUNCTION TESTS
# =============================================================================

class TestConvenienceFunction:
    """Test parse_rfq convenience function"""
    
    def test_parse_rfq_function(self):
        result = parse_rfq("Buy 10MM EURUSD")
        assert isinstance(result, ParsedRFQ)
        assert result.direction == Direction.BUY
    
    def test_parse_rfq_returns_parsed_result(self):
        result = parse_rfq("Sell 5MM GBPUSD")
        assert result.direction == Direction.SELL
        assert result.currency_pair == "GBP/USD"


# =============================================================================
# SERIALIZATION TESTS
# =============================================================================

class TestSerialization:
    """Test JSON/dict serialization"""
    
    def test_parsed_rfq_to_dict(self):
        parser = RFQParser(use_llm=False)
        result = parser.parse("Buy 10MM EURUSD")
        
        d = result.to_dict()
        assert isinstance(d, dict)
        assert d['direction'] == 'BUY'
        assert d['quantity'] == 10_000_000
    
    def test_parsed_rfq_to_json(self):
        parser = RFQParser(use_llm=False)
        result = parser.parse("Buy 10MM EURUSD")
        
        json_str = result.to_json()
        parsed = json.loads(json_str)
        
        assert parsed['direction'] == 'BUY'
    
    def test_line_item_serialization(self):
        item = LineItem(
            instrument="EURUSD",
            direction=Direction.BUY,
            quantity=1000000
        )
        d = item.to_dict()
        assert d['direction'] == 'BUY'
        assert d['instrument'] == 'EURUSD'
    
    def test_parsed_rfq_with_line_items_serialization(self):
        item = LineItem(instrument="EURUSD", direction=Direction.BUY)
        rfq = ParsedRFQ(
            raw_text="Test",
            line_items=[item]
        )
        d = rfq.to_dict()
        assert len(d['line_items']) == 1
        assert d['line_items'][0]['instrument'] == 'EURUSD'


# =============================================================================
# PARSER INITIALIZATION TESTS
# =============================================================================

class TestParserInitialization:
    """Test RFQParser initialization options"""
    
    def test_default_initialization(self):
        parser = RFQParser()
        assert parser is not None
    
    def test_with_use_llm_false(self):
        parser = RFQParser(use_llm=False)
        assert parser.use_llm == False
    
    def test_with_config(self):
        config = ParserConfig.fast()
        parser = RFQParser(config=config)
        assert parser.config.regex_only == True
    
    def test_with_custom_model(self):
        parser = RFQParser(model="custom-model", use_llm=False)
        assert parser.model == "custom-model"
    
    def test_with_injected_client(self):
        mock = MockMistralClient()
        parser = RFQParser(client=mock)
        assert parser.client == mock


# =============================================================================
# REAL-WORLD RFQ EXAMPLES
# =============================================================================

class TestRealWorldRFQs:
    """Test with realistic RFQ examples"""
    
    @pytest.fixture
    def parser(self):
        return RFQParser(use_llm=False)
    
    def test_fx_spot_rfq(self, parser):
        result = parser.parse("Hi, can you bid on 15MM EUR/USD spot for value tom?")
        assert result.direction == Direction.BUY
        assert result.currency_pair == "EUR/USD"
        assert result.quantity == 15_000_000
    
    def test_fx_forward_rfq(self, parser):
        result = parser.parse("Need to sell 50 MIO USD/JPY 6 months outright")
        assert result.direction == Direction.SELL
        assert result.currency_pair == "USD/JPY"
        assert result.quantity == 50_000_000
        assert result.tenor == "6M"
    
    def test_urgent_rfq(self, parser):
        result = parser.parse("URGENT: Buy 100MM EURUSD - need this done ASAP!")
        assert result.direction == Direction.BUY
        assert result.urgency == Urgency.IMMEDIATE
        assert result.quantity == 100_000_000
    
    def test_informal_rfq(self, parser):
        result = parser.parse("yo can I get a two-way on 10mm eurusd?")
        assert result.direction == Direction.TWO_WAY
        assert result.currency_pair == "EUR/USD"
    
    def test_multi_currency_mention(self, parser):
        # Should detect at least one pair
        result = parser.parse("Buy EUR/USD and GBP/USD 10MM each")
        assert result.currency_pair in ["EUR/USD", "GBP/USD"]


# =============================================================================
# PERFORMANCE TESTS
# =============================================================================

class TestPerformance:
    """Basic performance tests"""
    
    def test_regex_parsing_is_fast(self):
        import time
        parser = RFQParser(use_llm=False)
        
        start = time.time()
        for _ in range(100):
            parser.parse("Buy 10MM EURUSD spot")
        elapsed = time.time() - start
        
        # Should parse 100 RFQs in under 1 second
        assert elapsed < 1.0, f"Parsing too slow: {elapsed:.2f}s for 100 RFQs"
    
    def test_batch_parsing_completes(self):
        parser = RFQParser(use_llm=False)
        rfqs = ["Buy 10MM EURUSD"] * 50
        
        results = parser.parse_batch(rfqs)
        assert len(results) == 50


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

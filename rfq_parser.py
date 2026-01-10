"""
RFQ (Request for Quote) Parser using Mistral LLM
================================================
A robust parser for extracting structured data from free-form RFQ messages
commonly used in financial trading (FX, Fixed Income, Derivatives, etc.)

Single-file version with all classes included.
"""

import json
import re
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date
import os
import uuid

# Try importing mistralai - will gracefully handle if not installed
try:
    from mistralai import Mistral
    MISTRAL_AVAILABLE = True
except ImportError:
    MISTRAL_AVAILABLE = False
    Mistral = None

# Try importing C++ extension module
try:
    import rfq_cpp
    CPP_AVAILABLE = True
except ImportError:
    CPP_AVAILABLE = False
    rfq_cpp = None


# =============================================================================
# ENUMS
# =============================================================================

class Direction(Enum):
    BUY = "BUY"
    SELL = "SELL"
    TWO_WAY = "TWO_WAY"
    UNKNOWN = "UNKNOWN"


class AssetClass(Enum):
    FX_SPOT = "FX_SPOT"
    FX_FORWARD = "FX_FORWARD"
    FX_SWAP = "FX_SWAP"
    FX_OPTION = "FX_OPTION"
    BOND = "BOND"
    IRS = "INTEREST_RATE_SWAP"
    CDS = "CREDIT_DEFAULT_SWAP"
    EQUITY = "EQUITY"
    COMMODITY = "COMMODITY"
    UNKNOWN = "UNKNOWN"


class Urgency(Enum):
    IMMEDIATE = "IMMEDIATE"
    NORMAL = "NORMAL"
    EOD = "END_OF_DAY"
    UNKNOWN = "UNKNOWN"


class UrgencyLevel(Enum):
    """Alternative urgency enum with more granular levels"""
    CRITICAL = "CRITICAL"      # Needs immediate attention
    URGENT = "URGENT"          # ASAP
    HIGH = "HIGH"              # Within the hour
    NORMAL = "NORMAL"          # Standard turnaround
    LOW = "LOW"                # End of day / no rush
    UNKNOWN = "UNKNOWN"
    
    @classmethod
    def from_string(cls, value: str) -> 'UrgencyLevel':
        """Convert string to UrgencyLevel"""
        mapping = {
            'critical': cls.CRITICAL,
            'urgent': cls.URGENT,
            'asap': cls.URGENT,
            'immediate': cls.CRITICAL,
            'high': cls.HIGH,
            'normal': cls.NORMAL,
            'low': cls.LOW,
            'eod': cls.LOW,
            'end of day': cls.LOW,
        }
        return mapping.get(value.lower(), cls.UNKNOWN)


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ContactInfo:
    """Contact information for RFQ sender or recipient"""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    desk: Optional[str] = None              # e.g., "FX Trading", "Rates Desk"
    role: Optional[str] = None              # e.g., "Trader", "Sales", "PM"
    bloomberg_id: Optional[str] = None      # Bloomberg terminal ID
    reuters_id: Optional[str] = None        # Reuters dealing ID
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def is_empty(self) -> bool:
        """Check if contact info has any data"""
        return not any([self.name, self.email, self.phone, self.desk, 
                       self.role, self.bloomberg_id, self.reuters_id])


@dataclass
class CompanyInfo:
    """Company/counterparty information"""
    name: str = ""
    legal_entity: str = ""      # Legal entity name
    lei: str = ""               # Legal Entity Identifier
    country: str = ""
    sector: str = ""            # e.g., "Asset Manager", "Hedge Fund", "Corporate"
    relationship_manager: str = ""
    credit_rating: str = ""
    is_internal: bool = False   # Internal desk vs external client

    def __post_init__(self):
        if not self.name:
            raise ValueError("name is required")
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def is_empty(self) -> bool:
        """Check if company info has any data"""
        return not any([self.name, self.legal_entity, self.lei, 
                       self.country, self.sector])


@dataclass
class ParserConfig:
    """Configuration options for the RFQ parser"""
    # LLM settings
    use_llm: bool = True
    llm_model: str = "mistral-large-latest"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 2000
    llm_timeout: float = 30.0
    
    # Parsing behavior
    extract_contacts: bool = True
    extract_company: bool = True
    extract_line_items: bool = True
    default_currency: str = "USD"
    default_asset_class: AssetClass = AssetClass.UNKNOWN
    
    # Confidence thresholds
    min_confidence_threshold: float = 0.0  # Minimum confidence to return result
    high_confidence_threshold: float = 0.8
    
    # Regex fallback
    use_regex_fallback: bool = True
    regex_only: bool = False  # Force regex-only mode
    
    # Output options
    include_raw_text: bool = True
    include_timestamps: bool = True
    include_parsing_notes: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['default_asset_class'] = self.default_asset_class.value
        return result
    
    @classmethod
    def default(cls) -> 'ParserConfig':
        """Return default configuration"""
        return cls()
    
    @classmethod
    def fast(cls) -> 'ParserConfig':
        """Return fast config (regex only, no LLM)"""
        return cls(use_llm=False, regex_only=True)
    
    @classmethod
    def accurate(cls) -> 'ParserConfig':
        """Return high-accuracy config (LLM with lower temperature)"""
        return cls(use_llm=True, llm_temperature=0.05, min_confidence_threshold=0.5)


@dataclass
class LineItem:
    """
    Represents a single line item in a multi-item RFQ.
    Used when an RFQ contains multiple instruments or legs.
    """
    item_number: int = 1
    direction: Direction = Direction.UNKNOWN
    asset_class: AssetClass = AssetClass.UNKNOWN
    instrument: str = ""
    quantity: Optional[float] = None
    quantity_unit: str = ""
    unit: str = ""
    currency_pair: str = ""
    notional: Optional[float] = None
    notional_currency: str = ""
    settlement_date: Optional[str] = None
    tenor: str = ""
    strike: Optional[float] = None
    price: Optional[float] = None
    side: str = ""  # For swaps: "PAY" or "RECEIVE"
    rate: Optional[float] = None
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with enum values as strings"""
        result = asdict(self)
        result['direction'] = self.direction.value
        result['asset_class'] = self.asset_class.value
        return result


@dataclass
class ParsedRFQ:
    """Structured representation of a parsed RFQ"""
    raw_text: str
    rfq_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    direction: Direction = Direction.UNKNOWN
    asset_class: AssetClass = AssetClass.UNKNOWN
    instrument: str = ""
    quantity: Optional[float] = None
    quantity_unit: str = ""
    currency_pair: str = ""
    notional: Optional[float] = None
    notional_currency: str = ""
    settlement_date: Optional[str] = None
    tenor: str = ""
    strike: Optional[float] = None
    client_name: str = ""
    urgency: Urgency = Urgency.NORMAL
    urgency_level: UrgencyLevel = UrgencyLevel.NORMAL
    additional_terms: Dict[str, Any] = field(default_factory=dict)
    confidence_score: float = 0.0
    parsing_notes: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    line_items: List[LineItem] = field(default_factory=list)
    contact_info: Optional[ContactInfo] = None
    company_info: Optional[CompanyInfo] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with enum values as strings"""
        result = asdict(self)
        result['direction'] = self.direction.value
        result['asset_class'] = self.asset_class.value
        result['urgency'] = self.urgency.value
        result['urgency_level'] = self.urgency_level.value
        # Convert line items
        result['line_items'] = [item.to_dict() if hasattr(item, 'to_dict') else item for item in self.line_items]
        # Convert contact_info and company_info
        if self.contact_info:
            result['contact_info'] = self.contact_info.to_dict() if hasattr(self.contact_info, 'to_dict') else self.contact_info
        if self.company_info:
            result['company_info'] = self.company_info.to_dict() if hasattr(self.company_info, 'to_dict') else self.company_info
        return result

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=indent)

    def validate_with_cpp(self) -> Optional[Any]:
        """
        Validate this RFQ using C++ validator (if available)

        Returns:
            ValidationReport object from C++ if available, None otherwise
        """
        if not CPP_AVAILABLE:
            return None

        try:
            validator = rfq_cpp.SwapValidator()

            # Convert ParsedRFQ to dict for C++ validator
            data = {
                "direction": self.direction.value,
                "asset_class": self.asset_class.value,
                "instrument": self.instrument,
                "notional": str(self.notional) if self.notional else "",
                "notional_currency": self.notional_currency,
                "tenor": self.tenor,
                "urgency": self.urgency.value,
            }

            # Run validation
            results = validator.validate(data)

            # Add validation results to parsing notes
            if results:
                for result in results:
                    severity = "ERROR" if result.is_error() else ("WARNING" if result.is_warning() else "INFO")
                    note = f"[C++ {severity}] {result.field}: {result.message}"
                    if note not in self.parsing_notes:
                        self.parsing_notes.append(note)

            return rfq_cpp.ValidationReport(results) if results else None

        except Exception as e:
            self.parsing_notes.append(f"C++ validation error: {str(e)}")
            return None


# =============================================================================
# MOCK MISTRAL CLIENT (for testing)
# =============================================================================

@dataclass
class MockMessage:
    """Mock message response"""
    content: str
    role: str = "assistant"


@dataclass  
class MockChoice:
    """Mock choice in response"""
    message: MockMessage
    index: int = 0
    finish_reason: str = "stop"


@dataclass
class MockResponse:
    """Mock response from Mistral API"""
    choices: List[MockChoice]
    model: str = "mock-model"
    id: str = "mock-id"
    
    @classmethod
    def from_content(cls, content: str) -> 'MockResponse':
        """Create a mock response from content string"""
        return cls(
            choices=[MockChoice(message=MockMessage(content=content))]
        )


class MockMistralClient:
    """
    Mock Mistral client for testing without API calls.
    
    Provides deterministic responses for testing RFQ parsing
    without requiring actual API credentials.
    
    Usage:
        client = MockMistralClient()
        parser = RFQParser(client=client)
        result = parser.parse("Buy 10MM EURUSD")
    """
    
    def __init__(self, default_response: Optional[Dict[str, Any]] = None):
        """
        Initialize mock client.
        
        Args:
            default_response: Default JSON response to return for all requests
        """
        self.default_response = default_response or self._default_rfq_response()
        self.call_history: List[Dict[str, Any]] = []
        self.custom_responses: Dict[str, Dict[str, Any]] = {}

    @property
    def call_count(self) -> int:  # ADD - property instead of method
        return len(self.call_history)

    def parse_rfq(self, text: str) -> Dict[str, Any]:  # ADD THIS METHOD
        """Direct parsing method for testing"""
        return self._get_response_for_rfq(text)

    def _default_rfq_response(self) -> Dict[str, Any]:
        """Default RFQ parsing response"""
        return {
            "direction": "BUY",
            "asset_class": "FX_SPOT",
            "instrument": "EURUSD",
            "quantity": 10000000,
            "quantity_unit": "MM",
            "currency_pair": "EUR/USD",
            "urgency": "NORMAL",
            "confidence_score": 0.95,
            "parsing_notes": ["Parsed by MockMistralClient"]
        }
    
    def set_response(self, rfq_pattern: str, response: Dict[str, Any]) -> None:
        """
        Set a custom response for RFQs matching a pattern.
        
        Args:
            rfq_pattern: Substring to match in RFQ text
            response: JSON response to return
        """
        self.custom_responses[rfq_pattern.lower()] = response
    
    def _get_response_for_rfq(self, rfq_text: str) -> Dict[str, Any]:
        """Get appropriate response based on RFQ text"""
        rfq_lower = rfq_text.lower()
        
        # Check custom responses first
        for pattern, response in self.custom_responses.items():
            if pattern in rfq_lower:
                return response
        
        # Generate smart response based on content
        response = self.default_response.copy()
        
        # Detect direction
        if any(word in rfq_lower for word in ['sell', 'offer', 'short']):
            response['direction'] = 'SELL'
        elif any(word in rfq_lower for word in ['buy', 'bid', 'long']):
            response['direction'] = 'BUY'
        elif any(word in rfq_lower for word in ['two-way', '2-way', 'both']):
            response['direction'] = 'TWO_WAY'
        
        # Detect urgency
        if any(word in rfq_lower for word in ['urgent', 'asap', 'immediately']):
            response['urgency'] = 'IMMEDIATE'
        elif any(word in rfq_lower for word in ['eod', 'end of day']):
            response['urgency'] = 'END_OF_DAY'
        
        # Detect currency pairs
        pairs = ['eurusd', 'gbpusd', 'usdjpy', 'usdchf', 'audusd', 'nzdusd', 'usdcad']
        for pair in pairs:
            if pair in rfq_lower or f"{pair[:3]}/{pair[3:]}" in rfq_lower:
                response['currency_pair'] = f"{pair[:3].upper()}/{pair[3:].upper()}"
                response['instrument'] = pair.upper()
                break
        
        # Detect tenor (forward)
        tenor_match = re.search(r'(\d+)\s*(m|month|y|year|w|week|d|day)', rfq_lower)
        if tenor_match:
            num, unit = tenor_match.groups()
            unit_map = {'m': 'M', 'month': 'M', 'y': 'Y', 'year': 'Y', 
                       'w': 'W', 'week': 'W', 'd': 'D', 'day': 'D'}
            response['tenor'] = f"{num}{unit_map.get(unit, 'M')}"
            response['asset_class'] = 'FX_FORWARD'
        
        # Detect amount
        amount_match = re.search(r'(\d+(?:\.\d+)?)\s*(mm|m|k|b|mio|bn)?', rfq_lower)
        if amount_match:
            amount = float(amount_match.group(1))
            unit = (amount_match.group(2) or '').lower()
            multipliers = {'k': 1e3, 'm': 1e6, 'mm': 1e6, 'mio': 1e6, 'b': 1e9, 'bn': 1e9}
            response['quantity'] = amount * multipliers.get(unit, 1)
            response['quantity_unit'] = unit.upper() if unit else ''
        
        return response
    
    @property
    def chat(self):
        """Return self to mimic Mistral client structure"""
        return self
    
    def complete(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        response_format: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> MockResponse:
        """
        Mock the chat completion endpoint.
        """
        # Record the call
        self.call_history.append({
            'model': model,
            'messages': messages,
            'temperature': temperature
        })
        
        # Extract RFQ text from messages
        rfq_text = ""
        for msg in messages:
            if msg.get('role') == 'user':
                rfq_text = msg.get('content', '')
                break
        
        # Get response
        response_data = self._get_response_for_rfq(rfq_text)
        
        return MockResponse.from_content(json.dumps(response_data))
    
    def get_call_count(self) -> int:
        """Get number of API calls made"""
        return len(self.call_history)
    
    def get_last_call(self) -> Optional[Dict[str, Any]]:
        """Get the last API call made"""
        return self.call_history[-1] if self.call_history else None
    
    def reset(self) -> None:
        """Reset call history"""
        self.call_history = []


# =============================================================================
# RFQ PARSER
# =============================================================================

class RFQParser:
    """
    RFQ Parser with Mistral LLM backend
    
    Features:
    - Parses free-form RFQ messages from chat, email, or voice transcripts
    - Extracts structured fields using LLM understanding
    - Supports multiple asset classes (FX, Rates, Credit, etc.)
    - Provides confidence scoring and parsing notes
    - Falls back to regex patterns when LLM unavailable
    """
    
    # Default Mistral model - can be overridden
    DEFAULT_MODEL = "mistral-large-latest"
    
    # System prompt for Mistral
    SYSTEM_PROMPT = """You are an expert financial RFQ (Request for Quote) parser.
Your job is to extract structured information from free-form RFQ messages used in trading.

Extract the following fields when present:
- direction: BUY, SELL, or TWO_WAY (if asking for both sides)
- asset_class: FX_SPOT, FX_FORWARD, FX_SWAP, FX_OPTION, BOND, INTEREST_RATE_SWAP, CREDIT_DEFAULT_SWAP, EQUITY, COMMODITY, or UNKNOWN
- instrument: The specific instrument name (e.g., "EURUSD", "UST 10Y", "AAPL")
- quantity: Numeric quantity/amount
- quantity_unit: Unit for quantity (e.g., "MM", "K", "shares", "contracts")
- currency_pair: For FX, the currency pair (e.g., "EUR/USD")
- notional: Notional amount for derivatives
- notional_currency: Currency of the notional
- settlement_date: Settlement/value date if mentioned
- tenor: Tenor for forwards/swaps (e.g., "1M", "3M", "1Y")
- strike: Strike price for options
- client_name: Client/counterparty name if mentioned
- urgency: IMMEDIATE (urgent/ASAP), NORMAL, or END_OF_DAY
- additional_terms: Any other relevant terms as key-value pairs

Common abbreviations:
- MM = millions, K = thousands, B = billions
- T/N = tomorrow/next, S/N = spot/next, O/N = overnight
- IMM = IMM dates, MAT = maturity
- ATM = at-the-money, OTM = out-of-the-money, ITM = in-the-money

Respond ONLY with a valid JSON object containing the extracted fields.
If a field is not present or unclear, omit it or set to null.
Include a "confidence_score" (0.0-1.0) and "parsing_notes" array with any clarifications."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        use_llm: bool = True,
        config: Optional[ParserConfig] = None,
        client: Optional[Any] = None  # Allow injecting mock client
    ):
        """
        Initialize the RFQ Parser
        
        Args:
            api_key: Mistral API key (defaults to MISTRAL_API_KEY env var)
            model: Mistral model to use
            use_llm: Whether to use LLM (False = regex fallback only)
            config: ParserConfig object for detailed configuration
            client: Optional pre-configured client (for testing with MockMistralClient)
        """
        self.config = config or ParserConfig()
        self.model = model or self.config.llm_model
        self.use_llm = use_llm and not self.config.regex_only
        self.client = client  # Use injected client if provided
        
        # Initialize Mistral client if not injected
        if self.client is None and self.use_llm and MISTRAL_AVAILABLE:
            api_key = api_key or os.getenv("MISTRAL_API_KEY")
            if api_key:
                self.client = Mistral(api_key=api_key)
            else:
                self.use_llm = False
                print("Warning: No Mistral API key found. Using regex fallback.")

    def parse(self, rfq_text: str) -> ParsedRFQ:
        """
        Parse an RFQ message and return structured data
        
        Args:
            rfq_text: Free-form RFQ text
            
        Returns:
            ParsedRFQ object with extracted fields
        """
        rfq_text = rfq_text.strip()
        
        if self.use_llm and self.client:
            return self._parse_with_llm(rfq_text)
        else:
            return self._parse_with_regex(rfq_text)

    def _parse_with_llm(self, rfq_text: str) -> ParsedRFQ:
        """Parse RFQ using Mistral LLM"""
        try:
            # Handle both real Mistral client and MockMistralClient
            if hasattr(self.client, 'chat') and hasattr(self.client.chat, 'complete'):
                response = self.client.chat.complete(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.SYSTEM_PROMPT},
                        {"role": "user", "content": f"Parse this RFQ:\n\n{rfq_text}"}
                    ],
                    temperature=self.config.llm_temperature,
                    response_format={"type": "json_object"}
                )
            else:
                # MockMistralClient has complete directly
                response = self.client.complete(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.SYSTEM_PROMPT},
                        {"role": "user", "content": f"Parse this RFQ:\n\n{rfq_text}"}
                    ],
                    temperature=self.config.llm_temperature,
                    response_format={"type": "json_object"}
                )
            
            result_text = response.choices[0].message.content
            parsed_data = json.loads(result_text)
            
            return self._build_parsed_rfq(rfq_text, parsed_data)
            
        except Exception as e:
            # Fall back to regex on LLM failure
            result = self._parse_with_regex(rfq_text)
            result.parsing_notes.append(f"LLM parsing failed: {str(e)}. Used regex fallback.")
            return result

    def _parse_with_regex(self, rfq_text: str) -> ParsedRFQ:
        """Fallback regex-based parsing"""
        parsed = ParsedRFQ(raw_text=rfq_text)
        parsed.parsing_notes.append("Parsed using regex fallback (no LLM)")
        
        text_upper = rfq_text.upper()
        
        # Direction detection
        if any(word in text_upper for word in ['BUY', 'BID', 'LONG', 'MINE']):
            parsed.direction = Direction.BUY
        elif any(word in text_upper for word in ['SELL', 'OFFER', 'SHORT', 'YOURS']):
            parsed.direction = Direction.SELL
        elif any(word in text_upper for word in ['TWO-WAY', '2-WAY', 'BOTH SIDES']):
            parsed.direction = Direction.TWO_WAY
        
        # Currency pair detection (FX)
        valid_ccys = ['EUR', 'USD', 'GBP', 'JPY', 'CHF', 'AUD', 'NZD', 'CAD', 'CNY', 'HKD', 'SGD', 'NOK', 'SEK', 'DKK', 'MXN', 'ZAR']
        
        for ccy1 in valid_ccys:
            for ccy2 in valid_ccys:
                if ccy1 != ccy2:
                    patterns = [
                        rf'\b{ccy1}/{ccy2}\b',
                        rf'\b{ccy1}{ccy2}\b',
                        rf'\b{ccy1}\s+{ccy2}\b',
                    ]
                    for pattern in patterns:
                        if re.search(pattern, text_upper):
                            parsed.currency_pair = f"{ccy1}/{ccy2}"
                            parsed.instrument = f"{ccy1}{ccy2}"
                            parsed.asset_class = AssetClass.FX_SPOT
                            break
                    if parsed.currency_pair:
                        break
            if parsed.currency_pair:
                break
        
        # Amount detection
        amount_pattern = r'(\d+(?:\.\d+)?)\s*(MM|M|K|B|MIO|MLN|BN)?\b'
        amount_match = re.search(amount_pattern, rfq_text, re.IGNORECASE)
        if amount_match:
            amount = float(amount_match.group(1))
            unit = (amount_match.group(2) or '').upper()
            
            multipliers = {'K': 1e3, 'M': 1e6, 'MM': 1e6, 'MIO': 1e6, 'MLN': 1e6, 'B': 1e9, 'BN': 1e9}
            if unit in multipliers:
                parsed.quantity = amount * multipliers[unit]
                parsed.quantity_unit = unit
            else:
                parsed.quantity = amount
        
        # Tenor detection
        tenor_pattern = r'\b(\d+)\s*(D|W|M|Y|DAY|WEEK|MONTH|YEAR)S?\b'
        tenor_match = re.search(tenor_pattern, rfq_text, re.IGNORECASE)
        if tenor_match:
            num, unit = tenor_match.groups()
            unit_map = {'D': 'D', 'DAY': 'D', 'W': 'W', 'WEEK': 'W', 
                       'M': 'M', 'MONTH': 'M', 'Y': 'Y', 'YEAR': 'Y'}
            parsed.tenor = f"{num}{unit_map.get(unit.upper(), unit.upper())}"
            if parsed.asset_class == AssetClass.FX_SPOT:
                parsed.asset_class = AssetClass.FX_FORWARD
        
        # Urgency detection
        if any(word in text_upper for word in ['URGENT', 'ASAP', 'NOW', 'IMMEDIATELY']):
            parsed.urgency = Urgency.IMMEDIATE
            parsed.urgency_level = UrgencyLevel.URGENT
        elif any(word in text_upper for word in ['EOD', 'END OF DAY', 'CLOSE']):
            parsed.urgency = Urgency.EOD
            parsed.urgency_level = UrgencyLevel.LOW
        
        # Confidence based on fields extracted
        fields_found = sum([
            parsed.direction != Direction.UNKNOWN,
            parsed.asset_class != AssetClass.UNKNOWN,
            bool(parsed.instrument),
            parsed.quantity is not None,
            bool(parsed.currency_pair)
        ])
        parsed.confidence_score = min(fields_found / 5, 1.0)
        
        return parsed

    def _build_parsed_rfq(self, raw_text: str, data: Dict[str, Any]) -> ParsedRFQ:
        """Build ParsedRFQ from LLM response data"""

        # Map direction
        direction_str = data.get('direction', '').upper()
        direction_map = {
            'BUY': Direction.BUY,
            'SELL': Direction.SELL,
            'TWO_WAY': Direction.TWO_WAY,
            '2WAY': Direction.TWO_WAY
        }
        direction = direction_map.get(direction_str, Direction.UNKNOWN)

        # Map asset class
        asset_str = data.get('asset_class', '').upper().replace(' ', '_')
        asset_map = {
            'FX_SPOT': AssetClass.FX_SPOT,
            'FX_FORWARD': AssetClass.FX_FORWARD,
            'FX_SWAP': AssetClass.FX_SWAP,
            'FX_OPTION': AssetClass.FX_OPTION,
            'BOND': AssetClass.BOND,
            'INTEREST_RATE_SWAP': AssetClass.IRS,
            'IRS': AssetClass.IRS,
            'CREDIT_DEFAULT_SWAP': AssetClass.CDS,
            'CDS': AssetClass.CDS,
            'EQUITY': AssetClass.EQUITY,
            'COMMODITY': AssetClass.COMMODITY
        }
        asset_class = asset_map.get(asset_str, AssetClass.UNKNOWN)

        # Map urgency
        urgency_str = data.get('urgency', '').upper()
        urgency_map = {
            'IMMEDIATE': Urgency.IMMEDIATE,
            'NORMAL': Urgency.NORMAL,
            'END_OF_DAY': Urgency.EOD,
            'EOD': Urgency.EOD
        }
        urgency = urgency_map.get(urgency_str, Urgency.NORMAL)

        # Map urgency level
        urgency_level = UrgencyLevel.from_string(urgency_str) if urgency_str else UrgencyLevel.NORMAL

        parsed = ParsedRFQ(
            raw_text=raw_text,
            direction=direction,
            asset_class=asset_class,
            instrument=data.get('instrument', ''),
            quantity=data.get('quantity'),
            quantity_unit=data.get('quantity_unit', ''),
            currency_pair=data.get('currency_pair', ''),
            notional=data.get('notional'),
            notional_currency=data.get('notional_currency', ''),
            settlement_date=data.get('settlement_date'),
            tenor=data.get('tenor', ''),
            strike=data.get('strike'),
            client_name=data.get('client_name', ''),
            urgency=urgency,
            urgency_level=urgency_level,
            additional_terms=data.get('additional_terms', {}),
            confidence_score=data.get('confidence_score', 0.8),
            parsing_notes=data.get('parsing_notes', [])
        )

        # Run C++ validation if available
        if CPP_AVAILABLE:
            parsed.validate_with_cpp()

        return parsed

    def parse_batch(self, rfq_texts: List[str]) -> List[ParsedRFQ]:
        """Parse multiple RFQ messages"""
        return [self.parse(text) for text in rfq_texts]


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def parse_rfq(text: str, api_key: Optional[str] = None) -> ParsedRFQ:
    """Quick function to parse a single RFQ"""
    parser = RFQParser(api_key=api_key)
    return parser.parse(text)


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__version__ = "0.1.0"
__all__ = [
    # Core parser
    "RFQParser",
    "ParsedRFQ",
    "parse_rfq",
    # Data classes
    "LineItem",
    "ContactInfo",
    "CompanyInfo",
    "ParserConfig",
    # Enums
    "Direction",
    "AssetClass",
    "Urgency",
    "UrgencyLevel",
    # Mock client for testing
    "MockMistralClient",
    "MockResponse",
    "MockChoice",
    "MockMessage",
    # Availability flags
    "MISTRAL_AVAILABLE",
    "CPP_AVAILABLE",
]


# =============================================================================
# DEMO
# =============================================================================

if __name__ == "__main__":
    # Demo usage
    sample_rfqs = [
        "Buy 10MM EURUSD spot",
        "Need a price on 5M EUR/USD 1M forward",
        "Can I get a two-way on 100MM UST 10Y? Need this ASAP",
        "Selling 50K AAPL shares at market",
        "Looking to buy 25MM notional 5Y IRS receiving fixed USD"
    ]
    
    parser = RFQParser(use_llm=False)  # Use regex for demo
    
    print("=" * 60)
    print("RFQ Parser Demo (Regex Mode)")
    print("=" * 60)
    
    for rfq in sample_rfqs:
        print(f"\nInput: {rfq}")
        result = parser.parse(rfq)
        print(f"Direction: {result.direction.value}")
        print(f"Asset Class: {result.asset_class.value}")
        print(f"Instrument: {result.instrument}")
        print(f"Quantity: {result.quantity}")
        print(f"Confidence: {result.confidence_score:.0%}")
        print("-" * 40)

# RFQ Parser

> 🎯 Parse free-form Request for Quote messages into structured data using Mistral LLM

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-147%20passed-brightgreen.svg)](#-testing)

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/rfq_parser_app.git
cd rfq_parser_app

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest rfq_parser_tests.py app_tests.py -v

# Launch demo
streamlit run app.py
```

**No API key required!** The parser works out-of-the-box with regex mode.

## 💡 Features

- **LLM-Powered Parsing**: Uses Mistral Large for semantic understanding
- **Regex Fallback**: Works without API key for common patterns
- **Multi-Asset Support**: FX Spot, FX Forward, Bonds, IRS, CDS, Equities
- **Confidence Scoring**: Know how reliable the parse is
- **Batch Processing**: Parse multiple RFQs at once
- **Visual Demo**: Interactive Streamlit interface
- **Mock Client**: Test without API calls using `MockMistralClient`
- **🚀 C++ Extensions**: High-performance validation and derivatives pricing (see [cpp/README.md](cpp/README.md))

## 📖 Usage

### Basic Parsing (No API Key Needed)

```python
from rfq_parser import RFQParser, parse_rfq

# Quick parse (uses regex - no API key required)
result = parse_rfq("Buy 10MM EUR/USD spot")
print(result.direction)      # Direction.BUY
print(result.quantity)       # 10000000.0
print(result.currency_pair)  # EUR/USD
print(result.confidence_score)  # 1.0
```

### With Mistral LLM

```python
from rfq_parser import RFQParser

# With Mistral LLM (requires API key)
parser = RFQParser(api_key="your-mistral-key", use_llm=True)
result = parser.parse("Need two-way on 50 MIO GBPUSD 3M forward, ASAP!")
print(result.to_json())
```

### Using Mock Client (For Testing)

```python
from rfq_parser import RFQParser, MockMistralClient

# Use mock client - no API calls, deterministic responses
mock = MockMistralClient()
parser = RFQParser(client=mock, use_llm=True)
result = parser.parse("Sell 25MM USDJPY")
print(result.direction)  # Direction.SELL
```

### Output Structure

```json
{
  "raw_text": "Buy 10MM EUR/USD spot",
  "rfq_id": "550e8400-e29b-41d4-a716-446655440000",
  "direction": "BUY",
  "asset_class": "FX_SPOT",
  "instrument": "EURUSD",
  "quantity": 10000000,
  "quantity_unit": "MM",
  "currency_pair": "EUR/USD",
  "urgency": "NORMAL",
  "urgency_level": "NORMAL",
  "confidence_score": 1.0,
  "parsing_notes": ["Parsed using regex fallback (no LLM)"]
}
```

### Batch Processing

```python
parser = RFQParser(use_llm=False)
rfqs = [
    "Buy 10MM EURUSD",
    "Sell 5MM GBPUSD",
    "Two-way on USDJPY 3M"
]
results = parser.parse_batch(rfqs)
for r in results:
    print(f"{r.direction.value}: {r.currency_pair}")
```

### 🚀 C++ Components (Advanced)

High-performance C++ extensions for interest rate derivatives:

```python
import rfq_cpp
from rfq_parser import CPP_AVAILABLE

# Check if C++ module is available
print(f"C++ extensions: {CPP_AVAILABLE}")

# Create interest rate swap
pay_leg = (rfq_cpp.SwapLeg.builder()
           .with_currency("USD")
           .with_notional(10_000_000)
           .with_fixed_rate(0.05)
           .with_day_count(rfq_cpp.DayCountConvention.ACT_360)
           .build())

receive_leg = (rfq_cpp.SwapLeg.builder()
               .with_currency("USD")
               .with_notional(10_000_000)
               .with_floating_index(rfq_cpp.FloatingIndex.SOFR)
               .build())

swap = rfq_cpp.InterestRateSwap.create_vanilla_swap(
    pay_leg, receive_leg, "5Y", "2024-01-15"
)

# Create Bermudan swaption
exercise_dates = ["2025-01-01", "2026-01-01", "2027-01-01"]
swaption = rfq_cpp.Swaption.create_bermudan(
    rfq_cpp.SwaptionType.PAYER,
    swap,
    "2027-12-31",
    0.05,
    exercise_dates
)

# Validate RFQ data
validator = rfq_cpp.SwapValidator()
results = validator.validate({
    "direction": "PAY",
    "currency": "USD",
    "notional": "10000000",
    "tenor": "5Y"
})
```

**See [cpp/README.md](cpp/README.md) and [example_cpp_usage.py](example_cpp_usage.py) for complete examples.**

## 🧪 Testing

### Python Tests
```bash
# Run all tests (147 tests)
pytest rfq_parser_tests.py app_tests.py -v

# Run parser tests only (107 tests)
pytest rfq_parser_tests.py -v

# Run app tests only (40 tests)
pytest app_tests.py -v

# With coverage report
pytest rfq_parser_tests.py app_tests.py --cov=. --cov-report=html

# Run specific test category
pytest rfq_parser_tests.py -k "direction" -v
```

### C++ Tests
```bash
# Build and run C++ tests (Windows)
cd cpp
build.bat

# Build and run C++ tests (Linux/Mac)
cd cpp
chmod +x build.sh
./build.sh

# Or manually with CMake
cd cpp/build
ctest -V
```

### Test Coverage

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `rfq_parser_tests.py` | 107 | Parser, models, enums, mock client |
| `app_tests.py` | 40 | Streamlit app, utilities, formatting |
| **Total** | **147** | All components |

## 🎨 Demo

Launch the interactive Streamlit demo:

```bash
# Set API key (optional - regex works without it)
export MISTRAL_API_KEY="your-key"

# Run Streamlit app
streamlit run app.py
```

### Demo Features

| Feature | Description |
|---------|-------------|
| **Single Parse** | Parse one RFQ with visual output |
| **Sample RFQs** | Pre-loaded examples for testing |
| **Visual Metrics** | Color-coded direction, confidence |
| **JSON Export** | View structured output |
| **Batch Mode** | Parse multiple RFQs in table view |
| **Architecture View** | System diagram in expandable panel |

## 📊 Supported Fields

| Field | Description | Example |
|-------|-------------|---------|
| `direction` | BUY, SELL, TWO_WAY | `Direction.BUY` |
| `asset_class` | FX_SPOT, FX_FORWARD, BOND, etc. | `AssetClass.FX_SPOT` |
| `instrument` | Trading instrument | `"EURUSD"` |
| `quantity` | Amount | `10000000` |
| `quantity_unit` | Unit notation | `"MM"` |
| `currency_pair` | FX pair | `"EUR/USD"` |
| `tenor` | Forward tenor | `"3M"` |
| `settlement_date` | Value date | `"2024-03-15"` |
| `strike` | Option strike | `1.0850` |
| `urgency` | IMMEDIATE, NORMAL, EOD | `Urgency.IMMEDIATE` |
| `urgency_level` | CRITICAL, URGENT, HIGH, NORMAL, LOW | `UrgencyLevel.URGENT` |
| `confidence_score` | Parse reliability (0-1) | `0.95` |

## 🔧 Available Classes

```python
from rfq_parser import (
    # Core
    RFQParser,              # Main parser class
    ParsedRFQ,              # Parsed result
    parse_rfq,              # Quick parse function
    
    # Data classes
    LineItem,               # Multi-item RFQ support
    ContactInfo,            # Sender/recipient info
    CompanyInfo,            # Counterparty info
    ParserConfig,           # Parser configuration
    
    # Enums
    Direction,              # BUY, SELL, TWO_WAY
    AssetClass,             # FX_SPOT, BOND, etc.
    Urgency,                # IMMEDIATE, NORMAL, EOD
    UrgencyLevel,           # CRITICAL, URGENT, HIGH, NORMAL, LOW
    
    # Testing
    MockMistralClient,      # Mock for testing without API
)
```

## 🗺️ Roadmap

See [ROADMAP.md](ROADMAP.md) for the full development plan.

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1: Core Parser | ✅ Complete | Parser, models, regex fallback |
| Phase 2: Visual Demo | ✅ Complete | Streamlit app, batch processing |
| Phase 3: API Service | 📋 Planned | FastAPI, Docker |
| Phase 4: Advanced Features | 📋 Planned | Voice-to-RFQ, multi-asset |
| Phase 5: Enterprise | 📋 Planned | Monitoring, audit, multi-tenant |

## 📁 Project Structure

```
rfq_parser_app/
├── rfq_parser.py           # Core parser module
├── rfq_parser_tests.py     # Parser test suite (107 tests)
├── app.py                  # Streamlit demo application
├── app_tests.py            # App test suite (40 tests)
├── example_cpp_usage.py    # C++ integration examples
├── setup.py                # Installation with C++ extension
├── README.md               # This file
├── ROADMAP.md              # Development roadmap
├── requirements.txt        # Dependencies
├── screenshots/            # Demo screenshots
└── cpp/                    # C++ components (see cpp/README.md)
    ├── include/rfq/        # Header files
    │   ├── swap_leg.hpp
    │   ├── interest_rate_swap.hpp
    │   ├── swaption.hpp
    │   ├── swap_validator.hpp
    │   └── thread_safe_queue.hpp
    ├── src/                # Implementation files
    ├── bindings/           # pybind11 Python bindings
    ├── tests/              # Catch2 C++ tests
    ├── CMakeLists.txt      # Build configuration
    ├── build.bat/.sh       # Build scripts
    └── README.md           # C++ documentation
```

## 📦 Dependencies

```txt
mistralai>=1.0.0      # LLM integration (optional)
pytest>=7.0.0         # Testing
streamlit>=1.28.0     # Demo UI
```

## 🔧 Configuration

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `MISTRAL_API_KEY` | Mistral API key | None (uses regex) |

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/amazing`)
3. Run tests (`pytest rfq_parser_tests.py app_tests.py -v`)
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push (`git push origin feature/amazing`)
6. Open a Pull Request

## 📄 License

MIT License - see LICENSE for details.

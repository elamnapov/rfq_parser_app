# RFQ Parser

> 🎯 Parse free-form Request for Quote messages into structured data using Mistral LLM

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Launch demo
streamlit run demo/app.py
```

## 💡 Features

- **LLM-Powered Parsing**: Uses Mistral Large for semantic understanding
- **Regex Fallback**: Works without API key for common patterns
- **Multi-Asset Support**: FX, Rates, Credit, Equities
- **Confidence Scoring**: Know how reliable the parse is
- **Batch Processing**: Parse multiple RFQs at once
- **Visual Demo**: Interactive Streamlit interface

## 📖 Usage

### Basic Parsing

```python
from rfq_parser import RFQParser, parse_rfq

# Quick parse (uses regex fallback if no API key)
result = parse_rfq("Buy 10MM EUR/USD spot")
print(result.direction)     # Direction.BUY
print(result.quantity)      # 10000000.0
print(result.currency_pair) # EUR/USD

# With Mistral LLM
parser = RFQParser(api_key="your-mistral-key")
result = parser.parse("Need two-way on 50 MIO GBPUSD 3M forward, ASAP!")
print(result.to_json())
```

### Output Structure

```json
{
  "raw_text": "Buy 10MM EUR/USD spot",
  "direction": "BUY",
  "asset_class": "FX_SPOT",
  "instrument": "EURUSD",
  "quantity": 10000000,
  "quantity_unit": "MM",
  "currency_pair": "EUR/USD",
  "urgency": "NORMAL",
  "confidence_score": 0.85
}
```

### Batch Processing

```python
parser = RFQParser()
rfqs = [
    "Buy 10MM EURUSD",
    "Sell 5MM GBPUSD",
    "Two-way on USDJPY 3M"
]
results = parser.parse_batch(rfqs)
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# With coverage report
pytest tests/ --cov=src --cov-report=html

# Run specific tests
pytest tests/ -k "direction" -v
```

## 🎨 Demo

Launch the interactive demo:

```bash
# Set API key (optional)
export MISTRAL_API_KEY="your-key"

# Run Streamlit app
streamlit run demo/app.py
```

Demo features:
- Single RFQ parsing with visual output
- Pre-loaded sample RFQs
- Batch processing mode
- JSON export
- Architecture diagram

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
| `confidence_score` | Parse reliability (0-1) | `0.95` |

## 🗺️ Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md) for the full development plan.

**Current Phase:** Core Parser + Visual Demo ✅  
**Next Phase:** FastAPI Service

## 📁 Project Structure

```
rfq_parser/
├── src/
│   └── rfq_parser.py      # Core parser
├── tests/
│   └── test_rfq_parser.py # Test suite
├── demo/
│   └── app.py             # Streamlit demo
├── docs/
│   └── ROADMAP.md         # Development roadmap
└── requirements.txt       # Dependencies
```

## 🔧 Configuration

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `MISTRAL_API_KEY` | Mistral API key | None (uses regex) |

## 📄 License

MIT License - see LICENSE for details.

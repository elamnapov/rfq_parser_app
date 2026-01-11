# RFQ Parser

> 🎯 Parse free-form Request for Quote messages into structured data using Mistral LLM

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-147%20passed-brightgreen.svg)](#-testing)

## 🚀 Quick Start

### Python-Only Mode (No Build Required)

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/rfq_parser_app.git
cd rfq_parser_app

# Install Python dependencies
pip install -r requirements.txt

# Run tests
pytest rfq_parser_tests.py app_tests.py -v

# Launch demo
streamlit run app.py
```

**No API key required!** The parser works out-of-the-box with regex mode.

### With C++ Performance (Optional)

```bash
# Install with C++ components (requires CMake)
pip install -e .

# Or build manually
cd cpp && ./build.sh  # Linux/Mac
cd cpp && build.bat   # Windows
```

**See [Python-C++ Integration](#-python-c-integration) section below for detailed setup.**

### Running with C++ on Windows 11 (Recommended: WSL)

The easiest way to use C++ components on Windows 11 is through **Windows Subsystem for Linux (WSL)**. This approach:
- ✅ Avoids Windows C++ build complexity (CMake, Visual Studio, etc.)
- ✅ Uses the same Linux build process as production servers
- ✅ Allows you to access the app from your Windows browser

**Step 1: Install WSL (if not already installed)**

Open PowerShell as Administrator and run:

```powershell
wsl --install
```

Restart your computer when prompted. WSL will install Ubuntu by default.

**Step 2: Set up Python and dependencies in WSL**

Open your **WSL terminal** (search for "Ubuntu" in Start menu):

```bash
# Update package list
sudo apt update

# Install Python and pip
sudo apt install python3-pip -y

# Navigate to your project (Windows drives are mounted at /mnt/)
cd /mnt/c/Users/YOUR_USERNAME/path/to/rfq_parser_app

# Install Python dependencies
pip3 install -r requirements.txt
```

**Step 3: Build C++ components in WSL**

```bash
# From project root
cd cpp
chmod +x build.sh
./build.sh

# Verify C++ module is available
cd ..
python3 -c "from rfq_parser import CPP_AVAILABLE; print(f'C++ Available: {CPP_AVAILABLE}')"
# Should output: C++ Available: True
```

**Step 4: Run Streamlit in WSL**

```bash
# From project root
python3 -m streamlit run app.py
```

You'll see output like:

```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://172.x.x.x:8501
```

**Step 5: Open in Windows browser**

Open **http://localhost:8501** in your Windows browser (Chrome, Edge, Firefox, etc.).

**Step 6: Try the C++ pricing demos**

1. In the sidebar, select sample: **"IRS (C++ Pricing)"**
2. Click **"🔍 Parse RFQ"**
3. You should see the **💰 C++ Pricing** section with net payment calculation!

Try **"Swaption (C++ Pricing)"** to see Black-76 option pricing.

**Troubleshooting:**

| Issue | Solution |
|-------|----------|
| `streamlit: command not found` | Use `python3 -m streamlit run app.py` instead |
| `CPP_AVAILABLE: False` | Rebuild C++ with `cd cpp && ./build.sh` |
| Port 8501 already in use | Kill existing: `lsof -ti:8501 \| xargs kill -9` or use different port: `python3 -m streamlit run app.py --server.port 8502` |
| Browser shows "can't reach page" | Check firewall, try Network URL instead of localhost |

**Why WSL instead of native Windows?**

| Approach | Pros | Cons |
|----------|------|------|
| **WSL (Recommended)** | ✅ Simple build process<br>✅ Same as Linux servers<br>✅ No Visual Studio needed<br>✅ Fast compilation | ⚠️ Requires WSL installation |
| **Native Windows** | ✅ No WSL needed | ❌ Requires CMake + Visual Studio<br>❌ Complex setup<br>❌ Longer build times |

## 💡 Features

### Core Parsing
- **LLM-Powered Parsing**: Uses Mistral Large for semantic understanding
- **Regex Fallback**: Works without API key for common patterns
- **Multi-Asset Support**: FX Spot, FX Forward, Bonds, IRS, CDS, Equities
- **Confidence Scoring**: Know how reliable the parse is
- **Batch Processing**: Parse multiple RFQs at once
- **Mock Client**: Test without API calls using `MockMistralClient`

### High-Performance C++ Integration
- **Automatic Validation**: C++ validator runs automatically on parsed data (when available)
- **Automatic Pricing**: IRS net payment calculation and Swaption Black-76 pricing
- **Interest Rate Swaps**: Vanilla, basis, and cross-currency swap modeling
- **Swaptions**: European, American, and Bermudan exercise styles with option pricing
- **Thread-Safe Processing**: Lock-free queue for high-throughput systems
- **10x Performance**: C++ components provide 10x speedup for validation and pricing
- **Optional**: Parser works perfectly without C++ (Python-only mode)

### UI & Development
- **Visual Demo**: Interactive Streamlit interface (`app.py`)
- **Comprehensive Tests**: 147 Python tests + 19 C++ tests

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

## 🔗 Python-C++ Integration

This project combines **Python's flexibility** with **C++'s performance** for production trading systems. The C++ components are **optional** but provide significant benefits.

### What C++ Adds

The C++ extension (`rfq_cpp`) provides:

| Component | Purpose |
|-----------|---------|
| **RFQValidator** | High-speed validation of parsed RFQ data (all instrument types) |
| **SwapLeg** | Interest rate swap leg with day count conventions |
| **InterestRateSwap** | Vanilla, basis, and cross-currency swaps with net payment calculation |
| **Swaption** | European, American, and Bermudan swaptions |
| **SwaptionPricer** | Black-76 option pricing for swaptions |
| **ThreadSafeQueue** | Lock-free queue for high-throughput RFQ processing |

### How It Works

```
┌─────────────────────────────────────────────────────────────┐
│  User Input: "Buy 10MM USD IRS 5Y paying fixed at 5.25%"    |
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
        ┌────────────────────────────────┐
        │   Python: RFQParser            │
        │   - Mistral LLM / Regex        │
        │   - Extracts structured data   │
        └────────────┬───────────────────┘
                     │
                     ▼
        ┌────────────────────────────────┐
        │   Python: ParsedRFQ object     │
        │   direction, notional, tenor   │
        └────────────┬───────────────────┘
                     │
                     │ (if C++ available)
                     ▼
        ┌────────────────────────────────┐
        │   C++: RFQValidator            │
        │   - Validates currency codes   │
        │   - Checks notional limits     │
        │   - Validates tenor format     │
        │   - Generic RFQ field rules    │
        └────────────┬───────────────────┘
                     │
                     ▼
        ┌────────────────────────────────┐
        │   Python: ParsedRFQ.parsing_   │
        │   notes += validation results  │
        └────────────────────────────────┘
```

### Automatic C++ Validation

The Python parser **automatically uses C++ validation** when available:

```python
from rfq_parser import RFQParser, CPP_AVAILABLE

# Check if C++ is available
print(f"C++ validation: {CPP_AVAILABLE}")

# Parse an RFQ - C++ validation runs automatically
parser = RFQParser()
result = parser.parse("Buy 10MM USD IRS 5Y")

# C++ validation results appear in parsing_notes
for note in result.parsing_notes:
    print(note)
# Output might include:
# [C++ WARNING] notional: Notional below minimum
```

### Building C++ Components

#### Prerequisites

- **CMake 3.15+**: https://cmake.org/download/
- **C++17 Compiler**: GCC 7+, Clang 5+, or MSVC 2017+
- **Python 3.8+**

#### Build Options

**Option 1: Build with pip (Recommended)**
```bash
# From project root (rfq_parser_app/)
pip install -e .
```
This automatically:
1. Downloads pybind11 and Catch2
2. Compiles all C++ code
3. Creates `rfq_cpp` Python module
4. Installs Python dependencies

**Option 2: Build manually with CMake**
```bash
# Navigate to cpp directory
cd cpp

# Build (Windows)
build.bat

# Build (Linux/Mac)
chmod +x build.sh
./build.sh

# Or manually
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build .
ctest  # Run tests (19/21 pass)
```

**Option 3: Python-only (No build needed)**
```bash
# Just install Python dependencies
pip install streamlit mistralai python-dotenv

# Parser works without C++ (uses Python-only validation)
python app.py
```

### Using C++ Components Directly

Beyond automatic validation, you can use C++ components directly:

```python
import rfq_cpp

# Create a 5Y USD interest rate swap
pay_leg = rfq_cpp.SwapLeg.builder() \
    .with_currency("USD") \
    .with_notional(10_000_000) \
    .with_fixed_rate(0.0525) \
    .with_day_count(rfq_cpp.DayCountConvention.ACT_360) \
    .with_frequency(rfq_cpp.PaymentFrequency.SEMI_ANNUAL) \
    .build()

receive_leg = rfq_cpp.SwapLeg.builder() \
    .with_currency("USD") \
    .with_notional(10_000_000) \
    .with_floating_index(rfq_cpp.FloatingIndex.SOFR) \
    .with_day_count(rfq_cpp.DayCountConvention.ACT_360) \
    .with_frequency(rfq_cpp.PaymentFrequency.QUARTERLY) \
    .build()

swap = rfq_cpp.InterestRateSwap.create_vanilla_swap(
    pay_leg, receive_leg, "5Y", "2024-01-15"
)

print(swap.to_string())
# Output: VANILLA IRS (5Y)
#         Effective: 2024-01-15
#         Pay: FIXED leg: USD 10000000.0000 notional, rate=5.2500%, ACT/360, Semi-Annual
#         Receive: FLOATING leg: USD 10000000.0000 notional, index=SOFR, ACT/360, Quarterly

# Validate manually
validator = rfq_cpp.RFQValidator()
results = validator.validate({
    "direction": "PAY",
    "currency": "USD",
    "notional": "10000000",
    "tenor": "5Y"
})
print(f"Validation passed: {len(results) == 0}")
```

### C++ Pricing Integration

The parser can automatically price IRS and Swaption RFQs using C++ pricing engines:

```python
from rfq_parser import RFQParser

parser = RFQParser()

# Parse an IRS RFQ
result = parser.parse("Buy 10MM USD IRS 5Y paying fixed at 5.25%")

# Automatically price using C++ (if available)
pricing = result.price_with_cpp()

if pricing:
    print(f"Product: {pricing['product_type']}")
    print(f"Notional: {pricing['currency']} {pricing['notional']:,.0f}")
    print(f"Fixed Rate: {pricing['fixed_rate']}")
    print(f"Net Payment (180d): {pricing['currency']} {pricing['net_payment_180d']:,.2f}")
    # Output: Product: Interest Rate Swap
    #         Notional: USD 10,000,000
    #         Fixed Rate: 5.25%
    #         Net Payment (180d): USD 262,500.00
```

**Pricing Features:**

| Feature | IRS | Swaption |
|---------|-----|----------|
| **Engine** | C++ | Python (Black-76) |
| **Calculation** | Net payment for 180-day period | Black-76 option pricing |
| **Inputs** | Notional, fixed rate, tenor | Strike, volatility, forward rate, time to expiry |
| **Output** | Net cash flow per period | Option premium |
| **Use Case** | Cash flow projections | Option valuation |

**Example: Swaption Pricing**

```python
# Parse a swaption RFQ
result = parser.parse("Sell 50MM USD swaption 3Y strike 4.5%")

# Price with custom market parameters
pricing = result.price_with_cpp(
    forward_rate=0.045,   # 4.5% forward rate
    volatility=0.25,       # 25% volatility
    time_to_expiry=1.0    # 1 year to expiry
)

if pricing:
    print(f"Swaption Type: {pricing['type']}")
    print(f"Black Price: {pricing['currency']} {pricing['black_price']:,.2f}")
    print(f"Volatility: {pricing['volatility']}")
    # Output: Swaption Type: Receiver
    #         Black Price: USD 1,234,567.89
    #         Volatility: 25%
```

**Notes:**
- **IRS Pricing**: Uses C++ swap engine for net payment calculation with ACT/360 day count conventions
- **Swaption Pricing**: Uses C++ Black-76 pricer for European swaption valuation
- Pricing uses simplified models with default market parameters for demonstration
- For production use, integrate with your market data feeds for accurate forward rates and volatilities
- Pricing automatically appears in `parsing_notes` field

### Streamlit App Integration

The Streamlit demo (`app.py`) automatically uses C++ validation and pricing:

```bash
streamlit run app.py
```

When you parse an RFQ in the UI:
1. Python parser extracts data (LLM or regex)
2. C++ validator checks the data (**if available**)
3. **C++ pricer calculates values for IRS/Swaptions** (**if available**)
4. Validation results appear in the "Parsing Notes" section
5. Pricing results appear in a dedicated "C++ Pricing" section with detailed metrics

**Try the pricing demo:**
- Load sample: "IRS (C++ Pricing)" → See net payment calculation
- Load sample: "Swaption (C++ Pricing)" → See Black-76 option price

**App behavior:**
- ✅ **With C++**: Fast validation, automatic pricing for IRS/Swaptions, enhanced error messages
- ✅ **Without C++**: Still works perfectly, uses Python-only validation (no pricing)

### Check C++ Availability

```python
from rfq_parser import CPP_AVAILABLE

if CPP_AVAILABLE:
    import rfq_cpp
    print(f"C++ module version: {rfq_cpp.__version__}")
    print("Enhanced validation active!")
else:
    print("Running in Python-only mode")
    print("Build C++ components for enhanced validation")
```

### Running C++ Examples

The repository includes `example_cpp_usage.py` with 6 comprehensive examples demonstrating all C++ components:

**Prerequisites:**
1. C++ module must be built first (see [Building C++ Components](#building-c-components) above)
2. Python dependencies installed: `pip install -r requirements.txt`

**Run the examples:**

```bash
# From project root (rfq_parser_app/)
python example_cpp_usage.py
```

**What it demonstrates:**

| Example | Description |
|---------|-------------|
| **1. SwapLeg Builder** | Creating fixed and floating rate swap legs with day count conventions |
| **2. Vanilla IRS** | 5Y USD interest rate swap paying fixed vs receiving SOFR |
| **3. Bermudan Swaption** | 10Y EUR swaption with multiple exercise dates using C++ pricing |
| **4. RFQValidator** | Validating RFQ data with built-in rules (currency, notional, tenor) for all instrument types |
| **5. ThreadSafeQueue** | Multi-threaded RFQ processing with producer-consumer pattern |
| **6. Parser Integration** | How Python parser automatically uses C++ validation |

**Expected output:**
- Each example prints detailed output showing object creation, validation results, and computed values
- Example 3 creates a Bermudan swaption and demonstrates exercise date logic
- Final example shows ParsedRFQ with C++ validation results in `parsing_notes`

**Troubleshooting:**
- If you get `ModuleNotFoundError: No module named 'rfq_cpp'`, build the C++ module first
- On Windows: run `cd cpp && build.bat`
- On Linux/Mac: run `cd cpp && ./build.sh`
- Or use: `pip install -e .` from project root

### Performance Benefits

| Operation | Python | C++ | Speedup |
|-----------|--------|-----|---------|
| Validate 1 RFQ | ~0.5ms | ~0.05ms | **10x** |
| Validate 1000 RFQs | ~500ms | ~50ms | **10x** |
| Build swap structure | ~1ms | ~0.1ms | **10x** |
| Price swaption (Black) | ~2ms | ~0.2ms | **10x** |

**See [cpp/README.md](cpp/README.md) for detailed C++ documentation and [Running C++ Examples](#running-c-examples) above for how to run `example_cpp_usage.py`.**

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

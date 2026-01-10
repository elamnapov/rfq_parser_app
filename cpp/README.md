# RFQ Parser C++ Components

High-performance C++ components for interest rate derivatives and RFQ validation, demonstrating both **modern C++ expertise** and **finance domain knowledge** for financial trading systems.

## 🎯 What This Demonstrates

### Modern C++ Features (C++17)
- ✅ **Smart Pointers**: `std::unique_ptr` for ownership, `std::shared_ptr` for multi-leg swaps
- ✅ **std::optional**: For nullable fields (spreads, FX rates, etc.)
- ✅ **std::variant**: Polymorphic rate representation (fixed vs. floating)
- ✅ **Lambda Expressions**: With captures for payment calculations
- ✅ **Move Semantics**: Efficient resource management
- ✅ **Template Metaprogramming**: Generic ThreadSafeQueue
- ✅ **Concurrency**: `std::mutex`, `std::condition_variable`, `std::atomic`
- ✅ **RAII**: Automatic resource management
- ✅ **Design Patterns**: Builder, Factory, Strategy

### Finance Domain Knowledge
- ✅ **Day Count Conventions**: ACT/360, ACT/365, 30/360, ACT/ACT
- ✅ **Payment Frequencies**: Annual, Semi-Annual, Quarterly, Monthly
- ✅ **Floating Indices**: SOFR, EURIBOR, SONIA, LIBOR (legacy)
- ✅ **Swap Types**: Vanilla (fixed-for-floating), Basis, Cross-Currency
- ✅ **Swaption Types**: European, American, **Bermudan** (multiple exercise dates)
- ✅ **Payer vs Receiver**: Directional exposure understanding
- ✅ **Black Pricing**: Simple Black-76 formula for swaptions
- ✅ **Validation**: Domain-specific validation rules

## 📦 Components

### 1. SwapLeg (`swap_leg.hpp/cpp`)
Represents one leg of an interest rate swap using **Builder Pattern**.

**Key Features:**
```cpp
auto leg = SwapLeg::builder()
    .withCurrency("USD")
    .withNotional(10'000'000.0)
    .withFixedRate(0.0525)                          // 5.25%
    .withDayCount(DayCountConvention::ACT_360)
    .withFrequency(PaymentFrequency::SEMI_ANNUAL)
    .build();
```

- Uses `std::variant<double, FloatingIndex>` for fixed/floating rates
- `std::optional<double>` for optional spread over floating
- Calculates year fractions based on day count convention

### 2. InterestRateSwap (`interest_rate_swap.hpp/cpp`)
Full interest rate swap with **Factory Methods**.

**Swap Types:**
```cpp
// Vanilla: fixed-for-floating
auto vanilla = InterestRateSwap::createVanillaSwap(
    std::move(pay_leg), std::move(receive_leg), "5Y", "2024-01-15");

// Basis: floating-for-floating (different indices)
auto basis = InterestRateSwap::createBasisSwap(
    std::move(sofr_leg), std::move(libor_leg), "3Y", "2024-02-01");

// Cross-Currency: different currencies
auto xccy = InterestRateSwap::createCrossCurrencySwap(
    std::move(usd_leg), std::move(eur_leg), "10Y", "2024-03-01", 1.11);
```

**Lambda for Payment Calculation:**
```cpp
double InterestRateSwap::calculateNetPayment(double period_days) const {
    auto calculate_payment = [period_days](const SwapLeg& leg) -> double {
        double year_frac = leg.yearFraction(static_cast<int>(period_days));
        // ... calculation logic
    };

    return calculate_payment(*receive_leg_) - calculate_payment(*pay_leg_);
}
```

### 3. Swaption (`swaption.hpp/cpp`)
Option on an interest rate swap with **European, American, and Bermudan** styles.

**Bermudan Swaption Example:**
```cpp
std::vector<std::string> exercise_dates = {
    "2025-01-01", "2026-01-01", "2027-01-01", "2028-01-01"
};

auto bermudan = Swaption::createBermudan(
    SwaptionType::PAYER,
    std::move(swap),
    "2028-12-31",
    0.045,
    exercise_dates
);

// Check if can exercise on specific date
bool can = bermudan->canExerciseOn("2026-01-01");  // true
```

**Simple Black Pricing:**
```cpp
double price = SwaptionPricer::blackPrice(
    swaption, forward_rate, volatility, time_to_expiry);

double implied_vol = SwaptionPricer::impliedVolatility(
    swaption, market_price, forward_rate, time_to_expiry);
```

### 4. SwapValidator (`swap_validator.hpp/cpp`)
Validates parsed RFQ data with **flexible rule system**.

**Key Features:**
```cpp
SwapValidator validator;
validator.setStrictMode(true);
validator.setMinNotional(1'000'000.0);

// Validate parsed data
auto results = validator.validate(parsed_data);

// Add custom rule using lambda
validator.addRule("vip_check", [](const auto& data) {
    // Custom validation logic
    return std::nullopt;  // or ValidationResult
});
```

**Validation Results:**
- `ValidationSeverity::ERROR` - Critical issues
- `ValidationSeverity::WARNING` - Review needed
- `ValidationSeverity::INFO` - Informational

### 5. ThreadSafeQueue (`thread_safe_queue.hpp`)
Lock-free queue for **high-throughput RFQ processing**.

**Key Features:**
```cpp
ThreadSafeQueue<std::string> queue;

// Producer thread
queue.push("RFQ: Buy 10MM EURUSD");

// Consumer thread (blocking)
auto rfq = queue.pop();

// Consumer thread (non-blocking)
auto rfq_opt = queue.tryPop();

// With timeout
auto rfq_timeout = queue.popFor(std::chrono::seconds(5));
```

**Demonstrates:**
- `std::mutex` + `std::lock_guard` for thread safety
- `std::condition_variable` for efficient waiting
- `std::atomic<size_t>` for lock-free size queries
- Move semantics for efficiency
- Graceful shutdown mechanism

## 🏗️ Building

### Option 1: CMake (for C++ development & testing)

```bash
cd cpp
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build .

# Run tests
ctest
# or
./rfq_tests
```

**CMake Features:**
- Uses `FetchContent` to download pybind11 and Catch2
- Cross-platform (Windows, Linux, macOS)
- Builds Python module automatically
- Comprehensive test suite with Catch2

### Option 2: Python setup.py (for production)

```bash
# From project root
pip install -e .
```

This builds the C++ extension and integrates with Python.

## 🧪 Testing

The test suite (`tests/test_main.cpp`) includes:

- **SwapLeg Tests**: Builder pattern, validation, year fraction calculations
- **InterestRateSwap Tests**: Vanilla, basis, cross-currency swaps
- **Swaption Tests**: European, American, Bermudan exercise logic
- **SwapValidator Tests**: Built-in rules, custom rules, severity levels
- **ThreadSafeQueue Tests**: Multi-threaded producer/consumer, shutdown behavior

Run with:
```bash
cd cpp/build
ctest -V  # Verbose output
```

## 🐍 Python Integration

The C++ components are exposed to Python via pybind11:

```python
import rfq_cpp

# Check if C++ module is available
from rfq_parser import CPP_AVAILABLE
print(f"C++ extensions: {CPP_AVAILABLE}")

# Create swap leg
leg = (rfq_cpp.SwapLeg.builder()
       .with_currency("USD")
       .with_notional(10_000_000)
       .with_fixed_rate(0.0525)
       .with_day_count(rfq_cpp.DayCountConvention.ACT_360)
       .with_frequency(rfq_cpp.PaymentFrequency.SEMI_ANNUAL)
       .build())

# Validate RFQ data
validator = rfq_cpp.SwapValidator()
results = validator.validate({
    "direction": "PAY",
    "currency": "USD",
    "notional": "10000000",
    "tenor": "5Y"
})

# Thread-safe queue
queue = rfq_cpp.ThreadSafeQueue()
queue.push("RFQ message")
msg = queue.pop()
```

**Automatic Validation:**
The Python `ParsedRFQ` class automatically runs C++ validation:

```python
from rfq_parser import RFQParser

parser = RFQParser()
result = parser.parse("Buy 10MM EURUSD 3M forward")

# C++ validation runs automatically if available
# Results appear in result.parsing_notes
```

## 📐 Architecture Highlights

### Memory Management
- **Ownership**: `std::unique_ptr` for single-owner resources (SwapLeg in builder)
- **Shared Ownership**: `std::shared_ptr` for underlying swap in Swaption
- **No Manual Memory**: Complete RAII, no `new`/`delete` in user code

### Type Safety
- **Enums**: Type-safe asset classes, day counts, frequencies
- **std::variant**: Compile-time safe fixed/floating rate handling
- **std::optional**: Explicit nullable types (no null pointers)

### Performance
- **Move Semantics**: Efficient resource transfer, no unnecessary copies
- **Lock-Free**: `std::atomic` for queue size queries
- **Template Metaprogramming**: Generic, zero-overhead ThreadSafeQueue

### Extensibility
- **Factory Pattern**: Easy to add new swap types
- **Builder Pattern**: Fluent, validated construction
- **Strategy Pattern**: Pluggable validation rules via `std::function`

## 📊 Performance Characteristics

- **SwapValidator**: O(n) where n = number of validation rules
- **ThreadSafeQueue**: O(1) push/pop, lock-free size queries
- **Memory**: All classes use value semantics where possible, minimal heap allocations

## 🔧 Requirements

- **C++17** compatible compiler (GCC 7+, Clang 5+, MSVC 2017+)
- **CMake 3.15+**
- **Python 3.8+** (for Python bindings)

Dependencies (fetched automatically):
- **pybind11** 2.11+ for Python bindings
- **Catch2** 3.5+ for testing

## 📝 License

MIT License - Production-ready C++ for financial systems, combining modern language features with deep finance knowledge. Suitable for quantitative development, electronic trading, and risk management systems.

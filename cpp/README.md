# RFQ Parser C++ Components

High-performance C++ components for interest rate derivatives and RFQ validation, demonstrating both **modern C++ expertise** and **finance domain knowledge** for financial trading systems.

## 🎯 What This Demonstrates

### Modern C++ Features (C++17)

#### **Top 3 Critical Features**

**1. Smart Pointers** (`std::unique_ptr`, `std::shared_ptr`)
- **What:** Automatic memory management
- **Why:** No memory leaks, clear ownership semantics
- **Example:** Swaption uses `shared_ptr` to share underlying swap; Swap uses `unique_ptr` for exclusive leg ownership

**2. Concurrency** (`std::atomic`, `std::mutex`, `std::condition_variable`)
- **What:** Thread-safe operations
- **Why:** Trading systems are highly concurrent - market data, order processing, risk calculations all parallel
- **Example:** ThreadSafeQueue uses mutex for safety, atomic for lock-free size queries

**3. RAII** (Resource Acquisition Is Initialization)
- **What:** Automatic resource cleanup via scope-based lifetime
- **Why:** Exception safety - locks/resources released even when exceptions occur
- **Example:** `std::lock_guard` automatically unlocks mutex at end of scope

#### **High-Value Features**

**4. std::optional**
- **What:** Type-safe nullable values (no null pointers or sentinel values like -1)
- **Why:** Financial data has many optional fields - makes missing data explicit and safe
- **Example:** `std::optional<double> fx_rate_` (only exists for cross-currency swaps)

**5. Move Semantics**
- **What:** Transfer ownership without copying
- **Why:** Performance - avoid copying large objects millions of times per second
- **Example:** `std::move(pay_leg)` transfers ownership to swap without copying

**6. Lambda Expressions**
- **What:** Inline anonymous functions with captures
- **Why:** Flexible validation rules and calculations without defining separate functions
- **Example:** Custom validation rules, payment calculations

#### **Supporting Features**

- **std::variant:** Type-safe unions (fixed vs floating rate)
- **std::function:** Store any callable (lambdas, functors) uniformly
- **Enum classes:** Type-safe enumerations (can't mix `SwaptionType` with `ExerciseStyle`)
- **Templates:** Generic, zero-overhead data structures (ThreadSafeQueue works with any type)

#### **Why These Matter for Finance**

1. **Safety First:** Smart pointers + RAII = no memory leaks, no crashes → 24/7 uptime
2. **Correctness:** `optional` + `variant` + enum classes = type safety → fewer bugs → no costly pricing errors
3. **Performance:** Move semantics + templates = zero-cost abstractions → microsecond latency requirements met
4. **Concurrency:** Proper thread primitives = correct parallel execution → can handle high message throughput

**Bottom Line:** Modern C++ (C++17) lets you write financial software that is both **safe** AND **fast** - you don't have to choose between correctness and performance.

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

**Architecture Note - 2-Leg Design:**

The current architecture supports exactly **2 legs** (pay and receive):
```cpp
std::unique_ptr<SwapLeg> pay_leg_;      // Fixed: 2-leg architecture
std::unique_ptr<SwapLeg> receive_leg_;
```

**Multi-leg swaps (>2 legs) are NOT currently supported.** However, the modular design makes extension relatively straightforward:

- ✅ **SwapLeg is self-contained** - independent construction and validation
- ✅ **No tight coupling** - SwapLeg doesn't depend on InterestRateSwap
- ✅ **Clean composition** - Swap is composed of independent leg objects
- ✅ **Uniform interface** - All legs expose the same interface

**To extend to N legs**, the main change would be:
```cpp
// Replace fixed 2-leg members with:
std::vector<std::unique_ptr<SwapLeg>> legs_;
```

This would require API changes but minimal architectural refactoring due to good separation of concerns.

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

**Exercise Styles Supported:**
- ✅ **European** - Exercise only at expiry date
- ✅ **American** - Exercise any time up to expiry
- ✅ **Bermudan** - Exercise on specific dates (multiple exercise opportunities)

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
    exercise_dates  // Multiple exercise dates fully supported
);

// Check if can exercise on specific date
bool can = bermudan->canExerciseOn("2026-01-01");  // true
```

**Important:** Bermudan swaptions with multiple exercise dates are fully supported. However, the underlying swap must be a standard 2-leg swap (see InterestRateSwap section above).

**Simple Black Pricing:**
```cpp
double price = SwaptionPricer::blackPrice(
    swaption, forward_rate, volatility, time_to_expiry);

double implied_vol = SwaptionPricer::impliedVolatility(
    swaption, market_price, forward_rate, time_to_expiry);
```

### 4. RFQValidator (`rfq_validator.hpp/cpp`)
Validates parsed RFQ data with **flexible rule system** for all instrument types.

**Key Features:**
```cpp
RFQValidator validator;
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
- **RFQValidator Tests**: Built-in rules, custom rules, severity levels
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
validator = rfq_cpp.RFQValidator()
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

### STL Container Usage
This codebase uses 100% STL containers with no third-party container libraries. Each container was chosen for specific performance and semantic properties:

| STL Container | Where Used | Why This Choice |
|---------------|------------|-----------------|
| `std::vector<T>` | Validation results, exercise dates, error lists | Dynamic arrays with cache-friendly contiguous memory. O(1) indexed access, efficient iteration. Best for sequential access patterns. |
| `std::map<K,V>` | Validation rules, parsed data | Ordered key-value lookup with guaranteed iteration order. O(log n) lookup. Used when ordering matters or range queries needed. |
| `std::queue<T>` | ThreadSafeQueue implementation | FIFO semantics for RFQ processing pipeline. Provides clear queue interface (push/pop) with adapter pattern. |
| `std::optional<T>` | Nullable fields (fx_rate, spread, suggestion) | Type-safe nullability without pointers. Makes optionality explicit in type system. Better than sentinel values or raw pointers. |
| `std::function<T>` | Validation rule callbacks | Type-erased callable objects (lambdas, functors, function pointers). Enables Strategy pattern for pluggable validation rules. |
| `std::string` | Text fields (tenor, currency, dates) | Standard string handling with automatic memory management. Small string optimization in most implementations. |
| `std::shared_ptr<T>` | InterestRateSwap (shared by swaptions) | Shared ownership - multiple swaptions reference the same underlying swap. Thread-safe reference counting. |
| `std::unique_ptr<T>` | SwapLeg (exclusive ownership) | Exclusive ownership with move-only semantics. Zero overhead compared to raw pointers. Enforces single owner invariant. |

**Design Principles:**
- **Prefer STL**: Standard containers have decades of optimization and are well-understood by all C++ developers
- **Right tool for the job**: Each container chosen for its specific performance and semantic properties
- **Modern C++ idioms**: Use `std::optional` instead of null pointers, `std::variant` for type-safe unions
- **No premature optimization**: `std::vector` is the default choice; only use specialized containers when profiling shows a need

**Containers NOT used (and why):**
- `std::list` - Poor cache locality, only beneficial if frequent mid-sequence insertions/deletions
- `std::deque` - Not needed; `std::vector` sufficient for our append-heavy workloads
- `std::unordered_map` - Ordered iteration useful for validation rules; O(log n) acceptable
- `std::set` - No use case requiring unique ordered sets in this domain
- `std::array` - Fixed-size arrays not needed; sizes determined at runtime

### Performance
- **Move Semantics**: Efficient resource transfer, no unnecessary copies
- **Lock-Free**: `std::atomic` for queue size queries
- **Template Metaprogramming**: Generic, zero-overhead ThreadSafeQueue

### Extensibility
- **Factory Pattern**: Easy to add new swap types
- **Builder Pattern**: Fluent, validated construction
- **Strategy Pattern**: Pluggable validation rules via `std::function`

## 📊 Performance Characteristics

- **RFQValidator**: O(n) where n = number of validation rules
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

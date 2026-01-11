"""
Example usage of C++ components from Python

This demonstrates how to use the high-performance C++ components
from the Python RFQ parser.
"""

try:
    import rfq_cpp
    print("✓ C++ extension module loaded successfully")
    print(f"  Version: {rfq_cpp.__version__}\n")
except ImportError as e:
    print(f"✗ C++ extension not available: {e}")
    print("  Build the C++ extension first:")
    print("  cd cpp && mkdir build && cd build && cmake .. && cmake --build .")
    exit(1)


def example_swap_leg():
    """Example: Create swap legs using builder pattern"""
    print("=" * 60)
    print("EXAMPLE 1: SwapLeg with Builder Pattern")
    print("=" * 60)

    # Fixed leg
    fixed_leg = (rfq_cpp.SwapLeg.builder()
                 .with_currency("USD")
                 .with_notional(10_000_000)
                 .with_fixed_rate(0.0525)
                 .with_day_count(rfq_cpp.DayCountConvention.ACT_360)
                 .with_frequency(rfq_cpp.PaymentFrequency.SEMI_ANNUAL)
                 .build())

    print(f"Fixed Leg: {fixed_leg.to_string()}")

    # Floating leg
    floating_leg = (rfq_cpp.SwapLeg.builder()
                   .with_currency("USD")
                   .with_notional(10_000_000)
                   .with_floating_index(rfq_cpp.FloatingIndex.SOFR)
                   .with_day_count(rfq_cpp.DayCountConvention.ACT_360)
                   .with_frequency(rfq_cpp.PaymentFrequency.QUARTERLY)
                   .with_spread(50.0)  # 50 bps
                   .build())

    print(f"Floating Leg: {floating_leg.to_string()}\n")


def example_interest_rate_swap():
    """Example: Create vanilla interest rate swap"""
    print("=" * 60)
    print("EXAMPLE 2: Vanilla Interest Rate Swap")
    print("=" * 60)

    pay_leg = (rfq_cpp.SwapLeg.builder()
               .with_currency("USD")
               .with_notional(25_000_000)
               .with_fixed_rate(0.05)
               .with_day_count(rfq_cpp.DayCountConvention.ACT_360)
               .with_frequency(rfq_cpp.PaymentFrequency.SEMI_ANNUAL)
               .build())

    receive_leg = (rfq_cpp.SwapLeg.builder()
                   .with_currency("USD")
                   .with_notional(25_000_000)
                   .with_floating_index(rfq_cpp.FloatingIndex.SOFR)
                   .with_day_count(rfq_cpp.DayCountConvention.ACT_360)
                   .with_frequency(rfq_cpp.PaymentFrequency.QUARTERLY)
                   .build())

    swap = rfq_cpp.InterestRateSwap.create_vanilla_swap(
        pay_leg, receive_leg, "5Y", "2024-01-15"
    )

    print(swap.to_string())
    print(f"\nIs valid: {swap.is_valid()}")
    print(f"Notional: ${swap.notional():,.0f}\n")


def example_bermudan_swaption():
    """Example: Bermudan swaption with multiple exercise dates"""
    print("=" * 60)
    print("EXAMPLE 3: Bermudan Swaption")
    print("=" * 60)

    pay_leg = (rfq_cpp.SwapLeg.builder()
               .with_currency("EUR")
               .with_notional(15_000_000)
               .with_fixed_rate(0.03)
               .with_day_count(rfq_cpp.DayCountConvention.ACT_365)
               .with_frequency(rfq_cpp.PaymentFrequency.ANNUAL)
               .build())

    receive_leg = (rfq_cpp.SwapLeg.builder()
                   .with_currency("EUR")
                   .with_notional(15_000_000)
                   .with_floating_index(rfq_cpp.FloatingIndex.EURIBOR)
                   .with_day_count(rfq_cpp.DayCountConvention.ACT_365)
                   .with_frequency(rfq_cpp.PaymentFrequency.QUARTERLY)
                   .build())

    # Create vanilla swap (now returns shared_ptr, compatible with Swaption)
    swap = rfq_cpp.InterestRateSwap.create_vanilla_swap(
        pay_leg, receive_leg, "10Y", "2025-01-01"
    )

    # Bermudan: can exercise on specific dates
    exercise_dates = ["2025-01-01", "2026-01-01", "2027-01-01", "2028-01-01"]

    swaption = rfq_cpp.Swaption.create_bermudan(
        rfq_cpp.SwaptionType.PAYER,
        swap,
        "2028-12-31",
        0.03,
        exercise_dates,
        75_000.0  # premium
    )

    print(swaption.to_string())
    print(f"\nCan exercise on 2026-01-01: {swaption.can_exercise_on('2026-01-01')}")
    print(f"Can exercise on 2026-06-15: {swaption.can_exercise_on('2026-06-15')}\n")


def example_swap_validator():
    """Example: Validate RFQ data"""
    print("=" * 60)
    print("EXAMPLE 4: RFQ Validator")
    print("=" * 60)

    validator = rfq_cpp.RFQValidator()
    validator.set_min_notional(1_000_000)
    validator.set_max_notional(100_000_000)

    # Valid data
    valid_data = {
        "direction": "PAY",
        "currency": "USD",
        "notional": "10000000",
        "tenor": "5Y",
        "rate": "0.05",
        "day_count": "ACT/360"
    }

    results = validator.validate(valid_data)
    print(f"Valid data: {len(results)} issues")

    # Invalid data
    invalid_data = {
        "direction": "INVALID_DIR",
        "currency": "US",  # Should be 3 letters
        "notional": "-1000000",  # Negative
        "tenor": "INVALID",
        "rate": "5.0"  # Outside typical range
    }

    results = validator.validate(invalid_data)
    print(f"Invalid data: {len(results)} issues")

    for result in results:
        severity = "ERROR" if result.is_error() else "WARNING"
        print(f"  [{severity}] {result.field}: {result.message}")

    print()


def example_thread_safe_queue():
    """Example: Thread-safe queue for RFQ processing"""
    print("=" * 60)
    print("EXAMPLE 5: ThreadSafeQueue")
    print("=" * 60)

    queue = rfq_cpp.ThreadSafeQueue()

    # Push some RFQs
    rfqs = [
        "Buy 10MM EURUSD spot",
        "Sell 5MM GBPUSD 3M forward",
        "Two-way on 25MM USD IRS 5Y"
    ]

    for rfq in rfqs:
        queue.push(rfq)

    print(f"Queue size: {queue.size()}")
    print("Processing RFQs:")

    while not queue.empty():
        rfq = queue.try_pop()
        if rfq:
            print(f"  - {rfq}")

    print(f"Queue size after processing: {queue.size()}\n")


def example_integration_with_python_parser():
    """Example: Integration with Python RFQ parser"""
    print("=" * 60)
    print("EXAMPLE 6: Integration with Python Parser")
    print("=" * 60)

    from rfq_parser import RFQParser, CPP_AVAILABLE

    print(f"C++ validation available: {CPP_AVAILABLE}")

    if CPP_AVAILABLE:
        parser = RFQParser(use_llm=False)  # Use regex for demo
        result = parser.parse("Buy 10MM EURUSD 3M forward")

        print(f"\nParsed RFQ:")
        print(f"  Direction: {result.direction.value}")
        print(f"  Currency Pair: {result.currency_pair}")
        print(f"  Quantity: {result.quantity:,.0f}")
        print(f"  Tenor: {result.tenor}")

        print(f"\nValidation notes:")
        for note in result.parsing_notes:
            if "C++" in note:
                print(f"  {note}")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("RFQ Parser C++ Components - Python Integration Examples")
    print("=" * 60 + "\n")

    example_swap_leg()
    example_interest_rate_swap()
    example_bermudan_swaption()
    example_swap_validator()
    example_thread_safe_queue()
    example_integration_with_python_parser()

    print("=" * 60)
    print("All examples completed successfully!")
    print("=" * 60)

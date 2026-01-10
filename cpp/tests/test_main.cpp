#define CATCH_CONFIG_MAIN
#include <catch2/catch_test_macros.hpp>
#include <catch2/catch_approx.hpp>

#include "rfq/swap_leg.hpp"
#include "rfq/interest_rate_swap.hpp"
#include "rfq/swaption.hpp"
#include "rfq/swap_validator.hpp"
#include "rfq/thread_safe_queue.hpp"

#include <thread>
#include <chrono>

using namespace rfq;
using Catch::Approx;

// ============================================================================
// SwapLeg Tests
// ============================================================================

TEST_CASE("SwapLeg - Fixed leg construction", "[swap_leg]") {
    auto leg = SwapLeg::builder()
        .withCurrency("USD")
        .withNotional(10'000'000.0)
        .withFixedRate(0.0525)  // 5.25%
        .withDayCount(DayCountConvention::ACT_360)
        .withFrequency(PaymentFrequency::SEMI_ANNUAL)
        .build();

    REQUIRE(leg != nullptr);
    REQUIRE(leg->currency() == "USD");
    REQUIRE(leg->notional() == 10'000'000.0);
    REQUIRE(leg->isFixed());
    REQUIRE_FALSE(leg->isFloating());
    REQUIRE(leg->fixedRate() == Approx(0.0525));
    REQUIRE(leg->dayCount() == DayCountConvention::ACT_360);
    REQUIRE(leg->frequency() == PaymentFrequency::SEMI_ANNUAL);
}

TEST_CASE("SwapLeg - Floating leg construction", "[swap_leg]") {
    auto leg = SwapLeg::builder()
        .withCurrency("USD")
        .withNotional(5'000'000.0)
        .withFloatingIndex(FloatingIndex::SOFR)
        .withDayCount(DayCountConvention::ACT_360)
        .withFrequency(PaymentFrequency::QUARTERLY)
        .withSpread(50.0)  // 50 bps spread
        .build();

    REQUIRE(leg != nullptr);
    REQUIRE(leg->isFloating());
    REQUIRE_FALSE(leg->isFixed());
    REQUIRE(leg->floatingIndex() == FloatingIndex::SOFR);
    REQUIRE(leg->spread().has_value());
    REQUIRE(leg->spread().value() == 50.0);
}

TEST_CASE("SwapLeg - Year fraction calculation", "[swap_leg]") {
    auto leg = SwapLeg::builder()
        .withCurrency("USD")
        .withNotional(1'000'000.0)
        .withFixedRate(0.05)
        .withDayCount(DayCountConvention::ACT_360)
        .build();

    REQUIRE(leg->yearFraction(180) == Approx(0.5));
    REQUIRE(leg->yearFraction(360) == Approx(1.0));
}

TEST_CASE("SwapLeg - Builder validation", "[swap_leg]") {
    SECTION("Missing currency throws") {
        REQUIRE_THROWS_AS(
            SwapLeg::builder()
                .withNotional(1'000'000.0)
                .withFixedRate(0.05)
                .build(),
            std::invalid_argument
        );
    }

    SECTION("Negative notional throws") {
        REQUIRE_THROWS_AS(
            SwapLeg::builder()
                .withCurrency("USD")
                .withNotional(-1'000'000.0)
                .withFixedRate(0.05)
                .build(),
            std::invalid_argument
        );
    }
}

// ============================================================================
// InterestRateSwap Tests
// ============================================================================

TEST_CASE("InterestRateSwap - Vanilla swap creation", "[interest_rate_swap]") {
    auto pay_leg = SwapLeg::builder()
        .withCurrency("USD")
        .withNotional(10'000'000.0)
        .withFixedRate(0.05)
        .withDayCount(DayCountConvention::ACT_360)
        .withFrequency(PaymentFrequency::SEMI_ANNUAL)
        .build();

    auto receive_leg = SwapLeg::builder()
        .withCurrency("USD")
        .withNotional(10'000'000.0)
        .withFloatingIndex(FloatingIndex::SOFR)
        .withDayCount(DayCountConvention::ACT_360)
        .withFrequency(PaymentFrequency::QUARTERLY)
        .build();

    auto swap = InterestRateSwap::createVanillaSwap(
        std::move(pay_leg),
        std::move(receive_leg),
        "5Y",
        "2024-01-15"
    );

    REQUIRE(swap != nullptr);
    REQUIRE(swap->type() == SwapType::VANILLA);
    REQUIRE(swap->isVanilla());
    REQUIRE(swap->tenor() == "5Y");
    REQUIRE(swap->isValid());
    REQUIRE(swap->notional() == 10'000'000.0);
}

TEST_CASE("InterestRateSwap - Basis swap creation", "[interest_rate_swap]") {
    auto pay_leg = SwapLeg::builder()
        .withCurrency("USD")
        .withNotional(25'000'000.0)
        .withFloatingIndex(FloatingIndex::SOFR)
        .withDayCount(DayCountConvention::ACT_360)
        .withFrequency(PaymentFrequency::QUARTERLY)
        .build();

    auto receive_leg = SwapLeg::builder()
        .withCurrency("USD")
        .withNotional(25'000'000.0)
        .withFloatingIndex(FloatingIndex::LIBOR_USD)
        .withDayCount(DayCountConvention::ACT_360)
        .withFrequency(PaymentFrequency::QUARTERLY)
        .withSpread(25.0)
        .build();

    auto swap = InterestRateSwap::createBasisSwap(
        std::move(pay_leg),
        std::move(receive_leg),
        "3Y",
        "2024-02-01"
    );

    REQUIRE(swap != nullptr);
    REQUIRE(swap->type() == SwapType::BASIS);
    REQUIRE(swap->isBasis());
}

TEST_CASE("InterestRateSwap - Cross-currency swap", "[interest_rate_swap]") {
    auto pay_leg = SwapLeg::builder()
        .withCurrency("USD")
        .withNotional(10'000'000.0)
        .withFixedRate(0.05)
        .withDayCount(DayCountConvention::ACT_360)
        .build();

    auto receive_leg = SwapLeg::builder()
        .withCurrency("EUR")
        .withNotional(9'000'000.0)
        .withFixedRate(0.03)
        .withDayCount(DayCountConvention::ACT_365)
        .build();

    auto swap = InterestRateSwap::createCrossCurrencySwap(
        std::move(pay_leg),
        std::move(receive_leg),
        "10Y",
        "2024-03-01",
        1.11  // USD/EUR FX rate
    );

    REQUIRE(swap != nullptr);
    REQUIRE(swap->type() == SwapType::CROSS_CURRENCY);
    REQUIRE(swap->isCrossCurrency());
    REQUIRE(swap->fxRate().has_value());
    REQUIRE(swap->fxRate().value() == Approx(1.11));
}

TEST_CASE("InterestRateSwap - Net payment calculation", "[interest_rate_swap]") {
    auto pay_leg = SwapLeg::builder()
        .withCurrency("USD")
        .withNotional(10'000'000.0)
        .withFixedRate(0.05)
        .withDayCount(DayCountConvention::ACT_360)
        .build();

    auto receive_leg = SwapLeg::builder()
        .withCurrency("USD")
        .withNotional(10'000'000.0)
        .withFloatingIndex(FloatingIndex::SOFR)
        .withDayCount(DayCountConvention::ACT_360)
        .build();

    auto swap = InterestRateSwap::createVanillaSwap(
        std::move(pay_leg),
        std::move(receive_leg),
        "5Y",
        "2024-01-01"
    );

    // Calculate net payment for 180 days
    double net = swap->calculateNetPayment(180.0);
    REQUIRE(std::abs(net) > 0.0);  // Should have some value
}

// ============================================================================
// Swaption Tests
// ============================================================================

TEST_CASE("Swaption - European payer swaption", "[swaption]") {
    auto pay_leg = SwapLeg::builder()
        .withCurrency("USD")
        .withNotional(10'000'000.0)
        .withFixedRate(0.05)
        .withDayCount(DayCountConvention::ACT_360)
        .build();

    auto receive_leg = SwapLeg::builder()
        .withCurrency("USD")
        .withNotional(10'000'000.0)
        .withFloatingIndex(FloatingIndex::SOFR)
        .withDayCount(DayCountConvention::ACT_360)
        .build();

    auto swap = InterestRateSwap::createVanillaSwap(
        std::move(pay_leg),
        std::move(receive_leg),
        "5Y",
        "2025-01-01"
    );

    auto swaption = Swaption::createEuropean(
        SwaptionType::PAYER,
        std::move(swap),
        "2024-12-31",
        0.05,
        50'000.0
    );

    REQUIRE(swaption != nullptr);
    REQUIRE(swaption->isEuropean());
    REQUIRE(swaption->isPayer());
    REQUIRE(swaption->strikeRate() == Approx(0.05));
    REQUIRE(swaption->premium() == Approx(50'000.0));
}

TEST_CASE("Swaption - American receiver swaption", "[swaption]") {
    auto pay_leg = SwapLeg::builder()
        .withCurrency("EUR")
        .withNotional(5'000'000.0)
        .withFixedRate(0.03)
        .withDayCount(DayCountConvention::ACT_365)
        .build();

    auto receive_leg = SwapLeg::builder()
        .withCurrency("EUR")
        .withNotional(5'000'000.0)
        .withFloatingIndex(FloatingIndex::EURIBOR)
        .withDayCount(DayCountConvention::ACT_365)
        .build();

    auto swap = InterestRateSwap::createVanillaSwap(
        std::move(pay_leg),
        std::move(receive_leg),
        "3Y",
        "2025-06-01"
    );

    auto swaption = Swaption::createAmerican(
        SwaptionType::RECEIVER,
        std::move(swap),
        "2025-05-31",
        0.03
    );

    REQUIRE(swaption->isAmerican());
    REQUIRE(swaption->isReceiver());
    REQUIRE(swaption->canExerciseOn("2025-03-15"));  // Can exercise anytime before expiry
}

TEST_CASE("Swaption - Bermudan with multiple exercise dates", "[swaption]") {
    auto pay_leg = SwapLeg::builder()
        .withCurrency("USD")
        .withNotional(20'000'000.0)
        .withFixedRate(0.045)
        .withDayCount(DayCountConvention::ACT_360)
        .build();

    auto receive_leg = SwapLeg::builder()
        .withCurrency("USD")
        .withNotional(20'000'000.0)
        .withFloatingIndex(FloatingIndex::SOFR)
        .withDayCount(DayCountConvention::ACT_360)
        .build();

    auto swap = InterestRateSwap::createVanillaSwap(
        std::move(pay_leg),
        std::move(receive_leg),
        "10Y",
        "2025-01-01"
    );

    std::vector<std::string> exercise_dates = {
        "2025-01-01",
        "2026-01-01",
        "2027-01-01",
        "2028-01-01"
    };

    auto swaption = Swaption::createBermudan(
        SwaptionType::PAYER,
        std::move(swap),
        "2028-12-31",
        0.045,
        exercise_dates
    );

    REQUIRE(swaption->isBermudan());
    REQUIRE(swaption->exerciseDates().size() == 4);
    REQUIRE(swaption->canExerciseOn("2026-01-01"));
    REQUIRE_FALSE(swaption->canExerciseOn("2026-06-01"));
}

TEST_CASE("Swaption - Intrinsic value calculation", "[swaption]") {
    auto pay_leg = SwapLeg::builder()
        .withCurrency("USD")
        .withNotional(10'000'000.0)
        .withFixedRate(0.05)
        .withDayCount(DayCountConvention::ACT_360)
        .build();

    auto receive_leg = SwapLeg::builder()
        .withCurrency("USD")
        .withNotional(10'000'000.0)
        .withFloatingIndex(FloatingIndex::SOFR)
        .withDayCount(DayCountConvention::ACT_360)
        .build();

    auto swap = InterestRateSwap::createVanillaSwap(
        std::move(pay_leg),
        std::move(receive_leg),
        "5Y",
        "2025-01-01"
    );

    auto payer_swaption = Swaption::createEuropean(
        SwaptionType::PAYER,
        std::move(swap),
        "2024-12-31",
        0.05
    );

    // Payer swaption has positive intrinsic value when rates > strike
    REQUIRE(payer_swaption->intrinsicValue(0.06) > 0.0);
    REQUIRE(payer_swaption->intrinsicValue(0.04) == 0.0);
}

// ============================================================================
// SwapValidator Tests
// ============================================================================

TEST_CASE("SwapValidator - Valid swap data", "[swap_validator]") {
    SwapValidator validator;

    std::map<std::string, std::string> data = {
        {"direction", "PAY"},
        {"currency", "USD"},
        {"notional", "10000000"},
        {"tenor", "5Y"},
        {"rate", "0.05"},
        {"day_count", "ACT/360"}
    };

    REQUIRE(validator.isValid(data));
    auto results = validator.validate(data);
    REQUIRE(results.empty());
}

TEST_CASE("SwapValidator - Invalid direction", "[swap_validator]") {
    SwapValidator validator;
    validator.setStrictMode(true);

    std::map<std::string, std::string> data = {
        {"direction", "INVALID"},
        {"currency", "USD"},
        {"notional", "1000000"}
    };

    REQUIRE_FALSE(validator.isValid(data));
    auto errors = validator.getErrors(data);
    REQUIRE(errors.size() > 0);
}

TEST_CASE("SwapValidator - Notional limits", "[swap_validator]") {
    SwapValidator validator;
    validator.setMinNotional(1'000'000.0);
    validator.setMaxNotional(100'000'000.0);

    SECTION("Below minimum") {
        std::map<std::string, std::string> data = {
            {"notional", "500000"}
        };
        auto warnings = validator.getWarnings(data);
        REQUIRE(warnings.size() > 0);
    }

    SECTION("Above maximum") {
        std::map<std::string, std::string> data = {
            {"notional", "200000000"}
        };
        auto warnings = validator.getWarnings(data);
        REQUIRE(warnings.size() > 0);
    }
}

TEST_CASE("SwapValidator - Custom rule", "[swap_validator]") {
    SwapValidator validator;

    // Add custom rule to check for specific client
    validator.addRule("vip_client", [](const auto& data) -> std::optional<ValidationResult> {
        auto client = data.find("client");
        if (client != data.end() && client->second == "VIP_CLIENT") {
            return ValidationResult(ValidationSeverity::INFO, "client",
                                  "VIP client detected - expedite processing");
        }
        return std::nullopt;
    });

    std::map<std::string, std::string> data = {
        {"client", "VIP_CLIENT"},
        {"notional", "10000000"}
    };

    auto results = validator.validate(data);
    REQUIRE(results.size() > 0);
    REQUIRE(results[0].isInfo());
}

// ============================================================================
// ThreadSafeQueue Tests
// ============================================================================

TEST_CASE("ThreadSafeQueue - Basic push/pop", "[thread_safe_queue]") {
    ThreadSafeQueue<std::string> queue;

    queue.push("message1");
    queue.push("message2");

    REQUIRE(queue.size() == 2);
    REQUIRE_FALSE(queue.empty());

    auto item1 = queue.tryPop();
    REQUIRE(item1.has_value());
    REQUIRE(item1.value() == "message1");

    auto item2 = queue.tryPop();
    REQUIRE(item2.has_value());
    REQUIRE(item2.value() == "message2");

    REQUIRE(queue.empty());
}

TEST_CASE("ThreadSafeQueue - Try pop on empty", "[thread_safe_queue]") {
    ThreadSafeQueue<int> queue;

    auto item = queue.tryPop();
    REQUIRE_FALSE(item.has_value());
}

TEST_CASE("ThreadSafeQueue - Multi-threaded producer/consumer", "[thread_safe_queue]") {
    ThreadSafeQueue<int> queue;
    const int num_items = 100;

    // Producer thread
    std::thread producer([&queue, num_items]() {
        for (int i = 0; i < num_items; ++i) {
            queue.push(i);
        }
    });

    // Consumer thread
    std::atomic<int> sum{0};
    std::thread consumer([&queue, &sum, num_items]() {
        for (int i = 0; i < num_items; ++i) {
            auto item = queue.pop();
            if (item.has_value()) {
                sum.fetch_add(item.value());
            }
        }
    });

    producer.join();
    consumer.join();

    // Sum should be 0+1+2+...+99 = 4950
    REQUIRE(sum.load() == 4950);
    REQUIRE(queue.empty());
}

TEST_CASE("ThreadSafeQueue - Shutdown behavior", "[thread_safe_queue]") {
    ThreadSafeQueue<std::string> queue;

    queue.push("item1");
    queue.shutdown();

    REQUIRE(queue.isShutdown());

    // Try to push after shutdown should throw
    REQUIRE_THROWS_AS(queue.push("item2"), std::runtime_error);

    // Can still pop existing items
    auto item = queue.pop();
    REQUIRE(item.has_value());
    REQUIRE(item.value() == "item1");

    // Pop on empty + shutdown returns nullopt
    auto empty_item = queue.pop();
    REQUIRE_FALSE(empty_item.has_value());
}

TEST_CASE("ThreadSafeQueue - Move semantics", "[thread_safe_queue]") {
    ThreadSafeQueue<std::string> queue1;
    queue1.push("test");

    // Move construct
    ThreadSafeQueue<std::string> queue2(std::move(queue1));
    REQUIRE(queue2.size() == 1);

    auto item = queue2.pop();
    REQUIRE(item.has_value());
    REQUIRE(item.value() == "test");
}

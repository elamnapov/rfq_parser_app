#pragma once

#include <string>
#include <memory>
#include <optional>
#include <variant>
#include <stdexcept>

namespace rfq {

// Day count conventions used in interest rate markets
enum class DayCountConvention {
    ACT_360,     // Actual/360 - most USD derivatives
    ACT_365,     // Actual/365 - GBP, some others
    THIRTY_360,  // 30/360 - corporate bonds, some swaps
    ACT_ACT      // Actual/Actual - treasuries
};

// Payment frequency for swap legs
enum class PaymentFrequency {
    ANNUAL,
    SEMI_ANNUAL,
    QUARTERLY,
    MONTHLY
};

// Floating rate indices
enum class FloatingIndex {
    SOFR,      // Secured Overnight Financing Rate (USD)
    LIBOR_USD, // LIBOR USD (being phased out)
    EURIBOR,   // Euro Interbank Offered Rate
    SONIA,     // Sterling Overnight Index Average (GBP)
    TONAR,     // Tokyo Overnight Average Rate (JPY)
    ESTR       // Euro Short-Term Rate
};

// Type of swap leg
enum class LegType {
    FIXED,
    FLOATING
};

// Forward declaration for builder
class SwapLegBuilder;

/**
 * SwapLeg - Represents one leg of an interest rate swap
 *
 * Demonstrates:
 * - Modern C++ with std::optional for nullable fields
 * - std::variant for polymorphic rate representation
 * - Builder pattern for complex construction
 * - Finance domain knowledge
 */
class SwapLeg {
public:
    using Rate = std::variant<double, FloatingIndex>; // Fixed rate or floating index

    // Builder pattern access
    static SwapLegBuilder builder();

    // Getters
    LegType type() const { return type_; }
    const std::string& currency() const { return currency_; }
    double notional() const { return notional_; }
    const Rate& rate() const { return rate_; }
    DayCountConvention dayCount() const { return day_count_; }
    PaymentFrequency frequency() const { return frequency_; }
    std::optional<double> spread() const { return spread_; }

    // Get fixed rate (throws if floating)
    double fixedRate() const {
        if (auto* rate_ptr = std::get_if<double>(&rate_)) {
            return *rate_ptr;
        }
        throw std::runtime_error("Leg is floating, not fixed");
    }

    // Get floating index (throws if fixed)
    FloatingIndex floatingIndex() const {
        if (auto* index_ptr = std::get_if<FloatingIndex>(&rate_)) {
            return *index_ptr;
        }
        throw std::runtime_error("Leg is fixed, not floating");
    }

    // Check if leg is fixed or floating
    bool isFixed() const { return std::holds_alternative<double>(rate_); }
    bool isFloating() const { return std::holds_alternative<FloatingIndex>(rate_); }

    // Calculate year fraction between dates using day count convention
    double yearFraction(int days) const;

    // String representation
    std::string toString() const;

private:
    // Private constructor - use builder
    SwapLeg(LegType type, std::string currency, double notional, Rate rate,
            DayCountConvention day_count, PaymentFrequency frequency,
            std::optional<double> spread);

    LegType type_;
    std::string currency_;
    double notional_;
    Rate rate_;  // std::variant: either fixed rate (double) or floating index
    DayCountConvention day_count_;
    PaymentFrequency frequency_;
    std::optional<double> spread_;  // Spread over floating index (in bps)

    friend class SwapLegBuilder;
};

/**
 * SwapLegBuilder - Builder pattern for constructing SwapLeg objects
 *
 * Demonstrates fluent interface for complex object construction
 */
class SwapLegBuilder {
public:
    SwapLegBuilder() = default;

    // Fluent interface
    SwapLegBuilder& withCurrency(const std::string& currency) {
        currency_ = currency;
        return *this;
    }

    SwapLegBuilder& withNotional(double notional) {
        if (notional <= 0) {
            throw std::invalid_argument("Notional must be positive");
        }
        notional_ = notional;
        return *this;
    }

    SwapLegBuilder& withFixedRate(double rate) {
        rate_ = rate;
        type_ = LegType::FIXED;
        return *this;
    }

    SwapLegBuilder& withFloatingIndex(FloatingIndex index) {
        rate_ = index;
        type_ = LegType::FLOATING;
        return *this;
    }

    SwapLegBuilder& withDayCount(DayCountConvention day_count) {
        day_count_ = day_count;
        return *this;
    }

    SwapLegBuilder& withFrequency(PaymentFrequency frequency) {
        frequency_ = frequency;
        return *this;
    }

    SwapLegBuilder& withSpread(double spread_bps) {
        spread_ = spread_bps;
        return *this;
    }

    // Build the SwapLeg (move semantics)
    std::unique_ptr<SwapLeg> build() {
        validate();

        // Use std::unique_ptr for ownership
        return std::unique_ptr<SwapLeg>(new SwapLeg(
            type_, std::move(currency_), notional_, std::move(rate_),
            day_count_, frequency_, spread_
        ));
    }

private:
    void validate() const {
        if (currency_.empty()) {
            throw std::invalid_argument("Currency is required");
        }
        if (notional_ <= 0) {
            throw std::invalid_argument("Notional must be positive");
        }
        if (!std::holds_alternative<double>(rate_) &&
            !std::holds_alternative<FloatingIndex>(rate_)) {
            throw std::invalid_argument("Rate must be set (fixed or floating)");
        }
    }

    LegType type_ = LegType::FIXED;
    std::string currency_;
    double notional_ = 0.0;
    SwapLeg::Rate rate_ = 0.0;
    DayCountConvention day_count_ = DayCountConvention::ACT_360;
    PaymentFrequency frequency_ = PaymentFrequency::SEMI_ANNUAL;
    std::optional<double> spread_;
};

// Utility functions for enum conversions
std::string dayCountToString(DayCountConvention dc);
std::string frequencyToString(PaymentFrequency freq);
std::string floatingIndexToString(FloatingIndex index);

DayCountConvention stringToDayCount(const std::string& str);
PaymentFrequency stringToFrequency(const std::string& str);
FloatingIndex stringToFloatingIndex(const std::string& str);

} // namespace rfq

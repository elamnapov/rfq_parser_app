#pragma once

#include "interest_rate_swap.hpp"
#include <memory>
#include <vector>
#include <string>
#include <chrono>

namespace rfq {

// Exercise style for swaptions
enum class ExerciseStyle {
    EUROPEAN,   // Can only exercise at expiry
    AMERICAN,   // Can exercise any time up to expiry
    BERMUDAN    // Can exercise on specific dates only
};

// Payer or receiver swaption
enum class SwaptionType {
    PAYER,      // Right to enter swap paying fixed
    RECEIVER    // Right to enter swap receiving fixed
};

/**
 * Swaption - Option on an interest rate swap
 *
 * Demonstrates:
 * - std::shared_ptr for the underlying swap
 * - std::vector for Bermudan exercise dates
 * - Finance domain knowledge (payer vs receiver, exercise styles)
 * - std::chrono for date handling
 */
class Swaption {
public:
    // Constructor
    Swaption(SwaptionType type,
             ExerciseStyle style,
             std::shared_ptr<InterestRateSwap> underlying,
             const std::string& expiry_date,
             double strike_rate,
             double premium = 0.0);

    // Factory methods for different exercise styles
    static std::unique_ptr<Swaption> createEuropean(
        SwaptionType type,
        std::shared_ptr<InterestRateSwap> underlying,
        const std::string& expiry_date,
        double strike_rate,
        double premium = 0.0);

    static std::unique_ptr<Swaption> createAmerican(
        SwaptionType type,
        std::shared_ptr<InterestRateSwap> underlying,
        const std::string& expiry_date,
        double strike_rate,
        double premium = 0.0);

    static std::unique_ptr<Swaption> createBermudan(
        SwaptionType type,
        std::shared_ptr<InterestRateSwap> underlying,
        const std::string& expiry_date,
        double strike_rate,
        const std::vector<std::string>& exercise_dates,
        double premium = 0.0);

    // Getters
    SwaptionType type() const { return type_; }
    ExerciseStyle style() const { return style_; }
    const InterestRateSwap& underlying() const { return *underlying_; }
    std::shared_ptr<InterestRateSwap> underlyingPtr() const { return underlying_; }
    const std::string& expiryDate() const { return expiry_date_; }
    double strikeRate() const { return strike_rate_; }
    double premium() const { return premium_; }
    const std::vector<std::string>& exerciseDates() const { return exercise_dates_; }

    // Check if can exercise on a given date
    bool canExerciseOn(const std::string& date) const;

    // Check exercise style
    bool isEuropean() const { return style_ == ExerciseStyle::EUROPEAN; }
    bool isAmerican() const { return style_ == ExerciseStyle::AMERICAN; }
    bool isBermudan() const { return style_ == ExerciseStyle::BERMUDAN; }

    // Check swaption type
    bool isPayer() const { return type_ == SwaptionType::PAYER; }
    bool isReceiver() const { return type_ == SwaptionType::RECEIVER; }

    // Calculate intrinsic value (simplified)
    double intrinsicValue(double current_rate) const;

    // Validate swaption
    bool isValid() const;
    std::vector<std::string> validate() const;

    // String representation
    std::string toString() const;

    // Add Bermudan exercise dates
    void addExerciseDate(const std::string& date);

private:
    SwaptionType type_;
    ExerciseStyle style_;
    std::shared_ptr<InterestRateSwap> underlying_;  // Shared ownership of underlying swap
    std::string expiry_date_;
    double strike_rate_;                            // Strike rate as decimal (e.g., 0.05 = 5%)
    double premium_;                                // Premium paid
    std::vector<std::string> exercise_dates_;       // For Bermudan swaptions
};

/**
 * SwaptionPricer - Simple Black pricing for swaptions
 *
 * Demonstrates use of std::function and lambda callbacks
 */
class SwaptionPricer {
public:
    // Simple Black formula approximation
    static double blackPrice(
        const Swaption& swaption,
        double forward_rate,
        double volatility,
        double time_to_expiry);

    // Calculate implied volatility (simplified)
    static double impliedVolatility(
        const Swaption& swaption,
        double market_price,
        double forward_rate,
        double time_to_expiry);
};

} // namespace rfq

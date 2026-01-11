#pragma once

#include "swap_leg.hpp"
#include <memory>
#include <vector>
#include <string>

namespace rfq {

// Swap type classification
enum class SwapType {
    VANILLA,        // Standard fixed-for-floating IRS
    BASIS,          // Floating-for-floating (different indices)
    CROSS_CURRENCY, // Different currencies
    OVERNIGHT       // Overnight index swap
};

/**
 * InterestRateSwap - Represents an interest rate swap
 *
 * Demonstrates:
 * - std::shared_ptr for multi-leg ownership
 * - Factory pattern for different swap types
 * - Lambda functions with captures
 * - Modern C++ move semantics
 */
class InterestRateSwap {
public:
    // Factory methods for different swap types
    static std::shared_ptr<InterestRateSwap> createVanillaSwap(
        std::unique_ptr<SwapLeg> pay_leg,
        std::unique_ptr<SwapLeg> receive_leg,
        const std::string& tenor,
        const std::string& effective_date);

    static std::shared_ptr<InterestRateSwap> createBasisSwap(
        std::unique_ptr<SwapLeg> pay_leg,
        std::unique_ptr<SwapLeg> receive_leg,
        const std::string& tenor,
        const std::string& effective_date);

    static std::shared_ptr<InterestRateSwap> createCrossCurrencySwap(
        std::unique_ptr<SwapLeg> pay_leg,
        std::unique_ptr<SwapLeg> receive_leg,
        const std::string& tenor,
        const std::string& effective_date,
        double fx_rate);

    // Getters
    SwapType type() const { return type_; }
    const SwapLeg& payLeg() const { return *pay_leg_; }
    const SwapLeg& receiveLeg() const { return *receive_leg_; }
    const std::string& tenor() const { return tenor_; }
    const std::string& effectiveDate() const { return effective_date_; }
    std::optional<double> fxRate() const { return fx_rate_; }

    // Validate swap structure
    bool isValid() const;
    std::vector<std::string> validate() const;

    // Calculate notional (average if different legs)
    double notional() const;

    // Calculate net payments using lambda
    double calculateNetPayment(double period_days) const;

    // String representation
    std::string toString() const;

    // Swap classification
    bool isVanilla() const { return type_ == SwapType::VANILLA; }
    bool isBasis() const { return type_ == SwapType::BASIS; }
    bool isCrossCurrency() const { return type_ == SwapType::CROSS_CURRENCY; }

private:
    // Private constructor - use factory methods
    InterestRateSwap(SwapType type,
                     std::unique_ptr<SwapLeg> pay_leg,
                     std::unique_ptr<SwapLeg> receive_leg,
                     std::string tenor,
                     std::string effective_date,
                     std::optional<double> fx_rate = std::nullopt);

    SwapType type_;
    std::unique_ptr<SwapLeg> pay_leg_;    // Ownership via unique_ptr
    std::unique_ptr<SwapLeg> receive_leg_;
    std::string tenor_;                    // e.g., "5Y", "10Y"
    std::string effective_date_;           // Start date
    std::optional<double> fx_rate_;        // For cross-currency swaps
};

/**
 * Helper functions for swap construction
 */
namespace swap_utils {

// Check if two legs form a valid vanilla swap
bool isValidVanillaSwap(const SwapLeg& pay, const SwapLeg& receive);

// Check if two legs form a valid basis swap
bool isValidBasisSwap(const SwapLeg& pay, const SwapLeg& receive);

// Check if two legs form a valid cross-currency swap
bool isValidCrossCurrencySwap(const SwapLeg& pay, const SwapLeg& receive);

// Parse tenor string to months (e.g., "5Y" -> 60)
int tenorToMonths(const std::string& tenor);

} // namespace swap_utils

} // namespace rfq

#include "rfq/interest_rate_swap.hpp"
#include <sstream>
#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace rfq {

// Private constructor
InterestRateSwap::InterestRateSwap(SwapType type,
                                   std::unique_ptr<SwapLeg> pay_leg,
                                   std::unique_ptr<SwapLeg> receive_leg,
                                   std::string tenor,
                                   std::string effective_date,
                                   std::optional<double> fx_rate)
    : type_(type)
    , pay_leg_(std::move(pay_leg))
    , receive_leg_(std::move(receive_leg))
    , tenor_(std::move(tenor))
    , effective_date_(std::move(effective_date))
    , fx_rate_(fx_rate) {}

// Factory method: Vanilla swap (fixed-for-floating)
std::shared_ptr<InterestRateSwap> InterestRateSwap::createVanillaSwap(
    std::unique_ptr<SwapLeg> pay_leg,
    std::unique_ptr<SwapLeg> receive_leg,
    const std::string& tenor,
    const std::string& effective_date) {

    if (!swap_utils::isValidVanillaSwap(*pay_leg, *receive_leg)) {
        throw std::invalid_argument("Invalid vanilla swap structure");
    }

    return std::shared_ptr<InterestRateSwap>(new InterestRateSwap(
        SwapType::VANILLA,
        std::move(pay_leg),
        std::move(receive_leg),
        tenor,
        effective_date
    ));
}

// Factory method: Basis swap (floating-for-floating)
std::shared_ptr<InterestRateSwap> InterestRateSwap::createBasisSwap(
    std::unique_ptr<SwapLeg> pay_leg,
    std::unique_ptr<SwapLeg> receive_leg,
    const std::string& tenor,
    const std::string& effective_date) {

    if (!swap_utils::isValidBasisSwap(*pay_leg, *receive_leg)) {
        throw std::invalid_argument("Invalid basis swap structure");
    }

    return std::shared_ptr<InterestRateSwap>(new InterestRateSwap(
        SwapType::BASIS,
        std::move(pay_leg),
        std::move(receive_leg),
        tenor,
        effective_date
    ));
}

// Factory method: Cross-currency swap
std::shared_ptr<InterestRateSwap> InterestRateSwap::createCrossCurrencySwap(
    std::unique_ptr<SwapLeg> pay_leg,
    std::unique_ptr<SwapLeg> receive_leg,
    const std::string& tenor,
    const std::string& effective_date,
    double fx_rate) {

    if (!swap_utils::isValidCrossCurrencySwap(*pay_leg, *receive_leg)) {
        throw std::invalid_argument("Invalid cross-currency swap structure");
    }

    if (fx_rate <= 0.0) {
        throw std::invalid_argument("FX rate must be positive");
    }

    return std::shared_ptr<InterestRateSwap>(new InterestRateSwap(
        SwapType::CROSS_CURRENCY,
        std::move(pay_leg),
        std::move(receive_leg),
        tenor,
        effective_date,
        fx_rate
    ));
}

bool InterestRateSwap::isValid() const {
    return validate().empty();
}

std::vector<std::string> InterestRateSwap::validate() const {
    std::vector<std::string> errors;

    // Check legs exist
    if (!pay_leg_ || !receive_leg_) {
        errors.push_back("Both pay and receive legs required");
        return errors;
    }

    // Check tenor is valid
    if (tenor_.empty()) {
        errors.push_back("Tenor is required");
    }

    // Check effective date
    if (effective_date_.empty()) {
        errors.push_back("Effective date is required");
    }

    // Type-specific validation
    switch (type_) {
        case SwapType::VANILLA:
            if (!swap_utils::isValidVanillaSwap(*pay_leg_, *receive_leg_)) {
                errors.push_back("Invalid vanilla swap: one leg must be fixed, one floating");
            }
            break;

        case SwapType::BASIS:
            if (!swap_utils::isValidBasisSwap(*pay_leg_, *receive_leg_)) {
                errors.push_back("Invalid basis swap: both legs must be floating");
            }
            break;

        case SwapType::CROSS_CURRENCY:
            if (!swap_utils::isValidCrossCurrencySwap(*pay_leg_, *receive_leg_)) {
                errors.push_back("Invalid cross-currency swap: legs must have different currencies");
            }
            if (!fx_rate_ || *fx_rate_ <= 0.0) {
                errors.push_back("Cross-currency swap requires valid FX rate");
            }
            break;

        case SwapType::OVERNIGHT:
            errors.push_back("Overnight swap validation not yet implemented");
            break;
    }

    return errors;
}

double InterestRateSwap::notional() const {
    // For same-currency swaps, use pay leg notional
    // For cross-currency, average in base currency
    if (type_ == SwapType::CROSS_CURRENCY && fx_rate_) {
        return (pay_leg_->notional() + receive_leg_->notional() * (*fx_rate_)) / 2.0;
    }
    return pay_leg_->notional();
}

double InterestRateSwap::calculateNetPayment(double period_days) const {
    // Demonstrate lambda with captures for payment calculation
    auto calculate_payment = [period_days](const SwapLeg& leg) -> double {
        double year_frac = leg.yearFraction(static_cast<int>(period_days));

        if (leg.isFixed()) {
            return leg.notional() * leg.fixedRate() * year_frac;
        } else {
            // For floating, assume current index rate (simplified)
            // In reality, would look up actual fixing
            double assumed_rate = 0.045; // 4.5% placeholder (different from typical fixed to show net payment)
            double spread = leg.spread().value_or(0.0) / 10000.0; // bps to decimal
            return leg.notional() * (assumed_rate + spread) * year_frac;
        }
    };

    double pay_amount = calculate_payment(*pay_leg_);
    double receive_amount = calculate_payment(*receive_leg_);

    // Net payment (positive = receive, negative = pay)
    return receive_amount - pay_amount;
}

std::string InterestRateSwap::toString() const {
    std::ostringstream oss;

    switch (type_) {
        case SwapType::VANILLA: oss << "VANILLA IRS"; break;
        case SwapType::BASIS: oss << "BASIS SWAP"; break;
        case SwapType::CROSS_CURRENCY: oss << "CROSS-CURRENCY SWAP"; break;
        case SwapType::OVERNIGHT: oss << "OVERNIGHT SWAP"; break;
    }

    oss << " (" << tenor_ << ")\n";
    oss << "Effective: " << effective_date_ << "\n";
    oss << "Pay: " << pay_leg_->toString() << "\n";
    oss << "Receive: " << receive_leg_->toString();

    if (fx_rate_) {
        oss << "\nFX Rate: " << *fx_rate_;
    }

    return oss.str();
}

// ============================================================================
// swap_utils namespace implementation
// ============================================================================

namespace swap_utils {

bool isValidVanillaSwap(const SwapLeg& pay, const SwapLeg& receive) {
    // Vanilla: one fixed, one floating, same currency
    bool one_fixed_one_float = (pay.isFixed() && receive.isFloating()) ||
                                (pay.isFloating() && receive.isFixed());

    bool same_currency = pay.currency() == receive.currency();

    return one_fixed_one_float && same_currency;
}

bool isValidBasisSwap(const SwapLeg& pay, const SwapLeg& receive) {
    // Basis: both floating, same currency, different indices
    if (!pay.isFloating() || !receive.isFloating()) {
        return false;
    }

    if (pay.currency() != receive.currency()) {
        return false;
    }

    // Check different indices
    return pay.floatingIndex() != receive.floatingIndex();
}

bool isValidCrossCurrencySwap(const SwapLeg& pay, const SwapLeg& receive) {
    // Cross-currency: different currencies
    return pay.currency() != receive.currency();
}

int tenorToMonths(const std::string& tenor) {
    if (tenor.empty()) {
        return 0;
    }

    std::string upper = tenor;
    std::transform(upper.begin(), upper.end(), upper.begin(), ::toupper);

    size_t i = 0;
    while (i < upper.size() && std::isdigit(upper[i])) {
        ++i;
    }

    if (i == 0) {
        return 0; // No number found
    }

    int num = std::stoi(upper.substr(0, i));
    char unit = i < upper.size() ? upper[i] : 'M';

    switch (unit) {
        case 'D': return num / 30;  // Approximate
        case 'W': return num / 4;   // Approximate
        case 'M': return num;
        case 'Y': return num * 12;
        default: return num;
    }
}

} // namespace swap_utils

} // namespace rfq

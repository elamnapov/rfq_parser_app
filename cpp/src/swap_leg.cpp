#include "rfq/swap_leg.hpp"
#include <sstream>
#include <iomanip>
#include <algorithm>

namespace rfq {

// Private constructor
SwapLeg::SwapLeg(LegType type, std::string currency, double notional, Rate rate,
                 DayCountConvention day_count, PaymentFrequency frequency,
                 std::optional<double> spread)
    : type_(type)
    , currency_(std::move(currency))
    , notional_(notional)
    , rate_(std::move(rate))
    , day_count_(day_count)
    , frequency_(frequency)
    , spread_(spread) {}

SwapLegBuilder SwapLeg::builder() {
    return SwapLegBuilder{};
}

double SwapLeg::yearFraction(int days) const {
    switch (day_count_) {
        case DayCountConvention::ACT_360:
            return days / 360.0;
        case DayCountConvention::ACT_365:
            return days / 365.0;
        case DayCountConvention::THIRTY_360:
            // Simplified - actual 30/360 is more complex
            return days / 360.0;
        case DayCountConvention::ACT_ACT:
            return days / 365.25; // Simplified
        default:
            return days / 360.0;
    }
}

std::string SwapLeg::toString() const {
    std::ostringstream oss;
    oss << std::fixed << std::setprecision(4);

    oss << (type_ == LegType::FIXED ? "FIXED" : "FLOATING") << " leg: ";
    oss << currency_ << " " << notional_ << " notional, ";

    if (isFixed()) {
        oss << "rate=" << (fixedRate() * 100) << "%, ";
    } else {
        oss << "index=" << floatingIndexToString(floatingIndex());
        if (spread_) {
            oss << " + " << *spread_ << "bps, ";
        } else {
            oss << ", ";
        }
    }

    oss << dayCountToString(day_count_) << ", "
        << frequencyToString(frequency_);

    return oss.str();
}

// Utility function implementations
std::string dayCountToString(DayCountConvention dc) {
    switch (dc) {
        case DayCountConvention::ACT_360: return "ACT/360";
        case DayCountConvention::ACT_365: return "ACT/365";
        case DayCountConvention::THIRTY_360: return "30/360";
        case DayCountConvention::ACT_ACT: return "ACT/ACT";
        default: return "UNKNOWN";
    }
}

std::string frequencyToString(PaymentFrequency freq) {
    switch (freq) {
        case PaymentFrequency::ANNUAL: return "Annual";
        case PaymentFrequency::SEMI_ANNUAL: return "Semi-Annual";
        case PaymentFrequency::QUARTERLY: return "Quarterly";
        case PaymentFrequency::MONTHLY: return "Monthly";
        default: return "UNKNOWN";
    }
}

std::string floatingIndexToString(FloatingIndex index) {
    switch (index) {
        case FloatingIndex::SOFR: return "SOFR";
        case FloatingIndex::LIBOR_USD: return "LIBOR-USD";
        case FloatingIndex::EURIBOR: return "EURIBOR";
        case FloatingIndex::SONIA: return "SONIA";
        case FloatingIndex::TONAR: return "TONAR";
        case FloatingIndex::ESTR: return "ESTR";
        default: return "UNKNOWN";
    }
}

DayCountConvention stringToDayCount(const std::string& str) {
    std::string upper = str;
    std::transform(upper.begin(), upper.end(), upper.begin(), ::toupper);

    if (upper.find("ACT/360") != std::string::npos) return DayCountConvention::ACT_360;
    if (upper.find("ACT/365") != std::string::npos) return DayCountConvention::ACT_365;
    if (upper.find("30/360") != std::string::npos) return DayCountConvention::THIRTY_360;
    if (upper.find("ACT/ACT") != std::string::npos) return DayCountConvention::ACT_ACT;

    throw std::invalid_argument("Unknown day count convention: " + str);
}

PaymentFrequency stringToFrequency(const std::string& str) {
    std::string upper = str;
    std::transform(upper.begin(), upper.end(), upper.begin(), ::toupper);

    if (upper.find("ANNUAL") != std::string::npos && upper.find("SEMI") == std::string::npos)
        return PaymentFrequency::ANNUAL;
    if (upper.find("SEMI") != std::string::npos) return PaymentFrequency::SEMI_ANNUAL;
    if (upper.find("QUARTER") != std::string::npos) return PaymentFrequency::QUARTERLY;
    if (upper.find("MONTH") != std::string::npos) return PaymentFrequency::MONTHLY;

    throw std::invalid_argument("Unknown payment frequency: " + str);
}

FloatingIndex stringToFloatingIndex(const std::string& str) {
    std::string upper = str;
    std::transform(upper.begin(), upper.end(), upper.begin(), ::toupper);

    if (upper == "SOFR") return FloatingIndex::SOFR;
    if (upper.find("LIBOR") != std::string::npos) return FloatingIndex::LIBOR_USD;
    if (upper == "EURIBOR") return FloatingIndex::EURIBOR;
    if (upper == "SONIA") return FloatingIndex::SONIA;
    if (upper == "TONAR" || upper == "TONA") return FloatingIndex::TONAR;
    if (upper == "ESTR") return FloatingIndex::ESTR;

    throw std::invalid_argument("Unknown floating index: " + str);
}

} // namespace rfq

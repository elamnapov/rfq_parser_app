#include "rfq/swaption.hpp"
#include <sstream>
#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace rfq {

// Constructor
Swaption::Swaption(SwaptionType type,
                   ExerciseStyle style,
                   std::shared_ptr<InterestRateSwap> underlying,
                   const std::string& expiry_date,
                   double strike_rate,
                   double premium)
    : type_(type)
    , style_(style)
    , underlying_(std::move(underlying))
    , expiry_date_(expiry_date)
    , strike_rate_(strike_rate)
    , premium_(premium)
    , exercise_dates_() {

    if (!underlying_) {
        throw std::invalid_argument("Underlying swap cannot be null");
    }

    // For European, add expiry as the only exercise date
    if (style_ == ExerciseStyle::EUROPEAN) {
        exercise_dates_.push_back(expiry_date_);
    }
}

// Factory: European swaption
std::unique_ptr<Swaption> Swaption::createEuropean(
    SwaptionType type,
    std::shared_ptr<InterestRateSwap> underlying,
    const std::string& expiry_date,
    double strike_rate,
    double premium) {

    return std::unique_ptr<Swaption>(new Swaption(
        type, ExerciseStyle::EUROPEAN, std::move(underlying),
        expiry_date, strike_rate, premium
    ));
}

// Factory: American swaption
std::unique_ptr<Swaption> Swaption::createAmerican(
    SwaptionType type,
    std::shared_ptr<InterestRateSwap> underlying,
    const std::string& expiry_date,
    double strike_rate,
    double premium) {

    return std::unique_ptr<Swaption>(new Swaption(
        type, ExerciseStyle::AMERICAN, std::move(underlying),
        expiry_date, strike_rate, premium
    ));
}

// Factory: Bermudan swaption
std::unique_ptr<Swaption> Swaption::createBermudan(
    SwaptionType type,
    std::shared_ptr<InterestRateSwap> underlying,
    const std::string& expiry_date,
    double strike_rate,
    const std::vector<std::string>& exercise_dates,
    double premium) {

    auto swaption = std::unique_ptr<Swaption>(new Swaption(
        type, ExerciseStyle::BERMUDAN, std::move(underlying),
        expiry_date, strike_rate, premium
    ));

    // Add exercise dates
    swaption->exercise_dates_ = exercise_dates;

    if (swaption->exercise_dates_.empty()) {
        throw std::invalid_argument("Bermudan swaption requires at least one exercise date");
    }

    return swaption;
}

bool Swaption::canExerciseOn(const std::string& date) const {
    switch (style_) {
        case ExerciseStyle::EUROPEAN:
            return date == expiry_date_;

        case ExerciseStyle::AMERICAN:
            // Can exercise any time (simplified - would check date <= expiry)
            return date <= expiry_date_;

        case ExerciseStyle::BERMUDAN:
            return std::find(exercise_dates_.begin(), exercise_dates_.end(), date)
                   != exercise_dates_.end();

        default:
            return false;
    }
}

double Swaption::intrinsicValue(double current_rate) const {
    // Simplified intrinsic value calculation
    // Payer swaption: value increases when rates rise above strike
    // Receiver swaption: value increases when rates fall below strike

    double rate_diff = current_rate - strike_rate_;

    if (type_ == SwaptionType::PAYER) {
        // Payer benefits from rates above strike
        return std::max(0.0, rate_diff);
    } else {
        // Receiver benefits from rates below strike
        return std::max(0.0, -rate_diff);
    }
}

bool Swaption::isValid() const {
    return validate().empty();
}

std::vector<std::string> Swaption::validate() const {
    std::vector<std::string> errors;

    if (!underlying_) {
        errors.push_back("Underlying swap is required");
        return errors;
    }

    if (!underlying_->isValid()) {
        errors.push_back("Underlying swap is invalid");
    }

    if (expiry_date_.empty()) {
        errors.push_back("Expiry date is required");
    }

    if (strike_rate_ < 0.0 || strike_rate_ > 1.0) {
        errors.push_back("Strike rate must be between 0 and 1 (as decimal)");
    }

    // Bermudan-specific validation
    if (style_ == ExerciseStyle::BERMUDAN) {
        if (exercise_dates_.empty()) {
            errors.push_back("Bermudan swaption requires at least one exercise date");
        }

        // Check all exercise dates are before or at expiry
        for (const auto& date : exercise_dates_) {
            if (date > expiry_date_) {
                errors.push_back("Exercise date " + date + " is after expiry");
            }
        }
    }

    return errors;
}

std::string Swaption::toString() const {
    std::ostringstream oss;

    // Type and style
    oss << (type_ == SwaptionType::PAYER ? "PAYER" : "RECEIVER") << " ";

    switch (style_) {
        case ExerciseStyle::EUROPEAN: oss << "EUROPEAN"; break;
        case ExerciseStyle::AMERICAN: oss << "AMERICAN"; break;
        case ExerciseStyle::BERMUDAN: oss << "BERMUDAN"; break;
    }

    oss << " SWAPTION\n";
    oss << "Strike: " << (strike_rate_ * 100) << "%\n";
    oss << "Expiry: " << expiry_date_ << "\n";
    oss << "Premium: " << premium_ << "\n";

    if (style_ == ExerciseStyle::BERMUDAN) {
        oss << "Exercise dates: ";
        for (size_t i = 0; i < exercise_dates_.size(); ++i) {
            oss << exercise_dates_[i];
            if (i < exercise_dates_.size() - 1) oss << ", ";
        }
        oss << "\n";
    }

    oss << "\nUnderlying:\n" << underlying_->toString();

    return oss.str();
}

void Swaption::addExerciseDate(const std::string& date) {
    if (style_ != ExerciseStyle::BERMUDAN) {
        throw std::runtime_error("Can only add exercise dates to Bermudan swaptions");
    }

    // Avoid duplicates
    if (std::find(exercise_dates_.begin(), exercise_dates_.end(), date)
        == exercise_dates_.end()) {
        exercise_dates_.push_back(date);
        // Keep sorted
        std::sort(exercise_dates_.begin(), exercise_dates_.end());
    }
}

// ============================================================================
// SwaptionPricer implementation
// ============================================================================

namespace {
    // Standard normal cumulative distribution function
    double normalCDF(double x) {
        return 0.5 * std::erfc(-x / std::sqrt(2.0));
    }

    // Standard normal probability density function
    double normalPDF(double x) {
        return std::exp(-0.5 * x * x) / std::sqrt(2.0 * M_PI);
    }
}

double SwaptionPricer::blackPrice(
    const Swaption& swaption,
    double forward_rate,
    double volatility,
    double time_to_expiry) {

    double strike = swaption.strikeRate();
    double notional = swaption.underlying().notional();

    // Black formula for swaptions
    double d1 = (std::log(forward_rate / strike) + 0.5 * volatility * volatility * time_to_expiry)
                / (volatility * std::sqrt(time_to_expiry));
    double d2 = d1 - volatility * std::sqrt(time_to_expiry);

    double price;
    if (swaption.isPayer()) {
        price = notional * (forward_rate * normalCDF(d1) - strike * normalCDF(d2));
    } else {
        price = notional * (strike * normalCDF(-d2) - forward_rate * normalCDF(-d1));
    }

    // Simplified - should multiply by annuity factor
    return price;
}

double SwaptionPricer::impliedVolatility(
    const Swaption& swaption,
    double market_price,
    double forward_rate,
    double time_to_expiry) {

    // Simple Newton-Raphson solver for implied vol
    double vol = 0.20; // Initial guess: 20%
    const int max_iterations = 100;
    const double tolerance = 1e-6;

    for (int i = 0; i < max_iterations; ++i) {
        double price = blackPrice(swaption, forward_rate, vol, time_to_expiry);
        double diff = price - market_price;

        if (std::abs(diff) < tolerance) {
            return vol;
        }

        // Vega (sensitivity to volatility)
        double strike = swaption.strikeRate();
        double d1 = (std::log(forward_rate / strike) + 0.5 * vol * vol * time_to_expiry)
                    / (vol * std::sqrt(time_to_expiry));
        double vega = swaption.underlying().notional() * forward_rate *
                      normalPDF(d1) * std::sqrt(time_to_expiry);

        if (std::abs(vega) < 1e-10) {
            break; // Avoid division by zero
        }

        vol = vol - diff / vega;

        // Keep vol positive
        if (vol <= 0.0) {
            vol = 0.01;
        }
    }

    return vol;
}

} // namespace rfq

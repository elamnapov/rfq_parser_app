#include "rfq/swap_validator.hpp"
#include <algorithm>
#include <sstream>
#include <cctype>
#include <regex>

namespace rfq {

SwapValidator::SwapValidator()
    : strict_mode_(false)
    , min_notional_(1000.0)
    , max_notional_(1e12) {
    registerDefaultRules();
}

void SwapValidator::registerDefaultRules() {
    // Register built-in validation rules using lambdas

    rules_["direction"] = [this](const auto& data) {
        return validateDirection(data);
    };

    rules_["currency"] = [this](const auto& data) {
        return validateCurrency(data);
    };

    rules_["notional"] = [this](const auto& data) {
        return validateNotional(data);
    };

    rules_["tenor"] = [this](const auto& data) {
        return validateTenor(data);
    };

    rules_["rate"] = [this](const auto& data) {
        return validateRate(data);
    };

    rules_["day_count"] = [this](const auto& data) {
        return validateDayCount(data);
    };
}

void SwapValidator::addRule(const std::string& rule_name, ValidationRule rule) {
    rules_[rule_name] = std::move(rule);
}

void SwapValidator::removeRule(const std::string& rule_name) {
    rules_.erase(rule_name);
}

std::vector<ValidationResult> SwapValidator::validate(
    const std::map<std::string, std::string>& parsed_data) const {

    std::vector<ValidationResult> results;

    // Run all validation rules
    for (const auto& [rule_name, rule] : rules_) {
        auto result = rule(parsed_data);
        if (result) {
            results.push_back(*result);
        }
    }

    return results;
}

bool SwapValidator::isValid(
    const std::map<std::string, std::string>& parsed_data) const {

    auto results = validate(parsed_data);
    return std::none_of(results.begin(), results.end(),
                       [](const auto& r) { return r.isError(); });
}

std::vector<ValidationResult> SwapValidator::getErrors(
    const std::map<std::string, std::string>& parsed_data) const {

    auto all_results = validate(parsed_data);
    std::vector<ValidationResult> errors;

    std::copy_if(all_results.begin(), all_results.end(),
                std::back_inserter(errors),
                [](const auto& r) { return r.isError(); });

    return errors;
}

std::vector<ValidationResult> SwapValidator::getWarnings(
    const std::map<std::string, std::string>& parsed_data) const {

    auto all_results = validate(parsed_data);
    std::vector<ValidationResult> warnings;

    std::copy_if(all_results.begin(), all_results.end(),
                std::back_inserter(warnings),
                [](const auto& r) { return r.isWarning(); });

    return warnings;
}

std::optional<std::string> SwapValidator::getValue(
    const std::map<std::string, std::string>& data,
    const std::string& key) const {

    auto it = data.find(key);
    if (it != data.end() && !it->second.empty()) {
        return it->second;
    }
    return std::nullopt;
}

// Built-in validation rule implementations

std::optional<ValidationResult> SwapValidator::validateDirection(
    const std::map<std::string, std::string>& data) const {

    auto direction = getValue(data, "direction");

    if (!direction) {
        if (strict_mode_) {
            return ValidationResult(ValidationSeverity::ERROR, "direction",
                                  "Direction is required",
                                  "Specify BUY, SELL, or TWO_WAY");
        }
        return std::nullopt;
    }

    std::string upper = *direction;
    std::transform(upper.begin(), upper.end(), upper.begin(), ::toupper);

    if (upper != "BUY" && upper != "SELL" && upper != "TWO_WAY" &&
        upper != "TWO-WAY" && upper != "PAY" && upper != "RECEIVE") {
        return ValidationResult(ValidationSeverity::ERROR, "direction",
                              "Invalid direction: " + *direction,
                              "Valid values: BUY, SELL, TWO_WAY, PAY, RECEIVE");
    }

    return std::nullopt;
}

std::optional<ValidationResult> SwapValidator::validateCurrency(
    const std::map<std::string, std::string>& data) const {

    auto currency = getValue(data, "currency");

    if (!currency) {
        // Check alternative fields
        currency = getValue(data, "notional_currency");
    }

    if (!currency) {
        // Only warn in strict mode - otherwise allow missing currency
        if (strict_mode_) {
            return ValidationResult(ValidationSeverity::WARNING, "currency",
                                  "Currency not specified",
                                  "Default currency may be assumed");
        }
        return std::nullopt;
    }

    // Valid 3-letter ISO currency codes
    std::regex currency_regex("^[A-Z]{3}$");
    if (!std::regex_match(*currency, currency_regex)) {
        return ValidationResult(ValidationSeverity::ERROR, "currency",
                              "Invalid currency code: " + *currency,
                              "Use 3-letter ISO code (e.g., USD, EUR, GBP)");
    }

    return std::nullopt;
}

std::optional<ValidationResult> SwapValidator::validateNotional(
    const std::map<std::string, std::string>& data) const {

    auto notional_str = getValue(data, "notional");

    if (!notional_str) {
        notional_str = getValue(data, "quantity");
    }

    if (!notional_str) {
        if (strict_mode_) {
            return ValidationResult(ValidationSeverity::ERROR, "notional",
                                  "Notional amount is required");
        }
        return std::nullopt;
    }

    try {
        double notional = std::stod(*notional_str);

        if (notional <= 0) {
            return ValidationResult(ValidationSeverity::ERROR, "notional",
                                  "Notional must be positive");
        }

        if (notional < min_notional_) {
            return ValidationResult(ValidationSeverity::WARNING, "notional",
                                  "Notional below minimum: " + *notional_str,
                                  "Minimum is " + std::to_string(min_notional_));
        }

        if (notional > max_notional_) {
            return ValidationResult(ValidationSeverity::WARNING, "notional",
                                  "Notional exceeds maximum: " + *notional_str,
                                  "Maximum is " + std::to_string(max_notional_));
        }
    }
    catch (const std::exception&) {
        return ValidationResult(ValidationSeverity::ERROR, "notional",
                              "Invalid notional value: " + *notional_str,
                              "Must be a valid number");
    }

    return std::nullopt;
}

std::optional<ValidationResult> SwapValidator::validateTenor(
    const std::map<std::string, std::string>& data) const {

    auto tenor = getValue(data, "tenor");

    if (!tenor) {
        // Tenor might be optional for spot trades
        return std::nullopt;
    }

    // Valid tenor format: number followed by D/W/M/Y
    std::regex tenor_regex("^\\d+[DWMY]$", std::regex::icase);
    if (!std::regex_match(*tenor, tenor_regex)) {
        return ValidationResult(ValidationSeverity::ERROR, "tenor",
                              "Invalid tenor format: " + *tenor,
                              "Use format like '3M', '1Y', '5Y'");
    }

    return std::nullopt;
}

std::optional<ValidationResult> SwapValidator::validateRate(
    const std::map<std::string, std::string>& data) const {

    auto rate_str = getValue(data, "rate");

    if (!rate_str) {
        auto strike_str = getValue(data, "strike");
        if (!strike_str) {
            // Rate might be optional (e.g., for market orders)
            return std::nullopt;
        }
        rate_str = strike_str;
    }

    try {
        double rate = std::stod(*rate_str);

        // Reasonable range check for interest rates
        if (rate < -0.05 || rate > 1.0) {
            return ValidationResult(ValidationSeverity::WARNING, "rate",
                                  "Rate outside typical range: " + *rate_str,
                                  "Typical range: -5% to 100%");
        }
    }
    catch (const std::exception&) {
        return ValidationResult(ValidationSeverity::ERROR, "rate",
                              "Invalid rate value: " + *rate_str,
                              "Must be a valid number");
    }

    return std::nullopt;
}

std::optional<ValidationResult> SwapValidator::validateDayCount(
    const std::map<std::string, std::string>& data) const {

    auto day_count = getValue(data, "day_count");

    if (!day_count) {
        // Day count convention might have default
        return std::nullopt;
    }

    std::string upper = *day_count;
    std::transform(upper.begin(), upper.end(), upper.begin(), ::toupper);

    // Valid day count conventions
    if (upper.find("ACT/360") == std::string::npos &&
        upper.find("ACT/365") == std::string::npos &&
        upper.find("30/360") == std::string::npos &&
        upper.find("ACT/ACT") == std::string::npos) {

        return ValidationResult(ValidationSeverity::WARNING, "day_count",
                              "Unusual day count convention: " + *day_count,
                              "Common: ACT/360, ACT/365, 30/360, ACT/ACT");
    }

    return std::nullopt;
}

// ValidationReport implementation

std::string ValidationReport::toString() const {
    std::ostringstream oss;

    oss << "Validation Report\n";
    oss << "=================\n";
    oss << "Total issues: " << results_.size() << "\n";
    oss << "Errors: " << errorCount() << "\n";
    oss << "Warnings: " << warningCount() << "\n\n";

    for (const auto& result : results_) {
        std::string severity_str;
        switch (result.severity) {
            case ValidationSeverity::ERROR:   severity_str = "ERROR  "; break;
            case ValidationSeverity::WARNING: severity_str = "WARNING"; break;
            case ValidationSeverity::INFO:    severity_str = "INFO   "; break;
        }

        oss << "[" << severity_str << "] " << result.field << ": "
            << result.message;

        if (result.suggestion) {
            oss << " (" << *result.suggestion << ")";
        }

        oss << "\n";
    }

    return oss.str();
}

} // namespace rfq

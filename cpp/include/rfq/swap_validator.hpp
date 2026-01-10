#pragma once

#include <string>
#include <vector>
#include <map>
#include <optional>
#include <functional>

namespace rfq {

// Validation severity levels
enum class ValidationSeverity {
    ERROR,      // Critical error - trade cannot proceed
    WARNING,    // Issue that should be reviewed
    INFO        // Informational note
};

// Validation result for a single check
struct ValidationResult {
    ValidationSeverity severity;
    std::string field;
    std::string message;
    std::optional<std::string> suggestion;

    ValidationResult(ValidationSeverity sev, std::string fld, std::string msg,
                     std::optional<std::string> sugg = std::nullopt)
        : severity(sev), field(std::move(fld)), message(std::move(msg)),
          suggestion(std::move(sugg)) {}

    bool isError() const { return severity == ValidationSeverity::ERROR; }
    bool isWarning() const { return severity == ValidationSeverity::WARNING; }
    bool isInfo() const { return severity == ValidationSeverity::INFO; }
};

/**
 * SwapValidator - Validates parsed RFQ data from Python parser
 *
 * Demonstrates:
 * - Integration with Python data
 * - Flexible validation rules using std::function
 * - Domain-specific validation logic
 * - std::map for configuration
 */
class SwapValidator {
public:
    // Validation rule: takes parsed data, returns optional error
    using ValidationRule = std::function<std::optional<ValidationResult>(
        const std::map<std::string, std::string>&)>;

    SwapValidator();

    // Add custom validation rule
    void addRule(const std::string& rule_name, ValidationRule rule);

    // Remove a rule
    void removeRule(const std::string& rule_name);

    // Validate parsed RFQ data (from Python dict)
    std::vector<ValidationResult> validate(
        const std::map<std::string, std::string>& parsed_data) const;

    // Check if validation passed (no errors)
    bool isValid(const std::map<std::string, std::string>& parsed_data) const;

    // Get only errors
    std::vector<ValidationResult> getErrors(
        const std::map<std::string, std::string>& parsed_data) const;

    // Get only warnings
    std::vector<ValidationResult> getWarnings(
        const std::map<std::string, std::string>& parsed_data) const;

    // Configure validator
    void setStrictMode(bool strict) { strict_mode_ = strict; }
    bool strictMode() const { return strict_mode_; }

    void setMinNotional(double min_notional) { min_notional_ = min_notional; }
    void setMaxNotional(double max_notional) { max_notional_ = max_notional; }

    // Get rule count
    size_t ruleCount() const { return rules_.size(); }

private:
    // Built-in validation rules
    void registerDefaultRules();

    std::optional<ValidationResult> validateDirection(
        const std::map<std::string, std::string>& data) const;

    std::optional<ValidationResult> validateCurrency(
        const std::map<std::string, std::string>& data) const;

    std::optional<ValidationResult> validateNotional(
        const std::map<std::string, std::string>& data) const;

    std::optional<ValidationResult> validateTenor(
        const std::map<std::string, std::string>& data) const;

    std::optional<ValidationResult> validateRate(
        const std::map<std::string, std::string>& data) const;

    std::optional<ValidationResult> validateDayCount(
        const std::map<std::string, std::string>& data) const;

    // Helper to get value from map
    std::optional<std::string> getValue(
        const std::map<std::string, std::string>& data,
        const std::string& key) const;

    std::map<std::string, ValidationRule> rules_;
    bool strict_mode_;
    double min_notional_;
    double max_notional_;
};

/**
 * ValidationReport - Aggregates validation results
 */
class ValidationReport {
public:
    explicit ValidationReport(std::vector<ValidationResult> results)
        : results_(std::move(results)) {}

    bool hasErrors() const {
        return std::any_of(results_.begin(), results_.end(),
                          [](const auto& r) { return r.isError(); });
    }

    bool hasWarnings() const {
        return std::any_of(results_.begin(), results_.end(),
                          [](const auto& r) { return r.isWarning(); });
    }

    size_t errorCount() const {
        return std::count_if(results_.begin(), results_.end(),
                            [](const auto& r) { return r.isError(); });
    }

    size_t warningCount() const {
        return std::count_if(results_.begin(), results_.end(),
                            [](const auto& r) { return r.isWarning(); });
    }

    const std::vector<ValidationResult>& results() const { return results_; }

    std::string toString() const;

private:
    std::vector<ValidationResult> results_;
};

} // namespace rfq

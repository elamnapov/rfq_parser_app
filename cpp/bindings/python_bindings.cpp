#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>
#include <pybind11/chrono.h>

#include "rfq/swap_leg.hpp"
#include "rfq/interest_rate_swap.hpp"
#include "rfq/swaption.hpp"
#include "rfq/rfq_validator.hpp"
#include "rfq/thread_safe_queue.hpp"

namespace py = pybind11;
using namespace rfq;

PYBIND11_MODULE(rfq_cpp, m) {
    m.doc() = R"pbdoc(
        RFQ Parser C++ Extension
        ========================

        High-performance C++ components for RFQ parsing and validation.

        Demonstrates modern C++ features:
        - Smart pointers (unique_ptr, shared_ptr)
        - std::optional, std::variant
        - Builder and Factory patterns
        - Thread-safe concurrency primitives
        - Finance domain knowledge
    )pbdoc";

    // ========================================================================
    // ENUMS
    // ========================================================================

    py::enum_<DayCountConvention>(m, "DayCountConvention")
        .value("ACT_360", DayCountConvention::ACT_360)
        .value("ACT_365", DayCountConvention::ACT_365)
        .value("THIRTY_360", DayCountConvention::THIRTY_360)
        .value("ACT_ACT", DayCountConvention::ACT_ACT)
        .export_values();

    py::enum_<PaymentFrequency>(m, "PaymentFrequency")
        .value("ANNUAL", PaymentFrequency::ANNUAL)
        .value("SEMI_ANNUAL", PaymentFrequency::SEMI_ANNUAL)
        .value("QUARTERLY", PaymentFrequency::QUARTERLY)
        .value("MONTHLY", PaymentFrequency::MONTHLY)
        .export_values();

    py::enum_<FloatingIndex>(m, "FloatingIndex")
        .value("SOFR", FloatingIndex::SOFR)
        .value("LIBOR_USD", FloatingIndex::LIBOR_USD)
        .value("EURIBOR", FloatingIndex::EURIBOR)
        .value("SONIA", FloatingIndex::SONIA)
        .value("TONAR", FloatingIndex::TONAR)
        .value("ESTR", FloatingIndex::ESTR)
        .export_values();

    py::enum_<LegType>(m, "LegType")
        .value("FIXED", LegType::FIXED)
        .value("FLOATING", LegType::FLOATING)
        .export_values();

    py::enum_<SwapType>(m, "SwapType")
        .value("VANILLA", SwapType::VANILLA)
        .value("BASIS", SwapType::BASIS)
        .value("CROSS_CURRENCY", SwapType::CROSS_CURRENCY)
        .value("OVERNIGHT", SwapType::OVERNIGHT)
        .export_values();

    py::enum_<ExerciseStyle>(m, "ExerciseStyle")
        .value("EUROPEAN", ExerciseStyle::EUROPEAN)
        .value("AMERICAN", ExerciseStyle::AMERICAN)
        .value("BERMUDAN", ExerciseStyle::BERMUDAN)
        .export_values();

    py::enum_<SwaptionType>(m, "SwaptionType")
        .value("PAYER", SwaptionType::PAYER)
        .value("RECEIVER", SwaptionType::RECEIVER)
        .export_values();

    py::enum_<ValidationSeverity>(m, "ValidationSeverity")
        .value("ERROR", ValidationSeverity::ERROR)
        .value("WARNING", ValidationSeverity::WARNING)
        .value("INFO", ValidationSeverity::INFO)
        .export_values();

    // ========================================================================
    // UTILITY FUNCTIONS
    // ========================================================================

    m.def("day_count_to_string", &dayCountToString, "Convert day count to string");
    m.def("frequency_to_string", &frequencyToString, "Convert frequency to string");
    m.def("floating_index_to_string", &floatingIndexToString, "Convert index to string");
    m.def("string_to_day_count", &stringToDayCount, "Parse day count from string");
    m.def("string_to_frequency", &stringToFrequency, "Parse frequency from string");
    m.def("string_to_floating_index", &stringToFloatingIndex, "Parse index from string");

    // ========================================================================
    // SWAP LEG
    // ========================================================================

    py::class_<SwapLeg>(m, "SwapLeg")
        .def_static("builder", &SwapLeg::builder, "Create a SwapLegBuilder")
        .def("type", &SwapLeg::type)
        .def("currency", &SwapLeg::currency, py::return_value_policy::reference)
        .def("notional", &SwapLeg::notional)
        .def("day_count", &SwapLeg::dayCount)
        .def("frequency", &SwapLeg::frequency)
        .def("spread", &SwapLeg::spread)
        .def("is_fixed", &SwapLeg::isFixed)
        .def("is_floating", &SwapLeg::isFloating)
        .def("fixed_rate", &SwapLeg::fixedRate, "Get fixed rate (throws if floating)")
        .def("floating_index", &SwapLeg::floatingIndex, "Get floating index (throws if fixed)")
        .def("year_fraction", &SwapLeg::yearFraction, py::arg("days"))
        .def("to_string", &SwapLeg::toString)
        .def("__repr__", &SwapLeg::toString);

    py::class_<SwapLegBuilder>(m, "SwapLegBuilder")
        .def(py::init<>())
        .def("with_currency", &SwapLegBuilder::withCurrency, py::arg("currency"))
        .def("with_notional", &SwapLegBuilder::withNotional, py::arg("notional"))
        .def("with_fixed_rate", &SwapLegBuilder::withFixedRate, py::arg("rate"))
        .def("with_floating_index", &SwapLegBuilder::withFloatingIndex, py::arg("index"))
        .def("with_day_count", &SwapLegBuilder::withDayCount, py::arg("day_count"))
        .def("with_frequency", &SwapLegBuilder::withFrequency, py::arg("frequency"))
        .def("with_spread", &SwapLegBuilder::withSpread, py::arg("spread_bps"))
        .def("build", &SwapLegBuilder::build, "Build the SwapLeg");

    // ========================================================================
    // INTEREST RATE SWAP
    // ========================================================================

    py::class_<InterestRateSwap, std::shared_ptr<InterestRateSwap>>(m, "InterestRateSwap")
        .def_static("create_vanilla_swap",
                   [](SwapLeg& pay_leg, SwapLeg& receive_leg,
                      const std::string& tenor, const std::string& effective_date) {
                       // Create copies and move into factory
                       auto pay_copy = SwapLeg::builder()
                           .withCurrency(pay_leg.currency())
                           .withNotional(pay_leg.notional())
                           .withDayCount(pay_leg.dayCount())
                           .withFrequency(pay_leg.frequency())
                           .build();

                       auto receive_copy = SwapLeg::builder()
                           .withCurrency(receive_leg.currency())
                           .withNotional(receive_leg.notional())
                           .withDayCount(receive_leg.dayCount())
                           .withFrequency(receive_leg.frequency())
                           .build();

                       // Set rate appropriately
                       if (pay_leg.isFixed()) {
                           pay_copy = SwapLeg::builder()
                               .withCurrency(pay_leg.currency())
                               .withNotional(pay_leg.notional())
                               .withFixedRate(pay_leg.fixedRate())
                               .withDayCount(pay_leg.dayCount())
                               .withFrequency(pay_leg.frequency())
                               .build();
                       } else {
                           pay_copy = SwapLeg::builder()
                               .withCurrency(pay_leg.currency())
                               .withNotional(pay_leg.notional())
                               .withFloatingIndex(pay_leg.floatingIndex())
                               .withDayCount(pay_leg.dayCount())
                               .withFrequency(pay_leg.frequency())
                               .build();
                           if (pay_leg.spread()) {
                               // Rebuild with spread
                           }
                       }

                       if (receive_leg.isFixed()) {
                           receive_copy = SwapLeg::builder()
                               .withCurrency(receive_leg.currency())
                               .withNotional(receive_leg.notional())
                               .withFixedRate(receive_leg.fixedRate())
                               .withDayCount(receive_leg.dayCount())
                               .withFrequency(receive_leg.frequency())
                               .build();
                       } else {
                           receive_copy = SwapLeg::builder()
                               .withCurrency(receive_leg.currency())
                               .withNotional(receive_leg.notional())
                               .withFloatingIndex(receive_leg.floatingIndex())
                               .withDayCount(receive_leg.dayCount())
                               .withFrequency(receive_leg.frequency())
                               .build();
                       }

                       return InterestRateSwap::createVanillaSwap(
                           std::move(pay_copy), std::move(receive_copy), tenor, effective_date
                       );
                   },
                   py::arg("pay_leg"), py::arg("receive_leg"),
                   py::arg("tenor"), py::arg("effective_date"),
                   "Create a vanilla IRS (fixed-for-floating)")
        .def_static("create_basis_swap",
                   [](SwapLeg& pay_leg, SwapLeg& receive_leg,
                      const std::string& tenor, const std::string& effective_date) {
                       auto pay_copy = SwapLeg::builder()
                           .withCurrency(pay_leg.currency())
                           .withNotional(pay_leg.notional())
                           .withFloatingIndex(pay_leg.floatingIndex())
                           .withDayCount(pay_leg.dayCount())
                           .withFrequency(pay_leg.frequency())
                           .build();

                       auto receive_copy = SwapLeg::builder()
                           .withCurrency(receive_leg.currency())
                           .withNotional(receive_leg.notional())
                           .withFloatingIndex(receive_leg.floatingIndex())
                           .withDayCount(receive_leg.dayCount())
                           .withFrequency(receive_leg.frequency())
                           .build();

                       return InterestRateSwap::createBasisSwap(
                           std::move(pay_copy), std::move(receive_copy), tenor, effective_date
                       );
                   },
                   py::arg("pay_leg"), py::arg("receive_leg"),
                   py::arg("tenor"), py::arg("effective_date"),
                   "Create a basis swap (floating-for-floating)")
        .def_static("create_cross_currency_swap",
                   [](SwapLeg& pay_leg, SwapLeg& receive_leg,
                      const std::string& tenor, const std::string& effective_date, double fx_rate) {
                       auto pay_copy = SwapLeg::builder()
                           .withCurrency(pay_leg.currency())
                           .withNotional(pay_leg.notional())
                           .withDayCount(pay_leg.dayCount())
                           .withFrequency(pay_leg.frequency())
                           .build();

                       auto receive_copy = SwapLeg::builder()
                           .withCurrency(receive_leg.currency())
                           .withNotional(receive_leg.notional())
                           .withDayCount(receive_leg.dayCount())
                           .withFrequency(receive_leg.frequency())
                           .build();

                       if (pay_leg.isFixed()) {
                           pay_copy = SwapLeg::builder()
                               .withCurrency(pay_leg.currency())
                               .withNotional(pay_leg.notional())
                               .withFixedRate(pay_leg.fixedRate())
                               .withDayCount(pay_leg.dayCount())
                               .withFrequency(pay_leg.frequency())
                               .build();
                       } else {
                           pay_copy = SwapLeg::builder()
                               .withCurrency(pay_leg.currency())
                               .withNotional(pay_leg.notional())
                               .withFloatingIndex(pay_leg.floatingIndex())
                               .withDayCount(pay_leg.dayCount())
                               .withFrequency(pay_leg.frequency())
                               .build();
                       }

                       if (receive_leg.isFixed()) {
                           receive_copy = SwapLeg::builder()
                               .withCurrency(receive_leg.currency())
                               .withNotional(receive_leg.notional())
                               .withFixedRate(receive_leg.fixedRate())
                               .withDayCount(receive_leg.dayCount())
                               .withFrequency(receive_leg.frequency())
                               .build();
                       } else {
                           receive_copy = SwapLeg::builder()
                               .withCurrency(receive_leg.currency())
                               .withNotional(receive_leg.notional())
                               .withFloatingIndex(receive_leg.floatingIndex())
                               .withDayCount(receive_leg.dayCount())
                               .withFrequency(receive_leg.frequency())
                               .build();
                       }

                       return InterestRateSwap::createCrossCurrencySwap(
                           std::move(pay_copy), std::move(receive_copy), tenor, effective_date, fx_rate
                       );
                   },
                   py::arg("pay_leg"), py::arg("receive_leg"),
                   py::arg("tenor"), py::arg("effective_date"), py::arg("fx_rate"),
                   "Create a cross-currency swap")
        .def("type", &InterestRateSwap::type)
        .def("pay_leg", &InterestRateSwap::payLeg, py::return_value_policy::reference)
        .def("receive_leg", &InterestRateSwap::receiveLeg, py::return_value_policy::reference)
        .def("tenor", &InterestRateSwap::tenor, py::return_value_policy::reference)
        .def("effective_date", &InterestRateSwap::effectiveDate, py::return_value_policy::reference)
        .def("fx_rate", &InterestRateSwap::fxRate)
        .def("is_valid", &InterestRateSwap::isValid)
        .def("validate", &InterestRateSwap::validate)
        .def("notional", &InterestRateSwap::notional)
        .def("calculate_net_payment", &InterestRateSwap::calculateNetPayment, py::arg("period_days"))
        .def("is_vanilla", &InterestRateSwap::isVanilla)
        .def("is_basis", &InterestRateSwap::isBasis)
        .def("is_cross_currency", &InterestRateSwap::isCrossCurrency)
        .def("to_string", &InterestRateSwap::toString)
        .def("__repr__", &InterestRateSwap::toString);

    // ========================================================================
    // SWAPTION
    // ========================================================================

    py::class_<Swaption>(m, "Swaption")
        .def(py::init<SwaptionType, ExerciseStyle, std::shared_ptr<InterestRateSwap>,
                     const std::string&, double, double>(),
             py::arg("type"), py::arg("style"), py::arg("underlying"),
             py::arg("expiry_date"), py::arg("strike_rate"), py::arg("premium") = 0.0)
        .def_static("create_european", &Swaption::createEuropean,
                   py::arg("type"), py::arg("underlying"), py::arg("expiry_date"),
                   py::arg("strike_rate"), py::arg("premium") = 0.0,
                   "Create European swaption")
        .def_static("create_american", &Swaption::createAmerican,
                   py::arg("type"), py::arg("underlying"), py::arg("expiry_date"),
                   py::arg("strike_rate"), py::arg("premium") = 0.0,
                   "Create American swaption")
        .def_static("create_bermudan", &Swaption::createBermudan,
                   py::arg("type"), py::arg("underlying"), py::arg("expiry_date"),
                   py::arg("strike_rate"), py::arg("exercise_dates"), py::arg("premium") = 0.0,
                   "Create Bermudan swaption with multiple exercise dates")
        .def("type", &Swaption::type)
        .def("style", &Swaption::style)
        .def("underlying", &Swaption::underlying, py::return_value_policy::reference)
        .def("expiry_date", &Swaption::expiryDate, py::return_value_policy::reference)
        .def("strike_rate", &Swaption::strikeRate)
        .def("premium", &Swaption::premium)
        .def("exercise_dates", &Swaption::exerciseDates, py::return_value_policy::reference)
        .def("can_exercise_on", &Swaption::canExerciseOn, py::arg("date"))
        .def("is_european", &Swaption::isEuropean)
        .def("is_american", &Swaption::isAmerican)
        .def("is_bermudan", &Swaption::isBermudan)
        .def("is_payer", &Swaption::isPayer)
        .def("is_receiver", &Swaption::isReceiver)
        .def("intrinsic_value", &Swaption::intrinsicValue, py::arg("current_rate"))
        .def("is_valid", &Swaption::isValid)
        .def("validate", &Swaption::validate)
        .def("add_exercise_date", &Swaption::addExerciseDate, py::arg("date"))
        .def("to_string", &Swaption::toString)
        .def("__repr__", &Swaption::toString);

    py::class_<SwaptionPricer>(m, "SwaptionPricer")
        .def_static("black_price", &SwaptionPricer::blackPrice,
                   py::arg("swaption"), py::arg("forward_rate"),
                   py::arg("volatility"), py::arg("time_to_expiry"),
                   "Calculate Black price for swaption")
        .def_static("implied_volatility", &SwaptionPricer::impliedVolatility,
                   py::arg("swaption"), py::arg("market_price"),
                   py::arg("forward_rate"), py::arg("time_to_expiry"),
                   "Calculate implied volatility from market price");

    // ========================================================================
    // SWAP VALIDATOR
    // ========================================================================

    py::class_<ValidationResult>(m, "ValidationResult")
        .def(py::init<ValidationSeverity, std::string, std::string, std::optional<std::string>>(),
             py::arg("severity"), py::arg("field"), py::arg("message"),
             py::arg("suggestion") = std::nullopt)
        .def_readonly("severity", &ValidationResult::severity)
        .def_readonly("field", &ValidationResult::field)
        .def_readonly("message", &ValidationResult::message)
        .def_readonly("suggestion", &ValidationResult::suggestion)
        .def("is_error", &ValidationResult::isError)
        .def("is_warning", &ValidationResult::isWarning)
        .def("is_info", &ValidationResult::isInfo);

    py::class_<RFQValidator>(m, "RFQValidator")
        .def(py::init<>())
        .def("add_rule", &RFQValidator::addRule,
             py::arg("rule_name"), py::arg("rule"),
             "Add custom validation rule")
        .def("remove_rule", &RFQValidator::removeRule, py::arg("rule_name"))
        .def("validate", &RFQValidator::validate, py::arg("parsed_data"),
             "Validate parsed RFQ data")
        .def("is_valid", &RFQValidator::isValid, py::arg("parsed_data"))
        .def("get_errors", &RFQValidator::getErrors, py::arg("parsed_data"))
        .def("get_warnings", &RFQValidator::getWarnings, py::arg("parsed_data"))
        .def("set_strict_mode", &RFQValidator::setStrictMode, py::arg("strict"))
        .def("strict_mode", &RFQValidator::strictMode)
        .def("set_min_notional", &RFQValidator::setMinNotional, py::arg("min_notional"))
        .def("set_max_notional", &RFQValidator::setMaxNotional, py::arg("max_notional"))
        .def("rule_count", &RFQValidator::ruleCount);

    py::class_<ValidationReport>(m, "ValidationReport")
        .def(py::init<std::vector<ValidationResult>>(), py::arg("results"))
        .def("has_errors", &ValidationReport::hasErrors)
        .def("has_warnings", &ValidationReport::hasWarnings)
        .def("error_count", &ValidationReport::errorCount)
        .def("warning_count", &ValidationReport::warningCount)
        .def("results", &ValidationReport::results, py::return_value_policy::reference)
        .def("to_string", &ValidationReport::toString)
        .def("__repr__", &ValidationReport::toString);

    // ========================================================================
    // THREAD SAFE QUEUE
    // ========================================================================

    py::class_<ThreadSafeQueue<std::string>>(m, "ThreadSafeQueue")
        .def(py::init<>())
        .def("push", py::overload_cast<const std::string&>(&ThreadSafeQueue<std::string>::push),
             py::arg("item"), "Push item onto queue")
        .def("try_pop", &ThreadSafeQueue<std::string>::tryPop,
             "Try to pop item (non-blocking)")
        .def("pop", &ThreadSafeQueue<std::string>::pop,
             "Pop item (blocking until available)")
        .def("empty", &ThreadSafeQueue<std::string>::empty)
        .def("size", &ThreadSafeQueue<std::string>::size)
        .def("clear", &ThreadSafeQueue<std::string>::clear)
        .def("shutdown", &ThreadSafeQueue<std::string>::shutdown)
        .def("is_shutdown", &ThreadSafeQueue<std::string>::isShutdown)
        .def("restart", &ThreadSafeQueue<std::string>::restart);

    // Version info
    m.attr("__version__") = "0.1.0";

#ifdef VERSION_INFO
    m.attr("__version__") = VERSION_INFO;
#endif
}

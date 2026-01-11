cmake_minimum_required(VERSION 3.15)
project(rfq_parser_cpp VERSION 0.1.0 LANGUAGES CXX)

# C++17 required for std::optional, std::variant
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Export compile commands for IDE support
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Position independent code for shared libraries
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# ============================================================================
# Options
# ============================================================================

option(BUILD_TESTS "Build test suite" ON)
option(BUILD_PYTHON_MODULE "Build Python bindings" ON)

# ============================================================================
# Dependencies via FetchContent
# ============================================================================

include(FetchContent)

# pybind11 for Python bindings
if(BUILD_PYTHON_MODULE)
    message(STATUS "Fetching pybind11...")
    FetchContent_Declare(
        pybind11
        GIT_REPOSITORY https://github.com/pybind/pybind11.git
        GIT_TAG v2.11.1
    )
    FetchContent_MakeAvailable(pybind11)
endif()

# Catch2 for testing
if(BUILD_TESTS)
    message(STATUS "Fetching Catch2...")
    FetchContent_Declare(
        Catch2
        GIT_REPOSITORY https://github.com/catchorg/Catch2.git
        GIT_TAG v3.5.0
    )
    FetchContent_MakeAvailable(Catch2)
endif()

# ============================================================================
# Core C++ Library
# ============================================================================

set(RFQ_SOURCES
    src/swap_leg.cpp
    src/interest_rate_swap.cpp
    src/swaption.cpp
    src/rfq_validator.cpp
)

set(RFQ_HEADERS
    include/rfq/swap_leg.hpp
    include/rfq/interest_rate_swap.hpp
    include/rfq/swaption.hpp
    include/rfq/rfq_validator.hpp
    include/rfq/thread_safe_queue.hpp
)

# Static library for core functionality
add_library(rfq_core STATIC ${RFQ_SOURCES} ${RFQ_HEADERS})

target_include_directories(rfq_core PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)

# Compiler warnings
if(MSVC)
    target_compile_options(rfq_core PRIVATE /W4)
else()
    target_compile_options(rfq_core PRIVATE -Wall -Wextra -Wpedantic)
endif()

# Threading support (required for ThreadSafeQueue)
find_package(Threads REQUIRED)
target_link_libraries(rfq_core PUBLIC Threads::Threads)

# ============================================================================
# Python Module
# ============================================================================

if(BUILD_PYTHON_MODULE)
    pybind11_add_module(rfq_cpp bindings/python_bindings.cpp)

    target_link_libraries(rfq_cpp PRIVATE rfq_core)

    # Set version info
    target_compile_definitions(rfq_cpp PRIVATE
        VERSION_INFO="${PROJECT_VERSION}"
    )

    # Copy built module to project root for easy import
    add_custom_command(TARGET rfq_cpp POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy
            $<TARGET_FILE:rfq_cpp>
            ${CMAKE_CURRENT_SOURCE_DIR}/..
        COMMENT "Copying Python module to project root"
    )

    message(STATUS "Python module will be built as: rfq_cpp")
endif()

# ============================================================================
# Tests
# ============================================================================

if(BUILD_TESTS)
    enable_testing()

    add_executable(rfq_tests tests/test_main.cpp)

    target_link_libraries(rfq_tests PRIVATE
        rfq_core
        Catch2::Catch2WithMain
    )

    # Discover Catch2 tests
    include(CTest)
    include(Catch)
    catch_discover_tests(rfq_tests)

    message(STATUS "Tests enabled - run with 'ctest' or './rfq_tests'")
endif()

# ============================================================================
# Installation (optional)
# ============================================================================

include(GNUInstallDirs)

install(TARGETS rfq_core
    EXPORT rfq_core-targets
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
)

install(DIRECTORY include/
    DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}
)

# ============================================================================
# Summary
# ============================================================================

message(STATUS "")
message(STATUS "RFQ Parser C++ Configuration:")
message(STATUS "  CMake version:        ${CMAKE_VERSION}")
message(STATUS "  C++ standard:         ${CMAKE_CXX_STANDARD}")
message(STATUS "  Build type:           ${CMAKE_BUILD_TYPE}")
message(STATUS "  Build tests:          ${BUILD_TESTS}")
message(STATUS "  Build Python module:  ${BUILD_PYTHON_MODULE}")
message(STATUS "")

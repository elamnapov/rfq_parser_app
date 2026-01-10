#!/bin/bash
# Build script for Linux/macOS

set -e

echo "Building RFQ Parser C++ Components..."
echo ""

mkdir -p build
cd build

echo "Running CMake configuration..."
cmake .. -DCMAKE_BUILD_TYPE=Release

echo ""
echo "Building project..."
cmake --build . -- -j$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)

echo ""
echo "Build successful!"
echo ""
echo "Running tests..."
ctest --output-on-failure

echo ""
echo "Python module has been copied to project root."
echo "You can now use: import rfq_cpp"

cd ..

@echo off
REM Build script for Windows

echo Building RFQ Parser C++ Components...
echo.

if not exist build mkdir build
cd build

echo Running CMake configuration...
cmake .. -DCMAKE_BUILD_TYPE=Release
if %errorlevel% neq 0 (
    echo CMake configuration failed!
    exit /b %errorlevel%
)

echo.
echo Building project...
cmake --build . --config Release
if %errorlevel% neq 0 (
    echo Build failed!
    exit /b %errorlevel%
)

echo.
echo Build successful!
echo.
echo Running tests...
ctest -C Release --output-on-failure

echo.
echo Python module has been copied to project root.
echo You can now use: import rfq_cpp

cd ..

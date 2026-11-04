cmake_minimum_required(VERSION 3.24)
project(ECFpyDeskNative LANGUAGES CXX)

if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type" FORCE)
endif()

# ECF still uses std::random_shuffle, which C++17 removed.
set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Fused multiply-add changes the last bits of a result, and that is enough to send a
# run down another path. Keeping it off matches the SRM binary this build replaced.
add_compile_options($<$<NOT:$<CXX_COMPILER_ID:MSVC>>:-ffp-contract=off>)

# Link the C++ runtime statically on MSVC so that SRM.exe runs on a clean Windows.
set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")

set(SRM_OUTPUT_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../srm" CACHE PATH "Where the SRM binary goes")

# ECF and SRM use header-only parts of Boost, so nothing from Boost is linked.
# An installed Boost wins; without one, CMake downloads this pinned release.
include(FetchContent)
set(BOOST_INCLUDE_LIBRARIES foreach property_tree random)
FetchContent_Declare(Boost
    URL https://github.com/boostorg/boost/releases/download/boost-1.90.0/boost-1.90.0-cmake.tar.xz
    URL_HASH SHA256=aca59f889f0f32028ad88ba6764582b63c916ce5f77b31289ad19421a96c555f
    DOWNLOAD_EXTRACT_TIMESTAMP FALSE
    EXCLUDE_FROM_ALL
    FIND_PACKAGE_ARGS 1.83 CONFIG
)
FetchContent_MakeAvailable(Boost)

add_subdirectory(ecf)
add_subdirectory(SRM)

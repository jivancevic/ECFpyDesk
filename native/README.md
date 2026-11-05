# Building SRM

`native/ecf` is ECF 1.6.1 with small changes and `native/SRM` is the SRM source. ADR 0001 lists the changes. The build puts the binary where the app looks for it: `srm/SRM`, or `srm/SRM.exe` on Windows.

You need CMake 3.24 or newer and a C++ compiler: Xcode command line tools on macOS, GCC or Clang on Linux, Visual Studio 2022 on Windows. From the repo root:

```bash
cmake -S native -B build
cmake --build build --config Release --parallel 4
python native/smoke_test.py
```

The smoke test runs a short evolution for GP, GEP and AP on `srm/data_2var.txt`, checks that the error came down, and evaluates the best individual the way the app does for plots.

On macOS the binary targets arm64 and macOS 12 or newer. On an Intel Mac, add `-DCMAKE_OSX_ARCHITECTURES=x86_64` to the first command.

## Boost

ECF and SRM use header-only parts of Boost, so the binary links nothing from it. CMake uses an installed Boost 1.83 or newer (`brew install boost`, `apt install libboost-dev`). Without one, it downloads the pinned Boost 1.90.0 release (about 100 MB) during the first configure.

## Results across builds

The build turns off fused multiply-add (`-ffp-contract=off`). Newer Clang versions turn it on, and the tiny rounding change is enough to send a run down a different path.

A fixed `randomizer.seed` does not make a run repeatable. ECF seeds the Gaussian mutation operators from `std::random_device`.

`SimpleRandomizer` uses `rand()` on macOS and Linux and `std::mt19937` on MSVC, because MSVC's `RAND_MAX` is only 32767. The same seed gives different runs on different systems, but the search has the same resolution. A few parts of ECF call `rand()` directly (cuckoo search, particle swarm, the binary shuffle crossover). None of the SRM templates use them.

# Building SRM

`native/ecf` is ECF 1.6.1 with two small changes and `native/SRM` is the SRM source (see ADR 0001). The changes are `GEPChromosome::addFunction`, which SRM needs, and `SimpleRandomizer::initialize`, which read uninitialized memory for `randomizer.seed` 0 and now uses `std::random_device`. The build puts the binary where the app looks for it: `srm/SRM`, or `srm/SRM.exe` on Windows.

You need CMake 3.24 or newer and a C++ compiler: Xcode command line tools on macOS, GCC or Clang on Linux, Visual Studio 2022 on Windows. From the repo root:

```bash
cmake -S native -B build
cmake --build build --config Release --parallel 4
python native/smoke_test.py
```

The smoke test runs SRM once each for GP, GEP and AP on `srm/data_2var.txt`.

## Boost

ECF and SRM use header-only parts of Boost, so the binary links nothing from it. CMake uses an installed Boost 1.83 or newer (`brew install boost`, `apt install libboost-dev`). Without one, it downloads the pinned Boost 1.90.0 release (about 100 MB) during the first configure.

## Results across builds

The build turns off fused multiply-add (`-ffp-contract=off`). Newer Clang versions turn it on, and the tiny rounding change is enough to send a run down a different path.

A fixed `randomizer.seed` does not make a run repeatable. ECF seeds the Gaussian mutation operators from `std::random_device`, and `rand()` differs between systems.

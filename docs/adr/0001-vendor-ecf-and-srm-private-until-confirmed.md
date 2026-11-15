---
status: accepted
---

# ECF and SRM live in this repo, and the repo stays private until the mentor confirms

Decided by Josip on 2026-11-04.

SRM existed only in a local folder outside any repo, and only a Mac binary was tracked here. A build for other platforms needs the source, so `native/` now holds it: ECF 1.6.1 with a small patch, and SRM. The patch adds `GEPChromosome::addFunction`, which SRM needs and upstream did not have at that version.

The reproducible build added three more changes to the vendored code:

- `SimpleRandomizer::initialize` read uninitialized memory when `randomizer.seed` is 0. Apple clang 21 compiles that read to a trap, so SRM crashed at start-up. It now uses `std::random_device`.
- `SimpleRandomizer` uses `std::mt19937` on MSVC only, because MSVC's `RAND_MAX` is 32767. macOS and Linux keep `rand()`, so their results do not change.
- `native/SRM/infixTree.h` includes `<ecf/ECF.h>` instead of `ECF/ECF.h`, which fails on a case-sensitive file system.

We vendor instead of using a submodule because upstream has no SRM, and the patch would need a fork anyway. We stay on 1.6.1 because moving to 1.7 adds risk and no user-visible gain.

ECF is MIT licensed, which does not cover SRM. SRM derives from D. Stanković's 2016 master's thesis and its source carries no author or licence, so we do not know who may publish it. The repo therefore went private on 2026-11-04. Josip asks the mentor at handover. Once confirmed, the repo goes public with the right licence, and direct merge gives way to branch protection.

Update, 2026-11-12: branch protection came first, with GitHub Pro, while the repo was still private.

Update, 2026-11-15: the mentor confirmed. SRM is under MIT and the repo is public, see [ADR 0002](0002-publish-the-repo-with-srm-under-mit.md).

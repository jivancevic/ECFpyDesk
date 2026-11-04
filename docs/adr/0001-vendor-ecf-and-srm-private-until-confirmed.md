---
status: accepted
---

# ECF and SRM live in this repo, and the repo stays private until the mentor confirms

Decided by Josip on 2026-11-04.

SRM existed only in a local folder outside any repo, and only a Mac binary was tracked here. A build for other platforms needs the source, so `native/` now holds it: ECF 1.6.1 with a small patch, and SRM. The patch adds `GEPChromosome::addFunction`, which SRM needs and upstream did not have at that version.

We vendor instead of using a submodule because upstream has no SRM, and the patch would need a fork anyway. We stay on 1.6.1 because moving to 1.7 adds risk and no user-visible gain.

ECF is MIT licensed, which does not cover SRM. SRM derives from D. Stanković's 2016 master's thesis and its source carries no author or licence, so we do not know who may publish it. The repo therefore went private on 2026-11-04. Josip asks the mentor at handover. Once confirmed, the repo goes public with the right licence, and direct merge gives way to branch protection.

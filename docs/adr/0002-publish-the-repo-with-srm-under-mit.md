---
status: accepted
---

# The repo is public, and SRM is under the MIT licence

Decided by Josip on 2026-11-15. Supersedes the "private until confirmed" part of [ADR 0001](0001-vendor-ecf-and-srm-private-until-confirmed.md); vendoring ECF and SRM stays as 0001 describes.

ADR 0001 kept the repo private because SRM's source carries no author or licence. On 2026-11-15 the mentor confirmed by email that the work may be published, with no special restrictions. So:

- The root `LICENSE` (MIT) now covers SRM as well as the Python app, and names D. Stanković, whose 2016 master's thesis SRM comes from, as its first copyright holder. The licence rests on the mentor's confirmation; the source files themselves still carry no header.
- `native/ecf` keeps its own MIT licence in `native/ecf/license.txt`.
- The repo goes public once this decision is merged.

MIT, rather than a separate licence for SRM, keeps one licence for everything that is not ECF, and it matches ECF, which SRM is built on.

# tsweer: changes from upstream FilmCraft

Required by the Apache License 2.0 (section 4b): files we changed carry this notice through
this list.

- Branding (user-visible only, applied by `studio/rebrand.py`): the app name tsweer,
  the bundle id `ps.creative.studio.tsweer`, Help links to studio.creative.ps and this repository. Crate names
  and file formats keep their upstream names.
- App icon: the tsweer tile (`assets/app-icon/`).
- Removed upstream's ArtCraft brand assets (`docs/brand/`), as their brand terms require of forks.
- README and NOTICE: the fork, its credits and the Creative Studio suite.
- No upstream Discord button in the header and no ArtCraft links in About.
- Right-to-left interface for Arabic: the patched egui from Creative Studio rsm in `vendor/egui`
  (`studio/RTL.md`), `crates/ui-egui/tests/rtl.rs`; edits to upstream files are listed in
  `RTL_RULES` in `studio/rebrand.py`.
- Arabic: IBM Plex Sans Arabic (OFL) as the Arabic UI font, `crates/ui-egui/src/i18n/bidi.rs`, and
  the Arabic catalog `crates/ui-egui/src/i18n/ar.tsv` (3495 entries, from `studio/ar-work/`).

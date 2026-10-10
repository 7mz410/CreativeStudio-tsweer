#!/usr/bin/env python3
"""Apply the ShibShib tsweer branding on top of upstream FilmCraft.

Only user-visible text is rebranded; crate names, file formats and other internals keep their
upstream names so `git merge upstream/main` stays easy. The script is idempotent: after merging
upstream, resolve any conflicts in favour of upstream and run it again.

    python3 shibshib/rebrand.py
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAME = 'ShibShib tsweer'
REPO = 'https://github.com/7mz410/ShibShib-tsweer'
SITE = 'https://shibshib.art'
# Persisted names that saved catalogs and presets refer to; renaming them would break those.
KEEP = ('the FilmCraft authors', 'FilmCraft Project')

# Exact replacements, applied before the general rename (and kept idempotent: skipped once done).
RTL_RULES = [
    ('Cargo.toml', '[workspace.dependencies]', '[patch.crates-io]\n# ShibShib: egui with a right-to-left switch for the Arabic interface (shibshib/RTL.md).\negui = { path = "vendor/egui" }\n\n[workspace.dependencies]'),
    ('crates/ui-egui/Cargo.toml', '[dependencies]\n', '[dependencies]\nunicode-bidi = "0.3.18"\n'),
    ('crates/ui-egui/src/i18n/mod.rs', 'mod catalog;\n', '/// ShibShib: Arabic in visual order for egui.\npub(crate) mod bidi;\nmod catalog;\n'),
    ('crates/ui-egui/src/i18n/mod.rs', '    /// Simplified Chinese, persisted as `zh-cn`.\n    #[serde(rename = "zh-cn")]\n    ZhCn,\n}', '    /// Simplified Chinese, persisted as `zh-cn`.\n    #[serde(rename = "zh-cn")]\n    ZhCn,\n    /// ShibShib: Arabic, right to left.\n    Ar,\n}'),
    ('crates/ui-egui/src/i18n/mod.rs', 'static UKRAINIAN: OnceLock<Catalog> = OnceLock::new();\n', 'static UKRAINIAN: OnceLock<Catalog> = OnceLock::new();\nstatic ARABIC: OnceLock<Catalog> = OnceLock::new();\n'),
    ('crates/ui-egui/src/i18n/mod.rs', '    pub const ALL: [Self; 6] = [Self::En, Self::Ja, Self::Es, Self::PtBr, Self::Uk, Self::ZhCn];', '    pub const ALL: [Self; 7] = [Self::En, Self::Ja, Self::Es, Self::PtBr, Self::Uk, Self::ZhCn, Self::Ar];'),
    ('crates/ui-egui/src/i18n/mod.rs', '            Self::Uk => "Українська",\n', '            Self::Uk => "Українська",\n            Self::Ar => "العربية",\n'),
    ('crates/ui-egui/src/i18n/mod.rs', '            "uk" => Some(Self::Uk),\n', '            "uk" => Some(Self::Uk),\n            "ar" => Some(Self::Ar),\n'),
    ('crates/ui-egui/src/i18n/mod.rs', 'const PRIMARY: [(&str, Language); 5] = [("en", Language::En), ("ja", Language::Ja), ("es", Language::Es), ("pt", Language::PtBr), ("uk", Language::Uk)];', 'const PRIMARY: [(&str, Language); 6] = [("en", Language::En), ("ja", Language::Ja), ("es", Language::Es), ("pt", Language::PtBr), ("uk", Language::Uk), ("ar", Language::Ar)];'),
    ('crates/ui-egui/src/i18n/mod.rs', '            Self::Uk => "uk",\n', '            Self::Uk => "uk",\n            Self::Ar => "ar",\n'),
    ('crates/ui-egui/src/i18n/mod.rs', '            Self::Uk => Some(UKRAINIAN.get_or_init(|| Catalog::parse(include_str!("uk.tsv")))),\n', '            Self::Uk => Some(UKRAINIAN.get_or_init(|| Catalog::parse(include_str!("uk.tsv")))),\n            Self::Ar => Some(ARABIC.get_or_init(|| Catalog::parse(&bidi::visual_catalog(include_str!("ar.tsv"))))),\n'),
    ('crates/ui-egui/src/lib.rs', '    fn frame(&mut self, ui: &mut egui::Ui) {\n        i18n::set_current(self.ui.language);\n', '    fn frame(&mut self, ui: &mut egui::Ui) {\n        i18n::set_current(self.ui.language);\n        // ShibShib: Arabic lays the interface out right to left (vendor/egui). The switch is\n        // process-wide, so unit tests, which run in parallel, leave it off (tests/rtl.rs covers it).\n        #[cfg(not(test))]\n        egui::set_rtl(i18n::bidi::RTL_CODES.contains(&self.ui.language.code()));\n'),
    ('crates/ui-egui/src/theme.rs', '    add_craft_fonts(&mut fonts);\n    crate::cjk::install(&mut fonts);\n    ctx.set_fonts(fonts);', '    add_craft_fonts(&mut fonts);\n    crate::cjk::install(&mut fonts);\n    // ShibShib: Arabic glyphs (IBM Plex Sans Arabic, OFL) after every family\'s own faces.\n    fonts.font_data.insert("plex-arabic".into(), Arc::new(FontData::from_static(include_bytes!("../../../assets/fonts/IBMPlexSansArabic-Regular.ttf"))));\n    for family in font_families() {\n        fonts.families.entry(family).or_default().push("plex-arabic".into());\n    }\n    ctx.set_fonts(fonts);'),
]

SPECIFIC = {
    # The ArtCraft wordmark (upstream's docs/brand/, removed) gives way to the ShibShib tsweer logo.
    'crates/ui-egui/src/brand.rs': [
        ('include_bytes!("../../../docs/brand/artcraft-logo-white.png")', 'include_bytes!("../../../docs/shibshib/tsweer-logo-white.png")'),
        ('include_bytes!("../../../docs/brand/artcraft-logo.png")', 'include_bytes!("../../../docs/shibshib/tsweer-logo.png")'),
    ],
    'crates/ui-egui/src/links.rs': [
        ('pub const WEBSITE: &str = "https://getartcraft.com";', f'pub const WEBSITE: &str = "{SITE}";'),
        ('pub const APP_PAGE: &str = "https://getartcraft.com/apps/filmcraft";', f'pub const APP_PAGE: &str = "{SITE}";'),
        ('pub const GITHUB: &str = "https://github.com/storytold/filmcraft";', f'pub const GITHUB: &str = "{REPO}";'),
        ('pub const ISSUES: &str = "https://github.com/storytold/filmcraft/issues";', f'pub const ISSUES: &str = "{REPO}/issues";'),
        ('        assert_eq!(APP_PAGE, format!("{WEBSITE}/apps/{APP}"));\n        assert_eq!(GITHUB, format!("https://github.com/storytold/{APP}"));',
         f'        assert_eq!(APP_PAGE, "{SITE}");\n        assert_eq!(GITHUB, "{REPO}");'),
    ],
    # No ShibShib Discord yet: the header's Discord button and the About dialog's ArtCraft links go.
    'crates/ui-egui/src/header.rs': [
        ('        let w = g.size().x + 34.0;\n', '        let w = 0.0; // ShibShib: no community Discord button yet\n'),
        ('        ui.painter().rect_filled(r, 12.0, if resp.hovered() { t.accent_hover } else { t.accent });\n        icons::paint(ui.painter(), Rect::from_center_size(pos2(r.min.x + 14.0, r.center().y), vec2(14.0, 14.0)), Icon::Chat, Color32::WHITE);\n        ui.painter().galley(pos2(r.min.x + 25.0, r.center().y - g.size().y / 2.0), g, Color32::WHITE);\n', '        let _ = (g, resp);\n'),
        ('        if resp.clicked() {\n            crate::links::open(ui.ctx(), crate::links::DISCORD);\n        }\n', ''),
    ],
    'crates/ui-egui/src/panels/dialogs.rs': [
        ('    link(ui, "discord", Icon::Chat, tl!("Join the ArtCraft Discord"), links::DISCORD, true);\n    ui.add_space(6.0);\n', ''),
        ('    link(ui, "website", Icon::Globe, "getartcraft.com", links::WEBSITE, false);\n', ''),
    ],
}
# Exact replacements inside string literals and catalogs, before the general rename.
LITERALS = [
    ('FilmCraft on getartcraft.com', 'ShibShib Website'),
    ('Join the ArtCraft Discord (discord.gg/artcraft)', 'The upstream community on Discord (discord.gg/artcraft)'),
    ('Join the ArtCraft Discord', 'Upstream Community on Discord'),
    ('Join the ArtCraft community on Discord', 'The upstream ArtCraft community on Discord'),
    ('ArtCraft Website', 'ShibShib Website'),
]

STRING = re.compile(r'"(?:[^"\\\n]|\\.)*"')


def rename(text: str) -> str:
    for a, b in LITERALS:
        text = text.replace(a, b)
    if any(k in text for k in KEEP):
        return text
    return text.replace('FilmCraft', NAME)


def rebrand_rust(path: Path) -> bool:
    src = path.read_text(encoding='utf-8')
    out = src
    for a, b in SPECIFIC.get(path.relative_to(ROOT).as_posix(), []):
        if not b or b not in out:
            out = out.replace(a, b)
    out = STRING.sub(lambda m: rename(m.group(0)), out)
    if out != src:
        path.write_text(out, encoding='utf-8')
    return out != src


def source_strings() -> set:
    """Every string literal in the (rebranded) Rust sources, without quotes."""
    found = set()
    for p in list((ROOT / 'crates').rglob('*.rs')) + list((ROOT / 'apps').rglob('*.rs')):
        found.update(m.group(0)[1:-1] for m in STRING.finditer(p.read_text(encoding='utf-8')))
    return found


SOURCES = None


def rebrand_locale(path: Path) -> bool:
    # Catalog rows are `context<TAB>English<TAB>translation`. A row is renamed only when its renamed
    # English text is a string the sources use (some crates outside the UI keep upstream's name),
    # and a second row for the same text (two upstream labels that rename alike) is dropped.
    global SOURCES
    if SOURCES is None:
        SOURCES = source_strings()
    src = path.read_text(encoding='utf-8')
    rows, seen = [], set()
    for line in src.split('\n'):
        cells = line.split('\t')
        if len(cells) >= 3 and not line.startswith('#'):
            renamed = rename(cells[1])
            if renamed != cells[1] and renamed in SOURCES:
                cells = [cells[0], renamed, *(rename(c) for c in cells[2:])]
                line = '\t'.join(cells)
            if (cells[0], cells[1]) in seen:
                continue
            seen.add((cells[0], cells[1]))
        rows.append(line)
    out = '\n'.join(rows)
    if out != src:
        path.write_text(out, encoding='utf-8')
    return out != src


def rebrand_plist(path: Path) -> bool:
    src = path.read_text(encoding='utf-8')
    out = re.sub(r'(<key>CFBundle(?:Display)?Name</key>\s*<string>)FilmCraft(</string>)', rf'\g<1>{NAME}\2', src)
    out = out.replace('<string>ai.storyteller.filmcraft</string>', '<string>com.shibshib.tsweer</string>')
    if out != src:
        path.write_text(out, encoding='utf-8')
    return out != src


def RUST_FILES():
    return sorted((ROOT / 'crates/ui-egui/src').rglob('*.rs')) + sorted((ROOT / 'apps/filmcraft/src').rglob('*.rs'))


def apply_rtl_rules() -> list:
    changed = []
    for rel, a, b in RTL_RULES:
        path = ROOT / rel
        src = path.read_text(encoding='utf-8')
        if b not in src and a in src:
            path.write_text(src.replace(a, b), encoding='utf-8')
            changed.append(path)
    return changed


def main():
    changed = apply_rtl_rules()
    changed += [p for p in RUST_FILES() if rebrand_rust(p)]
    changed += [p for p in sorted((ROOT / 'crates/ui-egui/src/i18n').glob('*.tsv')) if rebrand_locale(p)]
    web = ROOT / 'apps/filmcraft-web/web/index.html'
    html = web.read_text(encoding='utf-8')
    branded = html.replace('<title>FilmCraft</title>', f'<title>{NAME}</title>').replace('Loading FilmCraft&hellip;', f"Loading {NAME}&hellip;").replace('Loading FilmCraft…', f'Loading {NAME}…').replace('content="FilmCraft:', f'content="{NAME}:')
    if branded != html:
        web.write_text(branded, encoding='utf-8')
        changed.append(web)
    plist = ROOT / 'packaging/macos/Info.plist.in'
    if plist.exists() and rebrand_plist(plist):
        changed.append(plist)
    for p in changed:
        print('rebranded', p.relative_to(ROOT))


if __name__ == '__main__':
    main()

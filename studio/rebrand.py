#!/usr/bin/env python3
"""Apply the tsweer branding on top of upstream FilmCraft.

Only user-visible text is rebranded; crate names, file formats and other internals keep their
upstream names so `git merge upstream/main` stays easy. The script is idempotent: after merging
upstream, resolve any conflicts in favour of upstream and run it again.

    python3 studio/rebrand.py
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAME = 'tsweer'
REPO = 'https://github.com/7mz410/CreativeStudio-tsweer'
SITE = 'https://studio.creative.ps'
# Persisted names that saved catalogs and presets refer to; renaming them would break those.
KEEP = ('the FilmCraft authors', 'FilmCraft Project')

# Exact replacements, applied before the general rename (and kept idempotent: skipped once done).
RTL_RULES = [
    # About shows our links only (no Discord, no ArtCraft website).
    ('crates/ui-egui/tests/links_ui.rs', 'for id in ["about.discord", "about.website", "about.appPage", "about.github", "about.reportIssue"] {', 'for id in ["about.appPage", "about.github", "about.reportIssue"] {'),
    ('Cargo.toml', '[workspace.dependencies]', '[patch.crates-io]\n# Creative Studio: egui with a right-to-left switch for the Arabic interface (studio/RTL.md).\negui = { path = "vendor/egui" }\n\n[workspace.dependencies]'),
    ('crates/ui-egui/src/i18n/mod.rs', 'mod catalog;\n', '/// Creative Studio: Arabic in visual order for egui.\npub(crate) mod bidi;\nmod catalog;\n'),
    ('crates/ui-egui/src/i18n/mod.rs', 'static UKRAINIAN: OnceLock<Catalog> = OnceLock::new();\n', 'static UKRAINIAN: OnceLock<Catalog> = OnceLock::new();\nstatic ARABIC: OnceLock<Catalog> = OnceLock::new();\n'),
    ('crates/ui-egui/src/i18n/mod.rs', '            Self::Uk => "Українська",\n', '            Self::Uk => "Українська",\n            Self::Ar => "العربية",\n'),
    ('crates/ui-egui/src/i18n/mod.rs', '            "uk" => Some(Self::Uk),\n', '            "uk" => Some(Self::Uk),\n            "ar" => Some(Self::Ar),\n'),
    ('crates/ui-egui/src/i18n/mod.rs', '            Self::Uk => "uk",\n', '            Self::Uk => "uk",\n            Self::Ar => "ar",\n'),
    ('crates/ui-egui/src/i18n/mod.rs', '            Self::Uk => Some(UKRAINIAN.get_or_init(|| Catalog::parse(include_str!("uk.tsv")))),\n', '            Self::Uk => Some(UKRAINIAN.get_or_init(|| Catalog::parse(include_str!("uk.tsv")))),\n            Self::Ar => Some(ARABIC.get_or_init(|| Catalog::parse(&bidi::visual_catalog(include_str!("ar.tsv"))))),\n'),
    ('crates/ui-egui/src/lib.rs', '    fn frame(&mut self, ui: &mut egui::Ui) {\n        i18n::set_current(self.ui.language);\n', '    fn frame(&mut self, ui: &mut egui::Ui) {\n        i18n::set_current(self.ui.language);\n        // Creative Studio: Arabic lays the interface out right to left (vendor/egui). The switch is\n        // process-wide, so unit tests, which run in parallel, leave it off (tests/rtl.rs covers it).\n        #[cfg(not(test))]\n        egui::set_rtl(i18n::bidi::RTL_CODES.contains(&self.ui.language.code()));\n'),
    ('crates/ui-egui/src/theme.rs', '    add_craft_fonts(&mut fonts);\n    crate::cjk::install(&mut fonts);\n    ctx.set_fonts(fonts);', '    add_craft_fonts(&mut fonts);\n    crate::cjk::install(&mut fonts);\n    // Creative Studio: Arabic glyphs (IBM Plex Sans Arabic, OFL) after every family\'s own faces.\n    fonts.font_data.insert("plex-arabic".into(), Arc::new(FontData::from_static(include_bytes!("../../../assets/fonts/IBMPlexSansArabic-Regular.ttf"))));\n    for family in font_families() {\n        fonts.families.entry(family).or_default().push("plex-arabic".into());\n    }\n    ctx.set_fonts(fonts);'),
]

SPECIFIC = {
    # The ArtCraft wordmark (upstream's docs/brand/, removed) gives way to the tsweer logo.
    'crates/ui-egui/src/brand.rs': [
        ('include_bytes!("../../../docs/brand/artcraft-logo-white.png")', 'include_bytes!("../../../docs/studio/tsweer-logo-white.png")'),
        ('include_bytes!("../../../docs/brand/artcraft-logo.png")', 'include_bytes!("../../../docs/studio/tsweer-logo.png")'),
    ],
    'crates/ui-egui/src/links.rs': [
        ('pub const WEBSITE: &str = "https://getartcraft.com";', f'pub const WEBSITE: &str = "{SITE}";'),
        ('pub const APP_PAGE: &str = "https://getartcraft.com/apps/filmcraft";', f'pub const APP_PAGE: &str = "{SITE}";'),
        ('pub const GITHUB: &str = "https://github.com/storytold/filmcraft";', f'pub const GITHUB: &str = "{REPO}";'),
        ('pub const ISSUES: &str = "https://github.com/storytold/filmcraft/issues";', f'pub const ISSUES: &str = "{REPO}/issues";'),
        ('        assert_eq!(APP_PAGE, format!("{WEBSITE}/apps/{APP}"));\n        assert_eq!(GITHUB, format!("https://github.com/storytold/{APP}"));',
         f'        assert_eq!(APP_PAGE, "{SITE}");\n        assert_eq!(GITHUB, "{REPO}");'),
    ],
    # No Creative Studio Discord yet: the header's Discord button and the About dialog's ArtCraft links go.
    'crates/ui-egui/src/header.rs': [
        ('        let w = g.size().x + 34.0;\n', '        let w = 0.0; // Creative Studio: no community Discord button yet\n'),
        ('        ui.painter().rect_filled(r, 12.0, if resp.hovered() { t.accent_hover } else { t.accent });\n        icons::paint(ui.painter(), Rect::from_center_size(pos2(r.min.x + 14.0, r.center().y), vec2(14.0, 14.0)), Icon::Chat, Color32::WHITE);\n        ui.painter().galley(pos2(r.min.x + 25.0, r.center().y - g.size().y / 2.0), g, Color32::WHITE);\n', '        let _ = &g;\n'),
        ('        if resp.clicked() {\n            crate::links::open(ui.ctx(), crate::links::DISCORD);\n        }\n', ''),
    ],
    'crates/ui-egui/src/panels/dialogs.rs': [
        ('    link(ui, "discord", Icon::Chat, tl!("Join the ArtCraft Discord"), links::DISCORD, true);\n    ui.add_space(6.0);\n', ''),
        ('    link(ui, "website", Icon::Globe, "getartcraft.com", links::WEBSITE, false);\n', ''),
    ],
}
# Exact replacements inside string literals and catalogs, before the general rename.
LITERALS = [
    ('FilmCraft on getartcraft.com', 'Creative Studio Website'),
    ('Join the ArtCraft Discord (discord.gg/artcraft)', 'The upstream community on Discord (discord.gg/artcraft)'),
    ('Join the ArtCraft Discord', 'Upstream Community on Discord'),
    ('Join the ArtCraft community on Discord', 'The upstream ArtCraft community on Discord'),
    ('ArtCraft Website', 'Creative Studio Website'),
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
    out = out.replace('<string>ai.storyteller.filmcraft</string>', '<string>ps.creative.studio.tsweer</string>')
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
        if (not b or b not in src) and a in src:
            path.write_text(src.replace(a, b), encoding='utf-8')
            changed.append(path)
    return changed


def add_arabic_language() -> list:
    """Arabic in the language enum, `ALL` and `PRIMARY`, whatever languages upstream lists."""
    p = ROOT / 'crates/ui-egui/src/i18n/mod.rs'
    s = p.read_text(encoding='utf-8')
    o = s
    if '    Ar,\n' not in o:
        o = re.sub(r'\n\}\n\nstatic JAPANESE', '\n    /// Creative Studio: Arabic, right to left.\n    Ar,\n}\n\nstatic JAPANESE', o, count=1)
    m = re.search(r'pub const ALL: \[Self; (\d+)\] = \[([^\]]*)\];', o)
    if m and 'Self::Ar' not in m.group(2):
        o = o[:m.start()] + f'pub const ALL: [Self; {int(m.group(1)) + 1}] = [{m.group(2)}, Self::Ar];' + o[m.end():]
    m = re.search(r'const PRIMARY: \[\(&str, Language\); (\d+)\] = \[(.*?)\n?(\s*)\];', o, re.S)
    if m and 'Language::Ar' not in m.group(2):
        body = m.group(2).rstrip()
        if '\n' in body:
            body += '\n            ("ar", Language::Ar),'
        else:
            body += ', ("ar", Language::Ar)'
        o = o[:m.start()] + f'const PRIMARY: [(&str, Language); {int(m.group(1)) + 1}] = [{body}{"" if "\n" not in body else chr(10) + m.group(3)}];' + o[m.end():]
    if o != s:
        p.write_text(o, encoding='utf-8')
        return [p]
    return []


# Creative Studio saves projects as `.tsweer` (the same contents as upstream's `.fcproj`, which still
# opens). Save dialogs and default names use the new extension first; the open filters keep both. Autosave
# and recovery file names stay `.fcproj` (renaming them would orphan users' recovery files). Applied as
# exact replacements; each one is skipped once its new text is in the file.
EXT_FILES = {
    'crates/format/src/lib.rs': [
        ('pub const FORMAT_ID: &str = "filmcraft.project";\n',
         'pub const FORMAT_ID: &str = "filmcraft.project";\n'
         '/// Upstream\'s project extension: still opened.\n'
         'pub const EXTENSION: &str = "fcproj";\n'
         '/// Creative Studio saves projects as `.tsweer` (the same contents as `.fcproj`).\n'
         'pub const STUDIO_EXTENSION: &str = "tsweer";\n'),
    ],
    'crates/engine/src/project_manager.rs': [
        ('dest_dir.join(format!("{name}.fcproj"))', 'dest_dir.join(format!("{name}.{}", filmcraft_format::STUDIO_EXTENSION))'),
    ],
    'crates/engine/src/project_tools.rs': [
        ('dir.join(format!("{}.fcproj", sanitize(&name)))', 'dir.join(format!("{}.{}", sanitize(&name), filmcraft_format::STUDIO_EXTENSION))'),
        ('.filter(|e| e.path().extension().is_some_and(|x| x == "fcproj"))',
         '.filter(|e| e.path().extension().is_some_and(|x| x == filmcraft_format::STUDIO_EXTENSION || x == filmcraft_format::EXTENSION))'),
        ('let path = if t.ends_with(".fcproj") || t.contains',
         'let path = if t.ends_with(".fcproj") || t.ends_with(".tsweer") || t.contains'),
        ('templates_dir(s).map(|d| d.join(format!("{}.fcproj", sanitize(t))))',
         'templates_dir(s).map(|d| d.join(format!("{}.{}", sanitize(t), filmcraft_format::STUDIO_EXTENSION)))'),
    ],
    'crates/engine/src/commands.rs': [
        ('    let stem = path.strip_suffix(".fcproj").unwrap_or(path);\n    format!("{stem} (schema v{schema} backup).fcproj")',
         '    // The backup keeps the file\'s own extension (`.tsweer`, or upstream\'s `.fcproj`).\n'
         '    let (stem, ext) = match path.rsplit_once(\'.\') {\n'
         '        Some((stem, ext)) if ext == filmcraft_format::STUDIO_EXTENSION || ext == filmcraft_format::EXTENSION => (stem, ext),\n'
         '        _ => (path, filmcraft_format::STUDIO_EXTENSION),\n'
         '    };\n'
         '    format!("{stem} (schema v{schema} backup).{ext}")'),
    ],
    'crates/engine/src/media_browser.rs': [
        ('const PROJECT_EXTENSIONS: [&str; 5] = ["fcproj", ',
         'const PROJECT_EXTENSIONS: [&str; 6] = [filmcraft_format::STUDIO_EXTENSION, filmcraft_format::EXTENSION, '),
    ],
    'crates/ui-egui/src/lib.rs': [
        ('    ("file.exportSelectionProject", "FilmCraft Project", "fcproj"),',
         '    ("file.exportSelectionProject", "tsweer Project", "tsweer"),'),
        ('format!("{} copy.fcproj", self.session.project.name) } else { format!("{}.fcproj", self.session.project.name) }',
         'format!("{} copy.tsweer", self.session.project.name) } else { format!("{}.tsweer", self.session.project.name) }'),
    ],
    'crates/ui-egui/src/panels/menu_dialogs.rs': [
        ('(tl!("FilmCraft Project"), "fcproj", tlf!("{name} Selection.fcproj", name = app.session.project.name))',
         '(tl!("tsweer Project"), "tsweer", tlf!("{name} Selection.tsweer", name = app.session.project.name))'),
    ],
    'crates/ui-egui/tests/export_menu_ui.rs': [
        ('    ("file.exportSelectionProject", "fcproj"),', '    ("file.exportSelectionProject", "tsweer"),'),
    ],
    'crates/ui-egui/src/panels/project.rs': [
        ('let mut crumb = format!("{}.fcproj", app.session.project.name);',
         'let mut crumb = format!("{}.tsweer", app.session.project.name);'),
    ],
    'apps/filmcraft/src/main.rs': [
        ('.add_filter(filmcraft_ui_egui::i18n::t("FilmCraft Project"), &file_filters::extensions(&["fcproj"]))',
         '.add_filter(filmcraft_ui_egui::i18n::t("tsweer Project"), &file_filters::extensions(&["tsweer", "fcproj"]))'),
        ('    let project = t("FilmCraft Project");', '    let project = t("tsweer Project");'),
        ('    file_filters::extensions(&["fcproj"])\n', '    file_filters::extensions(&["tsweer", "fcproj"])\n'),
        ('assert_eq!(project.first().map(String::as_str), Some("fcproj"));',
         'assert_eq!(project.first().map(String::as_str), Some("tsweer"));'),
    ],
    'apps/filmcraft/src/args.rs': [
        ('Path::new(path).extension().is_some_and(|e| e.eq_ignore_ascii_case("fcproj"))',
         'Path::new(path).extension().is_some_and(|e| e.eq_ignore_ascii_case("tsweer") || e.eq_ignore_ascii_case("fcproj"))'),
        ('for p in ["cut.fcproj", "CUT.FCPROJ",', 'for p in ["cut.tsweer", "cut.fcproj", "CUT.FCPROJ",'),
    ],
    'apps/filmcraft-web/src/import.rs': [
        ('.partition(|f| f.name().to_ascii_lowercase().ends_with(".fcproj"));',
         '.partition(|f| {\n            let n = f.name().to_ascii_lowercase();\n            n.ends_with(".tsweer") || n.ends_with(".fcproj")\n        });'),
        ('pick(&["fcproj"], false);', 'pick(&["tsweer", "fcproj"], false);'),
        ('/// Open a `.fcproj` file picked or dropped by the user.', '/// Open a `.tsweer` (or `.fcproj`) file picked or dropped by the user.'),
    ],
    # Finder: the owned document type and its exported type. The `.fcproj` type stays as it is.
    'packaging/macos/Info.plist.in': [
        ('    </dict>\n  </array>\n\n  <!-- Filmcraft\'s own format. -->',
         '    </dict>\n'
         '    <dict>\n'
         '      <key>CFBundleTypeName</key>\n'
         '      <string>tsweer Project</string>\n'
         '      <key>CFBundleTypeRole</key>\n'
         '      <string>Editor</string>\n'
         '      <key>LSHandlerRank</key>\n'
         '      <string>Owner</string>\n'
         '      <key>LSItemContentTypes</key>\n'
         '      <array>\n'
         '        <string>ps.creative.studio.tsweer.project</string>\n'
         '      </array>\n'
         '    </dict>\n'
         '  </array>\n\n  <!-- Filmcraft\'s own format. -->'),
        ('  <key>UTExportedTypeDeclarations</key>\n  <array>\n',
         '  <key>UTExportedTypeDeclarations</key>\n  <array>\n'
         '    <dict>\n'
         '      <key>UTTypeIdentifier</key>\n'
         '      <string>ps.creative.studio.tsweer.project</string>\n'
         '      <key>UTTypeDescription</key>\n'
         '      <string>tsweer Project</string>\n'
         '      <key>UTTypeConformsTo</key>\n'
         '      <array>\n'
         '        <string>public.data</string>\n'
         '        <string>public.json</string>\n'
         '      </array>\n'
         '      <key>UTTypeIconFile</key>\n'
         '      <string>FilmCraft</string>\n'
         '      <key>UTTypeTagSpecification</key>\n'
         '      <dict>\n'
         '        <key>public.filename-extension</key>\n'
         '        <array><string>tsweer</string></array>\n'
         '        <key>public.mime-type</key>\n'
         '        <array><string>application/x-tsweer</string></array>\n'
         '      </dict>\n'
         '    </dict>\n'),
    ],
    # Linux: the MIME type for `.tsweer`, and the desktop entry opens it.
    'packaging/linux/ai.storyteller.filmcraft.mime.xml': [
        ('  </mime-type>\n</mime-info>',
         '  </mime-type>\n'
         '  <mime-type type="application/x-tsweer">\n'
         '    <comment>tsweer project</comment>\n'
         '    <sub-class-of type="application/json"/>\n'
         '    <icon name="ai.storyteller.filmcraft"/>\n'
         '    <glob pattern="*.tsweer"/>\n'
         '  </mime-type>\n'
         '</mime-info>'),
    ],
    'packaging/linux/ai.storyteller.filmcraft.desktop': [
        ('MimeType=application/x-filmcraft;', 'MimeType=application/x-tsweer;application/x-filmcraft;'),
    ],
    'packaging/linux/ai.storyteller.filmcraft.metainfo.xml.in': [
        ('<mediatype>application/x-filmcraft</mediatype>',
         '<mediatype>application/x-tsweer</mediatype>\n    <mediatype>application/x-filmcraft</mediatype>'),
    ],
    # Build notes: the extension change is recorded with the other changes from upstream.
    'studio/CHANGES.md': [
        ('this list.\n\n- Branding', 'this list.\n\n- Branding'),
        ('Crate names\n  and file formats keep their upstream names.',
         'Crate names\n  keep their upstream names. Projects save as `.tsweer`; upstream\'s `.fcproj` still opens.'),
    ],
}
# A test for the extension rules, appended to the engine's file tests (once).
EXT_APPEND = {
    'crates/engine/src/file_tests.rs': (
        'fn tsweer_save_and_fcproj_open',
        '\n/// Creative Studio: a project saves as `.tsweer`, and upstream\'s `.fcproj` still opens.\n'
        '#[test]\n'
        'fn tsweer_save_and_fcproj_open() {\n'
        '    let d = temp_dir("tsweer-ext");\n'
        '    let saved = d.join("cut.tsweer").to_string_lossy().to_string();\n'
        '    demo().execute("file.saveAs", json!({"path": saved})).unwrap();\n'
        '    assert!(std::path::Path::new(&saved).is_file());\n'
        '    let old = d.join("old.fcproj").to_string_lossy().to_string();\n'
        '    demo().execute("file.saveAs", json!({"path": old})).unwrap();\n'
        '    let mut s = Session::default();\n'
        '    s.execute("file.open", json!({"path": old})).unwrap();\n'
        '    assert_eq!(s.path.as_deref(), Some(old.as_str()));\n'
        '}\n'
    ),
}


def rename_project_rows() -> list:
    # The project label's catalog rows follow the new label (`tsweer Project`); the translation keeps
    # its words and only the product name changes. Menu labels that contain "Selection as" stay as they are.
    changed = []
    for path in sorted((ROOT / 'crates/ui-egui/src/i18n').glob('*.tsv')):
        src = path.read_text(encoding='utf-8')
        rows = [line.replace('FilmCraft', NAME) if line.startswith('\tFilmCraft Project\t')
                else line.replace('.fcproj', '.tsweer') if line.startswith('\t{name} Selection.fcproj\t')
                else line
                for line in src.split('\n')]
        out = '\n'.join(rows)
        if out != src:
            path.write_text(out, encoding='utf-8')
            changed.append(path)
    return changed


def apply_extension_rules() -> list:
    changed = rename_project_rows()
    for rel, pairs in EXT_FILES.items():
        path = ROOT / rel
        src = path.read_text(encoding='utf-8')
        out = src
        for a, b in pairs:
            if b not in out:
                out = out.replace(a, b)
        if out != src:
            path.write_text(out, encoding='utf-8')
            changed.append(path)
    for rel, (marker, text) in EXT_APPEND.items():
        path = ROOT / rel
        src = path.read_text(encoding='utf-8')
        if marker not in src:
            path.write_text(src.rstrip('\n') + '\n' + text, encoding='utf-8')
            changed.append(path)
    return changed


def main():
    changed = apply_rtl_rules()
    changed += add_arabic_language()
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
    changed += apply_extension_rules()
    for p in changed:
        print('rebranded', p.relative_to(ROOT))


# Creative Studio: the macOS app folder in the .dmg and the volume name carry our name
# (packaging/macos/package.sh). Bundle and binary names inside the package stay as upstream has them.
PACKAGING_NAMES = {
    'packaging/macos/package.sh': [
        ('FilmCraft.app', 'tsweer.app'),
        ('-volname "FilmCraft"', '-volname "tsweer"'),
        ('-hfs-volume-name "FilmCraft"', '-hfs-volume-name "tsweer"'),
    ],
}


def apply_packaging_names() -> list:
    changed = []
    for rel, pairs in PACKAGING_NAMES.items():
        path = ROOT / rel
        src = path.read_text(encoding='utf-8')
        out = src
        for a, b in pairs:
            out = out.replace(a, b)
        if out != src:
            path.write_text(out, encoding='utf-8')
            changed.append(path)
    return changed


if __name__ == '__main__':
    main()
    for _p in apply_packaging_names():
        print('rebranded', _p.relative_to(ROOT))


# Creative Studio: the app's Arabic name in its Arabic interface (studio/arabic_names.py).
import sys  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
import arabic_names  # noqa: E402
for _p in arabic_names.apply(ROOT, NAME, "تصوير"):
    print("rebranded", _p.relative_to(ROOT))

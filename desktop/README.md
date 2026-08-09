# FinanceTracker Desktop App

A fully offline desktop finance tracker built with Tauri v2, React, and Rust. No account or server required. Users choose a local SQLite file to store their data.

- Platforms: Windows, macOS, Linux
- Languages: English, Portuguese (Brazil), Spanish

## Prerequisites

- **Node.js** 20+
- **Rust** toolchain — install via [rustup](https://rustup.rs/)

### Platform-Specific Dependencies

**Linux (Debian/Ubuntu):**

```bash
sudo apt install libwebkit2gtk-4.1-dev libappindicator3-dev librsvg2-dev patchelf libssl-dev
```

**macOS:**

```bash
xcode-select --install
```

**Windows:**

- [Microsoft Visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
- [WebView2](https://developer.microsoft.com/en-us/microsoft-edge/webview2/) (included in Windows 11; install manually on Windows 10)

## Development

```bash
cd desktop
npm install
npm run tauri dev
```

This starts the app with hot reload for both the React frontend and the Rust backend.

## Building for Production

```bash
npm run tauri build
```

Build output by platform:

| Platform | Output |
|---|---|
| macOS | `src-tauri/target/release/bundle/dmg/*.dmg` |
| Windows | `src-tauri/target/release/bundle/msi/*.msi` |
| Linux | `src-tauri/target/release/bundle/appimage/*.AppImage`, `deb/*.deb` |

### macOS Universal Binary

To build a universal binary supporting both Apple Silicon and Intel:

```bash
npm run tauri build -- --target universal-apple-darwin
```

## Project Structure

```
desktop/
├── src/                  # React frontend
│   ├── components/
│   ├── pages/
│   └── i18n/             # Translation files
│       ├── en.json
│       ├── pt-BR.json
│       ├── es.json
│       └── index.js
├── src-tauri/            # Rust backend
│   ├── src/
│   │   └── main.rs
│   ├── Cargo.toml
│   └── tauri.conf.json
├── package.json
└── vite.config.js
```

## Demo Database

A bundled `demo.db` file is included with sample transactions, categories, and budgets for testing.

To regenerate the demo database:

```bash
python scripts/generate_demo.py
```

## CI/CD

Two GitHub Actions workflows cover the desktop app.

### `.github/workflows/desktop-ci.yml` — per-PR checks

Runs on pull requests and pushes to `main` that touch `desktop/`. Builds the
frontend and runs `cargo check` against all four targets, so a compile break on
Windows or Intel macOS is caught without paying for full installer bundling.
`cargo fmt` and `cargo clippy` also run, but are advisory — see the comment in
the workflow for how to make them blocking.

### `.github/workflows/desktop-release.yml` — installers

- **Trigger:** push a tag matching `desktop-v*` (e.g. `desktop-v1.0.0`), or run
  it manually from the Actions tab.
- **Builds:**

  | Target | Runner | Output |
  |---|---|---|
  | macOS Apple Silicon (`aarch64`) | `macos-latest` | `.dmg`, `.app.tar.gz` |
  | macOS Intel (`x86_64`) | `macos-latest`, cross-compiled | `.dmg`, `.app.tar.gz` |
  | Linux `x86_64` | `ubuntu-22.04` | `.AppImage`, `.deb`, `.rpm` |
  | Windows `x86_64` | `windows-latest` | `.msi`, `.exe` (NSIS) |

- **Output:** every installer is uploaded as a build artifact; on a tag, a
  **draft** GitHub release is created with all of them attached.

Intel macOS is cross-compiled from the ARM runner rather than built on a
`macos-13` Intel image, since GitHub is retiring those. This is the same
mechanism Tauri's `universal-apple-darwin` build uses internally.

To cut a release, bump `version` in `src-tauri/tauri.conf.json` to match, then:

```bash
git tag desktop-v1.0.0
git push origin desktop-v1.0.0
```

The workflow warns if the tag and `tauri.conf.json` version disagree, because
the installer filenames come from the config, not the tag.

### Code signing (optional)

The release workflow passes these repository secrets through to
`tauri-action` when they are set, and skips signing entirely when they are not:

`APPLE_CERTIFICATE`, `APPLE_CERTIFICATE_PASSWORD`, `APPLE_SIGNING_IDENTITY`,
`APPLE_ID`, `APPLE_PASSWORD`, `APPLE_TEAM_ID`, `TAURI_SIGNING_PRIVATE_KEY`,
`TAURI_SIGNING_PRIVATE_KEY_PASSWORD`.

Until macOS signing secrets are configured, users must right-click → Open on
first launch.

## Adding Translations

1. Copy `src/i18n/en.json` to a new file (e.g., `fr.json`).
2. Translate all string values.
3. Register the new locale in `src/i18n/index.js`.

# Winter Cabin

A cosy snowy desktop for macOS 13 or later: a painted winter cabin scene with
gentle ambient motion behind your windows, and a layer of real falling snow in
front of them that drifts up on the Dock and on your window tops, takes
snowballs when you click the desktop, builds snowmen, and gets cleared every
few minutes by a small yellow plow.

Menu-bar only — no Dock icon, no window.

## What is in here

```
Package.swift                SwiftPM manifest (macOS 13+, universal)
Sources/WinterCabin/         the app
  main.swift                 entry point, menu-bar agent
  AppDelegate.swift          wires the layers together
  Settings.swift             user defaults and the snow density levels
  SceneManifest.swift        anchor points in the artwork + aspect-fill mapping
  Textures.swift             procedural dot and flake textures
  AmbientScene.swift         smoke, twinkling lights, window flicker, lake shimmer
  WallpaperController.swift  desktop-level window, one per screen
  SnowScene.swift            falling snow, piles, snowballs, snowmen, the plow
  SnowPile.swift             drift height fields
  SurfaceTracker.swift       Dock and window frames from CGWindowListCopyWindowInfo
  Figures.swift              snowball, snowman and snowplow artwork
  OverlayController.swift    click-through overlay window + global click monitor
  MenuBarController.swift    the snowflake menu
  WallpaperSetter.swift      sets and restores the desktop picture
  LaunchAtLogin.swift        SMAppService
  PowerMonitor.swift         pause on lock, display sleep and Low Power Mode
  WelcomeWindowController.swift  first-run explainer
  Resources/
    scene.jpg                live-layer base plate
    scene-manifest.json      measured anchor points

art/source.webp              the painted source artwork
tools/prepare_art.py         builds the wallpapers, base plate and manifest
tools/make_icon.py           builds scripts/AppIcon.iconset
tools/make_install_pdf.py    builds dist/How to install.pdf
tools/render_wallpaper.py    the earlier fully procedural scene renderer (unused)

scripts/build-app.sh         universal build + bundle + sign
scripts/make-dmg.sh          packs the .dmg
scripts/Info.plist           bundle Info.plist
scripts/AppIcon.iconset/     app icon PNGs (iconutil turns these into .icns)

Wallpapers/                  static stills, shipped inside the .dmg
dist/How to install.pdf      the guide that ships inside the .dmg
.github/workflows/build.yml  builds the .dmg on a macOS runner
```

## Building

On a Mac with Xcode or the Command Line Tools:

```sh
bash scripts/build-app.sh      # -> build/Winter Cabin.app  (arm64 + x86_64)
bash scripts/make-dmg.sh       # -> dist/WinterCabin.dmg
```

Without a Mac, push this repository to GitHub. The workflow builds it on a
`macos-14` runner and uploads `WinterCabin.dmg` as a build artifact; pushing a
`v*` tag also attaches it to a release.

### Signing

`build-app.sh` ad-hoc signs by default, so macOS shows the "unidentified
developer" warning on first launch (the install guide explains the right-click
→ Open workaround). With a paid Apple Developer ID you can avoid the warning
entirely:

```sh
DEVELOPER_ID="Developer ID Application: Your Name (TEAMID)" \
NOTARY_PROFILE="your-notarytool-keychain-profile" \
bash scripts/build-app.sh
```

## Permissions

None. Window positions come from `CGWindowListCopyWindowInfo` using only
`kCGWindowBounds`, `kCGWindowOwnerName` and `kCGWindowLayer`, none of which are
gated behind Screen Recording. Window titles and window images would be, so the
app never asks for them. The click monitor is an `NSEvent` global monitor for
mouse events, which does not need Accessibility (keyboard monitors would), and
it only observes — the overlay window sets `ignoresMouseEvents = true`, so
clicks always reach the Dock, desktop icons and apps.

## Regenerating the artwork assets

If you replace `art/source.webp` with a higher-resolution version of the same
painting, rebuild everything that derives from it:

```sh
python tools/prepare_art.py      # wallpapers, base plate, manifest
python tools/make_icon.py        # app icon
python tools/make_install_pdf.py # install guide
```

The anchor points in `tools/prepare_art.py` (`build_manifest`) are normalised,
so they survive a resolution change but would need re-measuring if the painting
itself changes.

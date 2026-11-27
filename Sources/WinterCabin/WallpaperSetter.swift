import AppKit

/// Sets the desktop picture to the Winter Cabin scene and puts the user's own
/// one back when the app quits.
enum WallpaperSetter {

    /// The image is copied out of the bundle so the desktop picture keeps
    /// working if the app is moved, and so macOS has a stable path to remember.
    private static var installedURL: URL? {
        guard let source = Textures.sceneURL() else { return nil }
        let support = FileManager.default.urls(for: .applicationSupportDirectory,
                                               in: .userDomainMask).first
        guard let folder = support?.appendingPathComponent("Winter Cabin", isDirectory: true)
        else { return nil }

        let destination = folder.appendingPathComponent("Winter Cabin.jpg")
        do {
            try FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)
            let sizeOf: (URL) -> Int? = { url in
                (try? FileManager.default.attributesOfItem(atPath: url.path))?[.size] as? Int
            }
            let needsCopy = !FileManager.default.fileExists(atPath: destination.path)
                || sizeOf(destination) != sizeOf(source)
            if needsCopy {
                if FileManager.default.fileExists(atPath: destination.path) {
                    try FileManager.default.removeItem(at: destination)
                }
                try FileManager.default.copyItem(at: source, to: destination)
            }
            return destination
        } catch {
            NSLog("Winter Cabin: could not install wallpaper: \(error)")
            return source
        }
    }

    private static func key(for screen: NSScreen) -> String {
        let field = NSDeviceDescriptionKey("NSScreenNumber")
        if let number = screen.deviceDescription[field] as? NSNumber {
            return number.stringValue
        }
        return "screen-\(NSScreen.screens.firstIndex(of: screen) ?? 0)"
    }

    static func apply() {
        guard let url = installedURL else { return }
        var previous = Settings.shared.previousWallpaper

        for screen in NSScreen.screens {
            let id = key(for: screen)
            if previous[id] == nil,
               let current = NSWorkspace.shared.desktopImageURL(for: screen),
               current != url {
                previous[id] = current.path
            }
            do {
                try NSWorkspace.shared.setDesktopImageURL(url, for: screen, options: [:])
            } catch {
                NSLog("Winter Cabin: could not set desktop picture: \(error)")
            }
        }
        Settings.shared.previousWallpaper = previous
    }

    static func restore() {
        let previous = Settings.shared.previousWallpaper
        guard !previous.isEmpty else { return }

        for screen in NSScreen.screens {
            guard let path = previous[key(for: screen)] else { continue }
            let url = URL(fileURLWithPath: path)
            guard FileManager.default.fileExists(atPath: url.path) else { continue }
            try? NSWorkspace.shared.setDesktopImageURL(url, for: screen, options: [:])
        }
        Settings.shared.previousWallpaper = [:]
    }
}

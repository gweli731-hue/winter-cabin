import Foundation

enum SnowDensity: Int, CaseIterable {
    case light = 0
    case medium = 1
    case blizzard = 2

    var flakeCount: Int {
        switch self {
        case .light:    return 160
        case .medium:   return 420
        case .blizzard: return 950
        }
    }

    /// Flakes added per second, which drives how fast the piles grow.
    var spawnRate: Double {
        switch self {
        case .light:    return 14
        case .medium:   return 38
        case .blizzard: return 90
        }
    }

    var title: String {
        switch self {
        case .light:    return "Light"
        case .medium:   return "Medium"
        case .blizzard: return "Blizzard"
        }
    }
}

final class Settings {
    static let shared = Settings()
    static let didChange = Notification.Name("WinterCabinSettingsDidChange")

    private let store = UserDefaults.standard

    private init() {
        store.register(defaults: [
            Keys.snowEnabled: true,
            Keys.density: SnowDensity.medium.rawValue,
            Keys.pileOnWindows: true,
            Keys.snowballsOnClick: true,
            Keys.ambientEnabled: true,
            Keys.setsWallpaper: true,
            Keys.hasSeenWelcome: false,
            Keys.plowIntervalMinutes: 7
        ])
    }

    private enum Keys {
        static let snowEnabled = "snowEnabled"
        static let density = "density"
        static let pileOnWindows = "pileOnWindows"
        static let snowballsOnClick = "snowballsOnClick"
        static let ambientEnabled = "ambientEnabled"
        static let setsWallpaper = "setsWallpaper"
        static let hasSeenWelcome = "hasSeenWelcome"
        static let plowIntervalMinutes = "plowIntervalMinutes"
        static let previousWallpaper = "previousWallpaperByScreen"
    }

    var snowEnabled: Bool {
        get { return store.bool(forKey: Keys.snowEnabled) }
        set { store.set(newValue, forKey: Keys.snowEnabled); post() }
    }

    var density: SnowDensity {
        get { return SnowDensity(rawValue: store.integer(forKey: Keys.density)) ?? .medium }
        set { store.set(newValue.rawValue, forKey: Keys.density); post() }
    }

    var pileOnWindows: Bool {
        get { return store.bool(forKey: Keys.pileOnWindows) }
        set { store.set(newValue, forKey: Keys.pileOnWindows); post() }
    }

    var snowballsOnClick: Bool {
        get { return store.bool(forKey: Keys.snowballsOnClick) }
        set { store.set(newValue, forKey: Keys.snowballsOnClick); post() }
    }

    var ambientEnabled: Bool {
        get { return store.bool(forKey: Keys.ambientEnabled) }
        set { store.set(newValue, forKey: Keys.ambientEnabled); post() }
    }

    var setsWallpaper: Bool {
        get { return store.bool(forKey: Keys.setsWallpaper) }
        set { store.set(newValue, forKey: Keys.setsWallpaper); post() }
    }

    var hasSeenWelcome: Bool {
        get { return store.bool(forKey: Keys.hasSeenWelcome) }
        set { store.set(newValue, forKey: Keys.hasSeenWelcome) }
    }

    var plowIntervalMinutes: Int {
        get { return max(1, store.integer(forKey: Keys.plowIntervalMinutes)) }
        set { store.set(newValue, forKey: Keys.plowIntervalMinutes); post() }
    }

    /// Remembers what the desktop picture was before we touched it, keyed by screen.
    var previousWallpaper: [String: String] {
        get { return store.dictionary(forKey: Keys.previousWallpaper) as? [String: String] ?? [:] }
        set { store.set(newValue, forKey: Keys.previousWallpaper) }
    }

    private func post() {
        NotificationCenter.default.post(name: Settings.didChange, object: nil)
    }
}

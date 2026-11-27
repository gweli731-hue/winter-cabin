import AppKit

final class AppDelegate: NSObject, NSApplicationDelegate {

    private let wallpaperLayer = WallpaperController()
    private let overlayLayer = OverlayController()
    private var menuBar: MenuBarController?

    func applicationDidFinishLaunching(_ notification: Notification) {
        PowerMonitor.shared.start()

        menuBar = MenuBarController(overlay: overlayLayer)

        if Settings.shared.setsWallpaper {
            WallpaperSetter.apply()
        }

        wallpaperLayer.start()
        overlayLayer.start()

        if !Settings.shared.hasSeenWelcome {
            Settings.shared.hasSeenWelcome = true
            WelcomeWindowController().show()
        }
    }

    func applicationWillTerminate(_ notification: Notification) {
        overlayLayer.stop()
        wallpaperLayer.stop()
        WallpaperSetter.restore()
    }

    func applicationSupportsSecureRestorableState(_ app: NSApplication) -> Bool {
        return true
    }
}

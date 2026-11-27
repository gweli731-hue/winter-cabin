import AppKit
import SpriteKit

/// One borderless, click-through window per screen, sitting at desktop level:
/// behind desktop icons and behind every app window.
final class WallpaperController: NSObject {

    private var windows: [NSWindow] = []
    private let manifest = SceneManifest.load()

    func start() {
        NotificationCenter.default.addObserver(
            self, selector: #selector(screensChanged),
            name: NSApplication.didChangeScreenParametersNotification, object: nil)
        NotificationCenter.default.addObserver(
            self, selector: #selector(settingsChanged), name: Settings.didChange, object: nil)
        NotificationCenter.default.addObserver(
            self, selector: #selector(powerChanged), name: PowerMonitor.didChange, object: nil)
        rebuild()
    }

    func stop() {
        windows.forEach { $0.orderOut(nil) }
        windows.removeAll()
    }

    // MARK: - windows

    private func rebuild() {
        stop()
        guard Settings.shared.ambientEnabled else { return }

        for screen in NSScreen.screens {
            let window = NSWindow(contentRect: screen.frame,
                                  styleMask: .borderless,
                                  backing: .buffered,
                                  defer: false,
                                  screen: screen)
            window.level = NSWindow.Level(rawValue: Int(CGWindowLevelForKey(.desktopWindow)))
            window.collectionBehavior = [.canJoinAllSpaces, .stationary, .ignoresCycle]
            window.ignoresMouseEvents = true
            window.isOpaque = true
            window.hasShadow = false
            window.backgroundColor = .black
            window.isReleasedWhenClosed = false
            window.setFrame(screen.frame, display: true)

            let view = SKView(frame: CGRect(origin: .zero, size: screen.frame.size))
            view.autoresizingMask = [.width, .height]
            view.preferredFramesPerSecond = 24
            view.ignoresSiblingOrder = true
            view.allowsTransparency = false

            let scene = AmbientScene(size: screen.frame.size, manifest: manifest)
            view.presentScene(scene)
            window.contentView = view

            window.orderFrontRegardless()
            windows.append(window)
        }
        applyPowerState()
    }

    private func applyPowerState() {
        let animate = PowerMonitor.shared.shouldAnimate
        for window in windows {
            guard let view = window.contentView as? SKView else { continue }
            view.isPaused = !animate
            // Low Power Mode still shows the scene, just frozen, which costs nothing.
            view.preferredFramesPerSecond = animate ? 24 : 1
        }
    }

    @objc private func screensChanged() { rebuild() }
    @objc private func powerChanged()   { applyPowerState() }

    @objc private func settingsChanged() {
        let wanted = Settings.shared.ambientEnabled
        if wanted && windows.isEmpty { rebuild() }
        if !wanted && !windows.isEmpty { stop() }
    }
}

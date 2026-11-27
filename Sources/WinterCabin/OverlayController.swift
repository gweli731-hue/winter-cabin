import AppKit
import SpriteKit

/// Owns the transparent, click-through snow window on every screen.
final class OverlayController {

    private var windows: [NSWindow] = []
    private var scenes: [SnowScene] = []
    private let tracker = SurfaceTracker()
    private var clickMonitor: Any?

    func start() {
        NotificationCenter.default.addObserver(
            self, selector: #selector(screensChanged),
            name: NSApplication.didChangeScreenParametersNotification, object: nil)
        NotificationCenter.default.addObserver(
            self, selector: #selector(settingsChanged), name: Settings.didChange, object: nil)
        NotificationCenter.default.addObserver(
            self, selector: #selector(powerChanged), name: PowerMonitor.didChange, object: nil)

        tracker.onUpdate = { [weak self] surfaces in
            guard let self = self else { return }
            for scene in self.scenes { scene.sync(surfaces: surfaces) }
        }

        rebuild()
    }

    func stop() {
        tracker.stop()
        if let monitor = clickMonitor {
            NSEvent.removeMonitor(monitor)
            clickMonitor = nil
        }
        windows.forEach { $0.orderOut(nil) }
        windows.removeAll()
        scenes.removeAll()
    }

    func sendPlow() {
        scenes.forEach { $0.sendPlow() }
    }

    // MARK: - windows

    private func rebuild() {
        stop()
        guard Settings.shared.snowEnabled else { return }

        for screen in NSScreen.screens {
            let window = NSWindow(contentRect: screen.frame,
                                  styleMask: .borderless,
                                  backing: .buffered,
                                  defer: false,
                                  screen: screen)
            // above the Dock (level 20) and ordinary app windows
            window.level = .statusBar
            window.collectionBehavior = [.canJoinAllSpaces, .stationary,
                                         .fullScreenAuxiliary, .ignoresCycle]
            window.ignoresMouseEvents = true           // never steals a click
            window.isOpaque = false
            window.backgroundColor = .clear
            window.hasShadow = false
            window.isReleasedWhenClosed = false
            window.setFrame(screen.frame, display: true)

            let view = SKView(frame: CGRect(origin: .zero, size: screen.frame.size))
            view.autoresizingMask = [.width, .height]
            view.allowsTransparency = true
            view.ignoresSiblingOrder = true
            view.preferredFramesPerSecond = 60

            let scene = SnowScene(size: screen.frame.size)
            scene.screenFrame = screen.frame
            view.presentScene(scene)
            window.contentView = view

            window.orderFrontRegardless()
            windows.append(window)
            scenes.append(scene)
        }

        tracker.start(interval: 0.5)
        installClickMonitor()
        applyPowerState()
    }

    private func applyPowerState() {
        let animate = PowerMonitor.shared.shouldAnimate
        for window in windows {
            guard let view = window.contentView as? SKView else { continue }
            view.isPaused = !animate
            view.preferredFramesPerSecond = animate ? 60 : 1
        }
    }

    // MARK: - clicks on the bare desktop

    private func installClickMonitor() {
        // A global monitor observes only; it never consumes the event, so the
        // Dock, desktop icons and apps all keep their clicks. Mouse monitors do
        // not need Accessibility permission (keyboard ones would).
        clickMonitor = NSEvent.addGlobalMonitorForEvents(matching: [.leftMouseDown]) {
            [weak self] _ in
            self?.handleClick()
        }
    }

    private func handleClick() {
        guard Settings.shared.snowEnabled, Settings.shared.snowballsOnClick else { return }

        let point = NSEvent.mouseLocation
        guard let index = NSScreen.screens.firstIndex(where: { $0.frame.contains(point) }),
              index < scenes.count else { return }
        let screen = NSScreen.screens[index]

        // not the menu bar
        if point.y > screen.visibleFrame.maxY { return }
        // not the Dock
        if let dock = tracker.dockRect, dock.insetBy(dx: -2, dy: -2).contains(point) { return }
        // not on top of any app window
        for surface in tracker.surfaces where surface.kind == .appWindow {
            if surface.rect.contains(point) { return }
        }

        let local = CGPoint(x: point.x - screen.frame.minX,
                            y: point.y - screen.frame.minY)
        scenes[index].dropSnowball(at: local)
    }

    // MARK: - notifications

    @objc private func screensChanged() { rebuild() }
    @objc private func powerChanged() { applyPowerState() }

    @objc private func settingsChanged() {
        let wanted = Settings.shared.snowEnabled
        if wanted && windows.isEmpty { rebuild() }
        if !wanted && !windows.isEmpty { stop() }
    }
}

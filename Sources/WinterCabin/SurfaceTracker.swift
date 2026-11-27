import AppKit

/// A horizontal edge that snow can settle on.
struct Surface {
    enum Kind { case screenBottom, dock, appWindow }

    let key: String
    let kind: Kind
    /// In AppKit global coordinates (origin bottom-left of the primary screen).
    let rect: CGRect

    /// The edge snow lands on.
    var topY: CGFloat { return rect.maxY }
}

/// Reads the Dock and visible app window frames from the window server.
///
/// Only `kCGWindowBounds`, `kCGWindowOwnerName`, `kCGWindowLayer` and
/// `kCGWindowAlpha` are used - none of which need Screen Recording or
/// Accessibility permission. Window *titles* and *images* would, so we never ask
/// for them.
final class SurfaceTracker {

    private(set) var surfaces: [Surface] = []
    private(set) var dockRect: CGRect?

    private var timer: Timer?
    private let ownPID = ProcessInfo.processInfo.processIdentifier
    private let queue = DispatchQueue(label: "WinterCabin.surfaces", qos: .utility)

    var onUpdate: (([Surface]) -> Void)?

    func start(interval: TimeInterval = 0.5) {
        stop()
        refresh()
        let t = Timer(timeInterval: interval, repeats: true) { [weak self] _ in self?.refresh() }
        RunLoop.main.add(t, forMode: .common)
        timer = t
    }

    func stop() {
        timer?.invalidate()
        timer = nil
    }

    private func refresh() {
        queue.async { [weak self] in
            guard let self = self else { return }
            let found = self.read()
            DispatchQueue.main.async {
                self.surfaces = found.surfaces
                self.dockRect = found.dock
                self.onUpdate?(found.surfaces)
            }
        }
    }

    private func read() -> (surfaces: [Surface], dock: CGRect?) {
        let options: CGWindowListOption = [.optionOnScreenOnly]
        guard let raw = CGWindowListCopyWindowInfo(options, kCGNullWindowID) as? [[String: Any]] else {
            return ([], nil)
        }

        var result: [Surface] = []
        var dock: CGRect?
        var dockBest: CGFloat = 0
        let screenArea = NSScreen.screens.reduce(CGFloat(0)) { $0 + $1.frame.width * $1.frame.height }

        for entry in raw {
            guard let boundsDict = entry[kCGWindowBounds as String] as? [String: Any],
                  let cgRect = CGRect(dictionaryRepresentation: boundsDict as CFDictionary)
            else { continue }

            let pid = entry[kCGWindowOwnerPID as String] as? pid_t ?? -1
            if pid == ownPID { continue }

            let owner = entry[kCGWindowOwnerName as String] as? String ?? ""
            let layer = entry[kCGWindowLayer as String] as? Int ?? 0
            let alpha = entry[kCGWindowAlpha as String] as? Double ?? 1

            if alpha < 0.15 { continue }
            if cgRect.width < 90 || cgRect.height < 50 { continue }

            let rect = SurfaceTracker.appKitRect(from: cgRect)

            if owner == "Dock" {
                // The Dock process owns several windows; the tile strip is the
                // largest one that is not effectively full screen.
                let area = rect.width * rect.height
                if area < screenArea * 0.6 && area > dockBest {
                    dockBest = area
                    dock = rect
                }
                continue
            }

            // Normal, user-facing windows only.
            guard layer == 0 else { continue }
            if owner == "Window Server" || owner == "WindowManager" { continue }

            let number = entry[kCGWindowNumber as String] as? Int ?? 0
            result.append(Surface(key: "w\(number)", kind: .appWindow, rect: rect))
        }

        if let dock = dock {
            result.append(Surface(key: "dock", kind: .dock, rect: dock))
        }

        return (result, dock)
    }

    /// Core Graphics reports window bounds with the origin at the top-left of the
    /// primary display; AppKit puts it at the bottom-left.
    static func appKitRect(from cg: CGRect) -> CGRect {
        let primary = NSScreen.screens.first(where: { $0.frame.origin == .zero }) ?? NSScreen.main
        let maxY = primary?.frame.maxY ?? cg.maxY
        return CGRect(x: cg.origin.x,
                      y: maxY - cg.origin.y - cg.height,
                      width: cg.width,
                      height: cg.height)
    }
}

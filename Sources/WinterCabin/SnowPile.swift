import AppKit
import SpriteKit

/// A drift of snow sitting on one horizontal edge, stored as a height field so
/// it can grow bumpily, be smoothed into soft mounds, and be shoved by the plow.
final class SnowPile {

    let key: String
    let kind: Surface.Kind
    /// Scene coordinates: the pile grows upward from `baseY` between `minX` and `maxX`.
    private(set) var minX: CGFloat
    private(set) var maxX: CGFloat
    private(set) var baseY: CGFloat

    private(set) var heights: [CGFloat]
    private let columnWidth: CGFloat = 14
    private let maxHeight: CGFloat = 48

    let node: SKShapeNode
    var lastSeen: CFTimeInterval = 0
    /// Set when the window it sat on moved or closed; the drift slides off.
    private(set) var isSliding = false
    private var slideElapsed: CGFloat = 0

    init(key: String, kind: Surface.Kind, minX: CGFloat, maxX: CGFloat, baseY: CGFloat) {
        self.key = key
        self.kind = kind
        self.minX = minX
        self.maxX = maxX
        self.baseY = baseY
        let count = max(2, Int((maxX - minX) / columnWidth) + 1)
        self.heights = Array(repeating: 0, count: count)

        node = SKShapeNode()
        node.fillColor = NSColor(calibratedRed: 0.95, green: 0.96, blue: 1.0, alpha: 0.97)
        node.strokeColor = NSColor(calibratedRed: 1.0, green: 1.0, blue: 1.0, alpha: 0.9)
        node.lineWidth = 1
        node.isAntialiased = true
        node.zPosition = 5
    }

    var isEmpty: Bool { return heights.allSatisfy { $0 < 0.4 } }

    var totalSnow: CGFloat { return heights.reduce(0, +) }

    // MARK: - geometry updates

    /// Follow a window as it moves or resizes, keeping the snow we already have.
    func reshape(minX: CGFloat, maxX: CGFloat, baseY: CGFloat) {
        let movedSideways = abs(minX - self.minX) > 1 || abs(maxX - self.maxX) > 1
        let movedUpDown = abs(baseY - self.baseY) > 1

        if movedUpDown && kind == .appWindow {
            // the window jumped - shake the drift loose
            beginSliding()
            return
        }

        if movedSideways {
            let count = max(2, Int((maxX - minX) / columnWidth) + 1)
            if count != heights.count {
                heights = SnowPile.resample(heights, to: count)
            }
            if kind == .appWindow && abs(minX - self.minX) > 6 {
                beginSliding()
            }
        }
        self.minX = minX
        self.maxX = maxX
        self.baseY = baseY
    }

    func beginSliding() {
        guard !isSliding else { return }
        isSliding = true
        slideElapsed = 0
    }

    private static func resample(_ src: [CGFloat], to count: Int) -> [CGFloat] {
        guard src.count > 1, count > 1 else { return Array(repeating: 0, count: count) }
        var out = Array(repeating: CGFloat(0), count: count)
        for i in 0..<count {
            let t = CGFloat(i) / CGFloat(count - 1) * CGFloat(src.count - 1)
            let a = Int(floor(t)), b = min(src.count - 1, a + 1)
            let f = t - CGFloat(a)
            out[i] = src[a] * (1 - f) + src[b] * f
        }
        return out
    }

    // MARK: - accumulation

    func add(atX x: CGFloat, amount: CGFloat) {
        guard x >= minX, x <= maxX, !isSliding else { return }
        let idx = index(forX: x)
        deposit(idx, amount * 0.6)
        deposit(idx - 1, amount * 0.2)
        deposit(idx + 1, amount * 0.2)
    }

    private func deposit(_ i: Int, _ amount: CGFloat) {
        guard i >= 0, i < heights.count else { return }
        heights[i] = min(maxHeight, heights[i] + amount)
    }

    private func index(forX x: CGFloat) -> Int {
        guard maxX > minX else { return 0 }
        let t = (x - minX) / (maxX - minX)
        return min(heights.count - 1, max(0, Int(t * CGFloat(heights.count - 1) + 0.5)))
    }

    /// Settle sharp spikes into soft, bumpy drifts.
    func relax() {
        guard heights.count > 2 else { return }
        var out = heights
        for i in 1..<(heights.count - 1) {
            let avg = (heights[i - 1] + heights[i] * 2 + heights[i + 1]) / 4
            // snow slumps towards the average but keeps a little bumpiness
            out[i] = heights[i] + (avg - heights[i]) * 0.22
        }
        heights = out
    }

    func heightAt(x: CGFloat) -> CGFloat {
        guard x >= minX, x <= maxX else { return 0 }
        return heights[index(forX: x)]
    }

    // MARK: - plow

    /// Scrape everything left of `x` and hand back how much snow came off.
    func scrape(upTo x: CGFloat) -> CGFloat {
        var removed: CGFloat = 0
        let limit = index(forX: min(max(x, minX), maxX))
        guard x >= minX else { return 0 }
        for i in 0...limit where i < heights.count {
            removed += heights[i]
            heights[i] = 0
        }
        return removed
    }

    func clearAll() {
        for i in heights.indices { heights[i] = 0 }
    }

    // MARK: - drawing

    func updateNode(deltaTime: CGFloat) {
        if isSliding {
            slideElapsed += deltaTime
            let drop = 420 * slideElapsed * slideElapsed       // gravity, roughly
            node.position = CGPoint(x: 0, y: -drop)
            node.alpha = max(0, 1 - slideElapsed * 1.4)
            return
        }

        node.position = .zero
        node.alpha = 1
        node.path = buildPath()
    }

    private func buildPath() -> CGPath? {
        guard heights.count > 1, maxX > minX else { return nil }
        let step = (maxX - minX) / CGFloat(heights.count - 1)
        let path = CGMutablePath()
        path.move(to: CGPoint(x: minX, y: baseY))

        // top edge through the column tops, smoothed with quadratic curves
        var previous = CGPoint(x: minX, y: baseY + heights[0])
        path.addLine(to: previous)
        for i in 1..<heights.count {
            let p = CGPoint(x: minX + CGFloat(i) * step, y: baseY + heights[i])
            let mid = CGPoint(x: (previous.x + p.x) / 2, y: (previous.y + p.y) / 2)
            path.addQuadCurve(to: mid, control: previous)
            previous = p
        }
        path.addLine(to: CGPoint(x: maxX, y: baseY + heights[heights.count - 1]))
        path.addLine(to: CGPoint(x: maxX, y: baseY))
        path.closeSubpath()
        return path
    }
}

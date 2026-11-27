import AppKit
import SpriteKit

/// The interactive layer: falling snow, drifts that build up on the screen
/// bottom, the Dock and window tops, clickable snowballs, snowmen and the plow.
final class SnowScene: SKScene {

    /// AppKit global frame of the screen this scene covers.
    var screenFrame: CGRect = .zero

    private let bottomKey = "bottom"

    // MARK: - model types

    private final class Flake {
        let node: SKSpriteNode
        var x: CGFloat = 0
        var y: CGFloat = 0
        var fall: CGFloat = 60
        var depth: CGFloat = 1
        var sway: CGFloat = 0
        var swaySpeed: CGFloat = 1
        init(node: SKSpriteNode) { self.node = node }
    }

    private final class Ball {
        let node: SKShapeNode
        var x: CGFloat
        var y: CGFloat
        var vx: CGFloat
        var vy: CGFloat
        let radius: CGFloat
        var settled = false

        init(node: SKShapeNode, x: CGFloat, y: CGFloat, vx: CGFloat, vy: CGFloat, radius: CGFloat) {
            self.node = node; self.x = x; self.y = y
            self.vx = vx; self.vy = vy; self.radius = radius
        }
    }

    private final class Stack {
        var x: CGFloat
        var balls: [Ball] = []
        init(x: CGFloat) { self.x = x }
    }

    private final class PlowRun {
        let node: SKNode
        let wave: SKShapeNode
        var x: CGFloat
        var y: CGFloat
        var carried: CGFloat = 0
        let height: CGFloat
        let speed: CGFloat

        init(node: SKNode, wave: SKShapeNode, x: CGFloat, y: CGFloat,
             height: CGFloat, speed: CGFloat) {
            self.node = node; self.wave = wave; self.x = x
            self.y = y; self.height = height; self.speed = speed
        }
    }

    // MARK: - state

    private var flakes: [Flake] = []
    private var piles: [String: SnowPile] = [:]
    private var balls: [Ball] = []
    private var stacks: [Stack] = []
    private var snowmen: [SKNode] = []
    private var plow: PlowRun?

    private var lastTime: TimeInterval = 0
    private var windPhase: CGFloat = 0
    private var relaxTimer: CGFloat = 0
    private var plowTimer: CGFloat = 0

    // MARK: - lifecycle

    override init(size: CGSize) {
        super.init(size: size)
        scaleMode = .resizeFill
        backgroundColor = .clear
    }

    required init?(coder: NSCoder) { fatalError("not supported") }

    override func didMove(to view: SKView) {
        makeBottomPile()
        rebuildFlakes()
        NotificationCenter.default.addObserver(
            self, selector: #selector(settingsChanged), name: Settings.didChange, object: nil)
    }

    override func didChangeSize(_ oldSize: CGSize) {
        super.didChangeSize(oldSize)
        guard size.width > 1 else { return }
        piles[bottomKey]?.reshape(minX: 0, maxX: size.width, baseY: 0)
    }

    @objc private func settingsChanged() {
        rebuildFlakes()
        if !Settings.shared.pileOnWindows {
            for (_, pile) in piles where pile.kind == .appWindow { pile.beginSliding() }
        }
    }

    private func makeBottomPile() {
        guard piles[bottomKey] == nil else { return }
        let pile = SnowPile(key: bottomKey, kind: .screenBottom,
                            minX: 0, maxX: max(1, size.width), baseY: 0)
        piles[bottomKey] = pile
        addChild(pile.node)
    }

    // MARK: - flakes

    private func rebuildFlakes() {
        let wanted = Settings.shared.snowEnabled ? Settings.shared.density.flakeCount : 0
        if wanted == flakes.count { return }

        if wanted < flakes.count {
            for flake in flakes[wanted...] { flake.node.removeFromParent() }
            flakes.removeSubrange(wanted...)
            return
        }

        for _ in flakes.count..<wanted {
            let depth = CGFloat.random(in: 0.35...1.0)
            let diameter = 3 + depth * 9
            let node = SKSpriteNode(texture: Textures.flake(diameter: 32))
            node.size = CGSize(width: diameter, height: diameter)
            node.alpha = 0.30 + depth * 0.55
            node.zPosition = 3 + depth
            addChild(node)

            let flake = Flake(node: node)
            flake.depth = depth
            flake.fall = 26 + depth * 95
            flake.swaySpeed = CGFloat.random(in: 0.6...2.0)
            flake.sway = CGFloat.random(in: 0...(.pi * 2))
            respawn(flake, initial: true)
            flakes.append(flake)
        }
    }

    private func respawn(_ flake: Flake, initial: Bool = false) {
        flake.x = CGFloat.random(in: -40...(size.width + 40))
        flake.y = initial ? CGFloat.random(in: 0...max(1, size.height))
                          : size.height + CGFloat.random(in: 10...180)
        flake.node.position = CGPoint(x: flake.x, y: flake.y)
    }

    private func stepFlakes(_ dt: CGFloat) {
        guard !flakes.isEmpty else { return }
        let gust = sin(windPhase) * 24 + sin(windPhase * 0.41 + 1.3) * 13

        for flake in flakes {
            flake.sway += flake.swaySpeed * dt
            let previousY = flake.y
            flake.x += (gust * flake.depth * 0.55 + sin(flake.sway) * 14 * flake.depth) * dt
            flake.y -= flake.fall * dt

            if flake.x < -50 { flake.x += size.width + 100 }
            if flake.x > size.width + 50 { flake.x -= size.width + 100 }

            if let pile = landingPile(x: flake.x, from: previousY, to: flake.y) {
                pile.add(atX: flake.x, amount: 0.75 * flake.depth)
                respawn(flake)
            } else if flake.y < -20 {
                respawn(flake)
            }
            flake.node.position = CGPoint(x: flake.x, y: flake.y)
        }
    }

    /// The highest drift the flake crossed this frame, so snow lands on the
    /// frontmost window rather than falling through it.
    private func landingPile(x: CGFloat, from y0: CGFloat, to y1: CGFloat) -> SnowPile? {
        var best: SnowPile?
        var bestTop = -CGFloat.greatestFiniteMagnitude
        for pile in piles.values where !pile.isSliding {
            guard x >= pile.minX, x <= pile.maxX else { continue }
            let top = pile.baseY + pile.heightAt(x: x)
            guard y0 >= top, y1 <= top, top > bestTop else { continue }
            bestTop = top
            best = pile
        }
        return best
    }

    // MARK: - surfaces

    func sync(surfaces: [Surface]) {
        guard size.width > 1 else { return }
        var seen: Set<String> = [bottomKey]
        var inFront: [CGRect] = []
        let allowWindows = Settings.shared.pileOnWindows

        // surfaces arrive front-to-back
        for surface in surfaces {
            let r = CGRect(x: surface.rect.minX - screenFrame.minX,
                           y: surface.rect.minY - screenFrame.minY,
                           width: surface.rect.width,
                           height: surface.rect.height)

            guard r.maxX > 4, r.minX < size.width - 4 else { continue }
            guard r.maxY > 8, r.maxY < size.height - 2 else { continue }

            if surface.kind == .appWindow {
                guard allowWindows else { continue }
                let strip = CGRect(x: r.minX, y: r.maxY - 6, width: r.width, height: 10)
                var hidden = false
                for front in inFront where front.intersects(strip) {
                    if front.intersection(strip).width > strip.width * 0.65 {
                        hidden = true
                        break
                    }
                }
                inFront.append(r)
                if hidden { continue }
            }

            let minX = max(0, r.minX)
            let maxX = min(size.width, r.maxX)
            guard maxX - minX > 40 else { continue }

            seen.insert(surface.key)
            if let existing = piles[surface.key] {
                existing.reshape(minX: minX, maxX: maxX, baseY: r.maxY)
            } else {
                let pile = SnowPile(key: surface.key, kind: surface.kind,
                                    minX: minX, maxX: maxX, baseY: r.maxY)
                piles[surface.key] = pile
                addChild(pile.node)
            }
        }

        // a window that moved away or closed drops its drift
        for (key, pile) in piles where !seen.contains(key) {
            pile.beginSliding()
        }
    }

    // MARK: - snowballs

    func dropSnowball(at point: CGPoint) {
        guard Settings.shared.snowballsOnClick else { return }
        guard point.x > -20, point.x < size.width + 20 else { return }

        let radius = CGFloat.random(in: 12...19)
        let node = Figures.snowball(radius: radius)
        node.position = point
        addChild(node)

        balls.append(Ball(node: node, x: point.x, y: point.y,
                          vx: CGFloat.random(in: -45...45), vy: 0, radius: radius))
    }

    private func stepBalls(_ dt: CGFloat) {
        let damping = CGFloat(pow(0.10, Double(dt)))
        var offscreen: [Ball] = []

        for ball in balls where !ball.settled {
            ball.vy -= 1500 * dt
            ball.x += ball.vx * dt
            ball.y += ball.vy * dt

            let floor = groundY(at: ball.x) + ball.radius
            if ball.y <= floor {
                ball.y = floor
                if ball.vy < -130 {
                    ball.vy = -ball.vy * 0.33
                    ball.vx *= 0.72
                } else {
                    ball.vy = 0
                    ball.vx *= damping
                    if abs(ball.vx) < 7 { settle(ball) }
                }
            }

            if ball.x < -80 || ball.x > size.width + 80 { offscreen.append(ball) }
            ball.node.position = CGPoint(x: ball.x, y: ball.y)
            ball.node.zRotation -= (ball.vx / max(ball.radius, 1)) * dt
        }

        for ball in offscreen {
            ball.node.removeFromParent()
            balls.removeAll { $0 === ball }
        }
    }

    private func settle(_ ball: Ball) {
        ball.settled = true

        if let stack = stacks.first(where: {
            abs($0.x - ball.x) < ball.radius * 1.4 && $0.balls.count < 3
        }) {
            ball.x = stack.x
            ball.y = stackTop(stack) + ball.radius
            stack.balls.append(ball)
            if stack.balls.count == 3 { makeSnowman(stack) }
        } else {
            let stack = Stack(x: ball.x)
            stack.balls.append(ball)
            stacks.append(stack)
        }
        ball.node.position = CGPoint(x: ball.x, y: ball.y)
    }

    private func stackTop(_ stack: Stack) -> CGFloat {
        var y = groundY(at: stack.x)
        for ball in stack.balls { y += ball.radius * 2 }
        return y
    }

    private func makeSnowman(_ stack: Stack) {
        let base = stack.balls[0].radius
        for ball in stack.balls {
            ball.node.removeFromParent()
            balls.removeAll { $0 === ball }
        }
        let figure = Figures.snowman(baseRadius: base * 1.05)
        figure.position = CGPoint(x: stack.x, y: groundY(at: stack.x))
        addChild(figure)
        snowmen.append(figure)
        stacks.removeAll { $0 === stack }
    }

    /// Top of the snow at `x`, including the Dock drift where it applies.
    private func groundY(at x: CGFloat) -> CGFloat {
        var y: CGFloat = 0
        if let bottom = piles[bottomKey] {
            y = bottom.baseY + bottom.heightAt(x: x)
        }
        if let dock = piles["dock"], x >= dock.minX, x <= dock.maxX {
            y = max(y, dock.baseY + dock.heightAt(x: x))
        }
        return y
    }

    /// The bare surface the plow rides along, ignoring the snow on top of it.
    private func plowSurfaceY(at x: CGFloat) -> CGFloat {
        var y: CGFloat = 0
        if let dock = piles["dock"], x >= dock.minX - 14, x <= dock.maxX + 14 {
            y = max(y, dock.baseY)
        }
        return y
    }

    // MARK: - plow

    func sendPlow() {
        guard plow == nil else { return }

        let height = max(34, min(74, size.height * 0.055))
        let node = Figures.plow(height: height)
        node.position = CGPoint(x: -height * 3, y: 0)
        addChild(node)

        let wave = SKShapeNode()
        wave.fillColor = NSColor(calibratedRed: 0.95, green: 0.96, blue: 1.0, alpha: 0.97)
        wave.strokeColor = NSColor(calibratedWhite: 1, alpha: 0.85)
        wave.lineWidth = 1
        wave.zPosition = 8
        addChild(wave)

        plow = PlowRun(node: node, wave: wave, x: -height * 3, y: 0,
                       height: height, speed: max(300, size.width / 6.5))
        plowTimer = 0
    }

    private func stepPlow(_ dt: CGFloat) {
        guard let run = plow else { return }

        run.x += run.speed * dt
        let blade = run.x + run.height * 1.5

        let target = plowSurfaceY(at: blade)
        run.y += (target - run.y) * min(1, 9 * dt)
        run.node.position = CGPoint(x: run.x, y: run.y)

        if let bottom = piles[bottomKey] { run.carried += bottom.scrape(upTo: blade) }
        if let dock = piles["dock"], blade >= dock.minX {
            run.carried += dock.scrape(upTo: blade)
        }
        // snow spills around the blade as it goes
        run.carried *= CGFloat(pow(0.985, Double(dt * 60)))

        let waveHeight = min(run.height * 1.5, run.carried * 0.05)
        let waveWidth = max(run.height * 0.8, min(run.height * 4, run.carried * 0.10))
        let path = CGMutablePath()
        path.move(to: CGPoint(x: blade - 6, y: run.y))
        path.addQuadCurve(to: CGPoint(x: blade + waveWidth, y: run.y),
                          control: CGPoint(x: blade + waveWidth * 0.35,
                                           y: run.y + waveHeight * 1.7))
        path.closeSubpath()
        run.wave.path = path

        sweepFigures(before: blade)

        if run.x > size.width + run.height * 4 {
            run.node.removeFromParent()
            run.wave.removeFromParent()
            plow = nil
        }
    }

    private func sweepFigures(before blade: CGFloat) {
        let caught = balls.filter { $0.x < blade }
        for ball in caught { ball.node.removeFromParent() }
        if !caught.isEmpty { balls.removeAll { ball in caught.contains { $0 === ball } } }
        stacks.removeAll { $0.x < blade }

        let flattened = snowmen.filter { $0.position.x < blade }
        for figure in flattened {
            figure.run(.sequence([
                .group([.fadeOut(withDuration: 0.35),
                        .scaleY(to: 0.15, duration: 0.35),
                        .moveBy(x: 24, y: 0, duration: 0.35)]),
                .removeFromParent()
            ]))
        }
        if !flattened.isEmpty { snowmen.removeAll { figure in flattened.contains(figure) } }
    }

    // MARK: - piles drawing

    private func drawPiles(_ dt: CGFloat) {
        var finished: [String] = []
        for (key, pile) in piles {
            pile.updateNode(deltaTime: dt)
            if pile.isSliding && pile.node.alpha <= 0.02 { finished.append(key) }
        }
        for key in finished {
            piles[key]?.node.removeFromParent()
            piles.removeValue(forKey: key)
        }
    }

    // MARK: - run loop

    override func update(_ currentTime: TimeInterval) {
        let raw = lastTime == 0 ? 1.0 / 60.0 : currentTime - lastTime
        lastTime = currentTime
        let dt = CGFloat(min(1.0 / 15.0, max(0, raw)))

        windPhase += dt * 0.32

        stepFlakes(dt)
        stepBalls(dt)
        stepPlow(dt)

        relaxTimer += dt
        if relaxTimer > 0.12 {
            relaxTimer = 0
            for pile in piles.values { pile.relax() }
        }

        drawPiles(dt)

        if Settings.shared.snowEnabled && plow == nil {
            plowTimer += dt
            if plowTimer > CGFloat(Settings.shared.plowIntervalMinutes * 60) {
                sendPlow()
            }
        }
    }
}

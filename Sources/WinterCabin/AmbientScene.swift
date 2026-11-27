import AppKit
import SpriteKit

/// The gentle motion that sits behind everything: smoke, twinkling lights,
/// window flicker, lake shimmer, stars and a breathing moon glow.
final class AmbientScene: SKScene {

    private let manifest: SceneManifest?
    private var mapper: SceneMapper {
        return SceneMapper(size: size, imageAspect: manifest?.aspect ?? 1.7768)
    }
    private var backdrop: SKSpriteNode?
    private var motionRoot = SKNode()

    init(size: CGSize, manifest: SceneManifest?) {
        self.manifest = manifest
        super.init(size: size)
        self.scaleMode = .resizeFill
        self.backgroundColor = NSColor(calibratedRed: 0.07, green: 0.08, blue: 0.18, alpha: 1)
    }

    required init?(coder: NSCoder) { fatalError("not supported") }

    override func didMove(to view: SKView) {
        addChild(motionRoot)
        buildBackdrop()
        rebuildMotion()
    }

    override func didChangeSize(_ oldSize: CGSize) {
        super.didChangeSize(oldSize)
        layoutBackdrop()
        rebuildMotion()
    }

    // MARK: - backdrop

    private func buildBackdrop() {
        guard let image = Textures.sceneImage() else { return }
        let node = SKSpriteNode(texture: SKTexture(image: image))
        node.zPosition = 0
        addChild(node)
        backdrop = node
        layoutBackdrop()
    }

    private func layoutBackdrop() {
        guard let node = backdrop, let tex = node.texture else { return }
        let imageAspect = tex.size().width / max(tex.size().height, 1)
        let viewAspect = size.width / max(size.height, 1)
        // aspect fill
        if viewAspect > imageAspect {
            node.size = CGSize(width: size.width, height: size.width / imageAspect)
        } else {
            node.size = CGSize(width: size.height * imageAspect, height: size.height)
        }
        node.position = CGPoint(x: size.width / 2, y: size.height / 2)
    }

    // MARK: - motion

    private func rebuildMotion() {
        motionRoot.removeAllChildren()
        motionRoot.zPosition = 10
        guard size.width > 1, size.height > 1 else { return }
        addStars()
        addMoonGlow()
        addChimneySmoke()
        addStringLights()
        addWindowFlicker()
        addLakeShimmer()
    }

    private func addStars() {
        let count = 90
        for i in 0..<count {
            let nx = CGFloat.random(in: 0.02...0.98)
            let ny = CGFloat.random(in: 0.02...0.52)
            let dot = SKSpriteNode(texture: Textures.softDot(diameter: 18))
            let s = CGFloat.random(in: 0.12...0.34)
            dot.size = CGSize(width: mapper.length(0.010) * s * 3,
                              height: mapper.length(0.010) * s * 3)
            dot.position = mapper.point(nx, ny)
            dot.blendMode = .add
            dot.alpha = 0
            dot.zPosition = 1
            motionRoot.addChild(dot)

            let up = SKAction.fadeAlpha(to: CGFloat.random(in: 0.25...0.75),
                                        duration: Double.random(in: 1.4...3.6))
            let down = SKAction.fadeAlpha(to: CGFloat.random(in: 0.02...0.18),
                                          duration: Double.random(in: 1.6...4.2))
            up.timingMode = .easeInEaseOut
            down.timingMode = .easeInEaseOut
            let wait = SKAction.wait(forDuration: Double(i) * 0.03)
            dot.run(.sequence([wait, .repeatForever(.sequence([up, down]))]))
        }
    }

    private func addMoonGlow() {
        guard let m = manifest?.moon else { return }
        let glow = SKSpriteNode(texture: Textures.softDot(
            diameter: 256, color: NSColor(calibratedRed: 1.0, green: 0.97, blue: 0.84, alpha: 1)))
        let d = mapper.length(m.r) * 7.5
        glow.size = CGSize(width: d, height: d)
        glow.position = mapper.point(m.x, m.y)
        glow.blendMode = .add
        glow.alpha = 0.10
        glow.zPosition = 0
        motionRoot.addChild(glow)

        let breathe = SKAction.sequence([
            .group([.fadeAlpha(to: 0.17, duration: 5.0), .scale(to: 1.06, duration: 5.0)]),
            .group([.fadeAlpha(to: 0.09, duration: 6.0), .scale(to: 0.97, duration: 6.0)])
        ])
        breathe.timingMode = .easeInEaseOut
        glow.run(.repeatForever(breathe))
    }

    private func addChimneySmoke() {
        guard let c = manifest?.chimney else { return }
        let e = SKEmitterNode()
        e.particleTexture = Textures.softDot(diameter: 64,
                                             color: NSColor(calibratedWhite: 0.86, alpha: 1))
        // sits just above the chimney mouth so it drifts through the painted plume
        e.position = mapper.point(c.x, c.y - 0.012)
        e.zPosition = 2
        e.particleBirthRate = 3.2
        e.particleLifetime = 16
        e.particleLifetimeRange = 5
        e.particlePositionRange = CGVector(dx: mapper.length(0.004), dy: mapper.length(0.002))
        e.emissionAngle = .pi / 2
        e.emissionAngleRange = 0.45
        e.particleSpeed = mapper.length(0.016)
        e.particleSpeedRange = mapper.length(0.008)
        e.xAcceleration = mapper.length(0.009)
        e.yAcceleration = mapper.length(0.004)
        e.particleAlpha = 0.085
        e.particleAlphaRange = 0.035
        e.particleAlphaSpeed = -0.007
        e.particleScale = mapper.length(0.0007)
        e.particleScaleRange = mapper.length(0.0004)
        e.particleScaleSpeed = mapper.length(0.0010)
        e.particleRotationRange = .pi
        e.particleRotationSpeed = 0.12
        e.particleColor = NSColor(calibratedWhite: 0.86, alpha: 1)
        e.particleColorBlendFactor = 1
        e.particleBlendMode = .alpha
        e.advanceSimulationTime(12)
        motionRoot.addChild(e)
    }

    private func addStringLights() {
        guard let manifest = manifest else { return }
        let warm = NSColor(calibratedRed: 1.0, green: 0.78, blue: 0.42, alpha: 1)
        let bulbSize = mapper.length(0.013)

        for (i, b) in manifest.bulbs.enumerated() {
            let dot = SKSpriteNode(texture: Textures.softDot(diameter: 48, color: warm))
            dot.size = CGSize(width: bulbSize, height: bulbSize)
            dot.position = mapper.point(b)
            dot.blendMode = .add
            dot.alpha = CGFloat.random(in: 0.10...0.30)
            dot.zPosition = 3
            motionRoot.addChild(dot)

            // each bulb breathes on its own slightly random schedule
            let a = SKAction.fadeAlpha(to: CGFloat.random(in: 0.34...0.62),
                                       duration: Double.random(in: 1.1...2.8))
            let b2 = SKAction.fadeAlpha(to: CGFloat.random(in: 0.06...0.20),
                                        duration: Double.random(in: 1.3...3.1))
            a.timingMode = .easeInEaseOut
            b2.timingMode = .easeInEaseOut
            dot.run(.sequence([.wait(forDuration: Double(i) * 0.07),
                               .repeatForever(.sequence([a, b2]))]))
        }

        for l in manifest.lanterns {
            let dot = SKSpriteNode(texture: Textures.softDot(diameter: 96, color: warm))
            let d = mapper.length(0.052)
            dot.size = CGSize(width: d, height: d)
            dot.position = mapper.point(l)
            dot.blendMode = .add
            dot.alpha = 0.16
            dot.zPosition = 3
            motionRoot.addChild(dot)
            dot.run(.repeatForever(.sequence([
                .fadeAlpha(to: 0.26, duration: Double.random(in: 0.9...1.7)),
                .fadeAlpha(to: 0.13, duration: Double.random(in: 1.1...2.2))
            ])))
        }
    }

    private func addWindowFlicker() {
        guard let manifest = manifest else { return }
        let warm = NSColor(calibratedRed: 1.0, green: 0.72, blue: 0.34, alpha: 1)
        for w in manifest.windows {
            let r = mapper.rect(w)
            let glow = SKSpriteNode(texture: Textures.softDot(diameter: 128, color: warm))
            glow.size = CGSize(width: r.width * 2.6, height: r.height * 2.6)
            glow.position = CGPoint(x: r.midX, y: r.midY)
            glow.blendMode = .add
            glow.alpha = 0.07
            glow.zPosition = 2
            motionRoot.addChild(glow)

            // irregular hearth-like flicker
            let flicker = SKAction.run { [weak glow] in
                guard let glow = glow else { return }
                let target = CGFloat.random(in: 0.045...0.135)
                glow.run(.fadeAlpha(to: target, duration: Double.random(in: 0.5...2.0)))
            }
            glow.run(.repeatForever(.sequence([flicker, .wait(forDuration: 0.9)])))
        }
    }

    private func addLakeShimmer() {
        guard let manifest = manifest else { return }
        let warm = NSColor(calibratedRed: 1.0, green: 0.76, blue: 0.44, alpha: 1)
        for (i, p) in manifest.reflections.enumerated() {
            for band in 0..<5 {
                let streak = SKSpriteNode(color: warm,
                                          size: CGSize(width: mapper.length(0.012),
                                                       height: max(1, mapper.length(0.0022))))
                let drop = CGFloat(band) * 0.026 + CGFloat.random(in: 0...0.012)
                streak.position = mapper.point(p.x + CGFloat.random(in: -0.004...0.004),
                                               p.y + 0.012 + drop)
                streak.blendMode = .add
                streak.alpha = 0.10 - CGFloat(band) * 0.012
                streak.zPosition = 2
                motionRoot.addChild(streak)

                let sway = SKAction.sequence([
                    .moveBy(x: mapper.length(0.004), y: 0, duration: Double.random(in: 1.8...3.4)),
                    .moveBy(x: -mapper.length(0.008), y: 0, duration: Double.random(in: 1.8...3.4)),
                    .moveBy(x: mapper.length(0.004), y: 0, duration: Double.random(in: 1.8...3.4))
                ])
                sway.timingMode = .easeInEaseOut
                let pulse = SKAction.sequence([
                    .fadeAlpha(to: 0.03, duration: Double.random(in: 1.0...2.4)),
                    .fadeAlpha(to: 0.13, duration: Double.random(in: 1.0...2.4))
                ])
                streak.run(.sequence([.wait(forDuration: Double(i) * 0.05),
                                      .group([.repeatForever(sway), .repeatForever(pulse)])]))
            }
        }
    }
}

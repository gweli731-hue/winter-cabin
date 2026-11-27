import AppKit
import SpriteKit

enum Figures {

    static let snowWhite = NSColor(calibratedRed: 0.96, green: 0.97, blue: 1.0, alpha: 1)
    static let snowEdge  = NSColor(calibratedRed: 0.80, green: 0.84, blue: 0.95, alpha: 1)

    /// A soft snowball.
    static func snowball(radius: CGFloat) -> SKShapeNode {
        let node = SKShapeNode(circleOfRadius: radius)
        node.fillColor = snowWhite
        node.strokeColor = snowEdge
        node.lineWidth = 1
        node.isAntialiased = true
        node.zPosition = 6

        let shine = SKShapeNode(circleOfRadius: radius * 0.42)
        shine.fillColor = NSColor(calibratedWhite: 1, alpha: 0.65)
        shine.strokeColor = .clear
        shine.position = CGPoint(x: -radius * 0.28, y: radius * 0.30)
        node.addChild(shine)
        return node
    }

    /// Three stacked balls, coal eyes, a carrot nose, a red scarf and buttons.
    static func snowman(baseRadius r: CGFloat) -> SKNode {
        let root = SKNode()
        root.zPosition = 7

        let rBottom = r
        let rMiddle = r * 0.74
        let rHead   = r * 0.52

        let yBottom = rBottom
        let yMiddle = yBottom + rBottom * 0.72 + rMiddle * 0.30
        let yHead   = yMiddle + rMiddle * 0.70 + rHead * 0.34

        for (radius, y) in [(rBottom, yBottom), (rMiddle, yMiddle), (rHead, yHead)] {
            let ball = SKShapeNode(circleOfRadius: radius)
            ball.fillColor = snowWhite
            ball.strokeColor = snowEdge
            ball.lineWidth = 1
            ball.position = CGPoint(x: 0, y: y)
            root.addChild(ball)
        }

        // coal eyes
        for sx in [-1.0, 1.0] as [CGFloat] {
            let eye = SKShapeNode(circleOfRadius: max(1.2, rHead * 0.13))
            eye.fillColor = NSColor(calibratedWhite: 0.12, alpha: 1)
            eye.strokeColor = .clear
            eye.position = CGPoint(x: sx * rHead * 0.34, y: yHead + rHead * 0.26)
            root.addChild(eye)
        }

        // carrot nose
        let nose = SKShapeNode()
        let p = CGMutablePath()
        p.move(to: CGPoint(x: 0, y: yHead + rHead * 0.12))
        p.addLine(to: CGPoint(x: rHead * 0.92, y: yHead + rHead * 0.02))
        p.addLine(to: CGPoint(x: 0, y: yHead - rHead * 0.10))
        p.closeSubpath()
        nose.path = p
        nose.fillColor = NSColor(calibratedRed: 0.95, green: 0.52, blue: 0.16, alpha: 1)
        nose.strokeColor = .clear
        root.addChild(nose)

        // coal smile
        for i in 0..<5 {
            let t = CGFloat(i) / 4
            let dot = SKShapeNode(circleOfRadius: max(0.9, rHead * 0.075))
            dot.fillColor = NSColor(calibratedWhite: 0.14, alpha: 1)
            dot.strokeColor = .clear
            let x = (t - 0.5) * rHead * 0.95
            let curve = abs(t - 0.5) * rHead * 0.22
            dot.position = CGPoint(x: x, y: yHead - rHead * 0.34 + curve)
            root.addChild(dot)
        }

        // red scarf around the neck
        let scarfY = (yHead - rHead * 0.72 + yMiddle + rMiddle * 0.70) / 2
        let scarf = SKShapeNode(rectOf: CGSize(width: rMiddle * 1.5, height: rHead * 0.40),
                                cornerRadius: rHead * 0.16)
        scarf.fillColor = NSColor(calibratedRed: 0.78, green: 0.17, blue: 0.19, alpha: 1)
        scarf.strokeColor = .clear
        scarf.position = CGPoint(x: 0, y: scarfY)
        root.addChild(scarf)

        let tail = SKShapeNode(rectOf: CGSize(width: rHead * 0.32, height: rMiddle * 0.85),
                               cornerRadius: rHead * 0.12)
        tail.fillColor = NSColor(calibratedRed: 0.70, green: 0.14, blue: 0.16, alpha: 1)
        tail.strokeColor = .clear
        tail.position = CGPoint(x: rMiddle * 0.62, y: scarfY - rMiddle * 0.42)
        tail.zRotation = -0.22
        root.addChild(tail)

        // buttons
        for i in 0..<3 {
            let button = SKShapeNode(circleOfRadius: max(1.1, rMiddle * 0.11))
            button.fillColor = NSColor(calibratedWhite: 0.16, alpha: 1)
            button.strokeColor = .clear
            button.position = CGPoint(x: 0, y: yMiddle + rMiddle * (0.34 - CGFloat(i) * 0.34))
            root.addChild(button)
        }

        // twig arms
        for sx in [-1.0, 1.0] as [CGFloat] {
            let arm = SKShapeNode()
            let a = CGMutablePath()
            a.move(to: CGPoint(x: sx * rMiddle * 0.85, y: yMiddle + rMiddle * 0.12))
            a.addLine(to: CGPoint(x: sx * rMiddle * 1.85, y: yMiddle + rMiddle * 0.75))
            a.move(to: CGPoint(x: sx * rMiddle * 1.45, y: yMiddle + rMiddle * 0.46))
            a.addLine(to: CGPoint(x: sx * rMiddle * 1.70, y: yMiddle + rMiddle * 0.98))
            arm.path = a
            arm.strokeColor = NSColor(calibratedRed: 0.34, green: 0.24, blue: 0.17, alpha: 1)
            arm.lineWidth = max(1.2, r * 0.07)
            arm.lineCap = .round
            root.addChild(arm)
        }

        // Santa hat
        let hatBase = yHead + rHead * 0.58
        let cone = SKShapeNode()
        let hp = CGMutablePath()
        hp.move(to: CGPoint(x: -rHead * 0.86, y: hatBase))
        hp.addLine(to: CGPoint(x: rHead * 0.86, y: hatBase))
        hp.addQuadCurve(to: CGPoint(x: rHead * 1.16, y: hatBase + rHead * 1.42),
                        control: CGPoint(x: rHead * 1.02, y: hatBase + rHead * 1.00))
        hp.addQuadCurve(to: CGPoint(x: -rHead * 0.86, y: hatBase),
                        control: CGPoint(x: -rHead * 0.12, y: hatBase + rHead * 0.76))
        hp.closeSubpath()
        cone.path = hp
        cone.fillColor = NSColor(calibratedRed: 0.80, green: 0.16, blue: 0.18, alpha: 1)
        cone.strokeColor = NSColor(calibratedRed: 0.58, green: 0.10, blue: 0.12, alpha: 1)
        cone.lineWidth = max(0.8, rHead * 0.05)
        root.addChild(cone)

        let brim = SKShapeNode(rectOf: CGSize(width: rHead * 1.92, height: rHead * 0.36),
                               cornerRadius: rHead * 0.18)
        brim.fillColor = NSColor(calibratedWhite: 0.97, alpha: 1)
        brim.strokeColor = .clear
        brim.position = CGPoint(x: 0, y: hatBase)
        root.addChild(brim)

        let pompom = SKShapeNode(circleOfRadius: rHead * 0.28)
        pompom.fillColor = NSColor(calibratedWhite: 0.97, alpha: 1)
        pompom.strokeColor = .clear
        pompom.position = CGPoint(x: rHead * 1.18, y: hatBase + rHead * 1.46)
        root.addChild(pompom)

        root.setScale(0.1)
        root.run(.sequence([
            .scale(to: 1.12, duration: 0.22),
            .scale(to: 1.0, duration: 0.14)
        ]))
        return root
    }

    /// A small yellow cartoon snowplow, facing right.
    static func plow(height h: CGFloat) -> SKNode {
        let root = SKNode()
        root.zPosition = 9

        let yellow = NSColor(calibratedRed: 0.98, green: 0.78, blue: 0.16, alpha: 1)
        let darkYellow = NSColor(calibratedRed: 0.82, green: 0.60, blue: 0.08, alpha: 1)
        let glass = NSColor(calibratedRed: 0.55, green: 0.76, blue: 0.90, alpha: 1)
        let tyre = NSColor(calibratedWhite: 0.16, alpha: 1)

        // body
        let body = SKShapeNode(rect: CGRect(x: -h * 0.95, y: h * 0.26,
                                            width: h * 1.70, height: h * 0.52),
                               cornerRadius: h * 0.10)
        body.fillColor = yellow
        body.strokeColor = darkYellow
        body.lineWidth = 1
        root.addChild(body)

        // cab
        let cab = SKShapeNode(rect: CGRect(x: -h * 0.70, y: h * 0.72,
                                           width: h * 0.86, height: h * 0.56),
                              cornerRadius: h * 0.10)
        cab.fillColor = yellow
        cab.strokeColor = darkYellow
        cab.lineWidth = 1
        root.addChild(cab)

        let window = SKShapeNode(rect: CGRect(x: -h * 0.56, y: h * 0.84,
                                              width: h * 0.56, height: h * 0.34),
                                 cornerRadius: h * 0.06)
        window.fillColor = glass
        window.strokeColor = .clear
        root.addChild(window)

        // blade
        let blade = SKShapeNode()
        let bp = CGMutablePath()
        bp.move(to: CGPoint(x: h * 0.72, y: h * 0.16))
        bp.addQuadCurve(to: CGPoint(x: h * 1.52, y: h * 1.00),
                        control: CGPoint(x: h * 1.52, y: h * 0.26))
        bp.addLine(to: CGPoint(x: h * 1.26, y: h * 1.02))
        bp.addQuadCurve(to: CGPoint(x: h * 0.62, y: h * 0.18),
                        control: CGPoint(x: h * 1.20, y: h * 0.28))
        bp.closeSubpath()
        blade.path = bp
        blade.fillColor = NSColor(calibratedRed: 0.88, green: 0.24, blue: 0.20, alpha: 1)
        blade.strokeColor = NSColor(calibratedRed: 0.62, green: 0.14, blue: 0.12, alpha: 1)
        blade.lineWidth = 1
        root.addChild(blade)

        // caterpillar tracks
        let trackBody = SKShapeNode(rect: CGRect(x: -h * 0.94, y: 0,
                                                 width: h * 1.68, height: h * 0.32),
                                    cornerRadius: h * 0.16)
        trackBody.fillColor = tyre
        trackBody.strokeColor = NSColor(calibratedWhite: 0.42, alpha: 1)
        trackBody.lineWidth = max(1, h * 0.04)
        root.addChild(trackBody)

        // tread marks that crawl backwards, so the track reads as moving
        for i in 0..<9 {
            let tread = SKShapeNode(rectOf: CGSize(width: h * 0.05, height: h * 0.24),
                                    cornerRadius: h * 0.02)
            tread.fillColor = NSColor(calibratedWhite: 0.44, alpha: 1)
            tread.strokeColor = .clear
            let startX = -h * 0.84 + CGFloat(i) * h * 0.21
            tread.position = CGPoint(x: startX, y: h * 0.16)
            root.addChild(tread)
            tread.run(.repeatForever(.sequence([
                .moveBy(x: -h * 0.21, y: 0, duration: 0.14),
                .moveBy(x: h * 0.21, y: 0, duration: 0)
            ])))
        }

        // rollers inside the track
        for i in 0..<4 {
            let roller = SKShapeNode(circleOfRadius: h * 0.11)
            roller.fillColor = NSColor(calibratedWhite: 0.62, alpha: 1)
            roller.strokeColor = NSColor(calibratedWhite: 0.32, alpha: 1)
            roller.lineWidth = max(1, h * 0.03)
            roller.position = CGPoint(x: -h * 0.64 + CGFloat(i) * h * 0.43, y: h * 0.16)
            let spoke = SKShapeNode(rectOf: CGSize(width: h * 0.14, height: h * 0.03))
            spoke.fillColor = NSColor(calibratedWhite: 0.32, alpha: 1)
            spoke.strokeColor = .clear
            roller.addChild(spoke)
            root.addChild(roller)
            roller.run(.repeatForever(.rotate(byAngle: -.pi * 2, duration: 0.5)))
        }

        // beacon
        let beacon = SKShapeNode(circleOfRadius: h * 0.11)
        beacon.fillColor = NSColor(calibratedRed: 1.0, green: 0.62, blue: 0.15, alpha: 1)
        beacon.strokeColor = .clear
        beacon.position = CGPoint(x: -h * 0.28, y: h * 1.34)
        beacon.run(.repeatForever(.sequence([
            .fadeAlpha(to: 0.25, duration: 0.35),
            .fadeAlpha(to: 1.0, duration: 0.35)
        ])))
        root.addChild(beacon)

        return root
    }
}

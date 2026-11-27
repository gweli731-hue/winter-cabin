import AppKit
import SpriteKit

enum Textures {
    private static var cache: [String: SKTexture] = [:]

    /// A radial-gradient dot that fades to nothing at the edge.
    static func softDot(diameter: CGFloat, color: NSColor = .white) -> SKTexture {
        let key = "dot-\(Int(diameter))-\(color.description)"
        if let hit = cache[key] { return hit }

        let size = CGSize(width: diameter, height: diameter)
        let image = NSImage(size: size)
        image.lockFocus()
        if let ctx = NSGraphicsContext.current?.cgContext {
            let rgb = color.usingColorSpace(.deviceRGB) ?? NSColor.white
            let colors = [rgb.withAlphaComponent(1).cgColor,
                          rgb.withAlphaComponent(0.55).cgColor,
                          rgb.withAlphaComponent(0).cgColor] as CFArray
            if let grad = CGGradient(colorsSpace: CGColorSpaceCreateDeviceRGB(),
                                     colors: colors, locations: [0, 0.45, 1]) {
                let c = CGPoint(x: diameter / 2, y: diameter / 2)
                ctx.drawRadialGradient(grad, startCenter: c, startRadius: 0,
                                       endCenter: c, endRadius: diameter / 2, options: [])
            }
        }
        image.unlockFocus()

        let tex = SKTexture(image: image)
        cache[key] = tex
        return tex
    }

    /// A snowflake: a bright core with a soft halo, so flakes read at small sizes.
    static func flake(diameter: CGFloat) -> SKTexture {
        let key = "flake-\(Int(diameter))"
        if let hit = cache[key] { return hit }

        let size = CGSize(width: diameter, height: diameter)
        let image = NSImage(size: size)
        image.lockFocus()
        if let ctx = NSGraphicsContext.current?.cgContext {
            let colors = [NSColor.white.withAlphaComponent(1).cgColor,
                          NSColor.white.withAlphaComponent(0.85).cgColor,
                          NSColor.white.withAlphaComponent(0).cgColor] as CFArray
            if let grad = CGGradient(colorsSpace: CGColorSpaceCreateDeviceRGB(),
                                     colors: colors, locations: [0, 0.35, 1]) {
                let c = CGPoint(x: diameter / 2, y: diameter / 2)
                ctx.drawRadialGradient(grad, startCenter: c, startRadius: 0,
                                       endCenter: c, endRadius: diameter / 2, options: [])
            }
        }
        image.unlockFocus()

        let tex = SKTexture(image: image)
        cache[key] = tex
        return tex
    }

    static func sceneImage() -> NSImage? {
        guard let url = Bundle.module.url(forResource: "scene", withExtension: "jpg") else { return nil }
        return NSImage(contentsOf: url)
    }

    static func sceneURL() -> URL? {
        return Bundle.module.url(forResource: "scene", withExtension: "jpg")
    }
}

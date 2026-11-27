import Foundation
import CoreGraphics

/// Anchor points exported by tools/prepare_art.py alongside the scene image.
/// All values are normalised 0...1 with the origin at the top-left of the artwork.
struct SceneManifest: Decodable {
    struct Point: Decodable { let x: CGFloat; let y: CGFloat }
    struct Circle: Decodable { let x: CGFloat; let y: CGFloat; let r: CGFloat }
    struct Rect: Decodable { let x: CGFloat; let y: CGFloat; let w: CGFloat; let h: CGFloat }

    /// Native aspect ratio of the artwork the coordinates were measured on.
    let aspect: CGFloat
    let moon: Circle
    let chimney: Point
    let lake: Rect
    let windows: [Rect]
    let lanterns: [Point]
    let bulbs: [Point]
    let reflections: [Point]
    let villageWindows: Rect

    static func load() -> SceneManifest? {
        guard let url = Bundle.module.url(forResource: "scene-manifest", withExtension: "json"),
              let data = try? Data(contentsOf: url) else { return nil }
        return try? JSONDecoder().decode(SceneManifest.self, from: data)
    }
}

/// Maps normalised scene coordinates onto a view that shows the artwork aspect-filled.
struct SceneMapper {
    let size: CGSize
    let imageAspect: CGFloat

    init(size: CGSize, imageAspect: CGFloat) {
        self.size = size
        self.imageAspect = imageAspect
    }

    private var drawn: CGSize {
        guard size.height > 0 else { return size }
        let aspect = size.width / size.height
        if aspect > imageAspect {
            return CGSize(width: size.width, height: size.width / imageAspect)
        }
        return CGSize(width: size.height * imageAspect, height: size.height)
    }

    /// Normalised top-left coordinates to SpriteKit points (origin bottom-left).
    func point(_ nx: CGFloat, _ ny: CGFloat) -> CGPoint {
        let d = drawn
        let ox = (size.width - d.width) / 2
        let oy = (size.height - d.height) / 2
        return CGPoint(x: ox + nx * d.width, y: oy + (1 - ny) * d.height)
    }

    func point(_ p: SceneManifest.Point) -> CGPoint { return point(p.x, p.y) }

    /// A normalised vertical length in points.
    func length(_ v: CGFloat) -> CGFloat { return drawn.height * v }

    func rect(_ r: SceneManifest.Rect) -> CGRect {
        let topLeft = point(r.x, r.y)
        let d = drawn
        return CGRect(x: topLeft.x,
                      y: topLeft.y - r.h * d.height,
                      width: r.w * d.width,
                      height: r.h * d.height)
    }
}

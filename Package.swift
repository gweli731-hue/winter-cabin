// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "WinterCabin",
    platforms: [.macOS(.v13)],
    targets: [
        .executableTarget(
            name: "WinterCabin",
            path: "Sources/WinterCabin",
            resources: [.process("Resources")]
        )
    ]
)

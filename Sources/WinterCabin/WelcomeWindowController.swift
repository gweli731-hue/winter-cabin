import AppKit

/// Shown once on first launch, and again from "About Winter Cabin".
final class WelcomeWindowController: NSObject, NSWindowDelegate {

    private var window: NSWindow?
    private static var retained: WelcomeWindowController?

    func show() {
        WelcomeWindowController.retained = self

        if let window = window {
            window.makeKeyAndOrderFront(nil)
            NSApp.activate(ignoringOtherApps: true)
            return
        }

        let size = CGSize(width: 580, height: 648)
        let window = NSWindow(contentRect: CGRect(origin: .zero, size: size),
                              styleMask: [.titled, .closable],
                              backing: .buffered,
                              defer: false)
        window.title = "Winter Cabin"
        window.isReleasedWhenClosed = false
        window.delegate = self
        window.center()
        window.contentView = makeContent(size: size)
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        self.window = window
    }

    func windowWillClose(_ notification: Notification) {
        window = nil
        WelcomeWindowController.retained = nil
    }

    // MARK: - content

    private func makeContent(size: CGSize) -> NSView {
        let root = NSView(frame: CGRect(origin: .zero, size: size))
        root.wantsLayer = true
        root.layer?.backgroundColor = NSColor(calibratedRed: 0.10, green: 0.12, blue: 0.22,
                                              alpha: 1).cgColor

        if let image = Textures.sceneImage() {
            let banner = NSImageView(frame: CGRect(x: 0, y: size.height - 176,
                                                   width: size.width, height: 176))
            banner.image = image
            banner.imageScaling = .scaleAxesIndependently
            banner.wantsLayer = true
            banner.layer?.masksToBounds = true
            root.addSubview(banner)
        }

        let title = label("Winter Cabin", size: 24, weight: .semibold,
                          color: NSColor(calibratedWhite: 0.98, alpha: 1))
        title.frame = CGRect(x: 32, y: size.height - 220, width: size.width - 64, height: 32)
        root.addSubview(title)

        let bodyText = """
        Snow is now falling over your desktop. It drifts past your windows, \
        settles along the bottom of the screen, on top of the Dock and on the \
        top edge of any window that is open.

        • Click an empty patch of desktop to drop a snowball.
        • Stack three snowballs and you get a snowman.
        • Every few minutes a little plow comes through and clears it all away. \
        You can also send it from the menu.

        Everything lives behind the snowflake in your menu bar — snow on or off, \
        how heavy it falls, and whether it piles up on windows.

        Winter Cabin needs no special permissions. It reads where your windows \
        are using only their position and size, never their contents, so macOS \
        does not ask for Screen Recording or Accessibility. The snow layer never \
        swallows a click: your Dock, icons and apps all behave normally.

        Quitting puts your previous desktop picture back.
        """
        let body = label(bodyText, size: 12.5, weight: .regular,
                         color: NSColor(calibratedWhite: 0.82, alpha: 1))
        body.frame = CGRect(x: 32, y: 66, width: size.width - 64, height: size.height - 296)
        root.addSubview(body)

        let button = NSButton(title: "Let it snow", target: self, action: #selector(close))
        button.bezelStyle = .rounded
        button.keyEquivalent = "\r"
        button.frame = CGRect(x: size.width - 152, y: 22, width: 120, height: 32)
        root.addSubview(button)

        return root
    }

    private func label(_ text: String, size: CGFloat, weight: NSFont.Weight,
                       color: NSColor) -> NSTextField {
        let field = NSTextField(wrappingLabelWithString: text)
        field.font = .systemFont(ofSize: size, weight: weight)
        field.textColor = color
        field.drawsBackground = false
        field.isBezeled = false
        field.isEditable = false
        field.isSelectable = false
        // this view is laid out by frame, not by constraints
        field.translatesAutoresizingMaskIntoConstraints = true
        return field
    }

    @objc private func close() {
        window?.close()
    }
}

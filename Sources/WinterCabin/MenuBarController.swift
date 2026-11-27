import AppKit

/// The snowflake in the menu bar and everything behind it.
final class MenuBarController: NSObject, NSMenuDelegate {

    private let statusItem: NSStatusItem
    private let overlay: OverlayController

    init(overlay: OverlayController) {
        self.overlay = overlay
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
        super.init()

        if let button = statusItem.button {
            button.image = NSImage(systemSymbolName: "snowflake",
                                   accessibilityDescription: "Winter Cabin")
            button.image?.isTemplate = true
            button.toolTip = "Winter Cabin"
        }

        let menu = NSMenu()
        menu.delegate = self
        menu.autoenablesItems = false
        statusItem.menu = menu
    }

    // MARK: - menu

    func menuNeedsUpdate(_ menu: NSMenu) {
        menu.removeAllItems()
        let settings = Settings.shared

        menu.addItem(toggle("Snow", #selector(toggleSnow), settings.snowEnabled))

        let densityItem = NSMenuItem(title: "Density", action: nil, keyEquivalent: "")
        let densityMenu = NSMenu()
        for level in SnowDensity.allCases {
            let item = NSMenuItem(title: level.title,
                                  action: #selector(pickDensity(_:)), keyEquivalent: "")
            item.target = self
            item.tag = level.rawValue
            item.state = settings.density == level ? .on : .off
            item.isEnabled = settings.snowEnabled
            densityMenu.addItem(item)
        }
        densityMenu.autoenablesItems = false
        densityItem.submenu = densityMenu
        densityItem.isEnabled = settings.snowEnabled
        menu.addItem(densityItem)

        menu.addItem(.separator())
        menu.addItem(toggle("Pile up on windows", #selector(togglePiles), settings.pileOnWindows))
        menu.addItem(toggle("Snowballs on click", #selector(toggleSnowballs),
                            settings.snowballsOnClick))

        menu.addItem(.separator())
        let plow = NSMenuItem(title: "Send the plow now",
                              action: #selector(sendPlow), keyEquivalent: "")
        plow.target = self
        plow.isEnabled = settings.snowEnabled
        menu.addItem(plow)

        menu.addItem(.separator())
        menu.addItem(toggle("Ambient wallpaper motion", #selector(toggleAmbient),
                            settings.ambientEnabled))
        menu.addItem(toggle("Use Winter Cabin as desktop picture",
                            #selector(toggleWallpaper), settings.setsWallpaper))

        menu.addItem(.separator())
        menu.addItem(toggle("Launch at login", #selector(toggleLogin), LaunchAtLogin.isEnabled))

        menu.addItem(.separator())
        let about = NSMenuItem(title: "About Winter Cabin",
                               action: #selector(showAbout), keyEquivalent: "")
        about.target = self
        about.isEnabled = true
        menu.addItem(about)

        let quit = NSMenuItem(title: "Quit Winter Cabin",
                              action: #selector(quit), keyEquivalent: "q")
        quit.target = self
        quit.isEnabled = true
        menu.addItem(quit)
    }

    private func toggle(_ title: String, _ action: Selector, _ on: Bool) -> NSMenuItem {
        let item = NSMenuItem(title: title, action: action, keyEquivalent: "")
        item.target = self
        item.state = on ? .on : .off
        item.isEnabled = true
        return item
    }

    // MARK: - actions

    @objc private func toggleSnow() {
        Settings.shared.snowEnabled.toggle()
    }

    @objc private func pickDensity(_ sender: NSMenuItem) {
        guard let level = SnowDensity(rawValue: sender.tag) else { return }
        Settings.shared.density = level
    }

    @objc private func togglePiles() {
        Settings.shared.pileOnWindows.toggle()
    }

    @objc private func toggleSnowballs() {
        Settings.shared.snowballsOnClick.toggle()
    }

    @objc private func sendPlow() {
        overlay.sendPlow()
    }

    @objc private func toggleAmbient() {
        Settings.shared.ambientEnabled.toggle()
    }

    @objc private func toggleWallpaper() {
        let on = !Settings.shared.setsWallpaper
        Settings.shared.setsWallpaper = on
        if on { WallpaperSetter.apply() } else { WallpaperSetter.restore() }
    }

    @objc private func toggleLogin() {
        let wanted = !LaunchAtLogin.isEnabled
        if !LaunchAtLogin.set(wanted) {
            let alert = NSAlert()
            alert.messageText = "Could not change Launch at Login"
            alert.informativeText = "macOS refused the change. You can set it yourself in "
                + "System Settings › General › Login Items."
            alert.alertStyle = .warning
            alert.runModal()
        }
    }

    @objc private func showAbout() {
        WelcomeWindowController().show()
    }

    @objc private func quit() {
        NSApp.terminate(nil)
    }
}

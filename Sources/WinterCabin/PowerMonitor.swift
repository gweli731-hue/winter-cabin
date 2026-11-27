import AppKit

/// Tells the renderers when to stop drawing: screen locked, screen saver up,
/// display asleep, or Low Power Mode engaged.
final class PowerMonitor {
    static let shared = PowerMonitor()
    static let didChange = Notification.Name("WinterCabinPowerDidChange")

    private(set) var isLocked = false
    private(set) var isDisplayAsleep = false

    var shouldAnimate: Bool {
        return !isLocked && !isDisplayAsleep && !ProcessInfo.processInfo.isLowPowerModeEnabled
    }

    private init() {}

    func start() {
        let dnc = DistributedNotificationCenter.default()
        dnc.addObserver(self, selector: #selector(lock),
                        name: NSNotification.Name("com.apple.screenIsLocked"), object: nil)
        dnc.addObserver(self, selector: #selector(unlock),
                        name: NSNotification.Name("com.apple.screenIsUnlocked"), object: nil)
        dnc.addObserver(self, selector: #selector(lock),
                        name: NSNotification.Name("com.apple.screensaver.didstart"), object: nil)
        dnc.addObserver(self, selector: #selector(unlock),
                        name: NSNotification.Name("com.apple.screensaver.didstop"), object: nil)

        let wnc = NSWorkspace.shared.notificationCenter
        wnc.addObserver(self, selector: #selector(sleepOn),
                        name: NSWorkspace.screensDidSleepNotification, object: nil)
        wnc.addObserver(self, selector: #selector(sleepOff),
                        name: NSWorkspace.screensDidWakeNotification, object: nil)

        NotificationCenter.default.addObserver(
            self, selector: #selector(changed),
            name: .NSProcessInfoPowerStateDidChange, object: nil)
    }

    @objc private func lock()      { isLocked = true;  changed() }
    @objc private func unlock()    { isLocked = false; changed() }
    @objc private func sleepOn()   { isDisplayAsleep = true;  changed() }
    @objc private func sleepOff()  { isDisplayAsleep = false; changed() }

    @objc private func changed() {
        NotificationCenter.default.post(name: PowerMonitor.didChange, object: nil)
    }
}

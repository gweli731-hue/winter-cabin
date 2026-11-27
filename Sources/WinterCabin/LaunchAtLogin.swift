import Foundation
import ServiceManagement

enum LaunchAtLogin {

    static var isEnabled: Bool {
        return SMAppService.mainApp.status == .enabled
    }

    @discardableResult
    static func set(_ enabled: Bool) -> Bool {
        do {
            if enabled {
                try SMAppService.mainApp.register()
            } else {
                try SMAppService.mainApp.unregister()
            }
            return true
        } catch {
            NSLog("Winter Cabin: launch at login change failed: \(error)")
            return false
        }
    }
}

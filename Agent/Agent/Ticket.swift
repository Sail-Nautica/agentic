import SwiftUI
import LocalAuthentication
import Security

// Authorization ticket issued by harnessd. The Secure Enclave key behind the keychain
// item never leaves the hardware; biometrics only gate reading and writing the stored
// ticket, they add nothing to the security of Google sign-in.
final class Ticket {
    static let shared = Ticket()
    private init() {}

    var vm: AppViewModel?
    var creator = ""
    var expiration = Date(timeIntervalSince1970: 0)
    private var _ticket: String?

    var ticket: String? {
        get { Date() > expiration ? nil : _ticket }
        set { _ticket = newValue }
    }

    private static let expirationFormat: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd HH:mm:ss '+'SSSS"
        return formatter
    }()

    private static let identity: [String: Any] = [
        kSecClass as String: kSecClassGenericPassword,
        kSecAttrDescription as String: "Ticket",
    ]

    private static func message(_ status: OSStatus) -> String {
        SecCopyErrorMessageString(status, nil) as String? ?? "OSStatus \(status)"
    }

    // the biometric prompt blocks until the user answers, so keep it off the main actor
    @concurrent
    private static func copyItem(_ query: [String: Any]) async -> (OSStatus, [String: Any]?) {
        var item: CFTypeRef?
        let status = SecItemCopyMatching(query as CFDictionary, &item)
        return (status, item as? [String: Any])
    }

    func open(errMsg: Binding<String>, showOk: Binding<Bool>) async {
        guard expiration == Date(timeIntervalSince1970: 0) else { return }

        guard SecItemCopyMatching(Ticket.identity as CFDictionary, nil) == errSecSuccess else {
            errMsg.wrappedValue = "No previous Ticket found. Will acquire on sign in."
            showOk.wrappedValue = true
            return
        }

        let context = LAContext()
        #if targetEnvironment(simulator)
        // the simulator keychain does not prompt, so simulate the biometric check
        guard (try? await context.evaluatePolicy(.deviceOwnerAuthentication,
                localizedReason: "To access ticket in Keychain.")) == true else {
            errMsg.wrappedValue = "Biometric authentication failed. Will acquire on sign in."
            showOk.wrappedValue = true
            return
        }
        #endif

        let (status, item) = await Ticket.copyItem(Ticket.identity.merging([
            kSecReturnData as String: true,
            kSecReturnAttributes as String: true,
            kSecUseAuthenticationContext as String: context,
        ]) { $1 })
        guard status == errSecSuccess, let item else {
            errMsg.wrappedValue = Ticket.message(status)
            return
        }

        guard let data = item[kSecValueData as String] as? Data,
              let stored = String(data: data, encoding: .utf8),
              let label = item[kSecAttrLabel as String] as? String,
              let storedExpiration = Ticket.expirationFormat.date(from: label) else {
            delete(errMsg: errMsg)
            errMsg.wrappedValue = "Invalid Ticket in Keychain. Will acquire on sign in."
            showOk.wrappedValue = true
            return
        }

        guard storedExpiration > Date() else {
            errMsg.wrappedValue = "Stored Ticket has expired. Will acquire on sign in."
            showOk.wrappedValue = true
            return
        }

        _ticket = stored
        expiration = storedExpiration
        creator = item[kSecAttrCreator as String] as? String ?? ""
    }

    func save(errMsg: Binding<String>, showOk: Binding<Bool>) {
        guard let ticket else { return }
        let attributes: [String: Any] = [
            kSecValueData as String: Data(ticket.utf8),
            kSecAttrLabel as String: Ticket.expirationFormat.string(from: expiration),
            kSecAttrCreator as String: creator,
        ]

        let status: OSStatus
        if SecItemCopyMatching(Ticket.identity as CFDictionary, nil) == errSecSuccess {
            status = SecItemUpdate(Ticket.identity as CFDictionary, attributes as CFDictionary)
        } else {
            guard let access = SecAccessControlCreateWithFlags(nil,
                    kSecAttrAccessibleWhenPasscodeSetThisDeviceOnly, .userPresence, nil) else {
                errMsg.wrappedValue = "Cannot create Keychain access control. You will need to sign in again on relaunch."
                return
            }
            status = SecItemAdd(Ticket.identity.merging(attributes) { $1 }
                .merging([kSecAttrAccessControl as String: access]) { $1 } as CFDictionary, nil)
        }

        if status == errSecSuccess {
            errMsg.wrappedValue = "Ticket saved"
            showOk.wrappedValue = true
        } else {
            errMsg.wrappedValue = "\(Ticket.message(status)). You will need to sign in again on relaunch."
        }
    }

    // forces a fresh sign-in when harnessd rejects the current ticket
    func delete(errMsg: Binding<String>) {
        let status = SecItemDelete(Ticket.identity as CFDictionary)
        if status != errSecSuccess && status != errSecItemNotFound {
            errMsg.wrappedValue += Ticket.message(status)
        }
    }
}

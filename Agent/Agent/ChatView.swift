import SwiftUI

@Observable
final class Chat: Identifiable {
    let id: UUID = UUID()   // view ID
    @ObservationIgnored
    var role: String
    var content: String   // for reactive UI to display streaming tokens
    @ObservationIgnored
    var timestamp: String
    
    init(role: String = "user", content: String = "", timestamp: String = Date().ISO8601Format()) {
        self.role = role
        self.content = content
        self.timestamp = timestamp
    }
}

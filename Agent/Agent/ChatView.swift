import SwiftUI

@Observable
final class Chat: Identifiable {
    let id: UUID = UUID()

    @ObservationIgnored
    var role: String

    var content: String

    @ObservationIgnored
    var timestamp: String

    init(
        role: String = "user",
        content: String = "",
        timestamp: String = Date().ISO8601Format()
    ) {
        self.role = role
        self.content = content
        self.timestamp = timestamp
    }

}

struct ChatView: View {
    let chat: Chat
    let onTrailingEnd: Bool

    var body: some View {
        VStack(alignment: onTrailingEnd ? .trailing : .leading, spacing: 4) {
            let msg = chat.content

            if !msg.isEmpty {
                Text(onTrailingEnd ? "" : chat.role)
                    .font(.subheadline)
                    .foregroundColor(.purple)
                    .padding(.leading, 4)

                Text(msg)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 8)
                    .background(Color(onTrailingEnd ? .systemBlue : .systemBackground))
                    .foregroundColor(onTrailingEnd ? .white : .primary)
                    .cornerRadius(20)
                    .shadow(radius: 2)
                    .frame(maxWidth: 300, alignment: onTrailingEnd ? .trailing : .leading)

                Text(chat.timestamp)
                    .font(.caption2)
                    .foregroundColor(.gray)

                Spacer()
                    .frame(maxWidth: .infinity)
            }
        }
        .padding(.horizontal, 16)
    }
}

struct ConversationView: View {
    @Environment(AppViewModel.self) private var vm
    
    var body: some View {
        ScrollViewReader { proxy in
            ScrollView {
                LazyVStack {
                    ForEach(vm.conversation) {
                        ChatView(chat: $0, onTrailingEnd: $0.role == "user")
                    }
                }
            }
            .defaultScrollAnchor(.bottom)
            .onChange(of: vm.conversation.count) {
                if let bottomID = vm.conversation.last?.id {
                    withAnimation {
                        proxy.scrollTo(bottomID, anchor: .bottom)
                    }
                }
            }
        }
    }
}

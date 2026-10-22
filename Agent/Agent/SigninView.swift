import SwiftUI
import GoogleSignIn
import GoogleSignInSwift

extension GIDSignIn {
    func signInAsync(withPresenting viewController: UIViewController) async -> String? {
        await withUnsafeContinuation { continuation in
            signIn(withPresenting: viewController) { result, _ in
                continuation.resume(returning: result?.user.idToken?.tokenString)
            }
        }
    }

    func restorePreviousSignInAsync() async -> String? {
        await withUnsafeContinuation { continuation in
            restorePreviousSignIn { user, _ in
                continuation.resume(returning: user?.idToken?.tokenString)
            }
        }
    }
}

struct SigninView: View {
    @Environment(AppViewModel.self) private var vm
    @Binding var isPresenting: Bool
    private let signinClient = GIDSignIn.sharedInstance
    @State private var isRefreshing = true

    var body: some View {
        let rootVC = UIApplication.shared.connectedScenes
            .compactMap { ($0 as? UIWindowScene)?.keyWindow?.rootViewController }.first

        GoogleSignInButton {
            Task {
                defer { isPresenting = false }
                guard let rootVC, let idToken = await signinClient.signInAsync(withPresenting: rootVC) else {
                    vm.errMsg = "Failed Google Sign-In. Please try again."
                    return
                }
                await getTicket(idToken)
            }
        }
        .frame(width: 100, height: 50)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .opacity(isRefreshing ? 0 : 1)
        .overlay {
            if isRefreshing {
                VStack {
                    Text("Refreshing credentials...")
                    ProgressView().scaleEffect(2).padding()
                }
            }
        }
        .task {
            let idToken = if let current = signinClient.currentUser?.idToken?.tokenString { current }
                else { await signinClient.restorePreviousSignInAsync() }
            guard let idToken else {
                isRefreshing = false
                return
            }
            await getTicket(idToken)
            isPresenting = false
        }
        .onDisappear {
            if let completion = vm.signinCompletion {
                vm.signinCompletion = nil
                Task { await completion() }
            }
        }
    }

    private func getTicket(_ idToken: String?) async {
        guard await vm.rein.addAgent(idToken, errMsg: Bindable(vm).errMsg) != nil else {
            vm.errMsg = "harnessd cannot add user. Please try again."
            isRefreshing = false
            return
        }
        Ticket.shared.save(errMsg: Bindable(vm).errMsg, showOk: Bindable(vm).showOk)
        // save reports its own failure; only a successful save is advertised as a refresh
        if vm.showOk { vm.errMsg = "Ticket refreshed." }
    }
}

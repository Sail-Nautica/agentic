//
//  ContentView.swift
//  Agent
//
//  Created by Amit Sail on 9/4/26.
//

import SwiftUI
import MapKit

struct SubmitButton: View {
    @Environment(AppViewModel.self) private var vm
    @State private var isSending = false

    var body: some View {
        Button {
            isSending = true
            vm.isBusy = true

            let chat = Chat(content: vm.message)
            vm.conversation.append(chat)
            
            // pass chat to harness in an array of `messages`
            // but Swift encoder cannot serialize @Observable hidden 
            // variable correctly (_content in this case) so must 
            // manually convert the hidden Chat._content to Message.content
            let messages = [Message(role: chat.role, content: chat.content)]   
            
            // prepare completion placeholder
            let completion = Chat(role: "assistant",
                                content: "", timestamp: "") // placeholder for assistant's streaming completion
            vm.conversation.append(completion)
            
            Task (priority: .background){
                await vm.rein.llmTools(messages, completion: completion, errMsg: Bindable(vm).errMsg)                
                // cleanup
                vm.message = ""
                isSending = false
                vm.isBusy = false
                vm.showError = !vm.errMsg.isEmpty
            }
        } label: {
            if isSending {
                ProgressView()
                    .progressViewStyle(CircularProgressViewStyle(tint: .secondary))
                    .padding(10)
            } else {
                Image(systemName: "paperplane.fill")
                    .foregroundColor(vm.message.isEmpty ? .gray : .yellow)
                    .padding(10)
            }
        }
        .disabled(isSending || vm.message.isEmpty || vm.isBusy)
        .background(Color(isSending || vm.message.isEmpty ? .secondarySystemBackground : .systemBlue))
        .clipShape(Circle())
        .padding(.trailing)
    }
}

struct ClearButton: View {
    @Environment(AppViewModel.self) private var vm

    var body: some View {
        Button {
            Task { await vm.resetGame() }
        } label: {
            if vm.isBusy {
                ProgressView().progressViewStyle(CircularProgressViewStyle(tint: .secondary)).padding(10)
            } else {
                Image(systemName: "trash.fill").foregroundColor(.red).padding(10)
            }
        }
        .disabled(vm.isBusy)
        .background(Color(.secondarySystemBackground))
        .clipShape(Circle())
        .padding(.trailing)
    }
}

struct MapArea: View {
    @Bindable private var loc = LocManagerViewModel.shared

    var body: some View {
        if loc.isPositioned {
            // UserAnnotation is the system's own location dot, not a marker we add
            Map(position: $loc.camera) { UserAnnotation() }
        } else {
            ProgressView().frame(maxWidth: .infinity, maxHeight: .infinity)
        }
    }
}

struct ContentView: View {
    @FocusState private var messageInFocus: Bool // tap background to dismiss kbd
    @Environment(AppViewModel.self) private var vm

    var body: some View {
        VStack {
            MapArea()

            if let hint = vm.hint {
                ScrollView {
                    Text(hint.content.trimmingCharacters(in: .whitespacesAndNewlines))
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(.horizontal, 16)
                }
                .frame(maxHeight: 160)
            }
            
            HStack (alignment: .bottom) {
                TextField(vm.instruction, text: Bindable(vm).message)
                    .focused($messageInFocus) // to dismiss keyboard
                    .textFieldStyle(.roundedBorder)
                    .cornerRadius(20)
                    .shadow(radius: 2)
                    .background(Color(.clear))
                    .border(Color(.clear))

                ClearButton()
                SubmitButton()
            }
            .padding(EdgeInsets(top: 0, leading: 20, bottom: 8, trailing: 0))
        }
        .contentShape(.rect)
        .onTapGesture {
            messageInFocus.toggle()
        }
        .task {
            // app-launch initialization: same wipe-then-rules start as Clear, so a relaunch never stacks on an old game
            guard vm.conversation.isEmpty, !vm.isBusy else { return }
            await vm.resetGame()
        }
            .alert(vm.showError ? "LLM Error" : "Advisory", isPresented: Binding<Bool>(
                get: { vm.showError || vm.showOk },
                set: { _ in
                    vm.showError = false
                    vm.showOk = false
                }
            )) {
                Button("OK") {
                    vm.errMsg = ""
                }
            } message: {
                Text(vm.errMsg)
            }
            .sheet(isPresented: Bindable(vm).getSignedin) {
                SigninView(isPresenting: Bindable(vm).getSignedin)
                    .presentationDetents([.fraction(0.25)])
                    .presentationDragIndicator(.hidden)
                    .interactiveDismissDisabled()
            }
    }
}

//
//  ContentView.swift
//  Agent
//
//  Created by Amit Sail on 9/4/26.
//

import SwiftUI

struct SubmitButton: View {
    @Environment(AppViewModel.self) private var vm

    @State private var isSending = false

    private var hasContent: Bool { !vm.systemPrompt.isEmpty || !vm.userPrompt.isEmpty }

    var body: some View {
        Button {
            isSending = true

            // fields persist until Send is clicked, then clear immediately
            let system = vm.systemPrompt
            let user = vm.userPrompt
            vm.systemPrompt = ""
            vm.userPrompt = ""

            Task(priority: .background) {
                await vm.sendTurn(system: system, user: user)
                isSending = false
                vm.showError = !vm.errMsg.isEmpty
            }

        } label: {
            if isSending {
                ProgressView().progressViewStyle(CircularProgressViewStyle(tint: .secondary)).padding(10)
            } else {
                Image(systemName: "paperplane.fill").foregroundColor(hasContent ? .yellow : .gray).padding(10)
            }
        }
        .disabled(isSending || !hasContent)
        .background(Color(isSending || !hasContent ? .secondarySystemBackground : .systemBlue))
        .clipShape(Circle())
        .padding(.trailing)
    }
}

struct ClearButton: View {
    @Environment(AppViewModel.self) private var vm

    @State private var isClearing = false

    var body: some View {
        Button {
            isClearing = true
            Task(priority: .background) {
                await vm.resetGame()
                isClearing = false
                vm.showError = !vm.errMsg.isEmpty
            }
        } label: {
            if isClearing {
                ProgressView().progressViewStyle(CircularProgressViewStyle(tint: .secondary)).padding(10)
            } else {
                Image(systemName: "trash.fill").foregroundColor(.red).padding(10)
            }
        }
        .disabled(isClearing)
        .background(Color(.secondarySystemBackground))
        .clipShape(Circle())
        .padding(.trailing)
    }
}

struct ContentView: View {
    @FocusState private var messageInFocus: Bool // tap background to dismiss
    @Environment(AppViewModel.self) private var vm

    var body: some View {
        VStack {
            Picker("Game", selection: Bindable(vm).game) {
                ForEach(Game.allCases) { Text($0.rawValue).tag($0) }
            }
            .pickerStyle(.segmented)
            .padding(.horizontal)
            .onChange(of: vm.game) {
                Task(priority: .background) { await vm.resetGame() }
            }

            ConversationView()

            VStack(spacing: 6) {
                TextField(vm.systemInstruction, text: Bindable(vm).systemPrompt)
                    .focused($messageInFocus)
                    .textFieldStyle(.roundedBorder)

                HStack(alignment: .bottom) {
                    TextField(vm.userInstruction, text: Bindable(vm).userPrompt)
                        .focused($messageInFocus)
                        .textFieldStyle(.roundedBorder)
                        .cornerRadius(20)
                        .shadow(radius: 2)
                        .backgroundStyle(Color(.clear))
                        .border(Color(.clear))
                    ClearButton()
                    SubmitButton()
                }
            }
            .padding(EdgeInsets(top: 0, leading: 20, bottom: 8, trailing: 0))
        }
        .contentShape(.rect)
        .onTapGesture {messageInFocus.toggle()}
        .navigationTitle(vm.game.rawValue)
        .navigationBarTitleDisplayMode(.inline)
        .task {
            // app-launch initialization: send the game rules before any user input
            guard vm.conversation.isEmpty else { return }
            await vm.sendTurn(system: vm.game.rules, user: "")
        }
        .alert("LLM Error", isPresented: Bindable(vm).showError) {
                Button("OK") {
                    vm.errMsg = ""
                }
            } message: {
                Text(vm.errMsg)
            }
    }
}

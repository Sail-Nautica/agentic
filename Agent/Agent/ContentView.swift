//
//  ContentView.swift
//  Agent
//
//  Created by Amit Sail on 9/4/26.
//

import SwiftUI

struct SubmitButton: View {
    @Environment(AppViewModel.self) private var vm

    private var hasContent: Bool { !vm.systemDraft.isEmpty || !vm.userDraft.isEmpty }

    var body: some View {
        Button {
            // both drafts persist across toggles until Send, then clear immediately; role reverts to user
            let system = vm.systemDraft
            let user = vm.userDraft
            vm.systemDraft = ""
            vm.userDraft = ""
            vm.draftIsSystem = false

            Task { await vm.sendTurn(system: system, user: user) }

        } label: {
            if vm.isBusy {
                ProgressView().progressViewStyle(CircularProgressViewStyle(tint: .secondary)).padding(10)
            } else {
                Image(systemName: "paperplane.fill").foregroundColor(hasContent ? .yellow : .gray).padding(10)
            }
        }
        .disabled(vm.isBusy || !hasContent)
        .background(Color(vm.isBusy || !hasContent ? .secondarySystemBackground : .systemBlue))
        .clipShape(Circle())
        .padding(.trailing)
    }
}

struct RoleToggleButton: View {
    @Environment(AppViewModel.self) private var vm

    var body: some View {
        Button {
            vm.draftIsSystem.toggle()
        } label: {
            Image(systemName: vm.draftIsSystem ? "gearshape.fill" : "person.fill")
                .foregroundColor(vm.draftIsSystem ? .orange : .blue).padding(10)
        }
        .background(Color(.secondarySystemBackground))
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
                Task { await vm.resetGame() }
            }

            ConversationView()

            HStack(alignment: .bottom) {
                TextField(vm.draftIsSystem ? vm.systemInstruction : vm.userInstruction, text: vm.draftIsSystem ? Bindable(vm).systemDraft : Bindable(vm).userDraft)
                    .focused($messageInFocus)
                    .textFieldStyle(.roundedBorder)
                    .cornerRadius(20)
                    .shadow(radius: 2)
                    .backgroundStyle(Color(.clear))
                    .border(Color(.clear))
                RoleToggleButton()
                ClearButton()
                SubmitButton()
            }
            .padding(EdgeInsets(top: 0, leading: 20, bottom: 8, trailing: 0))
        }
        .contentShape(.rect)
        .onTapGesture {messageInFocus.toggle()}
        .navigationTitle("llmTools")
        .navigationBarTitleDisplayMode(.inline)
        .task {
            // app-launch initialization: send the game rules before any user input
            guard vm.conversation.isEmpty else { return }
            await vm.sendTurn(system: vm.game.rules, user: "")
        }
        .alert(vm.showError ? "LLM Error" : "Advisory",
               isPresented: Binding(get: { vm.showError || vm.showOk },
                                    set: { if !$0 { vm.showError = false; vm.showOk = false } })) {
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

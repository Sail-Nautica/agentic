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

    private var hasContent: Bool { !vm.userDraft.allSatisfy(\.isWhitespace) }

    var body: some View {
        Button {
            let user = vm.userDraft
            vm.userDraft = ""

            Task { await vm.sendTurn(system: "", user: user) }

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
    @FocusState private var messageInFocus: Bool // tap background to dismiss
    @Environment(AppViewModel.self) private var vm

    var body: some View {
        VStack {
            MapArea()

            VStack {
                if let hint = vm.hint {
                    ScrollView {
                        Text(hint.content.trimmingCharacters(in: .whitespacesAndNewlines))
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .padding(.horizontal, 16)
                    }
                    .frame(maxHeight: 160)
                }

                HStack(alignment: .bottom) {
                    TextField(vm.userInstruction, text: Bindable(vm).userDraft)
                        .focused($messageInFocus)
                        .textFieldStyle(.roundedBorder)
                        .cornerRadius(20)
                        .shadow(radius: 2)
                        .backgroundStyle(Color(.clear))
                        .border(Color(.clear))
                    ClearButton()
                    SubmitButton()
                }
                .padding(EdgeInsets(top: 0, leading: 20, bottom: 8, trailing: 0))
            }
            .contentShape(.rect)
            .onTapGesture { messageInFocus = false } // dismiss only, and never from a tap on the map
        }
        .task {
            // app-launch initialization: same wipe-then-rules start as Clear, so a relaunch never stacks on an old game
            guard vm.conversation.isEmpty, !vm.isBusy else { return }
            await vm.resetGame()
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

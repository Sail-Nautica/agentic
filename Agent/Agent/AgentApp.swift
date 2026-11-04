//
//  AgentApp.swift
//  Agent
//
//  Created by Amit Sail on 9/4/26.
//

import SwiftUI
import Foundation

struct Exception: Error, LocalizedError {
    let errorDescription: String?
}

extension Optional where Wrapped == String {
    var nilIfEmpty: String? {
        guard let self, !self.isEmpty else {return nil}
        return self
    }
}

enum Game {
    case guessTheCity

    // system prompt sent once per game; /llmchat replays it from history on every later turn
    var rules: String {
        switch self {
        case .guessTheCity:
            "You are hosting a 'Guess the City' game with the user. Choose a well-known city yourself, picked at random from anywhere in the world; do not default to the most famous city and vary your choice from game to game. Reply in plain text with no markdown. On your very first reply, before any other text, output [SECRET: <the city you are choosing>] - for example [SECRET: Paris] - then give a short welcome and one hint. That marker is hidden from the player and is how you will remember your exact choice on every later turn, so treat it as fixed and never contradict it. Write it once, at the start of the game, and never again. Hints never include the city's name. When the user guesses wrong or asks for a clue, give one new hint. When the user guesses the city correctly, first call get_auth to obtain a ticket, then call recenter_map with that ticket and the city's latitude and longitude. Give the coordinates as plain decimal numbers (for example 48.8566 and 2.3522), negative for south and west, with no degree signs and no N, S, E or W letters, and never both zero. After recenter_map succeeds, congratulate the user and tell them to tap Clear for a new game. If get_auth reports that the task cannot be completed due to failed authorization, do not call it again: tell the user authorization failed, reveal the city, and tell them to tap Clear. If recenter_map reports a rejected ticket, follow the instruction in that message; no other retry rule applies. If the user gives up, reveal the city and tell them to tap Clear. After the game has ended, do not start another game; remind the user to tap Clear. Use only get_auth and recenter_map, and never call recenter_map before a correct guess."
        }
    }
}

@Observable
final class AppViewModel {
    let rein = Rein()

    var userDraft = ""
    var isBusy = false
    let userInstruction = "Type a message..."

    var errMsg = ""
    var showError = false
    var showOk = false
    var getSignedin = false
    @ObservationIgnored var signinCompletion: (() async -> Void)?

    var conversation: [Chat] = []
    var game: Game = .guessTheCity

    // the previous hint stays until the next reply streams in its first visible character
    var hint: Chat? {
        conversation.last { $0.role.hasPrefix("assistant") && !$0.content.allSatisfy(\.isWhitespace) }
    }

    // shared by SubmitButton and by game init/reset: empty fields omit their role's message
    func sendTurn(system: String, user: String) async {
        isBusy = true
        defer { isBusy = false }
        errMsg = "" // avoid re-surfacing a stale error left over from a dismissed turn
        var messages: [Message] = []

        if !system.isEmpty {
            conversation.append(Chat(role: "system", content: system))
            messages.append(Message(role: "system", content: system))
        }
        if !user.isEmpty {
            conversation.append(Chat(role: "user", content: user))
            messages.append(Message(role: "user", content: user))
        }

        let completion = Chat(role: "assistant", content: "", timestamp: "")
        conversation.append(completion)

        await rein.llmTools(messages, completion: completion, errMsg: Bindable(self).errMsg)
        // an advisory (showOk) shares errMsg and must not be promoted to an error
        showError = !errMsg.isEmpty && !showOk
    }

    func resetGame() async {
        isBusy = true
        defer { isBusy = false }
        LocManagerViewModel.shared.recenterOnUser()
        await rein.llmClear(errMsg: Bindable(self).errMsg)
        showError = !errMsg.isEmpty
        conversation.removeAll()
        await sendTurn(system: game.rules, user: "")
    }
}

@main
struct AgentApp: App {
    let vm = AppViewModel()

    init() {
        LocManager.shared.startUpdates()
        let vm = vm
        Ticket.shared.vm = vm
        Task { await Ticket.shared.open(errMsg: Bindable(vm).errMsg, showOk: Bindable(vm).showOk) }
    }

    var body: some Scene {
        WindowGroup {
            NavigationStack {
                ContentView()
                    .environment(vm)
            }
        }
    }
}

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

enum Game: String, CaseIterable, Identifiable {
    case guessTheCity = "Guess the City"
    case twentyQuestions = "20 Questions"

    var id: String { rawValue }

    // system prompt sent once per game; /llmchat replays it from history on every later turn
    var rules: String {
        switch self {
        case .guessTheCity:
            "You are hosting a 'Guess the City' game. Think of one real city and keep it secret. Give the user one clue at a time when they ask for one. When they correctly guess the city, congratulate them, reveal the city's approximate latitude and longitude, and invite them to play again."
        case .twentyQuestions:
            "You are hosting a game of 20 Questions. Think of one person, place, or thing and keep it secret. The user will ask up to 20 yes/no questions to narrow it down; answer each with Yes, No, or Not applicable, and tell them how many questions remain every few turns. When they correctly guess, congratulate them, reveal what you were thinking of, and invite them to play again."
        }
    }
}

@Observable
final class AppViewModel {
    let rein = Rein()

    var systemPrompt = ""
    var userPrompt = ""
    let systemInstruction = "System prompt (optional)..."
    let userInstruction = "Type a message..."

    var errMsg = ""
    var showError = false

    var conversation: [Chat] = []
    var game: Game = .guessTheCity

    // shared by SubmitButton and by game init/reset: empty fields omit their role's message
    @MainActor
    func sendTurn(system: String, user: String) async {
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

        await rein.llmPrompt(messages, completion: completion, errMsg: Bindable(self).errMsg)
        showError = !errMsg.isEmpty
    }

    @MainActor
    func resetGame() async {
        await rein.llmClear(errMsg: Bindable(self).errMsg)
        showError = !errMsg.isEmpty
        conversation.removeAll()
        await sendTurn(system: game.rules, user: "")
    }
}

@main
struct AgentApp: App {
    let vm = AppViewModel()

    var body: some Scene {
        WindowGroup {
            NavigationStack {
                ContentView()
                    .environment(vm)
            }
        }
    }
}

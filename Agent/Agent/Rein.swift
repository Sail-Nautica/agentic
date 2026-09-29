import SwiftUI
  
//Personal Phone
private let harness = "https://34.16.51.43"
private let api = "/llmchat"
private let clearApi = "/llmclear"
private let model = "gemini-3.6-flash"
private let appID = Bundle.main.bundleIdentifier


//Class
//private let harness = "https://mada.eecs.umich.edu"
//private let api = "/llmchat"
//private let clearApi = "/llmclear"
//private let model = "gemma4:e4b"
//private let appID = Bundle.main.bundleIdentifier


// a thinking model's reasoning can say the secret answer out loud before the
// game's payoff turn; the backend already persists reasoning independently of
// what's rendered here (handlers.py accumulates it server-side for replay),
// so hiding it from the bubble doesn't affect the model's own memory of it
private let showThinking = false

struct Message: Encodable {
    let role: String
    let content: String?

    init(role: String = "user", content: String = "") {
        self.role = role
        self.content = content
    }
}

struct OpenAIRequest: Encodable {
    let model: String
    //let max_tokens = 8192 // some models require it
    let messages: [Message]
    let stream = true       // always streaming
    let appID: String?

}

struct OpenAIResponse: Decodable {
    let model: String?
    let choices: [Choice]   // guaranteed only one completion choice
    let created: Double?

    struct Choice: Decodable {
        let delta: Delta
        let finish_reason: String?
    }
}

struct Delta: Decodable {
    let content: String?
    let reasoning: String?
    let reasoning_content: String?
}

enum SseEvent { case Error, Message, Unknown }

// a fresh-per-turn state machine that buffers the start of a completion just
// long enough to detect and strip a leading "[SECRET: ...]" marker before any
// of it reaches the visible bubble - see stripSecretMarker
enum SecretMarkerState {
    case buffering(String)
    case resolved
}

struct SseAccumulator {
    let completion: Chat
    let errMsg: Binding<String>
    var secretMarker: SecretMarkerState = .buffering("")
}

// the game rules instruct the model to pin its answer in this marker on the
// very first reply, before any other text; the marker is what /llmchat
// persists and replays back to the model every later turn as its exact prior
// commitment, so it never has to re-derive or drift from its own clues
private let secretPrefix = "[SECRET:"

private let Json = JSONDecoder()

struct Rein {
    private static var isThinking = false

    func llmPrompt(_ messages: [Message], completion: Chat, errMsg: Binding<String>) async {

        //test request url

        guard let harnessApi = URL(string: "\(harness)\(api)") else { 
            errMsg.wrappedValue = "Bad harness URL \(harness)\(api)"
            return
        }

        // prepare request

        let openAIRequest = OpenAIRequest(
            model: model,
            messages: messages,
            appID: appID,
        )

        let request = Result { try prepareRequest(harnessApi, openAIRequest)}
        guard case .success(let request) = request else {
            if case .failure(let error) = request {
                errMsg.wrappedValue = "Prepare request failed \(error)"
            }
            return
        }

        // post request

        let bytes = await Result { try await postPrompt(request)}
        guard case .success(let bytes) = bytes else {
            if case .failure(let error) = bytes {
                errMsg.wrappedValue = "Connect to harness failed \(error)"
            }
            return
        }

        // process response

        var acc = SseAccumulator(completion: completion, errMsg: errMsg)
        do {
            try await processSse(bytes, &acc)
        } catch {
            errMsg.wrappedValue = "SSE parsing failed \(error)"
        }

    }

    // reuses OpenAIRequest so /llmclear introduces no new message format
    func llmClear(errMsg: Binding<String>) async {
        guard let harnessApi = URL(string: "\(harness)\(clearApi)") else {
            errMsg.wrappedValue = "Bad harness URL \(harness)\(clearApi)"
            return
        }

        let openAIRequest = OpenAIRequest(model: model, messages: [], appID: appID)

        let request = Result { try prepareRequest(harnessApi, openAIRequest) }
        guard case .success(let request) = request else {
            if case .failure(let error) = request {
                errMsg.wrappedValue = "Prepare request failed \(error)"
            }
            return
        }

        let response = await Result { try await URLSession.shared.data(for: request) }
        switch response {
        case .success(let (_, response)):
            if let http = response as? HTTPURLResponse, http.statusCode != 200 {
                errMsg.wrappedValue = "\(http.statusCode): \(HTTPURLResponse.localizedString(forStatusCode: http.statusCode))"
            }
        case .failure(let error):
            errMsg.wrappedValue = "Connect to harness failed \(error)"
        }
    }

    private func prepareRequest(_ harnessApi: URL, _ payload: OpenAIRequest) throws -> URLRequest {
        let requestBody = try JSONEncoder().encode(payload)

        var request = URLRequest(url: harnessApi)
        request.timeoutInterval = 1200 // for 20 minutes
        request.httpMethod = "POST"
        request.setValue("application/json; charset=utf-8", forHTTPHeaderField: "Content-Type")
        request.setValue("text/event-stream", forHTTPHeaderField: "Accept")
        request.httpBody = requestBody
        
        return request
    }

    private func postPrompt(_ request: URLRequest) async throws -> URLSession.AsyncBytes {
        let (bytes, response) = try await URLSession.shared.bytes(for: request)

        if let http = response as? HTTPURLResponse, http.statusCode != 200 {
            var msg: String? = nil
            if let data = try? await bytes.reduce(into: Data(), {$0.append($1)}) {
                msg = String(decoding: data, as: UTF8.self)
            }
            throw Exception(
                errorDescription: "\(http.statusCode): \(msg ?? HTTPURLResponse.localizedString(forStatusCode: http.statusCode))"
            )
        }

        return bytes
    }

    private func processSse(_ bytes: URLSession.AsyncBytes, _ acc: inout SseAccumulator) async throws {
        var sseEvent = SseEvent.Message

        // AsyncSequence.lines skips empty lines,
        // must build lines from .characters instead:
        // https://developer.apple.com/forums/thread/725162
        var buffer = Data(capacity: 8192)

        for try await byte in bytes {
            if byte == UInt8(ascii: "\r") { continue } // ignore/skip `\r`
            if byte != UInt8(ascii: "\n") {
                buffer.append(byte)
                continue
            }

            let line = String(decoding: buffer, as: UTF8.self)
            buffer.removeAll(keepingCapacity: true)

            if line.isEmpty {
                // SSE events are delimited by "\n\n"

                if sseEvent == .Error {
                    // show error message in content bubble
                    acc.completion.content.append("\n\n**SSE Error Event**: \(acc.errMsg.wrappedValue)\n\n")
                }

                // new SSE event, default to Message
                sseEvent = .Message
                continue
            }

            //parse sse line

            guard let splitAt = line.firstIndex(of: ":") else { continue }

            let tag = line[..<splitAt]
            var tagline = line[line.index(after: splitAt)...]

            if tagline.first == " " {
                tagline = tagline.dropFirst()
            }

            if tag == "data" { 
                // OpenAI's `/v1/chat/completions` uses "data: [DONE]"
                // to indicate end of stream
                if tagline.isEmpty || tagline == "[DONE]" {continue}

                do {
                    switch sseEvent {
                    case .Message:
                         // OpenAI's `/v1/chat/completions` API requires that
                          // a serialized JSON object follows a `data:` tag.

                        let openAIResponse = try Json.decode(OpenAIResponse.self, from: Data(tagline.utf8))

                        if let delta = openAIResponse.choices.first?.delta {
                            let content = decoratedContent(from: delta, &acc)

                            if !content.isEmpty {
                                acc.completion.content.append(content)

                                if acc.completion.timestamp.isEmpty {
                                    if let model = openAIResponse.model {
                                        acc.completion.role = "assistant (\(model))"
                                    }

                                    let created = openAIResponse.created ?? Date().timeIntervalSince1970
                                    acc.completion.timestamp = Date(timeIntervalSince1970: created).ISO8601Format()
                                }
                            }
                        }

                        if let finishReason = openAIResponse.choices.first?.finish_reason, finishReason == "length" || finishReason == "content_filter" {
                            acc.errMsg.wrappedValue += "LLM STREAM CUT OFF!"
                            sseEvent = .Error
                        }
                        
                    case .Error:
                        if let errline = try? Json.decode(String.self, from: Data(tagline.utf8)){
                            acc.errMsg.wrappedValue += errline
                        } else {
                            acc.errMsg.wrappedValue += String(tagline) 
                        }
                    
                    default:
                        acc.errMsg.wrappedValue += "\n\n**Unknown SSE event**: \(tagline)\n\n"

                    }
                } catch {
                    acc.errMsg.wrappedValue += "\n\n**SSE stream JSON decode**: \(error)\n\(tagline)\n"
                }

            } else if tag == "event" {
                sseEvent = switch tagline {
                    case "error", "Error", "ERROR" : .Error
                    case "message", "Message", "MESSAGE" : .Message
                    default: .Unknown
                }
            }

        }

        


    }

    private func decoratedContent(from delta: Delta, _ acc: inout SseAccumulator) -> String {
        if let content = delta.content.nilIfEmpty {
            let visible = stripSecretMarker(content, &acc.secretMarker)
            guard !visible.isEmpty else { return "" }

            let result = Rein.isThinking ? "\n</think>\n\n" + visible : visible
            Rein.isThinking = false
            return result
        }

        if showThinking {
            if let reason = (delta.reasoning_content.nilIfEmpty ?? delta.reasoning.nilIfEmpty) {
                let result = Rein.isThinking ? reason : "<think>\n" + reason
                Rein.isThinking = false
                return result
            }
        }

        return ""
    }

    // buffers the start of a completion until it can either confirm and strip
    // a "[SECRET: ...]" marker, or confirm there isn't one and flush normally;
    // a model that opens the marker but never closes it is capped at 120
    // buffered characters, after which it's flushed through as ordinary text
    private func stripSecretMarker(_ token: String, _ state: inout SecretMarkerState) -> String {
        guard case .buffering(var buf) = state else { return token }
        buf += token

        let trimmed = buf.drop { $0 == " " || $0 == "\n" || $0 == "\t" }
        guard !trimmed.isEmpty else {
            state = .buffering(buf) // still all whitespace, keep waiting for the first real character
            return ""
        }

        guard trimmed.count >= secretPrefix.count else {
            if secretPrefix.hasPrefix(trimmed) {
                state = .buffering(buf)
                return ""
            }
            state = .resolved
            return buf
        }

        guard trimmed.hasPrefix(secretPrefix) else {
            state = .resolved
            return buf
        }

        if let closeRange = trimmed.range(of: "]") {
            state = .resolved
            return String(trimmed[closeRange.upperBound...])
        }

        guard buf.count < 120 else {
            state = .resolved
            return buf
        }

        state = .buffering(buf)
        return ""
    }

}

import SwiftUI
  
//Personal Phone
private let harness = "https://34.16.51.43"
private let api = "/llmtools"
private let clearApi = "/llmclear"
private let model = "qwen3.5:9b"
private let appID = Bundle.main.bundleIdentifier
private let toolbox = Toolbox()


//Class
//private let harness = "https://mada.eecs.umich.edu"
//private let api = "/llmtools"
//private let clearApi = "/llmclear"
//private let model = "qwen3.5:9b"
//private let appID = Bundle.main.bundleIdentifier


// a thinking model's reasoning can say the secret answer out loud before the
// game's payoff turn; the backend already persists reasoning independently of
// what's rendered here (handlers.py accumulates it server-side for replay),
// so hiding it from the bubble doesn't affect the model's own memory of it

    
private let showThinking = false

struct OpenAIFunction: Codable {
    let name: String?
    let arguments: String?
}

struct OpenAIToolCall: Codable {
    let id: String
    let type: String = "function"
    let function: OpenAIFunction

    // CodingKeys required "type" being immutable with default value
    enum CodingKeys: String, CodingKey {
        case id = "id"
        case type = "type"
        case function = "function"
    }
}

struct Message: Encodable {
    let role: String
    let content: String?
    var tool_calls: [OpenAIToolCall]?
    var tool_call_id: String?

    init(role: String = "user", content: String = "",
         tool_calls: [OpenAIToolCall]? = nil,
         tool_call_id: String? = nil) {
        self.role = role
        self.content = content
        self.tool_calls = tool_calls
        self.tool_call_id = tool_call_id
    }
}

struct OpenAIRequest: Encodable {
    let appID: String?
    let model: String
    let max_tokens = 8192   // don't cut off reasoning stream
    var messages: [Message]
    var stream = true
    var turnID: Int64?
    var tools: [OpenAIToolSchema]?
}

struct OpenAIResponse: Decodable {
    let model: String?
    let choices: [Choice]?   // guaranteed only one completion choice
    let created: Double?

    struct Choice: Decodable {
        let delta: Delta?
        let finish_reason: String?
    }
}

struct ToolCallDelta: Decodable {
    let index: Int
    let id: String?
    let function: OpenAIFunction?
}

struct Delta: Decodable {
    let content: String?
    let reasoning: String?
    let reasoning_content: String?
    let tool_calls: [ToolCallDelta]?
}

enum SseEvent { case Error, Message, ToolCalls, Unknown }

struct ToolCallsData: Decodable {
    let turnID: Int64
    let calls: [OpenAIToolCall]
}

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
    var turnID: Int64? = nil
    var parallelCalls = [OpenAIToolCall]()
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

        guard let harnessApi = URL(string: "\(harness)\(api)") else {
            errMsg.wrappedValue = "Bad harness URL \(harness)\(api)"
            return
        }

        // prepare request
        let openAIRequest = OpenAIRequest(
            appID: appID,
            model: model,
            messages: messages,
        )
        let request = Result { try prepareRequest(harnessApi, openAIRequest) }
        guard case .success(let request) = request else {
            if case .failure(let error) = request {
                errMsg.wrappedValue = "Prepare request failed \(error)"
            }
            return
        }

        // post request
        guard let bytes = try? await postPrompt(request) else {
            errMsg.wrappedValue = "Connect to harness failed"
            return
        }

        // process response
        var acc = SseAccumulator(completion: completion, errMsg: errMsg)
        do {
            try await processSse(bytes, &acc)
        } catch {
            errMsg.wrappedValue = "SSE parsing failed \(error)"
            completion.content.append("\n\n**\(errMsg.wrappedValue)**\n\n")
        }
    }

    func llmTools(_ messages: [Message], completion: Chat, errMsg: Binding<String>) async {
        guard let harnessApi = URL(string: "\(harness)\(api)") else {
            errMsg.wrappedValue = "Bad harness URL \(harness)\(api)"
            return
        }

        // prepare LLM request
        var openAIRequest = OpenAIRequest(
            appID: appID,
            model: model,
            messages: messages,
            tools: toolbox.schemas(),
        )

        var request: Result<URLRequest, any Error>
        var sendNewPrompt = true

        while sendNewPrompt {
            sendNewPrompt = false

            // prepare HTTP request
            request = Result { try prepareRequest(harnessApi, openAIRequest) }
            guard case .success(let request) = request else {
                if case .failure(let error) = request {
                    errMsg.wrappedValue = "Prepare request failed \(error)"
                }
                return
            }

            // post request
            /* Xcode 27
            bytes = await Result { try await postPrompt(request) }
            guard case .success(let bytes) = bytes else {
                if case .failure(let error) = bytes {
                    errMsg.wrappedValue = "Connect to harness failed \(error)"
                }
                return
            }*/
            // Xcode 26
            var bytes: URLSession.AsyncBytes
            do {
                bytes = try await postPrompt(request)
            } catch {
                errMsg.wrappedValue = "Connect to harness failed \(error)"
                return
            }

            // process response
            var acc = SseAccumulator(completion: completion, errMsg: errMsg)
            do {
                try await processSse(bytes, &acc)
            } catch {
                errMsg.wrappedValue = "SSE parsing failed \(error)"
                completion.content.append("\n\n**\(errMsg.wrappedValue)**\n\n")
                return
            }

            if !acc.parallelCalls.isEmpty {

                    guard let turnID = acc.turnID else {
                        errMsg.wrappedValue = "Tool call event missing turnID"
                        completion.content.append("\n\n**\(errMsg.wrappedValue)**\n\n")
                        return // LLM will be expecting the result if continue
                    }

                    // resolve each on-device tool call
                    var toolResults = [Message]()
                    for call in acc.parallelCalls {
                        let result = await toolbox.invoke(function: call.function) ??
                        "Tool '\(call.function.name ?? "unknown")' does not exist. Complete the prompt without the tool."

                        toolResults.append(Message(
                            role: "tool",
                            content: result,
                            tool_call_id: call.id,
                        ))
                    }

                    // POST ONLY the tool results, with turnID echoed, not the tools themselves
                    // (backend will retrieve the full history and tools from DB — sending the
                    // tools again here will create duplicates, confusing the LLM).
                    openAIRequest.messages = toolResults
                    openAIRequest.turnID = turnID
                    openAIRequest.tools = nil

                    sendNewPrompt = true

            }
        }
    }

    // reuses OpenAIRequest so /llmclear introduces no new message format
    func llmClear(errMsg: Binding<String>) async {
        guard let harnessApi = URL(string: "\(harness)\(clearApi)") else {
            errMsg.wrappedValue = "Bad harness URL \(harness)\(clearApi)"
            return
        }

        let openAIRequest = OpenAIRequest(appID: appID, model: model, messages: [])

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

    func addAgent(_ idToken: String?, errMsg: Binding<String>) async -> String? {
        guard let idToken else {
            return nil
        }

        guard let harnessApi = URL(string: "\(harness)/addagent") else {
            errMsg.wrappedValue = "addAgent: Bad URL"
            return nil
        }
        let agentAuth = [
            "clientID": "781310286343-vr6mocjh07pvrcg9rr5pkr2jhdtblh4d.apps.googleusercontent.com",   // replace with your client ID, keep the double quotation marks
            "idToken" : idToken
        ]
        guard let requestBody = try? JSONSerialization.data(withJSONObject: agentAuth) else {
            errMsg.wrappedValue = "addAgent: JSONSerialization error"
            return nil
        }

        var request = URLRequest(url: harnessApi)
        request.httpMethod = "POST"
        request.setValue("application/json; charset=utf-8", forHTTPHeaderField: "Content-Type")
        request.httpBody = requestBody

        do {
            let (data, response) = try await URLSession.shared.data(for: request)

            if let http = response as? HTTPURLResponse, http.statusCode != 200 {
                errMsg.wrappedValue = "addAgent: \(http.statusCode)\n\(harnessApi)\n\(HTTPURLResponse.localizedString(forStatusCode: http.statusCode))"
                return nil
            }

            guard let ticketObj = try? JSONSerialization.jsonObject(with: data) as? [String:Any] else {
                errMsg.wrappedValue = "addAgent: JSON deserialization"
                return nil
            }
            Ticket.shared.ticket = ticketObj["ticket"] as? String
            Ticket.shared.creator = ticketObj["creator"] as? String ?? ""
            Ticket.shared.expiration = Date()+(ticketObj["lifetime"] as! TimeInterval)-1 // ticket must be valid for at least 1 sec.

            return Ticket.shared.ticket

        } catch {
            errMsg.wrappedValue = "addAgent: POSTing failed \(error)"
            return nil
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
            var msg = ""
            for try await line in bytes.lines {
                guard let data = line.data(using: .utf8) else {
                    continue
                }
                msg += String(data: data, encoding: .utf8) ?? ""
            }
            throw Exception(errorDescription: "\(http.statusCode): \(msg.isEmpty ? HTTPURLResponse.localizedString(forStatusCode: http.statusCode) : msg)")
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
            if byte != UInt8(ascii: "\n") { buffer.append(byte); continue }

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

            // parse SSE line
            guard let splitAt = line.firstIndex(of: ":") else { continue }

            // separate out `tag: tagline` from the SSE line
            let tag = line[..<splitAt]
            var tagline = line[line.index(after: splitAt)...]
            // drop the first leading space (per SSE spec)
            if tagline.first == " " { tagline = tagline.dropFirst() }

            // "tag" can only be "data" or "event"
            if tag == "data" {

                // OpenAI's `/v1/chat/completions` uses "data: [DONE]"
                // to indicate end of stream
                if tagline.isEmpty || tagline == "[DONE]" { continue }

                do {
                    switch sseEvent {
                        // multiple data lines can belong to the same event
                        case .Message:

                            // OpenAI's `/v1/chat/completions` API requires that
                            // a serialized JSON object follows a `data:` tag.
                            let openAIResponse = try Json.decode(OpenAIResponse.self, from: Data(tagline.utf8))

                            // extract content from choices[0].delta.content.
                            // OpenAI defaults to generating only one completion
                            // choice when the 'n' parameter is not included in
                            // OpenAIRequest.
                            if let delta = openAIResponse.choices?.first?.delta {
                                let content = stripSecretMarker(decoratedContent(from: delta), &acc.secretMarker)
                                if !content.isEmpty {
                                    acc.completion.content.append(content)
                                    if acc.completion.timestamp.isEmpty {
                                        if let model = openAIResponse.model { acc.completion.role = "assistant (\(model))" }
                                        let created = openAIResponse.created ?? Date().timeIntervalSince1970
                                        acc.completion.timestamp = Date(timeIntervalSince1970: created).ISO8601Format()
                                    }
                                }
                            }
                            if let finishReason = openAIResponse.choices?.first?.finish_reason,
                               finishReason == "length" || finishReason == "content_filter" {
                                acc.errMsg.wrappedValue += "LLM STREAM CUT OFF!"
                                sseEvent = .Error
                            }

                        case .ToolCalls:
                            let event = try Json.decode(ToolCallsData.self, from: Data(tagline.utf8))
                            acc.turnID = event.turnID
                            acc.parallelCalls.append(contentsOf: event.calls)
                        case .Error:
                            // Json.decode removes escape characters
                            if let errline = try? Json.decode(String.self, from: Data(tagline.utf8)) {
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
                    case "error",   "Error",   "ERROR"   : .Error
                    case "message", "Message", "MESSAGE" : .Message
                    case "tool_calls", "Tool_calls", "TOOL_CALLS" : .ToolCalls
                    default: .Unknown
                }
            }

        }
    }

    private func decoratedContent(from delta: Delta) -> String {
        if let content = delta.content.nilIfEmpty {
            let result = Rein.isThinking ? "\n\u{3C}/think\u{3E}\n\n" + content : content
            Rein.isThinking = false
            return result
        }

        if showThinking {
            if let reason = (delta.reasoning_content.nilIfEmpty ?? delta.reasoning.nilIfEmpty) {
                let result = Rein.isThinking ? reason : "\u{3C}think\u{3E}\n" + reason
                Rein.isThinking = true
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

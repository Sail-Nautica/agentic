import Foundation

struct OpenAIToolSchema: Codable {
    let type: String = "function"
    let function: OpenAISchemaFunction

    enum CodingKeys: String, CodingKey {
        case type = "type"
        case function = "function"
    }
}

struct OpenAISchemaFunction: Codable {
    let name: String
    let description: String
    let parameters: OpenAIFunctionParams?
}

struct OpenAIFunctionParams: Codable {
    let type: String
    let properties: [String:OpenAIParamProp]?
    let required: [String]?
}

struct OpenAIParamProp: Codable {
    let type: String
    let description: String
    let enum_: [String]?
}

private let Json = JSONDecoder()

fileprivate func jsonToSchema(_ tool: String) -> OpenAIToolSchema {
    guard let url = Bundle.main.url(forResource: tool, withExtension: "json"),
            let data = try? Data(contentsOf: url) else {
        fatalError("Failed to find \(tool).json in bundle")
    }
    do {
        return try Json.decode(OpenAIToolSchema.self, from: data)
    } catch {
        fatalError("Failed to decode \(tool).json: \(error)")
    }
}

func getLocAuth(_ argv: [String]) async -> String {
    guard let ticket = Ticket.shared.ticket, argv[0] == ticket else {
        return "401 Unauthorized. Call get_auth to obtain a new ticket and retry. Never reuse an old ticket."
    }
    return "latitude: \(LocManagerViewModel.shared.location.lat), longitude: \(LocManagerViewModel.shared.location.lon)"
}

func getAuth(_ argv: [String]) async -> String {
    if let ticket = Ticket.shared.ticket { return "Authorization ticket is: \(ticket)" }

    // suspend the tool call until SigninView is dismissed
    await withUnsafeContinuation { continuation in
        Ticket.shared.vm?.signinCompletion = { continuation.resume() }
        Ticket.shared.vm?.getSignedin = true
    }

    guard let ticket = Ticket.shared.ticket else {
        return "401 Unauthorized. Complete the prompt by informing user that task cannot be completed due to failed authorization."
    }
    return "Authorization ticket is: \(ticket)"
}

typealias ToolFunction = ([String]) async -> String

struct Tool {
    let schema: OpenAIToolSchema
    let function: ToolFunction
}

struct Toolbox {
    let tools: [String: Tool]

    init() {
        self.tools = [
            "get_auth": Tool(schema: jsonToSchema("get_auth"), function: getAuth),
            "get_loc_auth": Tool(schema: jsonToSchema("get_loc_auth"), function: getLocAuth),
        ]
    }

    func schemas() -> [OpenAIToolSchema] {
        return tools.values.map { $0.schema }
    }

    // nil means the tool is not resident on this device
    func invoke(function: OpenAIFunction) async -> String? {
        guard let name = function.name, let tool = tools[name] else { return nil }
        guard let argsJson = function.arguments,
            let argsData = argsJson.data(using: .utf8),
            let args = try? JSONSerialization.jsonObject(with: argsData) as? [String: Any] else {
            return "bad tool arguments JSON"
        }

        let argv: [String] = (tool.schema.function.parameters?.required ?? []).map { label in
            switch args[label] {
            case let value as String:   return value
            case let value?:            return String(describing: value)
            default:                    return ""
            }
        }
        return await tool.function(argv)
    }
}

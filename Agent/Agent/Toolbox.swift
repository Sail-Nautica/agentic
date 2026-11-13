import Foundation
import CoreLocation

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

func getLocAuth(_ argv: [String]) async -> String {     //"Ann Arbor"
    Ticket.shared.ticket == argv[0]
    ? "latitude: \(LocManagerViewModel.shared.location.lat), longitude: \(LocManagerViewModel.shared.location.lon)"
    : "401 Unauthorized. Ask the user if they want to try again. If so, you **MUST** call the get_auth tool again to get a fresh new ticket and retry the operation. DO NOT reuse any ticket in context/history that came before this message."
}

func recenterMap(_ argv: [String]) async -> String {
    // same ticket check and 401 reply as getLocAuth, so the model handles a rejected ticket identically
    guard Ticket.shared.ticket == argv[0] else {
        return "401 Unauthorized. Ask the user if they want to try again. If so, you **MUST** call the get_auth tool again to get a fresh new ticket and retry the operation. DO NOT reuse any ticket in context/history that came before this message."
    }
    // a model that omits or zeroes the arguments sends 0,0, which passes the validity check; nan and inf parse as numbers
    guard let lat = Double(argv[1]), let lon = Double(argv[2]), lat.isFinite, lon.isFinite,
          CLLocationCoordinate2DIsValid(CLLocationCoordinate2D(latitude: lat, longitude: lon)),
          lat != 0 || lon != 0 else {
        return "Invalid coordinates. Latitude and longitude must be plain decimal numbers in range and not both zero. Correct them and call recenter_map again."
    }
    LocManagerViewModel.shared.recenter(lat: lat, lon: lon)
    return "The map is now centered on latitude \(lat), longitude \(lon)."
}

func getAuth(_ argv: [String]) async -> String {
    repeat {
        if let ticket = Ticket.shared.ticket {
            return "Authorization ticket is: \(ticket)"
        }

        if let vm = Ticket.shared.vm {
            await withUnsafeContinuation { getAuthAt in
                vm.signinCompletion = { () -> Void in
                    getAuthAt.resume()
                }
                vm.getSignedin = true
            }
            // here be getAuthAt
        }

        if Ticket.shared.ticket == nil { // failed to sign in, or vm is nil
                                         // or is currently signing in?
            return "401 Unauthorized. Complete the prompt by informing user that task cannot be completed due to failed authorization."
        }
    } while true
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
            "recenter_map": Tool(schema: jsonToSchema("recenter_map"), function: recenterMap),
        ]
    }

    func schemas() -> [OpenAIToolSchema] {
        return tools.values.map { $0.schema }
    }

    func invoke(function: OpenAIFunction) async -> String? {
        guard let name = function.name, let tool = tools[name] else { return nil }
        guard let argsJson = function.arguments,
            let argsData = argsJson.data(using: .utf8),
            let args = try? JSONSerialization.jsonObject(with: argsData) as? [String: Any] else {
            return "bad tool arguments JSON"
        }

        // get args in parameters.required order, they may arrive out of order from the back end
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

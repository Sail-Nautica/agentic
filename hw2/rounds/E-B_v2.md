# Exhibit E-B v2: Technical design for "Mystery City"

This version applies the product owner's answers (Q2, Q3, Q4, Q6) and the orchestrator's decisions (Q1, Q5, Q7 to Q11). The orchestrator decisions are flagged "[to confirm]" and repeated in section 9.

## 0. Summary

- **Back end unchanged [to confirm, Q1].** The game runs through the existing /llmtools, /addagent and /llmclear paths.
- **Two device tools.** `get_auth` (exists) returns the ticket. `recenter_map` (new) takes the ticket plus latitude and longitude. A normal win therefore takes three back-end requests ("legs"): the guess; the ticket result, which gets the recenter call; and the recenter result, which gets the closing text.
- **Fixed, secret city.** The first reply carries a hidden marker with the city name. The harness stores and replays it, and the app strips it from the screen.
- **The app is a small state machine** around Rein's network loop. It keeps only the latest reply and a "what would Retry resend" record. The harness keeps the conversation.
- **A win is "any game tool called this turn".** This includes a denial at `get_auth`.
- **Every back-end call has a 30 s total timer,** including /llmclear.

## 1. Reuse versus change

```mermaid
flowchart LR
  subgraph FE["iPhone app"]
    A["AgentApp / AppViewModel: CHANGE (game state machine)"]
    C["ContentView: REPLACE (map, hints, status row, input, Clear)"]
    R["Rein: CHANGE (Result, 30 s total timer, resume, wipe retry)"]
    T["Toolbox + tools/*.json: CHANGE (get_auth kept, recenter_map added)"]
    K["Ticket: CHANGE (Face ID read per turn, delete-then-add, no launch read)"]
    S["SigninView: REUSE, text removed"]
    L["LocManager: REUSE (permission only)"]
    X["ChatView, game picker, role toggle: REMOVE"]
  end
  subgraph BE["harnessd: NO CHANGE"]
    H["/llmtools: stores turns, replays full history"]
    D["/addagent: Google check, issues ticket"]
    Z["/llmclear"]
    Q["runners: random LLM per request"]
  end
  FE --> BE
```

**Front end, reused as-is:** the SSE byte reader, tool-call event parsing, request builder, `addAgent`, `llmClear`; Google sign-in wrappers; the Keychain item definition (generic password, this-device-only, userPresence); LocManager, used only to trigger the location permission prompt.

**Front end, changed**
- AppViewModel: drops the chat list, drafts, role toggle and `Game` enum; gains the phase, the latest reply, a "game tool called this turn" flag, a pending-Retry record, a per-turn ticket memo, the camera position and an optional pin.
- Rein: `llmTools` returns an explicit success or failure instead of writing to an error string; each request gets the 30 s total timer; it can resume from a stored turn ID plus tool results; it tells the view model when a game tool starts and finishes; a cap limits the legs per user action (section 4); `llmClear` also gets the timer and a real failure result.
- Toolbox: registers `get_auth` and `recenter_map` only.
- Ticket: the launch-time read in `AgentApp.init` is removed; a new "read with Face ID" returns the token or nothing; saving becomes delete-then-add (section 8, item 3); it no longer writes to the tutorial's alert strings.
- SigninView: remove "Refreshing credentials..." and every message that goes to the alert machinery; keep a bare progress indicator during silent refresh.
- Info.plist and build settings: portrait only; reword the location usage text, which currently says "weather" [to confirm, Q10]; keep the Face ID usage text, which produces a one-time system dialog, accepted.

**Back end.** Nothing changes. Tool schemas travel from the client and are stored per app. Unknown tool names are already forwarded to the client. The harness also offers `get_weather_auth` to every client; the rules tell the LLM to ignore it.

**Dead code to surface, not edit:** `get_loc_auth.json`, `get_location.json`, `getLocAuth`, `LocManagerViewModel`, `llmPrompt`, `ChatView.swift`, the `Game` enum, `showThinking`.

## 2. Rules, city choice, secrecy

**The LLM is stateless; the harness is not.** The app sends only new messages. The harness stores every turn (prompt, reply, reasoning, tool calls, tool results) in SQLite keyed by the bundle ID. On every request it rebuilds and resends the entire history to a randomly chosen upstream model. The upstream keeps nothing.

**The city is pinned by a marker in the first reply.** The rules tell the model to begin its first reply with the city in a `[SECRET: city]` marker. The harness stores the raw reply, marker included, and replays it on every later turn; that is how the model "remembers" its city. The app buffers each whole reply, removes any marker anywhere in it, and only then replaces the hints text. Buffering also matches E-A: the old hint stays visible until the new reply is complete.

**The first request** is one system message (the rules) plus one short user message ("Begin"). Some providers in runners.toml reject a conversation that ends with a system message, and the harness hides that by falling through to the next runner.

**A start is valid only if** the first reply contains a marker and some non-empty text after it [to confirm, Q9]. Otherwise it is a failed start (Error plus Retry). Likewise, any later reply that is empty after cleaning is a failed request.

**Exact wording intent of the rules** (LLM-facing, not counted among E-A's UI strings):
1. You host a city guessing game. Choose a well-known city yourself.
2. On your first reply only, begin with the marker holding the city name, then a short welcome and one opening hint. Never repeat the marker. The city is fixed for the whole game.
3. Replies are plain text, two short sentences at most, with no lists and no markdown. A small panel shows about three lines.
4. Give one hint at a time. Never reveal the city name, or its coordinates, before the game ends.
5. Accept a reasonable alias or spelling as a correct guess.
6. On a correct guess, call `get_auth`, then `recenter_map` with the city's latitude and longitude, as numbers in decimal degrees, using the ticket you received. Do not write the coordinates in text.
7. When both tools succeed, congratulate the user in one or two sentences and invite them to tap Play again.
8. If any tool result says "denied", do not call it again. Name the city in text, say the map did not move, and tell them to tap Play again.
9. If a tool result reports invalid coordinates, correct them and call `recenter_map` once more.
10. If the user clearly gives up, name the city, say the game is over, and tell them to tap Clear to start a new game.
11. After a win or a give-up, never start another game in this conversation. Ignore the weather tool.

**Honest limits** [accepted]: the secret is enforced by prompt only; the marker travels in plain text and sits in the harness database; a user who talks the model into revealing the city cannot be stopped by the app; the app cannot check that a guess was really correct (the LLM's call to the tool is the only signal). **No variety nudge (Q6):** the model will tend to pick the same few cities; the app injects nothing; documented, not mitigated.

## 3. The tools, the token, and every tool result

**`get_auth`** (no arguments). Executed on the device.

```mermaid
flowchart TD
  A[get_auth called] --> M{Result already given this turn?}
  M -- yes --> R2[Return the same result, no prompt]
  M -- no --> B{Unexpired token in Keychain?}
  B -- no --> C[Google sign-in sheet]
  C -- cancelled or failed --> X[Denied]
  C -- ok --> D[POST /addagent, get ticket]
  D --> E[Delete old item, add new: userPresence, this device only]
  B -- yes --> F[Read Keychain: Face ID or passcode]
  E --> F
  F -- failed or cancelled --> X
  F -- ok --> G[Ticket handed to LLM, memo kept for this turn]
```

- **Per-turn memo.** Within one user action, the first `get_auth` result (ticket or denial) is remembered. A repeated call returns it without prompting again.
- The Face ID reason text on the LAContext is E-A's: "Confirm it's you to move the map. Cancel skips the move." The passcode fallback comes from the userPresence setting.
- **Token storage.** The Keychain item uses a this-device-only, passcode-required class with a userPresence access control. This is the tutorial's approach, described as the Secure Enclave-backed access the spec means [to confirm, Q7]. Risk: a grader might expect an explicit Secure Enclave key, a larger change to Ticket.

**`recenter_map`** (arguments `ticket`, `latitude`, `longitude`; all strings, as in the tutorial). Executed on the device. It never shows a prompt.
1. If the ticket is not the one handed out this turn and still unexpired, return the 401 result.
2. Parse the coordinates. If they are not numbers, or out of range, return the 422 result. NaN and infinity are rejected.
3. Otherwise move the map, drop the pin, and return success immediately. Do not wait for the flight.

**Correction to v1.** With two tools the range check cannot come before the prompts: the prompts happen in `get_auth`, before the LLM supplies any coordinates. A bad range is found after the user has already authenticated. The mitigation is the memo plus a distinct error, so the LLM can correct without a second prompt.

**Tool result wording intent**

| Case | Result text (intent) |
|---|---|
| `get_auth` success | "Authorization ticket is: (ticket)". Unchanged from the tutorial. |
| `get_auth` denied (sign-in or Face ID cancelled or failed, no passcode, Keychain error) | "Denied. The user did not authorize moving the map, so the map will NOT move. Do not call get_auth or recenter_map again. Tell the user the mystery city's name and that they can tap Play again." |
| `recenter_map` success | "Done. The map is now centred on the city. Congratulate the user and invite them to tap Play again." |
| `recenter_map` bad ticket or expired | "401 Unauthorized. Call get_auth to obtain a new ticket and retry. Never reuse an old ticket." Unchanged from the tutorial. |
| `recenter_map` bad coordinates | "422 Invalid coordinates. Latitude must be between -90 and 90, longitude between -180 and 180. Correct them and call recenter_map again." An error, not a denial. |
| malformed arguments or unknown tool | The tutorial's existing messages. |

## 4. States, win detection, the timer

```mermaid
flowchart TD
  L[launch] --> ST[Starting]
  ST -- reply with marker --> RD[Ready]
  ST -- failure, 30 s, no marker, empty --> ER[Error]
  RD -- Send --> SD[Sending]
  SD -- plain reply --> RD
  SD -- game tool called --> WIN[Sending, win flag set]
  WIN -- final reply --> EN[Ended]
  SD -- failure or 30 s --> ER
  WIN -- failure or 30 s --> ER
  ER -- Retry: start --> ST
  ER -- Retry: guess or later leg --> SD
  RD -- Clear confirmed --> CL[Clearing]
  ER -- Clear confirmed --> CL
  EN -- Clear or Play again --> CL
  CL -- /llmclear ok --> ST
  CL -- /llmclear fails or 30 s --> ER
  ER -- Retry: wipe --> CL
```

**Three legs on a normal win**

```mermaid
sequenceDiagram
  participant U as User
  participant A as App
  participant H as harnessd
  participant M as LLM
  U->>A: guess
  A->>H: leg 1: guess
  H->>M: history + guess
  M-->>A: tool call get_auth
  A->>U: Google sheet (if needed), Face ID
  A->>H: leg 2: ticket result
  M-->>A: tool call recenter_map
  A->>A: fly map, drop pin
  A->>H: leg 3: recenter result
  M-->>A: closing text
  A->>U: Ended: closing text, Play again
```

**Win detection.** The tool functions set a flag on the view model, in the tutorial's `Ticket.shared.vm` style. The first game tool call sets it. When the closing reply arrives, the app goes to Ended if the flag is set, and to Ready otherwise. This also covers a denial at `get_auth` [owner decision, Q2]. Edge: the LLM calls `get_auth`, succeeds, then replies in text without calling `recenter_map`; the app ends the game with the map unmoved. Accepted limit; Clear and Play again recover it.

**Status text while a win runs.** "Correct! Moving the map..." starts at the first game tool call and stays until `recenter_map` has finished or a denial has been produced; only then "Thinking...". This avoids a flicker on legs 2 and 3. The keyboard is dismissed when the win flag is first set.

**The timer (Q4).** 30 s total per back-end request: from sending until the stream has ended, or the wipe has returned. It applies to Starting, each Sending leg, and /llmclear. It excludes Google sign-in, Face ID, and tool execution. It lives in Rein: a request and a 30 s sleep race each other, and the loser is cancelled. The SSE keep-alive pings do not matter because the timer is total rather than idle. The existing 1200 s request timeout stays as a backstop only.

**Tool-loop cap.** At most five requests per user action. Normal is three. A bad ticket or one coordinate correction fits within five. At the cap the loop stops and the state goes to Error. Retry grants a fresh budget [to confirm].

**Error causes.** Transport failure, an SSE error event, a cut-off stream (`finish_reason` length), the timer, a start with no marker, or an empty reply after cleaning.

## 5. Map, fly-to, pin

- A full-bleed SwiftUI `Map` bound to a camera-position value held by the view model. The user's blue dot is shown.
- **Launch.** The initial camera position is "follow the user, with a zoomed-out fallback". The system moves the map once when a fix arrives and stops following if the user pans. If location is denied the map stays on the fallback silently.
- **Win.** Set a city-sized region around the coordinates inside an animation of about 2 s. With Reduce Motion, set it without animation. The pin is a standard marker with an empty title; verify on device that it shows no label. The tool returns without waiting for the flight.
- **Framing above the panel.** First check whether the map frames inside the panel's inset. If not, shift the centre south by the panel's share of the visible span, computed once when the flight starts with the keyboard down. Needs a device check.
- **Clear and Play again** remove the pin and leave the camera where it is.
- Tapping the map dismisses the keyboard.

## 6. History and Retry

**What the app keeps:** the latest reply text, the phase, and a pending record saying what Retry resends. The harness keeps the conversation.

| Failed request | Retry does |
|---|---|
| Start (including no-marker or empty reply) | Silent /llmclear, then the rules again. Both under the timer. Prevents two rules turns, possibly with two different cities, if the first request actually finished on the server unseen. |
| Guess (leg 1) | Resends the same text as a new turn. The harness may already hold the failed prompt, so the LLM may see the guess twice. Accepted. |
| Any later leg (after tool results) | Resends only the stored turn ID plus the tool results already produced. No second Face ID, no second map move. The harness result update is idempotent. |
| Wipe (Clear or Play again) | Repeats /llmclear. On success, continues to Starting. |

**Send in Error [owner decision, Q3, extended; to confirm].** After a failure that follows a tool call, Send is disabled (Retry or Clear only), because a new turn would leave an assistant tool call with no tool result in the stored history and strict providers reject that; every later request would fail until Clear. The same rule is extended to a failed Start and a failed wipe: after a failed start no city is pinned, and after a failed wipe the old conversation is still on the server, so a guess sent then would be judged against the wrong game. Send stays enabled in Error only after a failed plain guess. Remaining risk: a leg-1 failure after the server stored a tool call but before the client saw it damages history until Clear; the window is tiny and accepted.

**Failed final request after the map moved.** Error; the pin stays; Retry resends only that leg.

## 7. Deviations from and amendments to E-A

| # | Where E-A says | This design | Reason |
|---|---|---|---|
| 1 | One tool call; the app handles the token inside it | Two tools, three legs; the LLM carries the ticket from `get_auth` to `recenter_map` | Spec requires the LLM to obtain the token (Q2). |
| 2 | Ended only after the recenter tool was called | Ended after any game tool call this turn, including a denial at `get_auth` | A denial happens before `recenter_map` is ever called, and the game still ends (Q2). |
| 3 | Face ID happens on "Tool requested" before coordinates are checked | Sign-in and Face ID happen inside `get_auth`, before any coordinates exist | Two-tool flow. |
| 4 | Bad coordinates are a denial | Bad coordinates are a 422 error the LLM can correct; only sign-in or Face ID failure is a denial. Range check happens after authentication. | A bad range is not the user's refusal, and it cannot be checked earlier. |
| 5 | "A local wipe cannot fail"; Clearing has no timer | Clearing has the 30 s timer and a failure path: Error, whose Retry repeats the wipe | Clear is a network call (Q4). |
| 6 | One timer for waiting on an LLM reply | Same 30 s, total, on every back-end call incl. /llmclear | Q4. |
| 7 | Send enabled in Error when the field has text | Disabled after a failed tool-call leg (Q3), a failed start, and a failed wipe | History would be damaged or judged against the wrong game. |
| 8 | Retry repeats the last failed request | Retry of a start also silently wipes first | Avoids two rules turns and two cities. |
| 9 | Biometric on every token read | On every read from the Keychain, but one read per user action (memo) | Prevents repeated Face ID prompts if the LLM calls `get_auth` twice. |
| 10 | Status "Correct! Moving the map..." then "Thinking..." for the final fetch | "Correct!" persists across legs 2 to 3 until the map action finishes | Avoids flicker with three legs. |
| 11 | Error for transport failure and timer | Also a start with no marker, an empty reply, or the leg cap | Needed for a pinned city and a bounded loop (Q9). |
| 12 | Overlays: confirmation, location, Google, Face ID | Also the one-time system "Allow Face ID" dialog; the location text is reworded | System behaviour; accepted (Q10). |
| 13 | Error message "Couldn't reach the game." | Also used for a failed wipe. No new strings added. | Keeps E-A's string count. |

## 8. Risks: resolved or accepted

1. **Shared conversation per bundle ID.** The appID is the bundle ID, so all testers on one back end share one conversation. Accepted [to confirm, Q5]. One tester at a time is supported. Another device's Clear wipes your game.
2. **180 s ticket cap.** Set by the back end and unchanged. After 3 minutes the next win re-runs sign-in. Accepted. When Google remembers the user the refresh is silent behind a bare progress indicator; otherwise the Google button shows.
3. **Double Face ID.** Updating an existing userPresence item likely prompts, then the read prompts again. Mitigation chosen [to confirm, Q11]: delete the old item and add a new one, which does not prompt. Must be verified on a device. Departs from CLAUDE.md's upsert preference, which concerns database rows.
4. **Tool-loop cap.** Five requests per user action; Error at the cap; Retry gives a fresh budget.
5. **SSE keep-alive and the timer.** Resolved: the timer is total, so pings are irrelevant.
6. **Thinking-model latency against 30 s.** Accepted limit. The local qwen model is the last-resort fallback and the most likely to exceed 30 s. Mitigations: the rules ask for short replies; each Retry draws a fresh random runner; a timed-out request is cancelled and the server stops generating. The request body's token limit stays as it is.
7. **Per-request model switching.** Different models may answer different turns in one game. Accepted. The rules are written for the weakest model.
8. **No timer on sign-in.** The `/addagent` call has the URLSession default of about 60 s, during which Clear and Send are off. Accepted.
9. **The app cannot verify a win.** The LLM's tool call is the only signal. Accepted.
10. **Orphan tool call after a leg-1 cut-off** (section 6). Accepted; Clear is the escape.
11. **Missing Secure Enclave key.** The grader might require an explicit key. Accepted risk [to confirm, Q7].
12. **First-launch false start** (location prompt over the first request). Accepted, as in E-A.
13. **Backgrounding mid-request** ends in Error. Accepted for a prototype.
14. **Simulator.** Face ID and Keychain behaviour differ. E-A says real device only.

## 9. Questions still open

**Blocking:** none.

**Non-blocking, confirm or amend (defaults shown are what will be implemented):**
1. Orchestrator decisions made on the owner's behalf, please confirm each: Q1 back end unchanged; Q5 no per-install appID, one tester at a time; Q7 tutorial Keychain approach counts as the Secure Enclave-backed access (if a grader expects an explicit key, Ticket.swift changes substantially, so decide soon); Q8 rules tell the LLM "tap Clear" after a give-up and "tap Play again" after a win; Q9 no-marker or empty reply is a failed request; Q10 location text reworded, Face ID dialog accepted; Q11 delete-then-add for the Keychain item.
2. Send disabled after a failed start and a failed wipe, in addition to after a failed tool-call leg (default: yes).
3. "Correct! Moving the map..." stays up until the map action finishes (default: yes).
4. Tool-loop cap of five requests per user action, with Retry granting a fresh budget (default: yes).
5. Should `/addagent` also get a timer? Default: no, because it counts as part of the tool (about 60 s system limit).
6. Should the amendments in section 7 be written back into E-A, or kept only in E-B?

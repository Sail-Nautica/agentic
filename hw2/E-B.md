# Exhibit E-B (final): Technical design for "Mystery City"

This version adds a "Verified facts" section, checked against the code in this repository. It folds in the product owner's answers on the Secure Enclave question and on keeping the deviations only in E-B. It also corrects v2 in four places, listed at the end of section 1.

## 0. Summary

- **Back end unchanged [to confirm, Q1].** Everything runs through /llmtools, /addagent and /llmclear.
- **Two device tools.** `get_auth` (exists) returns the ticket. `recenter_map` (new) takes ticket, latitude and longitude. A normal win is three back-end requests ("legs"): the guess, the ticket result, the recenter result.
- **Win detection.** Any game tool called this turn, including a denial at `get_auth`.
- **Secret city.** A hidden marker in the first reply. The harness stores and replays it. The app strips it from the screen.
- **Timer.** 30 s total per back-end call, including /llmclear. It excludes Google sign-in, Face ID and tool execution.
- **Retry has three behaviors** (section 7).
- **Accepted decision (product owner): the tutorial's Keychain approach is sufficient for the "Secure Enclave" requirement.** That approach is a this-device-only item protected with userPresence, which is Secure Enclave-backed access control. No explicit Secure Enclave key will be added. One-line risk note: a grader who expects an explicit key would find this approach short of it.
- **E-A is frozen.** All differences from it live only in section 8.

## 1. Verified facts

Each claim was checked in the code. Where I could not verify something, it says so.

**a. Resuming a turn with tool results (harnessd/handlers.py, `llmtools`)**
- When a request carries a turn ID above zero, the handler only updates stored results. For each tool message it sets the result of the call whose ID matches. Posting the same results twice sets the same value twice; nothing is inserted and nothing breaks.
- It then rebuilds the history from the database and sends it to the LLM again.
- So the stored result is idempotent, but the generation is not. Each post triggers a new LLM generation: if that generation produces tool calls, they are inserted as new rows; if it produces a final text, the stored completion is overwritten and the stored reasoning text grows.
- The result update matches on call ID alone, not on turn. A provider that reuses short IDs across turns could overwrite another turn's result. Provider behaviour could not be verified, and the table schema is not in the repository, so it is unknown whether the ID is a unique key.
- The history replay (`_retrieveHistory`) puts all of a turn's calls into one assistant message, ordered by turn and then `idx`. Each leg starts `idx` at 0, so the order within a multi-leg turn is not defined by the code. The result is still a valid parallel-call history, but it reads as if `get_auth` and `recenter_map` were called together.
- **Consequence.** Resuming a leg is safe when that leg produces only text (the final leg). It is not safe when the failed attempt had already stored new tool-call rows with no results (see e below).

**b. Tool schemas per app (handlers.py, `_upsertAgentTools`, `llmclear`)**
- Tool schemas are stored per app ID. A request that includes tools replaces the stored row. A request that omits them reads the stored row.
- `llmclear` deletes calls and turns only. It does not delete the tool row.
- The tutorial front end sends tools on every new prompt (Rein.swift, `llmTools`), so a changed tool set takes effect on the first request after a change, replacing (not merging) the old set.
- What the LLM sees is the back end's own tools (today `get_weather_auth`, from toolbox.py `Toolbox`) plus the latest client set.
- If a bundle ID is reused from another build, its old conversation is still there until cleared. The new build's tools apply, but old history can mention old tools.
- **Consequence.** The game must wipe before it starts. See "Corrections to v2" below.

**c. Unknown tool names (handlers.py `llmtools`, toolbox.py `Toolbox.invoke`)**
- Confirmed. A name the back end does not host returns "not resident", and the handler sends a `tool_calls` event with the turn ID and the call list to the client.
- It forwards any such name, whether or not the client advertised it. The client's `Toolbox.invoke` returns a "does not exist" message for names it does not know.

**d. The ticket (handlers.py `addagent`; Ticket.swift; Rein.swift `addAgent`; SigninView.swift)**
- The back-end ticket is a random 64-character hex string created by /addagent after the Google ID token passes verification. It is stored in the tickets table with the user's name and an expiry.
- Lifetime is the shorter of the Google token's remaining life and `TICKET_MAX_LIFETIME`, which is 180 s. The client sets its own expiry to the returned lifetime minus one second.
- The Keychain item is a generic password. The secret value is the ticket text. The expiry is stored in the item's label attribute as a formatted date string, and the user's name in the creator attribute. The access control is userPresence with a passcode-required, this-device-only class.
- Expiry therefore lives outside the protected secret value. By Apple's documented behaviour, reading attributes without the data does not require authentication. The tutorial's `Ticket.open` reads data and attributes together, so it prompts before it can learn that the item has expired. This could not be run on a device. An attribute-only check will be used first, to be verified on a device.
- The Google ID token is not stored by the app. `signInAsync` hands it straight to /addagent. The Google SDK keeps its own signed-in user and refreshes tokens in `restorePreviousSignIn`.
- **A tutorial bug found.** `SigninView`'s task first uses the SDK's current user token if present, which can be stale after an hour. The back end then answers 401 and the sheet closes, so `get_auth` would deny a user who could have been refreshed silently. The fix is to always call restore (which refreshes).
- **What "reuse within lifetime without revalidation" means here.** While the stored ticket is unexpired, a later win reads it from the Keychain (Face ID) and does not re-run Google sign-in or call /addagent. This is satisfied.
- **Because of the 180 s cap**, any win more than 3 minutes after the last sign-in needs a new ticket. This is an accepted limit: the cap is a back-end constant we may not rely on changing. The re-sign-in is silent when Google remembers the user (no tap needed, only a brief sheet with a progress indicator), and interactive the first time. Reuse is most likely to be exercised by two quick games in a row.

**e. Timed-out or cancelled request after the server stored a tool call**
- The handler inserts the call rows right after the LLM stream ends, then sends the `tool_calls` event. If the client has already disconnected and the generator is cancelled before the insert, nothing is stored.
- If the insert happened but the client never saw the event, the history contains an assistant tool call with no result. `_retrieveHistory` only emits tool messages for calls that have a result. Strict providers reject such a history; which runners do could not be verified. The local runner, as last resort, may accept it. If all fail, /llmtools answers with an SSE error inside a 200 response.
- A plain text reply cannot be damaged this way. The completion is saved only after the stream ends normally.
- **How likely, with a 30 s client timer.** The client gives up exactly when the model is slow, and slow runs are the ones that finish near 30 s. Damage happens when the server finishes in the short window around the client's cancel. Its size is a guess, not a measurement. It applies only to the two tool-producing legs of a win turn, once per game, but the consequence lasts until Clear. A low-probability, high-cost limit, not a negligible one.
- Not verified: that sse_starlette cancels the generator at disconnect (library default behaviour), and its keep-alive ping interval. The total timer makes pings irrelevant.

**Corrections to v2**
1. v2 called result resumption idempotent without qualification. Section 1a narrows it.
2. v2 relied on an empty history at launch. A relaunch (or a reused bundle ID) leaves the old conversation on the server, so the new rules would land on top of an old game and an old marker. Starting now always wipes first.
3. v2 reused the SigninView stale-token path. Section 1d fixes it.
4. v2's recenter check wording was garbled. See section 4.

## 2. Mapping to tutorial files and types

No new files, except one tool schema file beside the existing ones.

| File | Types / functions | Change |
|---|---|---|
| AgentApp.swift | `AppViewModel` | Extended: phase, latest reply, win flag, retry record, ticket memo, camera position, pin. `sendTurn` and `resetGame` keep their names and roles. The `Game` enum and picker are replaced by one rules string. |
| AgentApp.swift | `AgentApp.init` | Remove the launch-time `Ticket.open` call. Keep `LocManager.startUpdates`. |
| Rein.swift | `Rein.llmTools` | **Signature change, a tutorial-pattern change.** Today it returns nothing and reports errors by writing to a bound string. It now takes an optional resume (turn ID plus results) and returns an explicit outcome (reply text, or failure with what Retry needs). Reason: the state machine must tell a failed start from a failed guess from a failed tool leg, and the tutorial's string cannot carry that. |
| Rein.swift | `Rein.llmClear` | Returns an outcome and gets the timer. |
| Rein.swift | constants | Add the 30 s limit next to `harness`, `api`, `clearApi`. |
| Rein.swift | `processSse`, `stripSecretMarker`, `SseAccumulator` | Reused unchanged. The accumulator's `Chat` is scratch; its text is discarded on failure. |
| ChatView.swift | `Chat` | Keep the class as the scratch accumulator. Remove the two views (dead). |
| Toolbox.swift | `getAuth` | Face ID read plus per-action memo (section 4). |
| Toolbox.swift | `recenterMap` (new function), `Toolbox.init` | New function with the existing function signature, registered next to `get_auth`. `getLocAuth` is unregistered and left as dead code. |
| tools/ | `recenter_map.json` (new) | Beside `get_auth.json`, loaded by `jsonToSchema`. |
| Ticket.swift | `Ticket.open`, `save`, `delete` | `open` becomes a Face ID read that returns the ticket; an attribute-only expiry check first; `save` becomes delete-then-add; no alert strings. |
| SigninView.swift | `SigninView` | Always restore (not the stale user token); remove the text; keep the sheet, `getSignedin` and `signinCompletion`. |
| ContentView.swift | `ContentView`, `SubmitButton`, `ClearButton` | Map, hints, status row and input row. `SubmitButton` and `ClearButton` keep their names for Send and Clear. `RoleToggleButton` and the alert are removed. A confirmation dialog replaces the old direct Clear. |
| LocManager.swift | `LocManager` | Unchanged; permission only. `LocManagerViewModel` becomes dead code. |
| Info.plist / build settings | | Portrait only; reword the location text. |
| harnessd | | Nothing. |

## 3. Rules, city choice, secrecy

**The LLM is stateless; the harness is not** (section 1a, 1b). The app sends new messages only; the harness stores the history per app ID and replays it all to a randomly chosen upstream model each time.

**Pinning the city.** The first reply starts with a `[SECRET: city]` marker, which the harness stores and replays. The app buffers each whole reply, removes any marker anywhere in it, and then replaces the hints text.

**First request.** One system message (the rules) plus one short user message ("Begin"), because some providers reject a conversation that ends on a system message. Starting always wipes first (section 7).

**Marker-compliance policy [chosen: manual Retry only].** A first reply with no marker, or with nothing after it, is a failed start: Error plus Retry. Chosen over one silent automatic retry because it needs no counter and no hidden second attempt. A silent retry would also stretch Starting to up to four back-end calls (up to 120 s). An empty reply at any later point is a failed request.

**Exact wording intent of the rules** (LLM-facing, not part of E-A's UI strings):
1. You host a city guessing game. Choose a well-known city yourself.
2. On your first reply only, begin with the marker holding the city name, then a short welcome and one opening hint. Never repeat the marker. The city is fixed for the whole game.
3. Reply in plain text, two short sentences at most, no lists, no markdown.
4. Give one hint at a time. Never reveal the city name or its coordinates before the game ends.
5. Accept a reasonable alias or spelling as a correct guess.
6. On a correct guess, call `get_auth`, then `recenter_map` with the city's latitude and longitude as decimal numbers and the ticket you received. Do not write the coordinates in text.
7. When both succeed, congratulate in one or two sentences and tell the user to tap Play again.
8. If any tool result says "denied", do not call any tool again. Name the city, say the map did not move, and tell them to tap Play again.
9. If a tool result reports invalid coordinates, correct them and call `recenter_map` once more.
10. If the user clearly gives up, name the city, say the game is over, and tell them to tap Clear.
11. After a win or give-up never start another game in this conversation. Ignore the weather tool.

**Honest limits [accepted]**
- The secret is enforced by prompt only.
- The marker and the ticket both sit in plain text in the harness database: the marker in the stored first reply, and the ticket in the tickets table and, as the `get_auth` result, in the calls table. The ticket is also sent to the upstream LLM provider as part of the replayed history. The ticket lives at most 180 s; the marker lives until Clear.
- A user who talks the model into revealing the city cannot be stopped by the app.
- The app cannot verify that a guess was correct. The LLM's tool call is the only signal.
- No variety nudge (Q6): the model will tend to pick the same few cities. Documented, not mitigated.

## 4. Tools, token, and every tool result

```mermaid
flowchart TD
  A[get_auth called] --> M{Outcome already given in this user action?}
  M -- yes --> R2[Return the same outcome, no prompt]
  M -- no --> B{Keychain item present, attributes say unexpired?}
  B -- no --> C[Google sheet: silent refresh, else button]
  C -- cancelled or failed --> X[Denied]
  C -- ok --> D[POST /addagent, get ticket]
  D --> E[Delete old item, add new one]
  B -- yes --> F[Read the secret: Face ID or passcode]
  E --> F
  F -- failed or cancelled --> X
  F -- ok --> G[Ticket to the LLM, remembered for this action]
```

**The per-action memo [kept, narrowed].** It holds the first `get_auth` outcome (the ticket or the denial) for the current user action, and it is cleared when a new user action starts. It costs one optional field and a few lines in AppViewModel. A Retry after a tool call belongs to the same user action, so the memo survives it (a new user action starts only on a new Send, Play again or Clear). Without this, a resumed `recenter_map` would fail the ticket check and force a second Face ID. The alternative is a second Face ID prompt each time a confused model calls `get_auth` again; after a denial that would re-prompt a user who just cancelled, which contradicts "Cancel skips the move". It is therefore cheaper than the prompt. Accepted behavior: one Keychain read (one Face ID) per user action.

**`recenter_map`** (arguments `ticket`, `latitude`, `longitude`, all strings as in the tutorial). It never prompts.
1. It returns the 401 result if the ticket argument is not the ticket that `get_auth` handed out in this user action, or if that ticket has expired.
2. It returns the 422 result if either coordinate is not a number or is out of range. NaN and infinity count as invalid.
3. Otherwise it moves the map, drops the pin, and returns success at once without waiting for the flight.

Because the prompts happen inside `get_auth`, before the LLM supplies coordinates, a bad range can only be found after the user has authenticated. It is reported as an error, not a denial.

**Tool results (wording intent)**

| Case | Text |
|---|---|
| `get_auth` success | "Authorization ticket is: (ticket)". Unchanged from the tutorial. If the model calls `get_auth` again in the same action, the result adds: "This is the same ticket as before; copy it exactly into recenter_map." |
| `get_auth` denied (sign-in or Face ID failed or cancelled, no passcode, Keychain error) | "Denied. The user did not authorize moving the map, so the map will NOT move. Do not call any tool again. Tell the user the mystery city's name and that they can tap Play again." |
| `recenter_map` success | "Done. The map is now centred on the city. Congratulate the user and tell them to tap Play again." |
| `recenter_map` 401 | "401 Unauthorized. The ticket must be exactly the one get_auth returned; copy it character for character. If it has expired, call get_auth again." Adapted from the tutorial wording so a mangled copy does not loop into a pointless new sign-in. |
| `recenter_map` 422 | "422 Invalid coordinates. Latitude must be between -90 and 90, longitude between -180 and 180. Correct them and call recenter_map again." |
| malformed arguments or unknown tool | The tutorial's existing messages. |

## 5. States, win detection, timer

```mermaid
flowchart TD
  L[launch] --> ST["Starting: wipe, then rules"]
  ST -- reply with marker --> RD[Ready]
  ST -- failure, 30 s, no marker, empty --> ER[Error]
  RD -- Send --> SD[Sending]
  SD -- plain reply --> RD
  SD -- game tool called --> WIN[Sending, win flag set]
  WIN -- final reply --> EN[Ended]
  SD -- failure or 30 s --> ER
  WIN -- failure or 30 s --> ER
  ER -- Retry after start or wipe --> ST
  ER -- Retry after guess --> SD
  ER -- Retry after tool call --> WIN
  RD -- Clear confirmed --> CL[Clearing]
  ER -- Clear confirmed --> CL
  EN -- Clear or Play again --> CL
  CL -- wipe ok --> ST
  CL -- wipe fails or 30 s --> ER
```

```mermaid
sequenceDiagram
  participant U as User
  participant A as App
  participant H as harnessd
  participant M as LLM
  U->>A: guess
  A->>H: leg 1: guess
  M-->>A: tool call get_auth
  A->>U: Google (if needed), Face ID
  A->>H: leg 2: ticket result
  M-->>A: tool call recenter_map
  A->>A: fly map, drop pin
  A->>H: leg 3: recenter result
  M-->>A: closing text
  A->>U: Ended: closing text, Play again
```

- **Win detection.** The tool functions set a flag on the view model (the tutorial's `Ticket.shared.vm` pattern). When the closing reply arrives, a set flag means Ended and a clear flag means Ready. Edge: if the LLM gets a ticket and then replies in text without calling `recenter_map`, the app ends the game with the map unmoved. Accepted; Play again or Clear recovers.
- **Status text.** "Correct! Moving the map..." runs from the first game tool call until `recenter_map` finishes or a denial is produced (it spans legs 1 to 2, not leg 3). Then "Thinking..." while the closing text of leg 3 is fetched. The keyboard dismisses when the flag is first set.
- **Timer (Q4).** 30 s total per back-end call. The call and a 30 s sleep race, and the loser is cancelled. It lives in Rein. The old 1200 s request timeout stays as a backstop only. Starting is two calls (wipe, rules), so its worst case is 60 s.
- **Leg cap.** At most five requests per user action. Normal is three. At the cap the loop stops and the state goes to Error. Retry grants a fresh budget.
- **Error causes.** Transport failure, an SSE error event, a cut-off stream, the timer, a start with no marker, an empty reply, or the leg cap.

## 6. Map, fly-to, pin

- A full-bleed SwiftUI `Map` bound to a camera position held by the view model. The user's blue dot is shown.
- **Launch.** The initial camera position follows the user, with a zoomed-out fallback. The system moves the map once when a fix arrives and stops following if the user pans. With location denied it stays on the fallback silently.
- **Win.** Set a city-sized region around the coordinates inside a 2 s animation, or without animation when Reduce Motion is on. The pin is the standard marker with an empty title. Verify on a device that no label appears.
- **Framing above the panel.** Test whether the map frames inside the panel's inset. If not, shift the centre south by the panel's share of the visible span, computed once at flight start with the keyboard down.
- **Clear and Play again** remove the pin and leave the camera where it is. Tapping the map dismisses the keyboard.

## 7. History and Retry

**What the app keeps:** the latest reply text, the phase, the win flag, the memo, and a retry record. The harness keeps the conversation.

**Retry is three behaviors**

| Retry after | Does | Why |
|---|---|---|
| A failed start, or a failed wipe | Starting again: wipe, then the rules | A failed start may have stored a reply and a marker the user never saw. A fresh wipe prevents two rules turns and two cities. A failed wipe has the same cure. |
| A failed plain guess | Resends the same text as a new turn | There is no turn ID to resume (no tool call has happened), so a new turn is the only option. The harness may already hold the failed prompt, so the LLM may see the guess twice. Accepted. |
| A failure after a tool call | Resumes from the stored turn ID, sending only the latest leg's tool results. No second Face ID, no second map move. | Posting the guess again would create a new turn while the old turn holds a tool call that has no result, which would damage the history. Section 1a shows resuming is safe when the failed leg was the final text leg. |

- If the failed attempt was a tool-producing leg that had already stored rows, the resume cannot succeed. That is the orphan limit (section 9). Clear is the escape.
- The failed final request after the map moved is E-A's own case. Error, the pin stays, and Retry resumes the final leg.

**Send in Error.** After a failed start, a failed wipe, or a failure after a tool call, Send is disabled. It stays enabled only after a failed plain guess. No new text explains the disabled Send. The status row's message and Retry button are the only affordance, and the field stays editable. This may confuse a tester, which is a usability-test risk to watch.

## 8. Deviations from and amendments to E-A

| # | E-A says | This design | Reason |
|---|---|---|---|
| 1 | One tool call; the app handles the token inside it | Two tools, three legs; the LLM carries the ticket | Spec requires the LLM to obtain the token (Q2). |
| 2 | Ended only after the recenter tool was called | Ended after any game tool call, including a denial at `get_auth` | A denial happens before `recenter_map`, and the game still ends. |
| 3 | Face ID happens after "Tool requested", coordinates checked after | Sign-in and Face ID happen inside `get_auth`, before coordinates exist | Follows from two tools. |
| 4 | Bad coordinates are a denial | A 422 error the LLM can correct; only a failed sign-in or Face ID is a denial | A bad range is not the user's refusal. |
| 5 | A local wipe cannot fail; Clearing has no timer | Clearing has the 30 s timer and an Error path | The wipe is a network call. |
| 6 | One 30 s timer for waiting on an LLM reply | The same 30 s, total, on every back-end call including the wipe | Q4. Starting is two calls, worst case 60 s. |
| 7 | Send enabled in Error with text | Disabled after a failed start, a failed wipe, or a failure after a tool call; no explanatory text | The history would be damaged or judged against the wrong game (Q3, extended). |
| 8 | Launch sends the rules to an empty history | Launch and every Retry of a start wipe first (invisible to the user) | A relaunch or reused bundle ID leaves an old game on the server. |
| 9 | Retry repeats the last failed request | Same three behaviors as section 7: the start variants wipe first | See section 7. |
| 10 | Biometric on every token read | One Keychain read (one Face ID) per user action | Avoids repeat prompts when the LLM calls `get_auth` again. |
| 11 | "Correct! ..." then "Thinking..." for the final fetch | "Correct!" persists across the get_auth and recenter_map legs until the map action finishes, then "Thinking..." for the closing text | Avoids flicker between the two tool legs. |
| 12 | Error for transport failure and the timer | Also a start with no marker, an empty reply, and the leg cap | Needed for a pinned city and a bounded loop (Q9). |
| 13 | Overlays: confirmation, location, Google, Face ID | Also the one-time system "Allow Face ID" dialog; the location text is reworded | System behaviour (Q10). |
| 14 | Error message "Couldn't reach the game." | The same message is reused for a failed wipe | It is true for a wipe that did not reach the server, and it keeps E-A's string count. No new string. It still counts as a deviation because Error from Clearing is new. |

## 9. Risks: resolved or accepted

| Risk | Decision |
|---|---|
| Shared conversation per bundle ID | **Accepted [to confirm, Q5].** One tester at a time is supported. Another device's Clear or launch wipes your game. |
| 180 s ticket cap | **Accepted** (section 1d). The cap is a back-end constant we may not rely on changing. After 3 minutes a new ticket is needed; the sign-in is silent when Google remembers the user. |
| Double Face ID | **Mitigation chosen [to confirm, Q11].** Delete-then-add, plus an attribute-only expiry check, avoids a prompt on save and on checking expiry. Both must be verified on a device. |
| Tool-loop cap | Five requests per action; Error at the cap; Retry gives a fresh budget. |
| SSE keep-alive and the total timer | Resolved. The timer is total, so pings are irrelevant. |
| Thinking-model latency against 30 s | **Accepted.** The local qwen model is the last-resort fallback and the most likely to exceed 30 s. Short replies are requested in the rules; each Retry draws a fresh random runner. |
| Orphan tool call after a timeout | **Accepted.** See section 1e. The 30 s timer converts a slow-but-successful tool-producing leg into a client-abandoned one, which is exactly how an orphan arises. The size of the window is a guess, not a measurement. It is not detectable by the client, and the back end cannot be changed. Clear is the escape. |
| Model variability per request | Accepted. The rules are written for the weakest model. |
| No timer on sign-in | Accepted. `/addagent` uses the URLSession default of about 60 s while Clear and Send are off. |
| Win not verifiable | Accepted. |
| Missing explicit Secure Enclave key | **Accepted by the product owner.** One-line risk: a grader may expect an explicit key. |
| First-launch false start, backgrounding mid-request | Accepted, as in E-A or as prototype limits. |
| Duplicate call IDs across turns | Not verifiable here (schema and provider behaviour unknown). Accepted. |
| Replayed history reads as parallel calls | Because each leg restarts the call order at zero, the replay reads as if `get_auth` and `recenter_map` were called together, and `recenter_map` carries a ticket from a "parallel" call. A strict provider or a weak model may be confused. Quality risk, not a crash. Accepted. |
| A spurious tool call | A model that calls `get_auth` on a wrong guess ends the game early (win = any game tool). The app cannot tell. Accepted. |
| Retry of a plain guess shares the orphan limit | The client cannot know whether a failed guess leg stored a tool-call row on the server before the client gave up, so resending a guess can sit on top of an orphan. Same limit as the orphan row above; Clear is the escape. |
| Clear keeps the Keychain ticket | Clear and Play again wipe the harness conversation only; the stored ticket stays until it expires, as E-A requires. |

## 10. Questions still needing the product owner

**Blocking:** none. Implementation can start.

**Non-blocking (defaults shown are what will be implemented):**
1. Confirm the orchestrator decisions: Q1 back end unchanged; Q5 no per-install app ID; Q8 rules say "tap Clear" after a give-up and "tap Play again" after a win; Q9 a no-marker or empty reply is a failed request, with manual Retry only; Q10 location text reworded and the Face ID system dialog accepted; Q11 delete-then-add for the Keychain item.
2. Launch (and every start) now wipes the harness history. A relaunch therefore loses an unfinished game, and it also deletes any other conversation under the same bundle ID. Default: yes.
3. Is a 60 s worst case for Starting (wipe plus rules, each with its own 30 s timer) acceptable, or should one 30 s budget cover both? Default: separate timers.
4. Send disabled with no explanatory text in Error (section 7). Default: yes; watch it in the usability test.
5. Leg cap of five, with Retry granting a fresh budget. Default: yes.
6. Should `/addagent` get its own timer? Default: no.

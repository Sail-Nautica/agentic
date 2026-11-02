# Exhibit E-C v4: Project 2 Implementation Plan (full plan, no code)

Read-only session. I changed no files and ran nothing that changes state. I read no third-party library source. Claims I cannot support from our call sites, public headers or docs are marked UNVERIFIED. Mermaid diagrams are the only code-like blocks.

## 0. Rules this plan follows

**Inputs given to the coding agent**
- The course AGENTS.md. The repo contains only CLAUDE.md; this plan assumes the course AGENTS.md is supplied separately.
- `db_schema.sql`.
- `staff_feedback.md`, `design_specs.md` and `ui_requirements.md`.
- This plan.

**Sources**
- Staff feedback overrides the HW2 design doc wherever they conflict.
- Reasoning uses only:
  - our own call sites,
  - public header documentation, and
  - the data we receive, such as a token's own contents.

**Owner decisions (fixed)**
1. Keep the tutorial extras: game picker, 20 Questions, role toggle, full transcript. The only addition is the map.
2. Clear starts a new game immediately: wipe, then re-send the rules.
3. The legacy sweep applies to new and touched lines only, as defined in section 7. Baseline offenders are reported, not fixed.
4. First frame is a plain progress indicator. Then the map appears, already centered on the user, at the first location fix only. There is no cached last-known location.
5. The transcript is a user-opened, in-place swap for the map area. The hint area is the only always-visible text.
6. **Biometric timing is the tutorial behavior:**
   - Face ID happens when the Keychain item is read at launch, and when a ticket is saved.
   - A valid in-memory ticket is reused with no new prompt.
7. **After a win or a give-up, the LLM tells the user to tap Clear for a new game.**
   - A secret marker is written only at the start of a game.
   - There is no per-round marker, no "play another round in chat", and no play-again tests.

**Defaults (please confirm)**
- D1. The first message follows the tutorial: rules sent as the system message with no user message. Only if a runner fails on it do we add a short user message.
- D2. The system-drawn blue location dot is allowed. Zoom is city level.
- D3. The ticket lifetime comes from an environment variable read once at server startup, default 180 seconds.
- D4. The existing alert is kept for errors.
- D5. The tutorial tools stay registered: `get_loc_auth` on the phone, `get_weather_auth` on the server.
- D6. Whitespace-only text is not "something to send". With the role toggle kept, Send looks only at the currently shown draft.
- D7. No project-settings changes except the location permission text.
- D8. Tests run on one working runner plus the simulator. A real device only if available.

## 1. Departures from the HW2 design document

| # | HW2 said | This plan | Why |
|---|---|---|---|
| 1 | Decision F: full-bleed map, compact bottom panel, floating Clear | Tutorial layout: picker on top, map area, hint, one input row with Clear next to Send | Owner kept the tutorial layout |
| 2 | Rules plus a short "Begin" message | System-only first message (D1) | Follow the tutorial unless a runner fails |
| 3 | Pin, status row, Play Again button, Ended state, Decision C (game over detected from tool calls) | None of them | Staff feedback |
| 4 | 30 second timers and three kinds of Retry (Decision E) | None | Staff feedback |
| 5 | State machine: Starting, Ready, Sending, Error, Ended, Clearing | One busy flag (`isBusy`) in `AppViewModel`, as in the tutorial. Nothing models "ended". | Staff ban game-over detection and the status row |
| 6 | A failure shows one message with one Retry button | The tutorial's alert shows the error. There is no Retry. | Staff feedback |
| 7 | After a win the LLM invites the user to play again, and a Play again button appears. The requirements document also says the LLM "invites the user to play again". | After a win, a give-up or a denial, the LLM tells the user to tap Clear. No button is added. | Owner decision 7. Note this changes the requirement document's wording; flagged. |
| 8 | Ticket "saved behind Face ID, then read back with Face ID on each win" | Face ID at launch (Keychain read) and at save only. A valid in-memory ticket is reused with no new prompt. | Owner decision 6. This is how the tutorial code works. HW2 overstated it. |
| 9 | Clear asks for confirmation | No confirmation (the baseline has none) | The only addition is the map (Q2) |
| 10 | Server unchanged | Server changes: `llmclear` and the lifetime knob | Staff feedback |
| 11 | Picker, 20 Questions, role toggle, transcript were not part of the HW2 screen | All kept; the transcript sits behind a toolbar swap | Owner decision 1 |
| 12 | Marker written in the first reply | Unchanged: marker only at the start of a game | Same design, now with no later markers |

## 2. Schema facts (Step 0 is done: db_schema.sql is read)

- **turns:** `turnID` is the primary key. `appID` and `prompt` are required. `reasoning` and `completion` are optional. A `completed` column exists that the code never uses.
  - There is an index on app and turn.
  - A trigger stamps a completion time after the completion is first set. It fires on updates, not deletes.
- **calls:** `id` alone is the primary key. It is not scoped to an app or a turn.
  - There is an ordering index on turn and call position, and a trigger that stamps the result time.
  - A foreign key points at the turns table with no cascade.
  - The server switches foreign keys on at startup (`main.py`).
- **tools:** `appID` is the primary key, with the schema blob and a timestamp.
- **tickets:** its own table, independent of everything above.
- Views and a statistics table exist and are irrelevant to Clear.

**What this implies**
1. **Delete order is forced.** Calls go before turns. The existing two deletes are already in that order.
2. **The tools row has no dependants.** Deleting it is safe, and the next send re-upserts it.
3. **Do not touch tickets.**
4. **Risk: duplicate call ids.**
   - `calls.id` is globally unique, so a provider that reuses a call id would make an insert fail and produce an error event.
   - A win involves two tool rounds in one turn.
   - We cannot change the schema. This is tested (T4) and reported.
5. **"Feed the LLM the current schema"** is read as: give the coding agent this dump as the authoritative table definition. This is a guess to confirm (Q3).

## 3. Architecture (changes only)

```mermaid
flowchart LR
  subgraph Phone["iPhone app"]
    SCREEN["ContentView: picker, map or transcript, hint, input row"]
    VM["AppViewModel: sendTurn, resetGame, conversation"]
    LOC["LocManagerViewModel: camera + positioned flag"]
    REIN["Rein: llmTools, llmClear, addAgent"]
    TB["Toolbox: get_auth, get_loc_auth, recenter_map"]
    TK["Ticket: Keychain + biometric"]
    SI["SigninView"]
  end
  subgraph Server["harnessd"]
    CLR["llmclear: calls, turns, tools row"]
    LT["llmtools (unchanged)"]
    AA["addagent: lifetime knob"]
  end
  SCREEN --> VM --> REIN
  REIN -- "llmTools" --> LT --> LLM["LLM runner"]
  REIN -- "llmClear" --> CLR
  LT -- "tool_calls event" --> REIN --> TB
  TB --> TK --> SI --> AA
  TB -- "sets camera" --> LOC --> SCREEN
```

The view model reaches the clear handler only through `Rein.llmClear`.

## 4. Ordered steps

**Step 0 (done).** The live schema dump is read. Facts are in section 2. The coding agent receives db_schema.sql.
- **Satisfies:** staff backend item "feed the LLM the current database schema that supports tool calls".

### Back end

**B1. Clear removes everything for the app ID** (`handlers.llmclear`)
- Three plain deletes, in this order:
  1. the app's calls (found through its turns),
  2. the app's turns,
  3. the app's row in the tools table.
- No single transaction. The existing handlers never use explicit transactions (the connection is in autocommit).
- A partial failure is harmless:
  - If calls are deleted and turns remain, the app is just missing tool results.
  - If the tools row stays, the next fresh send overwrites it.
- Reuse the existing error and log helpers. Do not touch tickets. No new endpoint or schema change.
- **Reading of the professor's cut-off sentence.** "Clear deletes calls and turns but not stored tool schemas" is read as "Clear must also delete the tools row". This is a guess to confirm (Q3).
- **Done when:**
  - after a game that included tool calls, read-only counts of this app's rows in turns, calls and tools are all zero, while another app's rows and all tickets are unchanged;
  - the sequence Clear, then a new send, works (T9).
- **Satisfies:** "adapt llmclear() to remove data cleanly"; the requirement that Clear removes history and prompts (system and user prompts live in the turns' prompt blob).

**B2. Tunable ticket lifetime** (`handlers.TICKET_MAX_LIFETIME`)
- Read once from an environment variable at startup, default 180 seconds, following the existing `RUNNERS_CONFIG` and `AGENTIC_ROOT` pattern.
- The existing rule stays: the lifetime is the smaller of this value and the Google token's remaining life.
- **Done when:** a restart with a 20 second setting makes the `addagent` response report about 20, and an unset variable reports 180.
- **Satisfies:** "ticket lifetime is tunable".

**B3. Nothing else changes on the back end**
- `recenter_map` is phone-resident. Its schema rides in the existing tools field and is stored by the existing upsert.
- `toolbox.py`, routes and `/llmtools` are untouched.
- **Done when:** the harnessd diff touches only `handlers.py`, and a manual request offering the new schema gets a `tool_calls` event for it.
- **Satisfies:** "no change to API, data formats or schema; no new endpoints".

### Front end

**F1. Stale-token evidence FIRST, then a conditional fix** (file: `SigninView.swift` only)
- **F1a, evidence, before any sign-in code changes.**
  - Start this at the very beginning, because it needs more than an hour of wall-clock time.
  - **A person must do the interactive Google sign-in and then keep the app alive for over an hour.** The coding agent cannot do this itself.
  - Read the public header documentation for the Google user's refresh call and for the current-user and restore calls. Quote it.
  - Add temporary logging in `SigninView`, at the point where the ID token string is passed on to the server. It decodes the token's `exp` claim, which is a value we receive.
  - After the ticket expires, trigger a win so `get_auth` opens the sign-in task. Record the artifact set below.
  - Remove the logging afterwards.
- **F1b, fix, only if F1a shows an expired token reaching `/addagent`.**
  - Delete the branch that prefers the current user's raw token. Always use the existing silent-restore helper. No new callback wrapper.
  - Whether silent restore itself refreshes an expired token is UNVERIFIED from public docs. Repeat the same run after the fix.
  - Only if that run still shows a stale token, call the documented refresh-if-needed, and justify one wrapper in the same style as the existing helpers.
- If F1a does not reproduce, report "not reproduced" with the logged values and change nothing.
- **Artifact captured for the professor, exactly:**
  1. the logged `exp` values with the wall-clock time of each call;
  2. the server's accept or reject (HTTP status from `/addagent` and the server log line);
  3. the coding tool's own output for this one bug (its analysis plus the run).
- **Done when:** these three artifacts exist for the old code, and either the same run passes on the fixed code or the report says not reproduced.
- **Satisfies:** the professor's SigninView item ("show me your coding tool output just for this bug").

**F2. Camera state, first fix only** (`LocManagerViewModel`, `LocManager.startUpdates`)
- Add a map camera position and a single "positioned" flag to `LocManagerViewModel`. This follows the pattern where tool functions already read `LocManagerViewModel.shared`.
- **Two writers:**
  1. The first-fix writer runs only if the flag is unset, then sets it.
  2. The `recenter_map` writer runs on every call and also sets the flag.
- So the first-fix writer fires at most once per launch, and a late first fix can never overwrite a tool move.
- Later location updates change only the stored location that `get_loc_auth` reads.
- **Done when:**
  - with simulated location changes after launch, the camera moves once, at the first fix, and never again until a tool call;
  - with permission denied, only the progress indicator shows until `recenter_map` runs (see accepted limit L3).
- **Satisfies:** "map centered on the user's current location at launch; no default view; no later move".

**F3. The `recenter_map` tool, reusing the tutorial tool machinery** (`Toolbox`, `Tool`, `ToolFunction`, `getAuth`, `getLocAuth`, `Ticket`, `tools/*.json`)
- **Name:** `recenter_map`. It matches the tutorial's snake_case verb naming (`get_auth`, `get_loc_auth`, `get_weather_auth`).
- **Arguments:** three string arguments in this order: `ticket`, `latitude`, `longitude`. This mirrors `get_weather_auth.json`, so the existing argument-order mechanism in `Toolbox.invoke` works unchanged.
- **Schema file:** a new `recenter_map.json` beside `get_loc_auth.json`. The synchronized project group includes it automatically. The description says it moves the map and nothing else. It never mentions a game or "game over".
- **Function:** a new phone-side function next to `getLocAuth`, registered in `Toolbox.init`.
- **The function, in order:**
  1. It checks the ticket exactly as `getLocAuth` does, using the same baseline 401 text, accepted as it is. That guard is shared by both functions so the text exists in one place.
  2. It parses the two numbers. A non-number or an invalid coordinate makes it return an error sentence to the LLM without moving the map. The map must never jump to 0,0.
  3. It sets the camera and the positioned flag.
  4. It returns a short success sentence.
- **Done when:**
  - a valid ticket makes the map fly to the coordinates;
  - a wrong or expired ticket returns the 401 text and the map stays;
  - garbage coordinates return an error and the map stays.
- **Satisfies:** "recenter tool needs a token"; "MUST reuse tutorial tools and functions"; no duplication; "the tool only moves the map".

**F3b. Denial is distinguishable from an invalid ticket** (`getAuth`)
- **Smallest change:** the sentence `getAuth` returns when no ticket exists after the sign-in sheet closes is replaced with a clearly different "denied" result:
  - it does not start with "401" and does not say to call `get_auth`;
  - it says the user declined or failed authorization;
  - it tells the LLM not to call `get_auth` or `recenter_map` again, to reveal the city in text, and to tell the user to tap Clear.
- The invalid-ticket message is untouched.
- The structure is unchanged: same function, same single return point, one string differs.
- **What counts as denied:** the user cancels, or Google sign-in or the `/addagent` call fails, so there is no ticket after the sheet closes.
- **Done when:** a cancelled sign-in produces the "denied" text, an expired ticket produces the 401 text, and the LLM does not repeat the same tool call after a denial.
- **Satisfies:** the requirement that the map moves only with a valid token; denial and expiry are distinguishable.

**F4. Rules and secret city** (`Game.rules`, `AppViewModel.sendTurn`, the marker stripper in `Rein`)
- Rewrite only the Guess-the-City rules. 20 Questions rules are unchanged.
- The city rules say, in plain terms:
  - Pick a well-known city and begin the first reply with the hidden marker, then a short welcome and one hint. Never state the name in hints.
  - On a wrong guess, give a new hint.
  - On a correct guess, call `get_auth`, then call `recenter_map` with that ticket and the city's coordinates. After it, congratulate the user and tell them to tap Clear for a new game.
  - If `get_auth` reports that authorization was denied, say so, reveal the city in text, and tell the user to tap Clear.
  - If the user gives up, reveal the city and tell them to tap Clear.
  - The marker is written once, at the start of a game. Do not write it again.
- There is no retry rule for an invalid ticket. The baseline 401 text already tells the LLM what to do, and we accept it as it is.
- **Marker stripping while streaming.**
  - The existing stripper holds back the first characters of the reply until it can confirm the marker (and drops it up to the closing bracket) or rule it out.
  - Text reaches the hint only after the stripper releases it, so a half-arrived marker never flashes.
  - The stripper starts fresh for every request.
  - **Known limit L4:** if the LLM opens a marker but never closes it within 120 characters, the held text is flushed as ordinary text and would be visible.
- **Done when:**
  - over ten fresh starts, the first visible hint never contains marker text, even mid-stream (T13);
  - a correct guess leads to exactly `get_auth`, then `recenter_map`, then closing text that includes the Clear instruction;
  - a wrong guess leads to no tool call.
- **Satisfies:** "app sends rules; LLM picks the city; city fixed and secret"; owner decision 7.
- No game-state detection anywhere.

**F5. The screen** (`ContentView`, `SubmitButton`, `ClearButton`, `RoleToggleButton`, `ChatView`, `ConversationView`, `AppViewModel`)
- **Layout**, top to bottom in a plain vertical stack:
  1. the game picker,
  2. the map area, taking the remaining space,
  3. the hint area,
  4. one input row (text box, role toggle, Clear, Send).
- **Map area:**
  - Until the positioned flag is set: a progress indicator.
  - After that: the system MapKit view (SwiftUI `Map`) bound to the camera, with the system location dot.
  - A toolbar button in the existing navigation bar swaps this area in place with the transcript (`ConversationView`) and back. This is local view state.
  - The camera is kept in the model, so a recenter during the transcript view is not lost.
- **Hint area (precise behavior).**
  - It shows the content of the newest assistant entry in `conversation` that has non-empty text. No new stored state.
  - Because `sendTurn` appends an empty reply entry before streaming, the previous hint stays visible until the new reply's first visible character arrives. Then the new reply replaces it.
  - Entries from the user or system roles are never shown here, so a user message at the end of the list changes nothing.
  - Tool results are not in `conversation` at all. A tool round appends text to the same reply entry, so pre-tool and post-tool text accumulate there. If a tool round produces no text, the hint stays.
  - If a send fails, the error goes to the existing alert. An empty reply entry stays empty, so the previous hint remains. If the failure is a streaming parse failure, the tutorial appends its error text to the reply, and that becomes the shown hint.
  - After Clear, `conversation` is empty, so the hint is blank until the new rules reply arrives.
  - The hint area has a capped, scrollable height so a long reply cannot push the text box off screen.
- **Send and Clear (tutorial mechanism, reused).**
  - A single busy flag in `AppViewModel` disables Send, Clear and (new) the picker while a send or wipe runs.
  - Both buttons show the spinner while busy, as the tutorial does today. The app does not know which button was tapped, and the plan adds no mechanism for it.
  - Send is also disabled unless the currently shown draft has non-whitespace text (D6).
- The root tap currently toggles keyboard focus. Make it dismiss-only and keep it off the map, so a map tap never pops the keyboard open.
- **Done when:** on a phone-size simulator with a simulated location, launch shows the progress indicator and then the map on that spot, the hint sits directly above the text box, the transcript is reachable but never shown with the map, and the mutual-disable rule holds, including during the launch-time start and when the picker changes.
- **Satisfies:** all four screen requirements; "hints above, not side by side"; owner decisions 1 and 5.

**F6. Launch and Clear flow** (`AppViewModel.resetGame`, the `ContentView` launch task)
- Launch calls the same function as the Clear button: wipe on the server (through `Rein.llmClear`), then send the rules.
- **Why launch changes from the baseline (not cut):** without the wipe, a relaunch stacks new rules on the previous game's history and its marker, so "the city stays fixed" breaks. This reuses `resetGame` and adds no new code.
- Clear's behavior is otherwise the baseline's `resetGame`: the wipe, empty the conversation, send the rules. It does not newly clear drafts, which the requirement does not need. The map and the Keychain ticket stay.
- There is **no Retry feature**: no button, no automatic retry, and no stored-state resume.
- **Baseline issue surfaced, not fixed.** If the wipe fails, `resetGame` still empties the screen and sends the rules, and `sendTurn` then blanks the error text, so the alert can show an empty message.
- **Done when:** relaunching mid-game gives a brand-new city with the previous game gone from the server (T10).
- **Satisfies:** owner decision 2 and the Clear requirement.

**F7. Housekeeping**
- Update the location permission text to say the app centers the map on the user.
- Change comments only where my change makes them false. Do not delete existing comments.
- The Keychain item keeps its tutorial behavior of storing the ticket's expiry as a visible attribute. Nothing in this plan changes that.

**F8. Legacy sweep** (section 7).

**F9. Verification** (one working runner plus the simulator; a real device only if available)
- **T1.** Cold start with the permission prompt: progress indicator, then the map on the simulated location.
- **T2.** Wrong guess, then right guess: `get_auth`, `recenter_map`, map moves, closing text tells the user to tap Clear.
- **T3.** Right guess with a valid in-memory ticket: no sign-in sheet and no new prompt.
- **T4.** Two tool rounds in one turn: the call ids stay unique on this runner (schema risk 4).
- **T5.** Ticket expiry using the short B2 setting, then a win: the silent re-sign-in path.
- **T6.** Cancelled sign-in: the "denied" result, no loop, the city is revealed and the user is told to tap Clear.
- **T7.** Face ID cancelled or failed at save time after a successful sign-in: the ticket is still usable in memory and `recenter_map` works (section 6). This needs a real device, because the simulator does not prompt. If no device is available, report it as untested.
- **T8.** Give-up text: the city is revealed and the user is told to tap Clear.
- **T9.** Clear during and after a game. After Clear, read-only counts show zero rows for the app in turns, calls and tools. After the first new send, the tools row exists again, and the LLM can call `get_auth` in that very first new game.
- **T10.** Relaunch mid-game: a new city and a clean server state.
- **T11.** Picker switch and transcript swap during a send.
- **T12.** Failed send: the previous hint stays and the alert shows.
- **T13.** Ten fresh starts: the marker is never visible, even mid-stream.
- **Done when:** every test behaves as described (T7 as noted) and nothing from the do-not-build list appears.

## 5. How the map actually moves

- The Map is the system MapKit view, SwiftUI's `Map`, bound two-way to a camera position value held in `LocManagerViewModel`.
- Moving the map means assigning that value a new camera centered on the given latitude and longitude at city-level distance, inside an animation so it visibly flies. User panning also updates the value, so the next assignment still wins.
- **Writers:**
  1. the first-fix writer, which fires at most once per launch;
  2. `recenter_map`, which fires on every successful call.
- **Rejected:**
  - MapKit's "follow user" camera (it follows continuously and needs a fallback view, which is a default view);
  - a wrapped UIKit map;
  - any marker, pin or annotation that we add for the city. The system-drawn location dot (D2) is the only marker-like item and is allowed.
- **Concurrency:** the project setting `SWIFT_DEFAULT_ACTOR_ISOLATION = MainActor` is set in both build configurations of `project.pbxproj`, together with `SWIFT_APPROACHABLE_CONCURRENCY = YES`.
  - Under that setting the tool function should be able to write the state with no explicit main-actor attribute and no dispatch queue.
  - That consequence comes from the Swift compiler's documented behavior. It is UNVERIFIED until the project builds. Confirm with a clean build.
- **Edge cases:**
  - Assigning an equal value does nothing, which is harmless.
  - If the transcript is showing, the move still happens.

## 6. How the LLM obtains the token

```mermaid
flowchart TD
  A["LLM calls get_auth"] --> B{"Valid ticket in memory?"}
  B -- yes --> R["Return ticket text to LLM, no new prompt"]
  B -- no --> C["Sign-in sheet via getSignedin"]
  C --> D["Google restore or button, then /addagent"]
  D --> F{"Ticket now in memory?"}
  F -- yes --> G["Save to Keychain: this device only, passcode required, user presence; expiry kept as visible attribute"]
  G --> R
  F -- no --> X["Return DENIED text (not 401): do not retry, reveal city, tell user to tap Clear"]
  R --> H["LLM calls recenter_map with ticket, latitude, longitude"]
  H --> I{"Matches Ticket.shared and not expired?"}
  I -- yes --> J["Camera moves"]
  I -- no --> K["Return baseline 401 invalid-ticket text"]
```

**Biometric behavior (owner decision 6), per the tutorial's real code**
- **At launch,** `Ticket.open` reads the Keychain item.
  - On the simulator, it first runs a simulated biometric check.
  - If that check fails, the user sees an advisory ("Will acquire on sign in"), and the ticket is not loaded.
  - On a device, if the read itself fails or is cancelled, the user sees the error alert and the ticket is not loaded.
  - Either way, the next `get_auth` falls back to Google sign-in. It is not a denial.
- **A still-valid ticket in memory is reused with no new prompt.**
- **If Face ID is cancelled or fails at save time after a successful Google sign-in:**
  - The server ticket is already placed in memory before the save is attempted.
  - A save failure shows the error alert ("You will need to sign in again on relaunch").
  - The ticket stays usable in memory for its lifetime, so the sign-in sheet closes, `get_auth` returns the ticket, and `recenter_map` succeeds.
  - It is **not** a denial. Only the persistence to the Keychain is lost, so the next launch needs a new sign-in.
  - Whether a given Keychain add or update actually prompts is platform behavior I cannot verify from our call sites. The outcome above follows from the tutorial code either way.
- The recenter check compares against the phone's own copy of the ticket. The server's tickets table is used only by `get_weather_auth`.
- The Secure Enclave wording is satisfied only through the tutorial's Keychain access control. No explicit Secure Enclave key is created.

## 7. Legacy-pattern checklist

**"Touched lines only", defined.**
- A line is touched if it is added, if its text changes, or if it moves into a different statement.
- Pure re-indentation, or reordering of unchanged statements, does not make a line touched.
- **One rule is chosen: the line, not the enclosing function.** Every check below applies to touched lines only.
- **Consequence for what legacy code ships:** a touched function can still contain a baseline offender on lines we do not change. Examples that will ship unchanged:
  - `LocManager.startUpdates` keeps its `do/catch` and `print` (we change only the line that stores the location);
  - `getAuth` keeps its continuation call (we change only the denial sentence);
  - the `ContentView` buttons keep their `foregroundColor` and `cornerRadius` lines;
  - `SigninView` keeps its two continuation helpers.
- So the legacy count after this project is about the baseline's. The guarantee is only that added and edited lines are clean.
- **Risk note.** The staff wording is "presence of these legacy patterns in your code will lead to automatic point deductions". It may be applied to the whole code base, not just our changes, so baseline offenders may still cost points. This is the owner's accepted scope.
- The alternative, "enclosing function", would fix more offenders but enlarge the diff beyond the request.

**Swift checks, run on touched lines**
1. Search for `DispatchQueue`, `Task.sleep`, `Thread.sleep` and `RunLoop`: zero hits.
2. Search for `ObservableObject`, `@Published`, `@StateObject`, `@ObservedObject` and `@EnvironmentObject`: zero hits. `@Observable`, `@Environment` and `@Binding` are fine.
3. Search for `@MainActor`: zero hits.
4. Search for `ZStack` and `GeometryReader`: zero hits.
5. Search for `as?`, `as!` and `as `: zero new hits. Parse coordinates with a failable number conversion and validate with the system's coordinate-validity function.
6. Check every new `enum`: it must have cases.
7. Search for `do {` and `catch`: zero in new code. Use `Result`.
8. Review every new if/else that assigns a value: convert to an expression.
9. Touched views: use `foregroundStyle` and `clipShape`, not `foregroundColor` and `cornerRadius`, on touched lines.
10. Count new callback or continuation wrappers: zero, unless F1b is forced to add exactly one with its justification.
11. In the diff, count removed comment lines: zero, even where code is removed.
12. Every new comment explains why, not what.
13. The invalid-ticket sentence appears in exactly one place on the phone.
14. Names: every new identifier is a noun or a descriptive phrase for its function.

**Python checks for B1 and B2 (against the course AGENTS.md; CLAUDE.md stands in until it is supplied)**
1. No new import beyond what the change needs. B2 may need the standard `os` module.
2. No `threading`, `time.sleep`, `asyncio.get_event_loop`, or blocking calls in the handler. B1 uses the same awaited `rwdb` calls as today.
3. B1 contains no delete-then-insert. It is three pure deletes with bound `?` parameters and no string-built SQL.
4. B2 reads the variable once at import as a single expression with a default. No multi-line if/else, no config class, no argument parser.
5. Type hints, if any, use modern forms (`X | None`, built-in `list` and `dict`). Search for `Optional`, `List`, `Dict`, `typing.`: zero in changed lines.
6. Use f-strings only, no `.format(` and no `%` formatting.
7. No new helper function, class or wrapper for single-use code.
8. Errors reuse `_logClientErr`. No new broad exception handling beyond the one the handler already has.
9. The comment above the lifetime constant explains why it is tunable, and the existing "why capped" comment is kept.
10. Indentation and style match the surrounding lines. `handlers.py` mixes tabs and spaces, so match the nearest lines.
11. No validation of the environment value beyond what the existing code does. That would be hardening.

**Baseline Python offenders, reported not fixed**
- `from __future__ import annotations` on a Python 3.14 project (`pyproject` requires 3.14 or newer).
- Mixed tabs and spaces in `handlers.py`.
- A synchronous `requests` session in `main.py`.
- Broad `except Exception` clauses.

**Baseline Swift offenders, reported not fixed**
- `do/catch`: `Rein.llmTools`, `Rein.processSse`, `Toolbox.jsonToSchema`, `LocManager.startUpdates`.
- Type assertions (`as?`): `Toolbox.invoke`, `Rein.addAgent`, `Rein` response casts (unavoidable), `Ticket`, `SigninView`, and the client-id lookup.
- Continuation helpers: two in `SigninView`, one in `getAuth`.
- Deprecated styling: `foregroundColor` and `cornerRadius` in `ContentView` and `ChatView`.
- `print` in `LocManager`; static mutable `isThinking` in `Rein`.
- Not found: dispatch queues, old property wrappers, layered stacks, geometry readers, caseless enums.

## 8. Do-not-build list

The tutorial extras (picker, 20 Questions, role toggle, transcript) are kept. No Clear confirmation is added (Q2). Still forbidden:
- Pin, marker or annotation that we add on the map.
- Play Again button.
- Give Up button.
- Status row or status line.
- Timers and any time limit.
- A Retry feature in any form (button, automatic retry, or resume from stored tool results).
- Game-over or "Ended" detection, including treating any tool call as a win signal.
- Any new endpoint, or any change to a data format or the SQLite schema.
- Security, scalability or reliability hardening beyond the spec.

## 9. Accepted limits

- **L1. Stalled stream.**
  - With no timers (staff-mandated) and the kept mutual-disable rule, a stalled reply stream leaves Send, Clear and the picker disabled until the stream ends or the app is relaunched.
  - The tutorial request carries a 20 minute timeout, and the server sends keep-alive pings. Whether those pings defeat that timeout is UNVERIFIED.
  - This is an accepted consequence, not a bug to fix.
- **L2. Secrecy rests on LLM obedience.** The marker only hides the city from the screen, not from a model that ignores its rules.
- **L3. No location permission.** The area shows the progress indicator until the first `recenter_map`. Then the map appears centered on the city. This is a flagged limit.
- **L4. Unclosed marker.** After 120 characters the held text is shown.
- **L5. Duplicate call ids** from a provider could fail an insert (schema fact 4).
- **L6. Phone-side ticket check.** The recenter check is local, so the server's own ticket table is not consulted.

## 10. Goldfish 4 round 2 findings: not adopted or adopted in part

- **Finding 2, "cut the launch change in F6": not adopted.**
  - Reason: it is one reused call, and without it a relaunch stacks a new game on the old game's secret.
  - The extras the reviewer named are cut: the "removes stale-error behavior" claim (now a surfaced baseline issue), and Clear emptying the drafts.
- **Finding 3: adopted with one rule (line, not function).** Reason: it matches the owner's "new and touched code only" and the "every changed line traces to the request" principle. The consequence is stated in section 7.
- **Finding 6, the claim about main-actor isolation:** adopted as "per the project setting, effect UNVERIFIED until a clean build". I did not cite the library's behavior.
- All other findings are adopted.

## 11. Questions that still need the owner

1. **20 Questions wording (non-blocking, default: leave unchanged).** Its baseline rules still say "invite them to play again" and it never recenters. Owner decision 7 tells the city game to say "tap Clear". Should 20 Questions get the same wording?
2. **Clear confirmation (non-blocking, default: none).** The baseline has none. HW2 specified one, and the owner said to keep the extras. Adding one is a new feature and conflicts with "tapping it clears".
3. **The professor's cut-off sentence (non-blocking, but confirm before submission).** B1 reads it as "Clear must also delete the tools row", and reads "feed the LLM the current schema" as handing the coding agent db_schema.sql. Both are guesses. Can you check them with the professor?
4. **Person for the stale-token run (blocking only for closing F1).** A person must perform the interactive Google sign-in and keep the app alive for over an hour. Who and when?
5. **Test runner and device (non-blocking).** Which single runner is the test runner, and is a real device available? T7 (Face ID at save) cannot run without one.

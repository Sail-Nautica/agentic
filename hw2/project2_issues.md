# Professor feedback on HW2 and Project 2 issues

## HW2 resubmission (replaces the current submission, no penalty if addressed)
| Feedback | Fix | Status |
|---|---|---|
| Audit table missing Goldfish 1 and 3 rounds; Key Criticisms must summarize ALL criticisms of EACH Goldfish, grouped per Goldfish | One row per Goldfish (G1 on E-A, G2 on E-A, G3 on E-B), each summarizing every round | Done in wiki/Section-1 draft |
| G-A, G-B, G-C one-page summaries are in the wrong section | The one-page G-A, G-B, G-C now sit in the summary section, interleaved chronologically with E-A and E-B | Done in draft |
| E-B one-page summary lists key ideas, not what will be built | Rewritten to describe the deliverable: components, files, flows, constraints | Done in draft |
| Full exhibits of G-A, G-B, G-C not submitted; must be verbatim | Full exhibits are the Goldfish outputs verbatim: G-A = Goldfish 1 rounds 1 to 5, G-B = Goldfish 2 rounds 1 to 3, G-C = Goldfish 3 rounds 1 and 2. Recovered byte-for-byte from the saved agent transcripts (hw2/rounds/verbatim, prompts included) | Done in draft |
| Sections 2 and 3 | No resubmission | Unchanged |

## Project 2 issues (implementation must follow the requirement document, not E-A/E-B where they differ)
| Professor's point | What the design said | Project 2 action |
|---|---|---|
| Hints must be ABOVE the guess box, not side by side | E-A had hints above the box (panel order: hints, status row, input row) | Keep hints strictly above the text box; verify in the final layout |
| Map must be centered on the user's location on launch; no default view and no moving afterwards | E-A decision (b): default view first, then moves when a fix arrives | Do not show a default view: show the map already centered on the user's current location at launch (wait for the first fix before showing the map, or start it centered) |
| No pin in the requirement document | E-A/E-B drop a pin on a win | Remove the pin; only recenter the map on the city's latitude and longitude |
| No "Play again"; interactions are by natural language | E-A: field disabled after a win plus a Play again button; E-B: Ended state | Remove the button and the Ended state; the user types to the LLM (play again, give up) and the LLM handles it |
| No "status row" in the requirement document | E-A: reserved one-line status row | Remove it; show only the required elements (map, hints above the text box, text box with Send, Clear) and the in-progress indication on Send |
| Timer and three-way Retry not requested; hardening warned against | E-B: 30 s limit on every call, three Retry behaviors, leg cap | Remove the timer, the Retry behaviors and the leg cap; keep the tutorial's existing error handling |
| "Ended after ... a timer" | E-B/E-A: a timer ends the request into Error | Remove; no timer-driven game end |
| Stale-token claim in SigninView: show the coding tool's output for this bug | E-B section 1d: SigninView prefers the SDK's in-memory token, which can be stale | See evidence below. Decide whether to keep any change |
| "Clear deletes calls and turns but not stored tool schemas. The requirement doc says," (sentence is cut off) | E-B section 1b | Need the rest of the professor's note |
| "How to recenter the map?" | E-B: SwiftUI Map camera position set from the tool | Answer with the concrete approach when implementing (see questions) |

## Evidence for the SigninView stale-token claim
What was checked now (static, nothing was run on a device):
1. `Agent/Agent/SigninView.swift` line 55 uses `signinClient.currentUser?.idToken?.tokenString` if a current user exists, and only otherwise calls `restorePreviousSignInAsync()`.
2. Google Sign-In SDK header (GIDGoogleUser.h): `idToken` is a plain read-only property; a separate method, `refreshTokensIfNeededWithCompletion`, exists to refresh "if they have expired or are about to expire".
3. Google Sign-In SDK header (GIDSignIn.h): `restorePreviousSignIn` "restores user from the local cache and refreshes tokens if they have expired (>1 hour)".
4. `harnessd/handlers.py` `addagent` verifies the ID token with `verify_oauth2_token`, which rejects an expired token (the handler answers 401 on ValueError).
What is NOT shown: a run where the stale in-memory token actually produced a 401. The claim came from the Elephant's reading of the code; points 1 to 4 make it plausible but it is unproven until reproduced (for example, leave the app running for over an hour after signing in, then trigger sign-in). If it cannot be reproduced, the claim should be withdrawn from E-B and Project 2 should keep the tutorial's code unchanged.

## Legacy patterns (new in the updated feedback; deductions apply to the Project 2 code)
Source: https://reactive.eecs.umich.edu/lectures/AGENTS.pdf (2 slides; text recovered with PDFKit, parts of the slides are images and may be missing) and https://reactive.eecs.umich.edu/asns/AGENTS.md (summarized by the fetch tool, not verbatim).

Slide rules (each marked "Immediate 75% grade deduction" in the extracted text):
- Thread-based concurrency: any use of DispatchQueue (main or global), `.sync`/`.async`. Use coroutines/structured concurrency. No `Task.sleep()` or `Thread.sleep()` (suspend instead of polling), and no RunLoop.
- Older property wrappers: `ObservableObject`, `@Published`, `@StateObject`, `@ObservedObject`, `@EnvironmentObject`. Use the Observation package (`@Observable`, `@Environment`); `@Binding` is still fine.
- UI thread and layout: explicit `MainActor` use must be justified (Swift 6.2 default MainActor isolation applies), `ZStack` and `GeometryReader` use must be justified.
- Manual type assertion and caseless enums used as namespaces (the slide text is cut off in the extraction).

AGENTS.md rules that touch this project: Minimum Reproducible Example (no hardening; document rare unhandled cases in comments); prefer expressions over multi-line if-else; Result types over do-catch; native structured concurrency; atomic upserts instead of DELETE + INSERT (E-B's Keychain delete-then-add would need justification); no Docker; files kept separate by role.

Check of the current tutorial code (grep over Agent/Agent/*.swift): no DispatchQueue, Task.sleep, Thread.sleep, RunLoop, ObservableObject, @Published, @StateObject, @ObservedObject, @EnvironmentObject, MainActor, ZStack or GeometryReader. Casts (`as?`, `as String` on Keychain and JSON values) and two enums in Rein.swift (`SseEvent`, `SecretMarkerState`, with cases, so not caseless namespaces) are present.

Implications for the Project 2 plan:
- Drop the E-B 30 s race built on a sleep: it also violates the Task.sleep rule, on top of the professor's "no timer" point.
- Lay out the full-screen map plus bottom panel with overlay/safe-area modifiers, not ZStack or GeometryReader, unless justified.
- Keep the Observation-based `AppViewModel` (already `@Observable` with `@Environment`).
- Replace Keychain delete-then-add with SecItemUpdate/upsert semantics, or justify it in a comment.

## Answers found on the course pages (fetched 2026-11-02; text is a small-model summary of each page, so check the exact wording on the page before relying on a quote)
Sources: https://reactive.eecs.umich.edu/asns/Project2 and https://reactive.eecs.umich.edu/asns/HW2

- **"How to recenter the map?"** Project2 page, HW2 feedback: the implementation plan "needs to cover how you recenter the map given lat/lon. Not the authorization path, but how to actually move the map to recenter on the lat/lon." So the Project 2 plan needs a concrete map-moving mechanism, separate from the auth path (E-B section 6 only sketches it).
- **Map on launch:** "The map shows up already centered on the user's current location."
- **Pin:** "All you have to do is to center the map on the mystery city." No pin or marker is stipulated.
- **Give Up / Play Again buttons:** the HW2 requirement does not require either; the NLP text box covers them. **Status line:** not required; it takes up screen space.
- **Game-over detection:** the plans "spend a considerate amount of efforts in detecting when a game is over. Question your coding agent and yourself whether this is necessary." Also: "the tool call to move the map should only be used to move the map, not to signal the front-end that a game is over." (This contradicts E-B's win detection and Ended state.)
- **Ticket lifetime:** "not a fixed value. You can set it for playability or for testing"; several plans "got hung up on the short duration of the lifetime." (E-B treated the 180 s back-end constant as untouchable; the page says it can be tuned.)
- **Timers, retry:** not mentioned anywhere. Goldfish 2 must flag "any features added that were not required by and justified by the design requirements" and "No unspecified security, scalability, or realibility hardening"; Goldfish 3 audits for "enterprise-grade security, scalability, and realibility hardening."
- **Clear:** HW2 page: Clear must clear "all the conversation history/context associated with the app, including both 'system' and 'user' prompts"; Send and Clear disable each other. Project2 page, feedback: "Your llmclear() would need to be adapted to remove from the database cleanly"; "You'd need to feed your LLM the current back-end database schema that supports tool calls"; the schema itself may not change. **The professor's sentence about tool schemas is still not answered by either page**: neither mentions tool schemas.
- **Architecture:** structure and naming must match the tutorials or the project is not graded (ZERO); "You MUST reuse pre-existing tools and tool functions from the tutorials"; unnecessary code duplication triggers a full grade penalty. Interoperability with the staff back end on mada.eecs.umich.edu and with the cloud-hosted back end applies. Legacy patterns lead to automatic deductions.
- **Process:** Project 2 must "address any feedback you received from the teaching staff on your HW2 submission"; the Elephant and Goldfish LLMs generate no code.

Implications to carry into the Project 2 design: drop win/game-over detection and the Ended state, so the move-map tool only moves the map; no pin, no Play again, no status row, no timer or retry; reconsider the "two tools" and "any game tool" design against "reuse pre-existing tools"; plan the lat/lon map move concretely; the ticket lifetime can be set in the back end.

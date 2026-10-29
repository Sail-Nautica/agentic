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

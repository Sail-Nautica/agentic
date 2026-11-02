# Goldfish4_round3: verbatim output

PM COVERAGE REVIEW OF E-C v4 (read only the three files; no code)

Short answer: E-C covers the design as overridden by staff feedback, with a handful of real gaps. Five need attention: no stop-gap for the map's first appearance when location is denied (L3 is partly a contradiction), a hint-versus-transcript requirement conflict, the "Clear confirmation" dropped without it being listed in the departures table accurately, the stale-token item (F1) being a plan to gather evidence rather than an answer, and a few places where E-C quietly adds scope.

## 1. Coverage of the design document

How the design reads once staff feedback is applied: one-screen game; LLM picks secret city; hidden marker; guess; win via get_auth then recenter_map; denial path; Clear; known limits.

- One-screen iPhone game, map-dominant, bottom panel: PARTLY. E-C Departure 1 (F5) replaces Decision F's full-bleed map with the tutorial layout (picker on top, map, hint, input row). The map is no longer dominant, and the panel/floating Clear are gone. Declared in section 1, row 1. Acceptable as an owner call, but F5 gives no sizing rule saying the map takes "the remaining space" while a capped hint area is on screen, so "map-dominant" is not guaranteed.
- Map centered on the user at launch, no default view: FULLY via owner decision 4, F2, F5. One gap: with location permission denied, the user sees only a spinner forever (L3). The staff said "no default view", so this is defensible, but the game is then visibly broken before the first win. E-C should say plainly this is a dead screen, not just "limit".
- LLM chooses the city, never the app (Decision B, marker stored and replayed): FULLY (F4, Departure 12). The "Begin" message is dropped (Departure 2, D1) and it is declared. Note D1 is a default, not a decision, and has a fallback "only if a runner fails". That leaves the first-message behavior untested across runners, because D8 tests only one runner.
- Marker stripped before display: FULLY (F4, T13). L4 (unclosed marker after 120 characters shows) is a known leak. Fine for a prototype.
- Guess replaces the hint: PARTLY. Design says the reply replaces the clue. F5's hint area shows the newest non-empty assistant text, and also says tool rounds "append text to the same reply entry, so pre-tool and post-tool text accumulate". So after a win the hint can show welcome-to-closing text mashed together rather than a clean replacement. Not stated as a departure.
- Give-up as plain text: FULLY (F4, T8).
- Win: get_auth then recenter_map with ticket and coordinates (Decision A): FULLY (F3, F4, section 5/6, T2). The design says the phone "checks the ticket and the coordinates"; F3 does both and refuses to jump to 0,0. Good.
- Pin on success: DROPPED, correctly, by staff override (Departure 3). Correct.
- Closing text, then Ended + Play again: DROPPED (staff), replaced by "tap Clear" (owner decision 7, Departure 7). Handled correctly, and E-C flags that this changes the requirement document's wording ("invites the user to play again"). Substantive: the staff said no Play Again button and "interactions are by NLP", but they did not say the LLM may not invite another round in chat. Owner decision 7 forbids even that. That is a tightening beyond the feedback. Fine as an owner decision, but E-C should not present it as feedback-driven.
- Denial path (Decision C, point 4): FULLY and better than the design (F3b, T6). It does add a distinct "denied" string, which is new tool-result wording, justified because the LLM must tell denial from expiry.
- Errors and 30 s timer, three Retry kinds (Decision E): DROPPED by staff (Departure 4, 6). Correct.
- Clear asks for confirmation: DROPPED by owner/E-C (Departure 9). Declared. Reason given ("the only addition is the map") is weak: the design specified it, the staff did not forbid it, and E-C itself says in Q2 it conflicts with "tapping it clears". Leaving it out is probably right, but the table's stated "why" does not match the open Q2.
- Clear wipes through existing /llmclear, starts a new game, map and Keychain ticket stay: FULLY (B1, F6, T9). Extra: the design said server unchanged, E-C changes llmclear (Departure 10, staff-driven). Correct.
- Ticket lasts at most 3 minutes: FULLY, as a tunable (B2), default 180. Staff overrides "fixed value". Correct.
- Face ID on each win (design point 3): OVERRIDDEN by owner decision 6 (Departure 8). Declared, and honestly admits HW2 overstated it. Note, however, that Keychain item is "Face ID or passcode to read" per Decision D; E-C section 6 says the simulator and device behave differently at launch. Consistent.
- Decision D (tutorial Keychain, expiry as visible attribute): FULLY (F7, section 6). Secure Enclave wording is explicitly not met (stated in section 6). Admitted rather than hidden. Good.
- Decision G (MapKit): FULLY (F5, section 5).
- Decision H (no back-end change, one tester at a time, wipe at launch): PARTLY. Wipe at launch is covered (F6). The "no back-end change" part is changed by staff (B1, B2). One-tester-at-a-time is not listed in E-C's accepted limits L1-L6 even though the design listed it. Minor omission.
- "Known limits we accept": the design's limits are mostly reproduced; "LLM tends to choose the same few cities" and "timeout can damage conversation" are not carried over. The second is moot (no timers). Not a real gap.
- "Tools stay registered" (D5): get_loc_auth and get_weather_auth remain. Not in the design; see section 3 below.

Missing from the section 1 departures table:
- The hint replaces/accumulates behaviour (see above).
- Dropping the design's "Sending/Clearing" reflected as disabled buttons: E-C keeps a busy flag and ALSO adds disabling the picker (F5 "new"), which is a behavior the design never had. Not in the table.
- The design's "Send disabled during retry states": gone with Retry, correctly implied by Departure 6.
- Design's "status line": covered under Departure 3.
- Owner decision 5 (transcript swap) is under Departure 11, ok.
So the table is nearly complete; the two not listed are the hint-accumulation behavior and the picker-disable addition.

## 2. Staff feedback, item by item

1. Hints above the text box, not side by side: FULLY (F5 layout: hint directly above input row; done-when says so).
2. Map centered on current location at launch, no default view, no move afterwards: PARTLY. F2/F5 deliver it, but a first frame spinner is not a map "upon launch", and denied permission means no map (L3). Owner decision 4 accepts this. Real conflict: staff wording says "Upon launch shows the map centered on user's location"; a spinner until the first fix is the closest feasible. It is declared. Counts as addressed, with the L3 caveat.
3. No pin: FULLY (do-not-build list, section 5 "Rejected"). The blue system location dot is kept (D2); staff said no "marker/pin" for the city, so this is consistent but is a judgment call and appears only as a default (D2) to confirm.
4. No "Play again": FULLY (Departure 3, 7, do-not-build).
5. No status row: FULLY.
6. No timer/Retry/hardening: FULLY on timers and Retry (Departure 4, 6, do-not-build). PARTLY on "no reliability hardening": see section 3 below (mutual-disable rule, whitespace rule, ticket-lifetime knob validation notes, T4 call-id testing, 120-character flush).
7. Clear sentence (cut off): PARTLY, openly. B1 guesses "must also delete the tools row" and asks the owner to confirm (Q3). It cannot be fully addressed without the professor. E-C is honest about this. Note a risk it half-notes: deleting the tools row is harmless only if the next send re-registers it; T9 tests this.
8. "Ended after a timer": FULLY (no timers, no Ended state).
9. SigninView stale token: PARTLY. F1 is an investigation plan, conditional on a person running an hour-long test (Q4 is blocking for closing F1). The professor's demand is: show your coding tool's output if you are sure. E-C does not claim certainty, which is correct, but the deliverable cannot exist until someone runs it, so this item is not "addressed" in the plan itself, only scheduled. Substantive: F1a also adds temporary logging in the code, then removes it; that is reasonable but the "remove logging afterwards" has to be policed.
10. How to recenter the map: FULLY (section 5, F3). Clear and specific. One UNVERIFIED claim (main-actor behavior) is flagged honestly.
11. Legacy patterns: PARTLY. Section 7 covers new and touched lines only (owner decision 3). The staff wording says presence in "your code" causes automatic deductions, and E-C itself notes baseline offenders will ship (do/catch, as?, continuations, foregroundColor, print, a static mutable isThinking). So the likely deduction risk is acknowledged but left. Owner decision, flagged. Also: a staff-listed rule says caseless enums, MainActor use "must be justified", ZStack/GeometryReader "must be justified"; E-C sets @MainActor and ZStack/GeometryReader to zero hits, which is stricter than "justified" and fine.
12. Backend: feed LLM the schema: FULLY as interpreted (Step 0, section 2), with the guess in Q3 flagged.
13. Backend: adapt llmclear: FULLY (B1).
14. Backend: ticket lifetime tunable: FULLY (B2). E-C picks an environment variable read at startup; staff just say tunable. Fine.
15. Frontend: map recentered on lat/long: FULLY (F3, section 5).
16. No Give Up, Play Again, status line, marker/pin: FULLY.
17. Game-over detection must not be done; recenter tool must only move the map: FULLY (F3 schema text never mentions the game; "no game-state detection anywhere"). One caution: F3b makes `get_auth` return a distinct "denied" string and tells the LLM how to behave. That is not game-over detection in the app, since the LLM, not the app, reacts. Passes.
18. Architecture: reuse tutorial tools, no duplication, no API/schema/endpoint change: FULLY (F3, B3). One possible friction: F3 step 1 refactors the 401 guard so both getLocAuth and recenter_map share it. That edits an existing function to avoid duplication, which is what staff want, but conflicts with the "touched lines" scoping and with "baseline text accepted as is". Small.
19. Naming/structure match tutorials: FULLY (recenter_map naming, schema file beside the others).
20. MRE scope: PARTLY, see section 3.
21. Use the course AGENTS.md: PARTLY. The repo contains only CLAUDE.md; E-C assumes AGENTS.md is supplied. Section 7 uses CLAUDE.md as a stand-in for Python checks. This depends on an input the owner has not confirmed.

## 3. What E-C adds that nobody asked for

Cut or reconsider:
- Disabling the picker while busy (F5, "new"): not in the design or the feedback. Cut it. It also causes the L1 problem (a stalled stream locks the whole screen).
- Whitespace-only text is not sendable (D6) and the "currently shown draft" rule for the role toggle: this is input validation nobody requested. Cut or keep only if the tutorial already does it.
- Capped, scrollable hint area (F5): defensible usability, but it is design the requirement did not ask for. Keep only if the hint is long in practice; otherwise cut.
- Making the root tap "dismiss-only and off the map" (F5): a bug fix for a problem the map introduces. Justified because without it the map tap opens the keyboard. Keep.
- Parsing and validating coordinates, "map must never jump to 0,0" (F3 step 2): lightweight, and tied to the design ("the phone checks the ticket and the coordinates"). Keep, but do not expand.
- F3b distinct "denied" text: justified by the design's denial path.
- F6 launch-time wipe: justified (Decision H, rejected 3). Keep.
- T4 (duplicate call id check), T7 (Face ID on a real device), T11, T12: extra test cases that exist partly to verify hardening-flavored concerns. T4 is justified because staff added tool calls and the schema forbids a second call with the same id. T7 and the "ticket stays usable in memory" analysis are not asked for by anyone; they are explanations of tutorial behavior. Treat as optional.
- F1a's temporary logging and a one-hour manual run: the professor asked for evidence only if sure. Keep, since it is the cheapest way to answer, but keep it clearly separate from the app.
- Sections 6 and 7's very long explanations of biometric behavior and legacy checklists: not wrong, but heavy for an MRE. Section 7's 14 Swift checks and 11 Python checks are process, not product scope. Fine as guidance, but consider trimming.
- Section 10 (Goldfish findings) is review history, not plan content. Remove from the plan the coding agent receives.
- L1-L6 and the baseline-offender lists: reporting is fine, but they are noise in the plan.
- D2 keeps the system blue dot: needed for "shows where you are". Fine.

## 4. Contradictions E-C does not declare

1. L3 versus "no default view": F2 says the area is a spinner until a fix or until recenter_map runs; L3 then says the map "appears centered on the city" after a first win. That means in the denied-permission case the user sees a map that moves to a city while no user location exists, but the plan also says the positioned flag is set by recenter_map. This is consistent but means the map's first-ever appearance can be the answer, which also reveals the city only after a win, so not a leak. Acceptable but the tester-facing result (nothing on screen for the entire game until a win) should be called out as the actual user experience.
2. "A single busy flag disables Send, Clear and the picker" (F5) versus owner decision 2 ("Clear starts a new game immediately"): if Clear is disabled while a send is running and a stalled stream (L1) never ends, the user cannot Clear. E-C accepts this in L1, but it contradicts the point of Clear as the only way out of a stuck game.
3. Hint rule versus "tool rounds append text to the same reply entry": the design's "reply replaces the clue" and the staff's "hints appear above the text box" are served, but the plan says pre-tool and post-tool text accumulate. After a win the hint will show the full closing text, possibly with earlier pre-tool text. Not a contradiction with the requirement, but it contradicts the design sentence and is not in the departures table.
4. Decision 7 versus the requirement doc: E-C quotes the requirement document ("invites the user to play again") and then overrides it (Departure 7). It flags this, so it is declared; but the 20 Questions rules still say "invite them to play again" (Q1), so the two games now behave inconsistently. Declared as a question, defaults to leaving it.
5. D5 keeps `get_weather_auth` and `get_loc_auth` registered, while the "Do-not-build" and "MRE" principles argue for minimum surface. Also the LLM may call those tools in a city game. Not a contradiction with the sources, but it leaves unexplained tool surface in the game prompt. Also F3 step 1 refactors the guard "used by getLocAuth", which means getLocAuth is touched, in tension with D5's "stay registered" as-is and the section 7 touched-line rule.
6. Section 0 says "Reasoning uses only our own call sites, public header documentation..."; yet section 5 states Swift-compiler consequences (main-actor default isolation) and section 6 describes platform Keychain/biometric behavior from "the tutorial's real code". These are partly marked UNVERIFIED, partly stated flatly. The tutorial code itself was not given as an input here; I can only note this as unverified from the three files.
7. Owner decision 6 versus Decision D wording "Face ID or passcode to read" and the design's Keychain "behind Face ID": declared as Departure 8. No undeclared conflict.
8. "No timers" versus the 20-minute request timeout and keep-alive pings (L1): E-C says the tutorial request already carries a 20-minute timeout. That is a timer. It is baseline, not new, but "Timers and any time limit" is on the do-not-build list. Small semantic clash; worth one sentence.
9. Section 0 "inputs given to the coding agent" lists design_specs.md and ui_requirements.md, which the owner's input set for this review does not include; the plan relies on files this review could not see. Cannot check coverage against them.
10. B1 says "No single transaction... harmless partial failure", then the Done-when requires all three row counts zero. If a partial failure happens mid-way, Clear would still report success; that is a reliability argument, but the section 8 list bans hardening, so this is consistent. No contradiction.

## Verdict

Mostly substantive-but-small: the plan covers the design and the feedback well, with the staff overrides handled correctly and honestly declared. The substantive remaining items are (a) F1 and the Clear-sentence guess (Q3, Q4) cannot be closed without the owner or professor, (b) the picker-disable and whitespace-rule additions break the "no unrequested hardening" rule, (c) the hint-accumulation behavior and the L3 dead-screen experience are not listed as departures, and (d) the legacy sweep leaves known baseline offenders against staff wording. Change first: cut the extra disabling and validation behavior (picker lock, whitespace rule), then add the hint and L3 behaviors to the section 1 departures table, then resolve Q3/Q4 with the owner before the coding agent starts.

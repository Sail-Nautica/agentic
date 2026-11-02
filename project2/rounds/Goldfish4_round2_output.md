# Goldfish4_round2: verbatim output

**Scope:** I read only the three input files. I could not check anything E-C cites from outside them (Goldfish 2 and 4 findings, db_schema.sql, the requirement doc, the tutorial code).

## 1. Coverage of the HW2 design document

Fully covered:
- **Rules, secret city, marker, welcome plus one hint (F4, F6):** the wipe then rules order, marker stripping, and give-up as plain text are all there.
- **Two phone tools (F3, F3b, section 6):** `get_auth` then `recenter_map`. The ticket and coordinate checks are included, and the 3-request win is the same as HW2.
- **Keychain ticket with a visible expiry (F7, section 6):** matches Decision D.
- **MapKit map (F5, section 5):** matches Decision G.
- **Clear keeps the map and the Keychain ticket (F6).**
- **Wipe at launch (F6):** matches Decision H, rejected option 3.
- **No back-end change:** E-C says so in B3, but it actually changes the server (row 6).

Overrides by staff feedback, handled correctly:
- **Pin, status row, Play Again, Ended, Decision C (game-over detection):** removed (departure 3, section 8, F4 "no game-state detection").
- **Timer and Retry, Decision E:** removed (departure 4, F6, section 8).
- **Server changes:** B1 and B2 (departure 6).

Partly covered or weakened:
- **Layout (Decision F):** the full-bleed map, compact bottom panel and floating Clear are replaced by the tutorial layout (departure 1). This was fixed by the owner, but the HW2 "map-dominant, only current hints show" intent is now carried by the transcript swap (owner decision 5).
- **Denial (HW2 item 4):** HW2 said cancelled sign-in or Face ID leads to denial. E-C covers sign-in failure (F3b) and says a failed Face ID check at launch is not a denial (section 9).
  - It never says what happens if Face ID is cancelled at save time, after a successful Google sign-in. F3b defines denial as "no ticket after the sheet closes". If the ticket stays in memory, that cancelled Face ID would not be a denial.
- **Face ID on every win:** E-C drops it when a valid ticket is in memory (departure 5). This is the biggest departure that staff did not ask for, and it is only a "default, please confirm".
  - The effect is narrow: with a 3-minute ticket, Face ID is skipped only on reuse within the lifetime.
  - If the original assignment says each retrieval needs biometrics, this is a requirement failure. It should be confirmed before building, not defaulted.
- **After a give-up:** HW2 told the user to tap Clear. F4 says only "reveal the city". Nothing says what the user does next, and T10 tests only the text.

Not covered:
- **HW2 known limits:** one tester at a time, the LLM favouring the same cities, and the secret depending on LLM obedience are not restated. This is harmless.
- **Error recovery in HW2:** "one message, one Retry, Send disabled" is gone. That is correct per staff.

Missing from the section 1 departures table:
- **State machine:** the HW2 states Starting, Ready, Sending, Error and Clearing are replaced by one busy flag. Only "Ended" is listed.
- **Added screen elements:** picker, 20 Questions, role toggle and transcript swap appear only in section 0. Row 1 says only "tutorial layout".
- **Face ID as denial trigger:** this appears only in section 9 and Q4.
- **Give-up wording:** the "tap Clear" instruction was dropped.
- **Per-round fresh markers (D6):** this changes Decision B's "city stays fixed" and is not in the table.
- **Small change (same source):** error display moves to the tutorial alert (D7), replacing the HW2 single message plus Retry.

## 2. Staff feedback, item by item

**Professor's list**
- **Hints above the text box:** fully (F5).
- **Map centered on the user at launch, no default view:** mostly (F2, owner decision 4, which is fixed).
  - The user first sees a progress indicator, not a map.
  - With location permission denied or no fix, there is no map at all until a `recenter_map` call (Q5). That is neither "map upon launch" nor a default view.
- **No pin:** fully (section 5 rejects it, section 8 forbids it). The system location dot (D2) is allowed.
- **No Play Again:** fully (section 8).
- **No status row:** fully. The stale-hint behavior in F5 is not a status row.
- **Timer and Retry:** fully (section 8, F6).
- **"Clear deletes calls and turns but not stored tool schemas" (cut off):** partly (B1, Q3).
  - E-C guesses "also delete the tools row" and asks the owner to check with the professor.
  - The guess is low risk: the tools row is rewritten on each send (T7 checks this), so it is harmless either way.
- **No timer ending the game:** fully.
- **Stale sign-in token:** fully in design (F1a evidence, F1b conditional fix). Two gaps:
  - "Done when" asks for a recorded run, not the coding-tool output the professor asked to see.
  - The run needs a person to do the Google sign-in and wait over an hour.
- **How to recenter the map:** fully (section 5, F3).
- **Legacy patterns:** fully for new and touched Swift code (section 7), with the baseline risk stated. See sections 3 and 4 for gaps.

**Course page**
- **Feed the current schema (Step 0):** partly. The reading is a guess (Q3).
- **Adapt llmclear (B1):** fully.
- **Tunable ticket lifetime (B2):** fully.
- **Map recentered on a given latitude and longitude, separate from the auth path:** fully (section 5 is separate from section 6).
- **Map centered on launch:** see above, mostly.
- **No Give Up, Play Again, status line or pin:** fully.
- **No game-over detection:** fully. F3 says the tool "never mentions a game".
- **Tutorial structure, tool reuse, no duplication, no API, format or schema change, no new endpoints:** fully (F3 shares the invalid-ticket guard, B3).
- **Use the course AGENTS.md:** partly. E-C applies its rules in section 7 but never says the coding agent is given the file.
- **MRE scope:** mostly. See section 3.

## 3. Things E-C adds that nobody asked for

Cut or shrink:
- **D6 plus "invite another round" plus T6 and T8:** this is a new multi-round design.
  - It creates the stacked-marker problem, the call-order tie, and two extra tests.
  - Staff said "interactions are by NLP", which does not require an in-conversation replay.
  - Cut it, or follow the give-up pattern and tell the user to tap Clear.
- **F6 extras:** "removes the baseline's stale-error and half-reset behavior", and Clear also emptying both drafts. This is unrequested bug fixing and breaks the "every changed line traces to the request" rule.
- **F4 "call `get_auth` once and retry on an invalid ticket":** this is reliability hardening. It is cheap, but unrequested. Cut it, or accept the baseline 401 text as it is.
- **Section 10:** ten questions, mostly "non-blocking", plus an option to ask the professor. Q2 and Q8 are out of scope. Trim to the blocking items (Face ID, the cut-off sentence, no-permission behavior).

Keep, but justify:
- **Capped, scrollable hint (F5):** needed so the text box stays on screen. Keep.
- **Picker disabled while busy (F5, "new"):** needed only because the owner kept the picker. Acceptable.
- **Coordinate validation (F3):** HW2 asked for it. Keep.
- **Duplicate call-id risk and test T4 (section 2):** reasonable verification, not hardening.

## 4. Undeclared contradictions

- **Fixed or open:** owner decision 2 (Clear starts immediately) and departure 7 and section 8 treat "no confirmation" as settled. Q1 asks the owner again.
- **"Touched lines only" has no definition.** F2 edits `LocManager.startUpdates`, which E-C lists as a do/catch and print offender. F3b edits `getAuth`, a continuation offender. F5 touches views with deprecated styling. The line-versus-function rule changes how much legacy code ships.
- **Staff's literal legacy list:** it includes type assertions, and E-C reports baseline `as?` in several places and leaves them. The owner fixed this scope, so I am only flagging that the staff wording risks an automatic deduction.
- **No Python legacy check:** the professor warned about "mixed-language" legacy code. Section 7 has Swift checks only, plus one Python delete rule.
- **No timeout, but Send, Clear and the picker are disabled while busy.** A stalled stream leaves Clear disabled, and only a relaunch recovers. This follows from the staff-mandated removal of timers and from the kept mutual-disable rule. E-C does not acknowledge it.
- **Unmarked claim:** "the project defaults to main-actor isolation" (section 5) is not marked UNVERIFIED, though D5 and check 3 rely on it. This breaks E-C's own marking rule.
- **Smaller points:**
  - F1's file list names `Ticket` and `Rein.addAgent`, but the body only edits `SigninView`.
  - The section 3 diagram draws the view model calling the clear handler directly, while the diagram's `Rein` box lists the clear call.
  - Section 5 rejects "any annotation" while D2 keeps the location dot.

## Verdict

Mostly small points. E-C covers the staff feedback and nearly all of the HW2 design. The substantive items are few:
1. The Face ID reuse departure and the unstated save-time cancel case.
2. D6 and the extra F6 cleanups, which are unrequested scope.
3. An incomplete departures table.

Change first: settle the Face ID and denial behavior, then cut D6, T6, T8 and the F6 extras, then finish the section 1 table.

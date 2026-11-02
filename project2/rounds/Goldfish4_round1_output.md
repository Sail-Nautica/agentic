# Goldfish4_round1: verbatim output

E-C v2 PM coverage review. Inputs read: design doc, staff feedback, E-C v2. No code read, no files written. Where E-C claims something about the baseline code, I could not check it, so I mark it as an E-C assertion.

Overall: E-C covers the design as overridden by staff reasonably well. The problems are (a) a legacy-pattern scope decision that likely loses points, (b) a stale-token fix sequenced before any evidence, (c) several unrequested UI extras, and (d) several quiet departures from the design.

## 1. Coverage of the design document

Overrides by staff are marked (S). "Handled correctly" means E-C removes or changes the item the way staff require.

- **One-screen game, map shows where you are.** Fully. F2, F5, D2 (location dot).
- **Floating Clear button, full-bleed map, compact bottom panel (Decision F).** Not covered, and not declared as an override. F5 is a plain vertical stack of picker, map, hint and input row, with Clear inside the input row. Decision F explicitly rejected "Clear beside Send". The owner's "keep tutorial extras" decision explains most of this, but E-C never says it departs from Decision F.
- **Clue panel above the guess box (S: "above, not side by side").** Fully. F5. Handled correctly.
- **Status line (S: removed).** Handled correctly. The do-not-build list (section 7) forbids it, and errors go to the existing alert (D7).
- **Pin (S: removed).** Handled correctly. Section 4 rejects annotations.
- **Map starts at the user's location (S: no default view, no later move).** Mostly. F2 and F5 use a spinner, then the map once, with later updates ignored. Two weaknesses:
  - The "cached last-known location" shortcut can centre the map on a stale location, which is not "current location".
  - The wording is ambiguous about whether the real first fix still moves the camera when a cached one was used. F2 says "moves exactly once"; section 4 says "assigned only twice".
- **Game states Starting, Ready, Sending, Error, Ended, Clearing (S: no Ended).** Handled correctly. No game-state machine is built (F4, section 7).
- **Network loop with 30 s limit and three Retry kinds (S: removed).** Handled correctly. Section 7 forbids both.
  - Wording clash: section 7 forbids "Retry, in any form", while F6 says "Pressing Clear again is the retry".
  - Side effect: a failed guess leaves no Retry and, per F5, the hint is already blank (see section 4, item 8).
- **Starting: wipe, then send rules plus a short "Begin" (Decision H: wipe at launch).** Partly.
  - Wipe at launch: covered (F6).
  - "Begin": reversed. D1 sends system-only rules, with "Begin" only as a contingency (F4, Q5). This is declared as a default, but it does not say it overrides the design.
- **Hidden city marker, stored and replayed by the server, stripped by the app (Decision B).** Partly.
  - F4 covers the rules text and the "no marker in first hint" check.
  - Gap: "the marker stripper in Rein" is named as if it already exists. No step says to build or change it for the streaming case, where a half-arrived marker could flash on screen.
  - Gap: nothing tests markers from a second round (D6).
- **Guessing: reply replaces the clue; give-up is plain text.** Fully. F4 and F5.
- **Winning: get_auth, then recenter_map, then closing text (Decision A).** Mostly.
  - The sequence is covered by F3, F4 and section 5.
  - The tool is never named. The design says `recenter_map`; E-C says "the recenter tool" everywhere. Naming must match tutorial conventions, so this is a real gap.
  - Ticket and coordinate checks are covered by F3, including a range check so the map never jumps to 0,0.
- **Face ID on read-back of the ticket.** Partly, with a quiet change. The design saves behind Face ID and reads back with Face ID each win. D4 does the biometric check "at launch and at ticket save, not on every get_auth" and reuses the in-memory ticket. D4 says this is "as in HW2", which is not accurate.
- **Ticket expiry kept as a visible Keychain attribute (Decision D).** Not mentioned. Likely tutorial behaviour, but E-C should say so.
- **Denial: map does not move, city is revealed in text.** Mostly. Section 5 and F4. The issue is that denial returns the same 401 text as an invalid ticket (see section 4, item 6).
- **Errors: one message.** Covered by D7, the existing alert.
- **Clear: confirmation, wipe, new game, map and ticket stay.** Partly.
  - Wipe, new game, and keeping the map and ticket: covered (B1, F6).
  - Confirmation: dropped (Q2). The reasoning is plausible, but see section 3 on inconsistent standards.
- **Decision C (watch tool calls to detect game over) (S: removed).** Handled correctly. F4 and F3 forbid game-state detection, and the tool description never mentions a game.
- **Decision E (timer and retry) (S: removed).** Handled correctly.
- **Decision G (MapKit).** Implied only. Section 4 says "Map view bound to a camera position" but never names MapKit. Fine in practice.
- **Decision H (no back-end change) (S: llmclear and ticket lifetime must change).** Handled correctly. B1, B2 and B3 limit the diff to `handlers.py` and add no endpoints.
- **Known limits (secret enforced only by LLM obedience, one tester at a time, same few cities).** Not restated, which is harmless.
  - The 3-minute ticket becomes a tunable default of 180 s (B2), which matches the staff feedback.

## 2. Staff feedback, item by item

- **Hints above the text box.** Fully. F5.
- **Map centred at launch, no default view.** Partly. F2 and F5 are right in intent. The cached-location shortcut and the ambiguity in section 1 weaken it.
- **No pin.** Fully. Section 4 and section 7.
- **No Play again.** Fully. Section 7. Note that F4 has the LLM "invite another round" and D6 allows a fresh marker. That is a reasonable natural-language replacement, but it is untested (F9 has no second-round scenario).
- **No status row.** Fully.
- **No timer, Retry or 30 s limit.** Fully.
- **"Clear deletes calls and turns but not stored tool schemas" (sentence cut off).** Partly.
  - B1 deletes calls, turns and the tools row, which is a plausible reading.
  - E-C never states that the professor's sentence is truncated and that its reading is a guess. That should be a question to the owner.
  - The claim "dropping the tools row is safe because the fresh-turn path re-sends and upserts schemas" is an unchecked E-C assertion. F9 does not explicitly test that the first turn after Clear gets its tools back.
- **"Ended after … a timer".** Fully. There is no Ended and no timer.
- **SigninView stale-token claim ("show me your Claude output just for this bug").** Partly.
  - E-C is honest that it cannot prove the claim from public documentation, and it plans an evidence run.
  - F1 still rewrites the code first, and its reasoning rests on the very claim it marks UNVERIFIED. The evidence should come before the fix.
  - The evidence needs a run more than an hour after the last sign-in (Q8) and is not produced yet, so the professor's request is only planned.
  - The possible new wrapper around a callback API adds a legacy-style pattern.
- **"How to recenter the map?"** Fully. Section 4 and F3 explain a single camera value, assigned inside an animation, by the tool.
- **Legacy patterns (automatic deductions).** Partly, and this is the weakest point.
  - The checklist covers the right rules.
  - Decision 3 sweeps only new and touched code and merely reports baseline offenders: `do/catch`, `withUnsafeContinuation` helpers, `foregroundColor` and `cornerRadius`, `print`, a static mutable `isThinking`, many manual type assertions.
  - Staff say "presence of these legacy patterns in your code will lead to automatic point deductions", and the graded submission includes that baseline code.
  - Three checklist rows say only "Check" (multi-line if/else, comments, naming). Those are placeholders, not results.
  - D5 keeps Swift language mode 5.0, which sits awkwardly with "Swift 6.2 default MainActor isolation" and the legacy rules.
- **Backend: feed the LLM the current schema.** Partly. Step 0 and Q7 plan it, but the schema has not been obtained.
  - E-C asserts "the definition is not in the repo" and lists the expected tables as guesses. A schema has to be created somewhere, so this claim should be challenged.
  - Q7 is marked blocking.
- **Backend: adapt llmclear.** Addressed by B1 (see the truncated-sentence caveat above).
- **Backend: ticket lifetime tunable.** Fully. B2.
- **Frontend: how the map is actually recentered.** Fully. Section 4 and F3.
- **Frontend: no Give Up, Play Again, status line or pin.** Fully.
- **No game-over detection; the move-map tool only moves the map.** Fully. F3 and F4.
- **Architecture: match tutorial structure and naming, reuse tutorial tools, avoid duplication.** Mostly.
  - F3 reuses the tool machinery and shares the ticket guard with `getLocAuth`.
  - The new tool's name is unspecified (see section 1).
  - Using the course AGENTS.md is implied by the checklist, not stated as a step.
- **No back-end API, data format or schema change; no new endpoints.** Fully. B3.
- **MRE scope, no hardening.** Mostly. See the items to cut in section 3.

## 3. Additions neither document asks for

Cut or reduce:
- **Transcript toggle in the toolbar, with an in-place swap over the map.**
  - This is the largest unrequested addition: new UI, and new behaviour on every state it touches.
  - It exists only because the tutorial transcript conflicts with "only current hints show" (Q1).
  - The simplest fix is to drop the transcript from the main screen, which Q1 already lists as an alternative.
  - It also drives the whole "avoid a second sheet" discussion.
  - The owner decision "keep extras" explains this, but E-C chose the expensive way to keep them.
- **Cached last-known location for an instant first frame.** This is an optimisation with a correctness risk (stale centre). Cut it.
- **Single database transaction in B1.** This is reliability hardening unless the existing handlers already use transactions. Cut it or justify it as matching existing style.
- **Hint area height cap and scrolling.** It is a small robustness measure. Justified if kept to one line of intent; otherwise cut.
- **Dismiss-only tap and "keep it off the map".** Small, but only needed if the transcript or map interaction conflicts. It follows from keeping a map on screen, so it is acceptable.
- **F9 scenario 10 ("each reachable runner") and real-device testing.** Heavy for an MRE (D10, Q9). Reduce it to one working runner plus the simulator.
- **Section 0 "Opaque Dependencies correction".** It is process history, not plan content. Trim it to the single rule: do not cite library source.

Justified:
- **Step 0 and B1 to B3.** Staff-requested.
- **F1.** Professor-requested, though the sequencing is wrong.
- **F3 coordinate range check.** The design asks the phone to check coordinates.
- **Spinner before the first fix.** It avoids a default view.
- **Keeping the tutorial tools `get_loc_auth` and `get_weather_auth` (D8).** Staff require reuse.
- **Picker and mutual-disable rules.** These come from the UI requirements document, which I did not receive. E-C cites it, so I accept this only on E-C's word.
- **Role-toggle Send gating.** It is a small consequence of keeping the toggle. Acceptable.
- **F7 permission text.** Needed for the permission prompt.
- **D6 fresh marker per round.** It is the natural-language replacement for Play again. Keep it, but add a test.

## 4. Contradictions E-C does not declare

1. **Inconsistent standard on "additions".** E-C refuses a one-line Clear confirmation (design feature) because "the only addition is the map", yet adds a transcript toolbar button, a swap view, a dismiss-only tap, a hint cap and draft-gated Send.
2. **Face ID.** D4 claims the tutorial approach is accepted "as in HW2". HW2 reads the ticket back with Face ID on each win. E-C reads it from memory, and it also adds a biometric prompt at launch, which the design never had.
3. **"Begin".** The design sends "Begin" with the rules. E-C does not, and does not say it overrides the design.
4. **Decision F.** E-C reintroduces "Clear beside Send" in the input row, which the design rejected, without saying so.
5. **"Retry, in any form" is forbidden (section 7), but F6 calls pressing Clear again "the retry".** This is wording, but it will confuse the implementer.
6. **Denial versus invalid ticket.**
   - Section 5 says denial returns the "existing 401 text", the same text as for a wrong ticket.
   - Section 5's diagram says on a 401 "LLM may call get_auth again".
   - The rules say to reveal the city on denial.
   - The LLM cannot tell denial from an invalid ticket, so it may loop on sign-in sheets. The design said `get_auth` reports "denied".
7. **F1.** The plan states it relies on nothing unverified, yet it changes sign-in code to fix a bug it marks UNVERIFIED, and it plans to produce the evidence only afterwards.
8. **F5 hint behaviour.**
   - It says "no new state" and "blank until the first token". That needs a placeholder entry for the new reply, or new state.
   - The hint is blank as soon as the user sends, because the user's message becomes the last entry. If the send then fails, the clue is gone with no Retry.
   - The last entry can also be a tool message during `get_auth`, which leaves the hint undefined.
9. **F5 single busy flag.** It says to "reuse the single busy flag, with the spinner on the button that was tapped". One flag cannot say which button was tapped.
10. **F2 camera.** "Cached location used at launch" and "camera moves exactly once" conflict when a real fix follows.
11. **Section 0 versus F1.** "Nothing below relies on [the withdrawn reading]" is stated, but the bug's reality is assumed by F1's design.
12. **Legacy scope versus staff wording.** Decision 3 reports offenders as "baseline", but staff penalise "your code".

## Verdict

The remaining critique is substantive, not nitpicks. First change: widen the legacy sweep to everything that will be graded, then cut the unrequested UI extras (transcript swap, cached location, transaction), fix the denial signal, and reorder F1 to run the evidence before changing the code.

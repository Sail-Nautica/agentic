# Goldfish 3 critique, round 2 (on E-B v3 + design_specs + E-A) — condensed transcription of the agent's report

Verdict: remaining critique mostly minor, with two small substantive items.

## Coverage
Covered: city secrecy via marker, recenter + play again, token flow, no end-game tool, denial reveal, E-A deviations 2, 7, 9 declared. Not stated: what happens to the Keychain ticket on Clear (presumably stays); Return = Send (not contradicted).
Undeclared contradiction (small): section 5 says "Correct!" ends when recenter_map finishes, deviation 11 says it persists over legs 2 and 3. Pick one.
Camera "follows the user" is a behavior E-A never specified (harmless).

## Substantive items
- Ticket crosses the LLM as plain text; a weak model that mangles the 64-char hex gets a 401, whose text says call get_auth again, which returns the same memoized ticket: possible loop to the leg cap. Fix: say "same ticket, copy it exactly" in the repeat get_auth result and the 401.
- Retry after a tool call: is it a new user action? If the memo clears, a resumed recenter_map fails the ticket check and forces a second Face ID, contradicting "no second Face ID". Define Retry as the same action.

## Moderate / minor
- Within-turn call order (idx restarts at 0) makes the replay read like parallel calls; model-confusion risk should be listed under accepted risks.
- The "one percent" orphan figure has no basis; drop it.
- Retry of a plain guess shares the orphan limit (client cannot know if a tool-call row was stored).
- A spurious get_auth on a wrong guess ends the game early (note in section 3/9).
- Ticket may expire during a slow turn (minor); two graders on the same build clobber each other (declared Q5); Return key not restated; Reason string not restated.

## Over-engineering (option, product owner's call)
Three-way Retry + resume by turn ID + per-action memo + leg cap with fresh budget is the heaviest part; simplest alternative: any failure after a tool call = Clear-and-start-over, keeping only two Retry behaviors. Cost: drops E-A's "Retry resends only the final request".

## Constraint violations
None. Compatibility notes: a tutorial front end sharing the app ID would replace this game's tool row and be hit by the start wipe (declared). The Rein.llmTools signature change is the one place a structure grader might mark down; keep its name and general shape.

## Orchestrator disposition
Adopted (applied directly to the final E-B): Retry = same user action (memo survives); repeat get_auth and 401 wording; single status-text rule; three added accepted risks; "one percent" removed; Clear keeps the Keychain ticket. Not adopted: replacing resume-by-turn-ID with Clear (keeps E-A's final-request promise; owner chose Q3 on that basis).

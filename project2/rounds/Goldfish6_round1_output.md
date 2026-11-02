# Goldfish6_round1: verbatim output

Review of E-C_v7.md (read only that file; no code, no other files).

**1. Ambiguities and gaps (question I would ask)**
- Pass/fail for F1 is a person-run, hour-long manual test. Who owns it, and may the coding agent finish the rest without it? (Q4 says it is "blocking only for closing F1", but nothing says the other steps may proceed.)
- B1: how does the handler learn the app ID, and is "the app's calls (found through its turns)" a subquery delete or two passes? Only the order is specified. Fine for an agent to guess, but say "subquery on turn IDs".
- B2: what is the variable's name? The plan gives the pattern but not the name. Test steps ("restart with a 20 second setting") need it. Name it.
- F2/F5: where does the camera type live and what is it exactly? "A map camera position" is vague. Question: is it a SwiftUI map-camera value, and what is the initial value before the first fix (the progress indicator is shown, so presumably none)? Say so.
- F2: how does `startUpdates` know a fix is the "first"? Only the flag is described, but is the camera set from the fix itself with city-level zoom? State the zoom distance (D2 says "city level" but gives no number).
- F3: argument format. Three strings, but the schema file has no stated content for descriptions or "required" fields. Does the model get a hint to pass numbers as plain decimals? L11 hints at the "48.85 N" problem, but the schema description is where to prevent it. Add one sentence.
- F3: the shared guard. What is its name and where does it live (Toolbox or Ticket)? The agent must invent it. Acceptable, but the plan should say it is a function in `Toolbox.swift` returning either the ticket-valid result or the 401 sentence.
- F4: the actual rules text is not given, only its gist. The marker string itself ("hidden marker") is never named. Question: is the marker the baseline one already in the code, and should the new rules reuse it exactly? If the agent writes a different marker, the stripper breaks.
- F4: do the city rules need to give the city's coordinates as degrees to the model? The model is trusted to know them (L11). Confirm that is intended.
- F5: toolbar button icon/label and the transcript's relationship to the existing `ChatView`/`ConversationView` are unclear. Which already exists and which is new? The agent must read code to know whether `ChatView` is replaced.
- F5: "capped height" has no value. Minor, but it is a guess.
- F6: what exactly does the busy check at launch do if the flag is set (skip silently)? Probably yes; say so.
- F1: "the Google user's refresh call" and the restore call are named only descriptively. The agent must find them in the SDK headers. The plan says to read headers but no path is given, and the plan forbids reading third-party source (the section 0 rule). Clarify that headers in the package are allowed.
- Inputs: section 0 says AGENTS.md is "supplied separately" and may not exist. If it is absent the agent falls back to CLAUDE.md (Python checks say so, Swift checks do not). Say which governs Swift.
- The plan says "the input files it lists" include `staff_feedback.md`, `design_specs.md`, `ui_requirements.md`, but the plan cites their content only secondhand. If those files differ from what the plan paraphrases, who wins? Section 0 says staff feedback over HW2, but nothing says plan over staff feedback.

**2. Ordering and dependency problems**
- F1a requires a frozen baseline build with logging, built before any other change on that simulator, but the plan lists it as step F1 after B and mixed with F2-F6. The agent must do this first (or at least before other changes ship). Move F1a to "first, before any other front-end work".
- F1b changes `SigninView.swift`, which T5, T6, T3 all exercise. Tests T3/T5/T6 should run after F1 closes, or the results are not final. The plan does not say so.
- F4 (rules) depends on F3 (tool name and arguments); F5 (hint area) depends on the marker stripper in F4; F6 depends on B1 (`llmclear` must delete correctly before launch-time wipe is useful). The plan's listed order (B1, B2, B3, F1...F6) mostly works, but F3 must come before F4 and this is not stated.
- F2 and F5 both touch map state and the progress indicator; F5 needs F2's flag and camera. State F2 before F5.
- T5 requires B2 deployed on the server and the server restarted; T9 and T10 require B1. Fine, but no test-readiness gate says "back end deployed first". Also the back end is on Ubuntu while dev is local: the plan never says how the back end is run for tests (local or the real host, and whether tests write to the live database; B1 already hints at "live database").
- B3's check ("after the first send from the new app") needs F3's schema file built and a working app, so B3 is not closable in the back-end group; it closes after F3.

**3. Too vague or too large**
- F5 is the biggest: layout, map swap, hint logic, busy flag, picker disable, tap handling, and five view files in one step. Split into: (a) layout and picker/busy disable; (b) map area with progress and camera; (c) hint computation and stripper interplay; (d) transcript swap and tap behavior.
- F1 is a research task plus a conditional fix plus human-run evidence. Treat as a separate track and not part of the first coding pass.
- F4 mixes prompt authoring and a "verify the stripper" task. Split: write rules text; confirm existing stripper handles the marker (no code change expected). The plan never says whether the stripper needs code changes; it reads as no.
- F9 has 13+ tests with sample counts that depend on a live LLM. For an MRE this is heavy. Tag which are must-run (T1, T2, T9, T10) versus nice-to-have (T4, T7, T11, T12b, T13).
- F7/F8 housekeeping and the sweep are post-hoc checks; make the sweep one final step with a checklist output, and say who performs it (the agent greps its own diff).

**4. Easy to misread**
- "Clear starts a new game immediately" versus F6 where launch also wipes: an agent could add wiping to every `ContentView` appearance, causing double wipes on view rebuild. The plan guards this but only in prose; stress "once per launch, via the existing launch task."
- "Touched lines only" sweep versus "do not edit adjacent code": an agent may "clean up" baseline offenders it sees, expanding the diff, or conversely leave new code with `as?`. The rule is stated but depends on a per-line judgment; the extracted guard in `getLocAuth` could tempt a rewrite of the whole function.
- Section 1 row 7 says the requirements document's "play again" wording is changed. An agent may implement a Play Again prompt per the requirements doc. Section 8 forbids it, but the conflict with `ui_requirements.md` (an input) will confuse the agent. Say plainly in the first lines: where inputs conflict with this plan, this plan wins.
- "Hint shows the newest non-empty assistant text": an agent may add a new stored hint variable (the plan says no new stored state). Reinforce it is a computed value.
- D1: "rules as system message with no user message" can fail on some providers; the contingency is test-driven, which could cause back-and-forth. Decide which runner is the test runner up front (Q5 is "non-blocking" but T1 depends on it).
- "Face ID happens at launch": an agent might add explicit biometric calls. The plan says tutorial behavior; make "write no biometric code" explicit.
- "Never mentions a game" in the tool description: easy to violate by copying `get_weather_auth.json` wording.
- 0,0 rejection versus "no extra plausibility checks": the 0,0 check is a plausibility check by another name. Fine, but an agent may remove it as hardening. The plan justifies it; keep.
- Python mixed tabs/spaces: an agent's edit tool may normalize whitespace and make the diff huge. The plan warns; good.

**5. Self-consistency of files and types**
- Mostly consistent. `LocManagerViewModel`, `LocManager.startUpdates`, `Toolbox`, `Rein`, `AppViewModel`, `ContentView`, `SigninView`, `handlers.py` recur coherently.
- Mismatches and loose ends:
  - Section 0 says the agent receives `db_schema.sql`, `staff_feedback.md`, `design_specs.md`, `ui_requirements.md`, but the Swift and Python source files the plan edits are not listed as inputs. "The input files it lists" means the agent has no stated access to the code; confirm the repo is provided.
  - `TICKET_MAX_LIFETIME` is named in B2 as `handlers.TICKET_MAX_LIFETIME`, while the env variable has no name.
  - F5 lists `SubmitButton`, `ClearButton`, `RoleToggleButton`, `ChatView`, `ConversationView` as touched but only describes changes to the busy flag, picker, and tap handling; which of them actually change is unclear.
  - `Game.rules`, `Game` type and picker are mentioned without saying which file holds them.
  - L-numbering skips (L13 after L15) and section 10 references "Goldfish 5 round 1" with no context; harmless noise for an implementer.
  - Section 1 row 5 says one busy flag `isBusy`, F5 says "single busy flag"; consistent.
  - Section 2 point 5 and Q3 call db_schema.sql handling a "guess"; B1's tools-row delete rides on a second guess. Two guesses carry a back-end behavior (deleting the tools row); a wrong guess is cheap but should be reversible by one line. Note it.
  - Step 0 labelled "done" is not a step the agent performs.

**Verdict:** Not quite ready; it is close. Blockers for a clean first pass: no named test runner, no env-var name, no stated precedence over the input docs, and F5 is too big. What I would change first: add a short "decisions the agent must not reopen" header (plan wins over input docs; marker string reused as in baseline; env var name; zoom level), then split F5 and move F1a to the front as its own human-driven track.

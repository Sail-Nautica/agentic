# Goldfish5_round1: verbatim output

REVIEW OF E-C v5 (plan read only; no other files touched, no code written)

## 1. Missed assumptions

- **The database is assumed to be the only place a conversation lives.** B1 and T9/T10 treat "wipe the tables" as "game gone." If any runner keeps its own session or history (CLI-style runners often do), or the server caches anything per app in memory, a wiped game can still leak into the next one. Consequence: "the city stays fixed" and "fresh game" fail on that runner while the row counts all read zero. Add a check that a new game after Clear cannot recall the old city.
- **The 401 text and the "tools row has no dependants" claim are accepted without being shown.** The plan relies on the baseline invalid-ticket sentence to steer the LLM, but never quotes it. Consequence: if it just says "call get_auth again," a ticket that expires between get_auth and recenter_map (or an LLM that garbles a long ticket string) becomes a get_auth/recenter_map loop. The plan has no loop cap and no retry rule.
- **Nothing is said about whether the tool-call loop has a limit.** Denial, bad coordinates and 401 all depend on the LLM choosing to stop. Consequence: one stubborn model gives an endless sign-in-sheet loop with Send, Clear and the picker all locked (L1), so only a relaunch recovers.
- **The ticket lifetime is 180s, but the plan keeps Face ID at launch.** Almost any ticket saved in the previous session is expired by the next launch. Consequence: every launch shows a biometric prompt (competing with the location prompt and the launch-time wipe/rules request) to load a ticket that is already useless. I am not re-arguing the decision; the issue is that T1 never tests the three prompts together.
- **Add versus update in the Keychain is never examined.** After the first run an item already exists, so every later save is a replace, not a first add. The plan only reasons about the first save. Consequence: "save failed, sign in again on relaunch" alerts may appear on every re-sign-in (T5), and T5 does not check the save outcome.
- **"Face ID at save" is asserted as owner behavior, but an add of a protected item normally does not prompt; the prompt comes on read or update.** The plan admits it cannot verify this. Consequence: decision 6's "prompt at save" may simply not happen on the first save, so T7 may test a path that is never reached.
- **The first location fix may be a stale or coarse one.** The plan says "center at first fix" without noting that iOS often delivers a cached or approximate fix first. Consequence: the map can open on the wrong part of the city or the wrong spot, and it never corrects (by design).
- **All the UNVERIFIED items are left as open claims instead of build-time checks.** Examples: main-actor behavior, silent-restore refreshing tokens, keep-alive pings versus the 20 minute timeout. A coding agent can settle most of these by building and running. Consequence: they stay unresolved. Also, the checklist bans main-actor attributes, so if the concurrency claim turns out false the agent has no sanctioned fix.
- **Two devices on one bundle ID (L7) is tied to the test plan.** D8 uses a simulator and possibly a real device with the same bundle ID. Since launch now wipes, launching on the device wipes the simulator's game. Consequence: confusing test results if both are used in one session.
- **The simulator's default location is "none."** T1 and F2 say "simulated location" but never say it must be set, else the progress indicator spins forever and looks like a bug.

## 2. Edge cases not handled

- **The launch wipe is now the very first thing the app does, so the baseline "empty alert" bug (acknowledged) becomes the most common failure.** Server down or slow at launch: wipe fails, rules still sent, error text blanked, alert shows empty (or a second alert is dropped because one is already up, e.g. the Face ID failure alert). Consequence: the most likely first-run failure gives a blank, unhelpful alert.
- **Wipe racing an in-flight server turn.** Relaunching (or Clear after a force-quit) while the server is still finishing a previous turn can let the old turn insert rows after the deletes, or fail the turn-delete on the foreign key with no cascade. Consequence: orphan rows, or a wipe that errors, then a new game stacked on leftovers. Not covered because "no transaction" reasoning only considers the wipe alone.
- **"Partial failure is harmless" is overstated.** If calls are deleted but turns survive, the next history replay has tool calls with no results, which many providers reject. It heals only because resetGame wipes again. Consequence: a failed wipe followed by the baseline "send rules anyway" can give a confusing second error.
- **Sign-in sheet dismissed by swipe.** F3b assumes "no ticket after the sheet closes" always happens, which needs the waiting call to resume on every dismissal path, not just a Cancel button. If it does not, the tool call hangs forever with the busy flag on. T6 only tests one way of cancelling.
- **Google sign-in app-switching or the app being suspended mid-stream.** The stream drops, the busy flag may stay on, and there is no timer to recover (L1). Worth stating alongside L1 rather than only "stalled stream."
- **Map and the equal-value case.** If the LLM's city happens to be the simulated location (or the user panned back to it), the "assign equal value does nothing" note means no visible move; T2's "map moves" cannot be judged. The tester cannot choose the city.
- **Wrong-but-valid coordinates.** The LLM may swap or sign-flip a city's coordinates; the plan only rejects non-numbers and out-of-range values. Consequence: the map flies somewhere plausible but wrong, and the check "map flew" still passes.
- **Coordinates as strings.** LLMs often add degree signs, "N/S", or "lat, lon" in one field. These return an error, which may start another loop.
- **After a win, the user keeps chatting.** The LLM can start a new city mid-conversation; the marker rule covers only the very first reply, so a new marker appearing later is stripped only if it is at the start of a reply. Mid-text it would show. Probably acceptable for an MRE, but the plan says nothing.
- **Role-toggle drafts.** With a system draft and a user draft held separately, "Send looks only at the shown draft" leaves the other draft untouched and unexplained; the plan does not say whether it is sent, kept or cleared.
- **Several system prompts at once on launch** (Face ID, location permission, error alert) are never sequenced or tested together.
- **Keyboard and the vertical layout.** A text box under a map and a capped hint area will squeeze the map to almost nothing on a small phone with the keyboard up; not mentioned.
- **The launch task may re-run.** If the view that owns it is rebuilt (rotation, scene change, the view swap), the wipe-and-rules start could fire again mid-game and erase it. The plan should require a single run per launch.

## 3. Technical errors or things that will not work as written

- **T11 is impossible as written.** It says "picker switch ... during a send," but section 1 item 14 and F5 disable the picker while a send runs. The test should assert that it is disabled.
- **T3 and T7 cannot be seen on the simulator.** "No new prompt" is invisible there because the simulator does not show Face ID; only "no sign-in sheet" is observable. T7 admits this; T3 does not.
- **F1 is internally inconsistent.** It says to start first because it needs over an hour, but the trigger needs a running game, and any rebuild during that hour kills the run (rebuilding replaces the running app). It must run on a frozen baseline build on its own simulator. Also artifact 3 ("the coding tool's own output for this bug") conflicts with a human driving the run.
- **F1b's fix is chosen before the evidence.** "Delete the branch that prefers the raw token" assumes the cause. If Google's restore call already refreshes, the "not reproduced" result from a single run is weak evidence (an hour-long run that happened to not hit the case).
- **F7 versus checklist item 11 contradict.** F7 says to change comments that become false; item 11 counts removed comment lines as zero. A rewritten comment shows as a removed line in the diff.
- **The shared guard in F3 touches `getLocAuth` lines** ("moves into a different statement" counts as touched under section 7), so the "touched lines only" rule pulls baseline offenders in that function into scope. The plan says what ships unchanged but not that this particular move creates touched lines.
- **Python mixed tabs and spaces:** Python rejects inconsistent mixing within one block, so "match the nearest line" must mean sibling lines in the same block, not just the nearest.
- **B2's done-when assumes the `addagent` response reports the lifetime.** If it reports only an expiry timestamp, the "reports about 20" check needs rewording.
- **"Send enabled only when ..." versus the busy-flag gap.** Between the wipe finishing and the rules send starting, one busy flag may drop briefly, so the mutual-disable rule can flicker open. Nitpick-level, but it contradicts the "holds, including during launch" claim.

## 4. "Done when" statements that cannot be checked as written

- **T6 "LLM does not repeat the same tool call after a denial"** and **T2/T8 "closing text tells the user to tap Clear"**: depend on model obedience; one run proves nothing either way. Define a number of runs and an accepted pass rate, or call them observations.
- **T13 "never visible in ten starts"**: ten samples cannot show "never." Also depends on the model putting the marker first. State it as a sample, not a guarantee.
- **B3 "a manual request ... gets a tool_calls event for it"**: nondeterministic. Check instead that the stored tools row contains the new schema.
- **T12 "previous hint stays and the alert shows"**: passes even if the alert is blank (known baseline issue), and the parse-failure variant says the opposite (error text becomes the hint). Two different outcomes under one label.
- **F5 "hint directly above the text box" and "transcript never shown with the map"**: fine by eye, but with a capped scrolling hint and a keyboard it cannot be confirmed on one screen size; name the device size.
- **F1 "or the report says not reproduced"**: always satisfiable, so the step cannot fail. Require the logged values to show the ticket really outlived the Google token's hour.
- **T5**: does not say that the sign-in must happen once, then 20+ seconds pass, then a second win occurs (which needs a Clear in between). As written, it is unclear how to get an expired ticket in one launch.
- **T4**: proves unique ids on one runner only; it should not be read as covering the schema risk.

## Verdict

The critique is substantive, not nitpicks: the biggest are the unprotected launch-wipe/failure path (empty alert, race with an unfinished turn), the unexplained tool-call loop and 401 text, the F1 sequencing, and test steps that are impossible (T11) or LLM-dependent. Change first: make launch/Clear failures show a real error and lock out re-runs of the launch task, quote the 401 text and add a hard cap on tool rounds, and rewrite F1 as a frozen-build run on its own simulator before fixing T11, T3, T5 and T12 so each can actually pass or fail.

# Goldfish7_round1: verbatim output

QA AUDIT OF E-D_v1.md (plain English, no code)

1. MISCLASSIFICATIONS

Static items that really depend on runtime, a person, or timing:
- S05/S06 (B2 lifetime): the plan itself admits the proof needs "the right file deployed and the restart read the variable". That is runtime. It is half-handled by E-B2, but the S06 premise "worker inherits the parent's environment" is stated as a proved fact. It is an assumption. Move it to empirical only. Keep the "formula line untouched" part static.
- S11/S12 (camera writers "fire at most once, late fix can't overwrite"): this is an event-ordering claim about CoreLocation and a tool call racing. The plan's own caveat (BB10: Swift language mode 5, so isolation errors are only warnings) means the "main actor, no suspension point" premise is not compiler-enforced. Reading code can show intent, not ordering. Keep a static check for "exactly two camera writes", but treat the ordering claim as empirical (E-NODEFAULT does partly cover it; the "tool then fix" order is never induced).
- S14/S15 "PASS": the plan says "nan"/"inf" validity depends on a system function it admits it cannot verify. That is an unproven premise. The conclusion "only valid pairs reach the camera" is therefore not proved. Make it empirical only for that row (the plan does, in E-F3) and downgrade S15's verdict to conditional.
- S18 (stripper trace): the trace of the code is fine statically. But the table's last rows conclude "FAIL of the model, not the code". That is an LLM behavior outcome, correctly pushed to E-LEAK. The "PASS" label should be limited to the code claim only; as written it reads as if the leak requirement passes.
- S23 reactivity proof: relies on how the observation framework treats an "ignored" property. This is third-party framework behavior the plan says it did not read. Premise unproven. Needs a one-time visual check (E-HINT partially covers it, but E-HINT never tests the whitespace-only row).
- S24 "dismiss tap is not an ancestor of the map": view hierarchy gesture behavior is a runtime matter. The plan covers it with E-TAP; fine, but the static "PASS" shouldn't stand alone.
- S29 (ticket arithmetic "regardless of clock differences"): fine in principle, but the Keychain label storing local-time expiry with fractional seconds is a timezone/locale/DST risk that code reading cannot settle. Empirical, on device.
- S30 (20 km zoom): "metre-based construction gives city-level" is a visual judgment. Static check of the construction is fine, but "city-level" needs one screenshot.
- S20 residual window (tap to flag): the plan accepts a race and still labels the item PASS. Timing issue; a static proof cannot cover it. Label it "pass with accepted race".

Empirical items that could be settled statically (cheaper, deterministic):
- E-B1 (delete only touches one app): the plan already has S01/S02 for this, then tests it again on a scratch database. Pure duplication. The foreign key effect on a scratch copy is deterministic and read-only; keep one of them, not both. Cheapest is the scratch run, since the "foreign keys on" claim in S01 is a pragma fact the plan itself says is read from main.py but actually depends on the connection.
- E-B3 (stored schema contains recenter_map): this is a read of a file in the bundle plus a database row. The bundle half is static; only "the first send really stored it" is runtime. Can shrink to one row read.
- E-T9 first scenario (controls disabled while sending): static S20 already proves this. The empirical version needs a stalled backend, which is costly. Make it one screenshot, n=1.
- E-F3 "unparseable text, out-of-range, (0,0)" rows: these are deterministic code paths covered by S15. Only "nan" needs running (the plan says so itself), so remove the rest from E-F3.
- E-LAYOUT "no overlap and ordering": ordering is static (S19). Only overlap/clipping with keyboard and large text needs a screenshot.
- E-20Q: regression with n=2 is deterministic app code; a static "diff does not touch 20 Questions rules" (already in S17) plus one run is enough.
- E-SECURE/E-BIO: the plan says these are "covered" by tests that don't exercise them (see section 3 below). The access-control flags are a static read; do that and stop claiming empirical coverage.

2. WEAK OR INVALID STATIC PROOFS

- "Plan-level PASS" is the central problem. Every verdict is made before any code exists, against the baseline. A proof that cannot see the implementation cannot fail, so the PASS column carries almost no information. Only "obligations the diff must meet" are real; label verdicts PENDING, not PASS, until the diff is read.
- S01: step 7 says "if foreign keys were off the order would still do no harm", which makes the proof independent of its own premise, so it cannot fail. Also, the claim that the delete order is "forced" ignores that the existing handler is unchanged baseline code: the real new claim (tools delete has no dependants) is a single sentence; the rest is padding.
- S02: "no statement names the tickets table" is a text search, not a proof of isolation. The calls delete is described as "a subquery on that app's turn IDs", but that is the existing statement, so the proof reduces to "I didn't change it". Fine, but then it proves nothing about B1's new statement except one line.
- S03: relies on "autocommit" as a premise, never established (no reference given). Conclusion "repaired by one more Clear" ignores a failure between calls and turns that leaves turns with no calls, which breaks the next replay in a way that is not repaired if the replay reads those turns first. Premise 5 (interleaving) is accepted away, contradicting "PASS".
- S05: "if and only if the formula line is untouched" is circular: it just restates the diff. And it explicitly allows zero or negative lifetimes, which contradicts the stated requirement (a usable limited-life ticket). The property "smaller of" does not follow to "works".
- S06: conclusion "PASS" while step 4 says a bad value causes an unbounded respawn loop. That is a failure mode in the very property being proved.
- S10: "present only if F1a reproduces" is a process rule, not a proof. S04 has a "premise is a guess" note yet still says PASS; a guess cannot be a proven premise.
- S13: "ships automatically" is hedged ("only if synchronized folder") and then "confirmed by E-B3". That is a static proof relying on an empirical test. Also the crash-on-missing-`required` claim is an inference from reading Toolbox, not a diff check.
- S16/S33/S35: "no write to busy flag etc." can only be found by search, and the plan's own searches (P6) are admitted noisy. The proof is only as good as the search terms; "no literal coordinates or city names" is not searchable as written (a number is not recognisable as a coordinate).
- S17: "all 12 points present in plain English" and "hints never name the city" are not static facts. The first is a review judgment; the second is an LLM behavior. Move the second to E-LEAK only.
- S19/S22: "no ZStack" does not prove the layout order the plan wants; a vertical stack with hidden/overlay modifiers can still overlap. Cannot fail on the stated test.
- S21: fine, but BB12 shows the stated rule ("at least one draft non-whitespace") still sends a whitespace system message, so "PASS" conflicts with the requirement "enabled only when something to send".
- S27/S28: the text-search lists contain bare terms like `30`, `win`, `status`, `pin`, `drop`, `Marker` that will hit unrelated code (constants, "twin", "pinned", "Marker" in the stripper). The whitelist covers only three items. Result: either always-fail or reviewers skip them. Searching for the absence of a feature by keyword cannot prove absence anyway.
- S28 "Game-over detection: check no branch inspects `recenter_map`" is a good check; the keyword list is not.
- S37 timeline: asserts "t above 3650 returns 401" and the skew number, both premises about Google's and the server's token checks not shown. The conclusion is labeled PASS but is a hypothesis; the plan admits this two paragraphs later.

3. WEAK GHERKIN TESTS

- E-T1: "no map in the first frame" depends on frame timing; "first frame" is not observable to a tester taking screenshots. "No marker text appears at any moment" cannot be observed by sampling (L-level flashes last milliseconds). Needs screen recording, which is not mentioned. n=3 on a fresh install requires reinstall each time; no pass criterion for the permission prompt text.
- E-NODEFAULT: screenshots every second miss a sub-second flash of a default map, so "no frame shows a map" can pass wrongly. Needs a recording. "Simulated location changes twice -> map does not move" also needs the first fix to have happened; Given doesn't say so. Also not independent: reuses launch state from T1.
- E-DENIED: "only the progress indicator is shown" with no pass/fail on duration; "record how it looks" is an observation, not a criterion.
- E-LAYOUT: "do not overlap" has no measurement method and no threshold; "visible" while the keyboard is open on the smallest device is exactly where it can fail, but the pass line is a human glance. No sample size, no performer for the large-text case.
- E-HINT: "previous hint stays until first non-blank character" cannot be observed at screenshot rate; needs a recording or a stalled stream. Pass criteria cannot distinguish "replaced at first character" from "replaced at end".
- E-WRONG: "reply gives one new hint" is subjective (one vs two hints, restating an old hint). Misjudgments are "recorded separately", so there is no pass threshold at all. The check "no get_auth call in log" is good; the semantic part isn't. Also no ground truth for the hidden city except a server query that the Given does not mention.
- E-WIN: strong on the order check, but "the map flies from user's location to the named city" depends on screenshots; the final map center is observable, the flight isn't. "Exclude games where the city equals the current view" is a post-hoc exclusion that can hide failures. Needs open ocean AND a check that coordinates are correct to within a tolerance; none is given, so a wrong-but-valid city location would pass. Also asks one test to check six things, so a failure doesn't localise.
- E-LEAK: "no frame shows" has the same sampling problem. Searching hints for the city name by string will miss alternate spellings, accents, nicknames ("the Big Apple").
- E-GIVEUP: "reveals the city" is judged by a person with no rule; "no recenter_map" is checkable. Fine, but depends on the spec question Q10 which is unanswered.
- E-T3: "Void the trial if more than 150 s elapsed" is sensible but the test cannot fail for the interesting reason: biometric prompt presence is stated as not observable on the simulator, so the key claim (a valid in-memory ticket avoids both sign-in AND biometric) is only half checked. "No sign-in sheet" is observable; fine.
- E-T5: "get_auth meets an expired ticket and runs sign-in again" is not separately observable from the user's view when sign-in is silent; the pass criterion collapses to "map moves", which would also pass if the old ticket were wrongly accepted by the server. Needs the server log (a new ticket row) as evidence.
- E-T6: requires a human cancel on a fresh install three times; the Then bundles five outcomes including model wording. "App is not hung" has no measurable duration.
- E-T7: device only, n=3, human; "Keychain save is cancelled or fails" - no way to induce failure besides cancelling; "ticket still works" is fine.
- E-PERSIST: n not stated; the simulated Face ID path proves the code path, not the secure enclave behavior the requirement names. "Records the prompt" with the default setting is an observation.
- E-T9: three scenarios in one with a long chain of Thens; "no stored text from the previous game remains" has no query definition. The "slow or stopped back end" Given contradicts the second scenario (needs the back end alive).
- E-RELAUNCH: "server shows one wipe then one rules message" - how is that observed? Server log content not guaranteed to record deletes; no query given.
- E-PICKER n=2, E-TAP n=2: fine for deterministic UI, but "keyboard does not open on map tap" cannot be reliably seen on a simulator with a hardware keyboard connected (a very common default). Missing prerequisite.
- E-FAIL: T12b is "report untested if cannot induce"; a test that may not run is not a validation.
- E-T4: "n=10 wins" and the duplicate-id error: the error appears only if the model makes parallel calls with the same ID, which is rare; ten wins may never exercise it, so the test cannot distinguish a correct fix from no coverage. "Coherent reply" is subjective.
- E-STALE: 65 minutes of waiting is for a hypothesis, one occasion; result categories include "inconclusive", so it can end without a verdict.

4. COVERAGE GAPS AND ORPHANS

Gaps (requirement has no real validation):
- Secure Enclave / biometric requirement (Rule 3): traced to E-SECURE and E-BIO, which are explicitly "covered by" other tests. S32 only proves nobody changed Ticket.swift. Nothing tests that the stored item is actually protected (e.g. unreadable without the check). In an MRE this is probably acceptable, but the trace table overstates it; say "documented, not validated".
- "Hints are overwritten, only current shown" is traced to E-HINT, yet the decision table in S23 (tool round with no text, error text becoming hint) has no test. Parse-error-as-hint is covered only by the may-not-run T12b.
- Requirement "Send enabled only when something to send": S21 only; BB12 shows it is violated by a mixed whitespace case and no empirical test covers it.
- "Staff: no timer, no ended-by-timer" traced to E-SLOW, which has no pass line and is "observation only". That is not validation.
- "Staff: no Retry, no hardening" traced to E-FAIL, which tests error display, not absence of retry.
- "Staff: no pin / no Play Again / no status row" traced to E-WIN/E-LAYOUT "(visual)": no criterion in those Gherkin mentions the absence, so a pin would not fail any test.
- Rule 2 "invites the user to play again": the plan says "wording per P10" but E-WIN checks "tap Clear", so the requirement text itself is untested.
- Course page "lifetime tunable": E-B2 tests only 20 and unset; fine.
- Legacy patterns and Do-not-build rows: purely keyword search. Acknowledged, but the search lists are the weak part.

Orphans (validation tracing to nothing real, or redundant):
- E-20Q traces to "reuse tutorial tools / structure and naming match", which is a code-structure requirement; a runtime regression test does not validate naming or duplication. Real validation for that row is S33 only.
- E-SLOW, E-BIO, E-SECURE: no pass criteria; observation items.
- S22/S35 "no initial camera before a fix" is traced to E-NODEFAULT and E-T1; fine. But S31 (default main-actor isolation) traces to nothing in requirements; it is a premise, not a requirement.
- The P1 to P12 and BB01 to BB15 lists are useful findings but several trace to no test (BB05, BB06, BB08 etc. "documented only"). That is fine for an MRE, but it inflates the sense of coverage.

5. FEASIBILITY

- Run order conflicts: Phase 1 puts E-T6 on a fresh install "before any successful sign-in", but Phase 1 also includes E-T1, E-NODEFAULT, E-LAYOUT which would each need fresh installs and permission resets, and E-DENIED needs permission denied (a state that cannot be undone without reinstall). Then Phase 2 requires a first human sign-in. There is no stated reinstall step between them, and T6 is run n=3 "each from a fresh install" (three reinstalls plus a Google account human each time).
- E-B2 requires a human sign-in with a "fresh token" and then restart with unset variable and ANOTHER fresh sign-in; yet later phases (3, 4, 5) each restart the server. Every restart means the next sign-in is again silent only if the Google session persists. Not addressed.
- Destructive shared resource: tests restart the live server, wipe app rows via Clear (E-T9 n=3, E-RELAUNCH, every launch wipes), and run a 65-minute baseline test on the same app ID. P2 is flagged but its remedy is deferred to "question 1" (blocking). Until answered, Track A and the main run cannot both go.
- E-T9 "use a slow or stopped back end" then later "other app IDs' rows unchanged" requires other apps' rows to exist; the plan doesn't set them up on the live server (it moves that to the scratch DB in E-B1 but E-T9's Then clause still asserts it live).
- E-F3 requires "a temporary debug call that is removed afterwards", i.e. editing source during validation; this breaks "validate what you ship" and conflicts with F8's sweep (needs question 15 approved).
- E-STALE needs 65 minutes of simulator uptime with the app alive, a human at start, and a Google account; the simulator can sleep or lose the app. The log analysis depends on temporary logging added to the baseline, which means it isn't strictly the frozen baseline.
- E-T7, E-PERSIST need a physical device the plan doesn't know exists (Q11, non-blocking though it blocks two tests).
- Groq free-tier rate limits: n=20 leak starts plus n=10 wins plus n=10 wrong guesses, each several requests, will likely hit limits; the plan notes it but has no wait strategy. Also, "any request on a non-Groq runner voids the sample" could void most of the data.
- Keyboard test (E-TAP) on simulator: see above.
- Server certificate trust (BB15) is listed as an environment prerequisite but the first test (E-B4) is the first thing that would reveal it; ordering should put a plain connectivity check before B2.
- Static proofs "run first" are all against a diff that doesn't exist yet; the run order puts them before deploy, which is fine, but the plan-level PASS verdicts cannot be rerun on the diff without redoing the whole of section 4.

6. MRE FIT

The plan is heavy for an MRE: about 37 static items, about 28 empirical scenarios, 15 baseline bugs, 12 plan defects and 15 questions. Much of that is documentation of tutorial code the student is told not to fix. Cut BB05/BB06/BB08, S29/S30/S31, E-SLOW/E-BIO/E-SECURE, and most of E-20Q, E-PICKER, E-TAP. Keep the core.

VERDICT: The critique is substantive, not nitpicks: the "plan-level PASS" verdicts cannot fail, several Gherkin tests are unobservable at screenshot speed, and the Track A / shared-app-ID conflict blocks the run. First change: relabel static verdicts PENDING until the diff exists and drop the keyword searches that cannot prove absence; then add screen recording plus server-log evidence as the observation method for E-T1, E-NODEFAULT, E-HINT and E-T5, and resolve the shared app ID (P2) before anything runs.

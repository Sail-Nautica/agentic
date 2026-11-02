# Goldfish6_round2: verbatim output

Review of E-C_v8.md (read only that file; no code written).

**1. Ambiguities and gaps (question I would ask)**
- Where are the files and which Xcode scheme/simulator? Plan names Swift files but never says the project path or which simulator. Question: which device is "the named simulator" and where does the iOS project live?
- Hint area vs. map "remaining space": how tall may the hint be (the "capped, scrollable height")? Question: what cap? Implementer will guess. Minor.
- F5c says the hint uses "the existing ChatView". Does ChatView accept a single entry, or the whole conversation? Question: should the implementer pass one `Chat` item, or must a new small view be written? The plan says "all already exist and are reused" but not their inputs.
- F3 says "the system's coordinate-validity check" and "a region of about 20 km". Fine, but it never says how a span in km becomes the camera value (distance vs. degrees). Question: use a camera distance or a coordinate region? The two differ visibly at high latitudes. Low impact.
- F5d: "a toolbar button in the existing navigation bar". Does a navigation bar exist in the baseline? If not, the implementer must add one. Question: confirm it exists.
- F5d: the tap change. "Attach it to the parts other than the map area" is clear in intent but the baseline tap may sit on the root; the implementer must restructure it. Not stated how Clear/keyboard focus is handled when the transcript is shown.
- B4: how harnessd runs and how Groq-only is set is "UNVERIFIED... implementer finds out". The implementer needs ssh host, user, path and env mechanism. Question: give host, deploy path, restart command, and where the Groq key lives. As written, B4 will stall at the first command.
- B1 "Done when" needs read-only DB access (sqlite path on server). Question: path to the live database and the app ID value.
- The plan refers to `staff_feedback.md`, `design_specs.md`, `ui_requirements.md` and "the course AGENTS.md (if supplied)". Their contents are not summarized except in pieces. Fine if supplied, but the implementer cannot tell which staff items matter beyond what the plan quotes.
- D1 contingency: "an empty or odd first reply" has no threshold. Question: how many empty replies before adding a user message? Minor.
- Section 7 / F4a rule 6: tells the LLM to give coordinates as decimals, but F3 says the tool's three args are strings. Fine, but who guarantees the LLM picks "latitude" before "longitude"? Mild; the schema file must state order. Plan says the schema description "must" cover several points but not the order explicitly.

**2. Ordering and dependency problems**
- Track A (F1a) says the frozen baseline is built "before any other front-end change is installed on that simulator", yet F1a logging and the sign-in flow require a working server and Google sign-in; the baseline also launches with the old `llmclear`/lifetime behaviour. The 180 s default ticket is fine, but the hour-long run's win step needs the baseline rules ("win" triggers get_auth) to work, and the baseline `Game.rules` presumably does not use `recenter_map`. Question: does the baseline trigger `get_auth` on a win? The diagram implies yes; the plan does not state it. If not, Track A cannot reproduce anything.
- Diagram: B3 "closes" after F3, but B4 (deploy) depends on B3. Deploy needs only handlers.py (B1, B2); B3 is a check on the phone's first send, which needs B4 already done. So B3 -> B4 is circular in practice (B3's done-when needs a deployed server and the new app; B4's arrow says B3 comes first). Fix: B4 depends on B1, B2 only; B3's check is part of F9.
- F6 (launch calls resetGame) depends on B1 being deployed to be testable, not just on F5a. The diagram shows only F5a -> F6. Minor.
- F8 depends on F1b only if it happens; the diagram handles that. OK.
- F1b is conditional and can land long after everything else, forcing a re-run of T3/T5/T6 and the F8 sweep. Acceptable, but the plan should say the other work can be submitted without it if Q4 is unanswered.
- Q4 (a human for an hour-plus run) and Q5 (server go-ahead) block closing F1 and all tests; both are listed only at the end. They should be answered before coding starts.

**3. Steps too vague or too large**
- F5 is the largest: five sub-steps across three files, with layout, a new view, the hint, toolbar swap and tap handling. It is split already; I would add a short build-and-look checkpoint after F5a and F5b rather than only at the end.
- F1 is correctly split, but F1a mixes a human process and coding-agent analysis. Sharpen to: (a) agent adds logging and hands over the build, (b) human runs, (c) agent analyzes the logs. Say which artifact the human returns (log file, how captured).
- F8 sweep is heavy for an MRE (14 Swift + 11 Python checks, each with recorded counts). It is detailed enough; consider it a checklist, not a step that blocks. The distinction "touched line" is well defined.
- F9: 6 must-run tests, several needing the live server and a human sign-in. T3/T6 depend on F1, so the "must-run" set cannot finish until Q4 is answered.
- B4 is not really a step an implementer can complete without credentials and permissions.

**4. Things the implementer could misread into a wrong build**
- "Delete the branch that prefers the current user's raw token" (F1b) is meaningful only after the logs; fine. But "Always use the existing silent-restore helper" could be read as removing the interactive button path as well. Clarify that only the preference order changes.
- B2: "assigned from the variable" and "default 180": the variable arrives as a string; the plan says non-numeric fails at startup, but does not say to convert it to a number. An implementer could leave a string and break the "smaller of" comparison. Mention integer conversion.
- B1 order: "calls selected by a subquery on this app's turn IDs" is explicit. But the tools row delete conflicts with the earlier-stated fact that the next send "re-upserts"; if the tools row is missing mid-game and the LLM is mid-turn, tools vanish. Plan accepts this (L10). OK.
- F5c: the hint is "newest assistant entry with non-whitespace". After a win with tool rounds, entries accumulate in one reply, so the hint shows pre-tool text plus the closing text. Plan states this, but it conflicts with the requirement that hints replace clues; a player may see a long concatenation. Accepted but visible.
- F4a rule 2 says write the marker "before any other text". Combined with D1 (system-only first message), a model may produce no output at all or ask a question. The contingency exists. OK.
- F2 "positioned flag" and "camera" are set by two writers, but F5b says the map appears "until the positioned flag is set: progress indicator". With permission denied the flag stays unset; the plan accepts this (L3), but it means the whole app is a spinner until a win. A tester will think it is broken. Accepted limit, but mention in hand-off.
- Decision 5 says the Groq runner is first "in runners.toml" yet then says the order is random; the single-key approach is the real mechanism. Clear enough.
- F6 launch guard: "keeps the baseline guard that the conversation is empty" plus a busy check. An implementer who changes the task to run on every appearance (instead of once) would break it; plan says "once per launch", which is enough.
- T2 says set the simulated location mid-ocean; a simulated location must be a place the Simulator accepts. Fine.

**5. Self-consistency (names, IDs)**
- Step IDs: B1-B4, F1-F9 (F1a/b, F5a-d, F4a/b), T1-T13 with T12a/T12b, L1-L15, D1-D6, Q1-Q6 are used consistently. Q numbering: the "Departures" table cites Q2 (Clear confirmation) and Q3 correctly; the do-not-build list cites Q2 correctly.
- "Satisfies"/section references: F8 refers to "section 7" for the checks, but the checks are in section 8 (section 7 is "How the LLM obtains the token"). Section 0 and owner decision 3 also say "defined in section 7". Wrong cross-reference, appears several times; an implementer could look in the wrong place. Also F8 and section 9 refer to the "do-not-build list in section 9", which is correct.
- F3 mentions "(section 6)" for the span; correct.
- The title says "Exhibit E-C v8" and the diagram shows "F9 tests" while T tests are defined under F9; consistent.
- "Mermaid diagrams are the only code-like blocks": true as far as read.
- Diagram: the F1b/RERUN edges are consistent with text. The B3 -> B4 edge is the one inconsistency with the text (see section 2).
- Test lists: "Must-run: T1, T2, T9, T10, T6, T3" in F9 and the diagram's "T1, T2, T9, T10 and the rest" are consistent. T4 is nice-to-have yet L5 and schema fact 4 say it is "sampled in T4 and reported", fine.
- Decision 3 says the variable is read "next to the definition of TICKET_MAX_LIFETIME"; B2 matches it.

**Overall**
Very detailed and mostly self-consistent; much of it is process and test scaffolding larger than an MRE needs (14+11 sweep checks, 13 tests, 15 accepted limits), but that is thoroughness, not a blocker.

**Verdict:** Ready for a first pass on the code steps (B1, B2, F2 to F7). Blockers are operational, not design: B4 needs server access details and the owner's go-ahead (Q5), and F1/T3/T5/T6 need a person for a one-hour sign-in run (Q4). Remaining critique is mostly nitpicks (wrong "section 7" cross-reference should be section 8, the B3-before-B4 arrow, B2 integer conversion, F5c/F5d input details). The one substantive item is the missing server/DB access details and the unstated assumption that the baseline's win path calls `get_auth` so Track A can reproduce anything.

# Elephant (E-C), round 3: verbatim prompt (message sent to the resumed session)

Please produce a complete E-C v3 (full plan, not a diff). Still no code, plain English, diagrams allowed; do not read third-party library source. A fresh Product Manager (Goldfish 4) reviewed E-C v2 against the HW2 design document and the staff feedback and called it substantive. New inputs and decisions first:

NEW INPUT: the live database schema (read-only dump) is at /Users/nautica/Documents/classes/eecs498-8/agentic/project2/inputs/db_schema.sql. Read it and replace every guess about the tables with facts (note: calls.id alone is the primary key; calls has a foreign key to turns without cascade; tools is keyed by appID; tickets has its own table; turns has triggers). Step 0 is now done: say so, and state what the schema implies for B1 (delete order, whether the tools row should go, what "feed the LLM the current schema" then means: give the coding agent this dump).
OWNER DECISION: the transcript stays as a user-opened in-place swap for the map area (hint area = the only always-visible text). Keep it, as decided.
ORCHESTRATOR DECISIONS: legacy sweep scope stays "new and touched code" (owner decision) BUT add a prominent risk note that the staff wording ("presence of these patterns in your code") may also penalize baseline tutorial code, and turn the "Check" placeholders in the checklist into concrete checks.

Goldfish 4 findings to address (adopt unless you give a reason; list non-adopted items with reasons):
1. Name the new tool explicitly: recenter_map (match tutorial naming conventions), with its three string arguments.
2. Denial vs invalid ticket: they must be distinguishable. Specify the smallest change so that a cancelled sign-in or failed biometric makes get_auth return a clearly different "denied" result (not the 401 text), reusing the tutorial structure, so the LLM does not loop on sign-in. Remove the contradictory diagram note.
3. F1 sequencing: produce the stale-token evidence BEFORE changing sign-in code (a short run, public header documentation only); make the fix conditional on the evidence; avoid adding a new callback wrapper (legacy pattern) unless unavoidable and justified.
4. Cut the cached last-known location (stale-centre risk); first fix only. Fix the contradiction "moves exactly once" vs "assigned twice".
5. Cut or justify the single transaction in B1 (does existing handler code use transactions? If not, cut).
6. Reduce F9: one working runner plus the simulator; real device only if available.
7. Trim section 0 to the rules (no process history).
8. Fix the declared-nowhere contradictions: (a) say the plan departs from Decision F (floating Clear, compact panel) because the owner kept the tutorial layout, and from "Begin" (D1); (b) D4 claims "as in HW2": correct it (HW2 read the ticket with Face ID on each win; this plan follows the tutorial: biometric at launch and at save) and state this as a deliberate departure to confirm; (c) "Retry in any form" vs "Clear again is the retry": reword; (d) "single busy flag with the spinner on the tapped button": specify how the app knows which button (reuse the tutorial's mechanism, say what it is); (e) F5 hint behavior: define it precisely (the hint should keep the last assistant reply until the new reply's first token arrives, what happens when the user's message becomes the last entry, when a tool message is last, and when a send fails); (f) marker stripping while streaming: say how a half-arrived marker never flashes, and add a second-round marker test; (g) mention ticket expiry as a visible Keychain attribute (tutorial behavior); (h) state that the professor's truncated Clear/tool-schema sentence is being read as "Clear must also delete the tools row" and that this reading is a guess to confirm.
9. Add a test that the first turn after Clear still gets its tool schemas back.
10. Keep MapKit named explicitly in the map section.

Output: full E-C v3, a short "Not adopted" list with reasons, and only the questions that still need the owner (mark blocking or not).

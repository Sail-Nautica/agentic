# Goldfish5_round2: verbatim prompt

Your only input is the single file /Users/nautica/Documents/classes/eecs498-8/agentic/project2/inputs/E-C_v6.md (an implementation plan for an iOS game app plus a small Python back-end change). Read that file and nothing else; do not read any other file, source code or the repo, and write no files.

I do not want you to create code. We are not going to create code. Resist your impulse to create code. Plain English, minimal jargon. Do not simply accept claims in the plan; challenge them. Note: section 0 lists owner decisions that are fixed and section 9 lists accepted limits; you may point out technical problems they cause, but do not just re-argue them. The plan's claims about the existing code were checked by its author against that code; you cannot re-check them, so challenge them only where they are internally inconsistent.

Act as an Expert Technical Reviewer. The plan will be handed to a coding agent. Find, as short bullets, each with why it matters and the likely consequence:
1. Missed assumptions.
2. Edge cases not handled (concurrency, state, ordering, failure and cancellation paths, platform behaviors of maps, location, sign-in, keychain/biometrics, streaming, tool-call loops, database deletes).
3. Technical errors or things that would not work as written.
4. Steps whose "done when" cannot actually be checked as stated.
Keep the goal in mind: a Minimum Reproducible Example prototype. Do not ask for enterprise-grade security, scalability or reliability hardening.
End with a one-line verdict on whether the remaining critique is substantive or only nitpicks, and what you would change first.

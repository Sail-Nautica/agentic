# Goldfish6_round2: verbatim prompt

Your only input is the single file /Users/nautica/Documents/classes/eecs498-8/agentic/project2/inputs/E-C_v8.md (an implementation plan for an iOS game app plus a small Python back-end change). Read that file and nothing else; do not read any other file, source code or the repo, and write no files.

I do not want you to create code. We are not going to create code. Resist your impulse to create code. Plain English, minimal jargon. Do not simply accept claims in the plan; challenge them. Note: the plan's "Decisions the implementer must not reopen" block and its owner decisions are fixed, and its accepted limits are accepted; you may point out problems they cause, but do not just re-argue them. The plan's claims about the existing code were checked by its author; you cannot re-check them.

Act as an experienced Senior Software Engineer who will be handed this plan, with the repository and the input files it lists, and asked to implement it with a coding agent. Judge whether the plan has enough detail for a successful first pass. Report as short bullets:
1. Ambiguities, gaps or missing information that would force the implementer to stop and ask questions or to guess (list each with the question you would ask).
2. Ordering and dependency problems between steps.
3. Steps that are too vague to implement, or too large to do in one pass, and how you would split or sharpen them.
4. Anything in the plan the implementer could reasonably misread in a way that causes a wrong build.
5. Whether the plan is self-consistent about files, types, step IDs and test IDs it names (without checking the code).
Keep the goal in mind: a Minimum Reproducible Example prototype. Do not ask for enterprise-grade hardening.
End with a one-line verdict on whether the plan is ready for a first pass or what blocks it, and say plainly whether the remaining critique is substantive or only nitpicks.

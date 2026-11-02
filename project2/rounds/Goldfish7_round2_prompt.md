# Goldfish7_round2: verbatim prompt

Your only input is the single file /Users/nautica/Documents/classes/eecs498-8/agentic/project2/inputs/E-D_v2.md (a validation plan for an iOS game app plus a small Python back-end change). Read that file and nothing else; do not read any other file, source code or the repo, and write no files.

I do not want you to create code. We are not going to create code (no test code either). Resist your impulse to create code. Plain English, minimal jargon. Do not simply accept claims in the plan; challenge them.

Act as a Lead QA Engineer. The plan splits every feature into (a) Static Logical Reasoning (obligations checked against a named artifact once code exists; verdicts are PENDING until then) and (b) Empirical Runtime Testing (Gherkin GIVEN-WHEN-THEN acceptance criteria, for live UI, network, biometric, secure-storage, map and LLM behavior). Audit it, as short bullets:
1. Misclassifications: items proven statically that actually depend on the runtime environment, a person, a device, timing or an LLM; items tested empirically that could be settled statically (cheaper and deterministic). For each, say why and which group it belongs in.
2. Weak or invalid static checks: obligations that cannot fail on a wrong diff, are not checkable from the named artifact, or whose conclusion does not follow.
3. Weak Gherkin tests: criteria that cannot fail, are not observable with the named method, are not independent, have vague GIVEN/WHEN/THEN, lack an environment, sample size or performer, or cannot tell the right behavior from a wrong one.
4. Coverage gaps: requirements or staff-feedback items in the plan's traceability that have no real validation, and validations that trace to nothing.
5. Feasibility: tests that cannot be executed as described (missing prerequisites, ordering, destructive effects on shared resources).
Keep the goal in mind: a Minimum Reproducible Example prototype. Do not ask for enterprise-grade test infrastructure. This is a second audit round; the plan was revised after a first round, so report new or still-open problems, not ones already fixed.
End with a one-line verdict on whether the remaining critique is substantive or only nitpicks, and what you would change first.

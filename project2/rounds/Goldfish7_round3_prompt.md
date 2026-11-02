# Goldfish7_round3: verbatim prompt

Your only input is the single file /Users/nautica/Documents/classes/eecs498-8/agentic/project2/inputs/E-D_v3.md (a validation plan for an iOS game app plus a small Python back-end change). Read that file and nothing else; do not read any other file, source code or the repo, and write no files.

I do not want you to create code. We are not going to create code (no test code either). Resist your impulse to create code. Plain English, minimal jargon. Do not simply accept claims in the plan; challenge them.

Act as a Lead QA Engineer. The plan splits every feature into (a) Static Logical Reasoning (obligations checked against a named artifact once code exists; verdicts are PENDING until then) and (b) Empirical Runtime Testing (Gherkin GIVEN-WHEN-THEN acceptance criteria, for live UI, network, biometric, secure-storage, map and LLM behavior). Audit it, as short bullets:
1. Misclassifications: items proven statically that actually depend on the runtime environment, a person, a device, timing or an LLM; items tested empirically that could be settled statically. For each, say why and which group it belongs in.
2. Weak or invalid static checks: obligations that cannot fail on a wrong diff, are not checkable from the named artifact, or whose conclusion does not follow.
3. Weak Gherkin tests: criteria that cannot fail, are not observable with the named method, are not independent, have vague GIVEN/WHEN/THEN, lack an environment, sample size or performer.
4. Coverage gaps and orphans in the traceability.
5. Feasibility problems (prerequisites, ordering, destructive effects on shared resources, budget).
Keep the goal in mind: a Minimum Reproducible Example prototype. Do not ask for enterprise-grade test infrastructure. This is a third audit round; the plan was revised twice, so report only new or still-open problems.
End with a one-line verdict that says plainly whether the remaining critique is substantive or only nitpicks, and what you would change first.

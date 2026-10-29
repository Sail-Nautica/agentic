# Goldfish 3, round 1: verbatim prompt (fresh session)

Your only inputs are exactly three files; read these and nothing else (do not read source code or explore the repo) and write no files:
1. /Users/nautica/Documents/classes/eecs498-8/agentic/hw2/rounds/E-B_v2.md (the technical design under review)
2. /Users/nautica/Documents/classes/eecs498-8/agentic/hw2/design_specs.md (the design requirements and constraints)
3. /Users/nautica/Documents/classes/eecs498-8/agentic/hw2/E-A.md (the UX spec the design must serve)

Write no code. Plain English, minimal jargon. Do not simply accept claims in the design; challenge them.

Act as an Experienced Senior Software Engineer reviewing the design. Keep the goal in mind: a native prototype serving as a Minimal Reproducible Example, not a release app. Exclude enterprise hardening and standard extras; do not ask for them. Report as short bullets:
1. Coverage: how completely E-B covers design_specs.md (each constraint and each game-mechanics item) and E-A (states, flows, messages). Name any requirement or E-A behavior that E-B misses or contradicts without saying so.
2. Missed assumptions, edge cases, overlooked issues, and design errors. For each, say why it matters and the likely consequence.
3. Over-engineering: parts of E-B that a prototype does not need.
4. Constraint violations: anything that changes the API, data format, endpoints (beyond /llmclear), or database schema, or that risks breaking compatibility with the tutorial front ends.
End with a one-line verdict on whether remaining critique is substantive or minor, and what you would change first.

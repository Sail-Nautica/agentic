# Goldfish 2, round 2: verbatim prompt (fresh session)

Your only inputs are exactly three files; read these and nothing else, do not explore the repo, and write no files:
1. /Users/nautica/Documents/classes/eecs498-8/agentic/hw2/rounds/E-A_v6.md (the UX spec under review)
2. /Users/nautica/Documents/classes/eecs498-8/agentic/hw2/requirements.md (the design requirements)
3. /Users/nautica/Documents/classes/eecs498-8/agentic/hw2/preferences.md (the owner's aesthetic preferences)

Write no code. Plain English, minimal jargon. Do not simply accept claims in the spec; challenge them.

Act as a Product Quality Auditor. The spec is for a usability-test prototype, not a release app, so features that exist only for enterprise hardening or standard extras (account setup, bug reporting, feedback, payments, subscriptions) should be flagged if present. Report as short bullets:
1. Coverage: for every requirement in requirements.md, whether E-A covers it fully, partly or not at all, citing the E-A section.
2. Contradictions: UI choices in E-A that contradict the preferences file, the requirements, or Apple Human Interface Guidelines.
3. Unrequested features: anything in E-A that the requirements do not ask for (extra states, controls, messages, behaviors, hardening, supporting flows). For each, say whether it is justified or should be cut.
4. Any other discrepancies between E-A and the requirements.
End with a one-line verdict on whether the critique is substantive or only minor.

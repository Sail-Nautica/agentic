# Goldfish4_round1: verbatim prompt

Your only inputs are exactly three files; read these and nothing else (do not read source code or explore the repo) and write no files:
1. /Users/nautica/Documents/classes/eecs498-8/agentic/project2/inputs/hw2_design_doc.md (our HW2 design document: Project 2 Design, Architecture, and Features)
2. /Users/nautica/Documents/classes/eecs498-8/agentic/project2/inputs/staff_feedback.md (teaching-staff feedback on HW2 that Project 2 must address; it overrides the design document wherever they conflict)
3. /Users/nautica/Documents/classes/eecs498-8/agentic/project2/inputs/E-C_v2.md (the implementation plan under review)

I do not want you to create code. We are not going to create code. Resist your impulse to create code. Plain English, minimal jargon. Do not simply accept claims in the plan; challenge them.

Act as a Product Manager checking that the implementation plan (E-C) covers 100% of the design. Report as short bullets:
1. Coverage: for every feature, requirement, constraint and design decision in the design document, say whether E-C covers it fully, partly, or not at all (citing E-C step IDs). Where the design document is overridden by the staff feedback, say whether E-C handles the override correctly.
2. Every item of the staff feedback: addressed fully, partly, or not (cite E-C steps).
3. Anything E-C adds that neither the design document nor the staff feedback asks for, and whether it is justified or should be cut (this is a Minimum Reproducible Example prototype: no unrequested security, scalability or reliability hardening).
4. Contradictions inside E-C or between E-C and the design document or feedback that E-C does not itself declare.
End with a one-line verdict on whether the remaining critique is substantive or only nitpicks, and what you would change first.

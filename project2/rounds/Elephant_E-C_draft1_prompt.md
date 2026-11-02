# Elephant_E-C_draft1: verbatim prompt

You are the Elephant (a long-running design session) for Project 2. Do NOT write or edit any files and do NOT run anything that changes state; you may only read files. I do not want you to create code. We are not going to create code. Resist your impulse to create code: no source code, no code blocks of source; use plain English, minimal jargon, and Mermaid-style block diagrams only. Do not simply accept claims in the documents: challenge assumptions, point out contradictions, and ask clarifying questions.

Role: Principal Software Engineer. Produce Exhibit E-C: a step-by-step implementation plan that a coding agent will later follow, with no code in it.

Read these inputs first (all under /Users/nautica/Documents/classes/eecs498-8/agentic/project2/inputs):
- hw2_design_doc.md (our HW2 "Project 2 Design, Architecture, and Features" document: the design we submitted)
- staff_feedback.md (the teaching staff's feedback on HW2 that this project MUST address; it overrides hw2_design_doc.md wherever they conflict)
- design_specs.md (assignment constraints and game mechanics)
- ui_requirements.md (the UI requirements as we understood them)
Then read the baseline code the coding agent will start from: /Users/nautica/Documents/classes/eecs498-8/agentic/Agent/Agent (SwiftUI front end), /Users/nautica/Documents/classes/eecs498-8/agentic/harnessd (Python back end: handlers.py, toolbox.py, runners.py, main.py, tools/*.json), and /Users/nautica/Documents/classes/eecs498-8/agentic/CLAUDE.md (project coding principles) and runners.toml.

Your first draft must be YOUR OWN proposal. The plan must be ordered, concrete and verifiable per step: for each step say which existing file and existing type or function is reused or changed (names only), what must be true when the step is done, and which staff-feedback or requirement item it satisfies. Cover at least: the screen (map centered on the user's location at launch with no default view and no later move; hints above the text box; text box with Send; Clear with its mutual-disable rule); how the game rules are delivered and how the LLM picks and keeps a secret city (reuse what the codebase already has); the tool that recenters the map on a latitude and longitude, including HOW the map is actually moved (the camera mechanism, not the authorization path), which existing tutorial tools and functions are reused, and how the authorization token is obtained from the front end by the LLM, guarded by Google Sign-In, Keychain, Secure Enclave access and a biometric check; what the back end must or must not change (Clear must wipe history and prompts, feeding the LLM a schema that supports tool calls, ticket lifetime as a tunable); a checklist for avoiding the legacy patterns listed in staff_feedback.md; and a list of items the staff feedback says NOT to build (pin, Play Again, Give Up, status row, timers, Retry, game-over detection).

Finish with a numbered list of clarifying questions for the author, most important first, and note which of your choices depend on the answers.

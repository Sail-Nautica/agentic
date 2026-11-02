# Teaching staff feedback on HW2 that Project 2 must address (verbatim from the professor, plus course-page guidance)

## Verbatim from the professor (issues for Project 2)

UI:

- requirement doc says, "the hints for the mystery city should appear above the text box in which user enters their guesses". Note: **above**, not side by side.
- requirement doc says, "Your app must show: upon launch, a map centered on the user's current location." NOT: "On launch the map starts on a default view and moves to the user once a location fix arrives." No default view and not moving to user location. Upon launch shows the map centered on user's location.
- "the map to the city and drops a pin". There's no pin in the requirement doc.
- "After a win the field is disabled and Play again appears." There's no "Play again" in requirement doc. Interactions are by NLP.
- "The status row stays reserved so nothing jumps." What status row? There's no "status row" in the requirement doc.
- "Timer and Retry. Every back-end call, including the wipe, has a 30 s total limit. Retry has three behaviors: restart after a failed start or wipe, resend after a failed guess, and resume with the stored tool results after a failure that follows a tool call." The requirement doc doesn't ask for this. Goldfish 2 was specifically warned against, "No unspecified security, scalability, or reliability hardening."
- "Clear deletes calls and turns but not stored tool schemas." The requirement doc says, [the sentence is cut off in the professor's note]
- "Ended after . . . a timer". No timer ending game in the requirement doc.
- SigninView's task first uses the SDK's current user token if present, which can be stale after an hour. If you are sure about this, show me your coding tool (Claude) output just for this bug.
- How to recenter the map?

Prevent the LLM from generating outdated, inefficient, or mixed-language code with legacy patterns. Presence of these legacy patterns in your code will lead to automatic point deductions.

## From the Project 2 course page (feedback section, summarized by a fetch tool)
- Backend: feed the LLM the current database schema that supports tool calls; adapt llmclear() to remove data cleanly; the ticket lifetime is tunable for playability or testing, not a fixed value.
- Frontend: the implementation plan must cover how the map is actually recentered on a given latitude and longitude (not the authorization path); the map shows up already centered on the user's current location; no Give Up, Play Again, status line or marker/pin ("All you have to do is to center the map on the mystery city"); interactions are by the NLP text box.
- Game-over detection: do not spend effort detecting when a game is over; "the tool call to move the map should only be used to move the map, not to signal the front-end that a game is over."
- Architecture: structure, separation of concerns and naming must match the tutorials (otherwise not graded); "You MUST reuse pre-existing tools and tool functions from the tutorials"; unnecessary code duplication is penalized; no change to the back-end API, data format or SQLite schema; no new endpoints beyond /llmclear; avoid legacy patterns; use the course AGENTS.md; Minimum Reproducible Example scope with no enterprise-grade security, scalability or reliability hardening.

## Legacy patterns (from the course AGENTS.pdf slides; automatic deductions)
- Thread-based concurrency: any DispatchQueue (main or global) with .sync or .async; Task.sleep() and Thread.sleep(); RunLoop. Use structured concurrency / suspension instead.
- Older property wrappers: ObservableObject, @Published, @StateObject, @ObservedObject, @EnvironmentObject. Use the Observation package (@Observable, @Environment); @Binding is still fine.
- MainActor use must be justified (Swift 6.2 default MainActor isolation), ZStack and GeometryReader use must be justified, avoid manual type assertions and caseless enums used as namespaces.
- AGENTS.md: Minimum Reproducible Example, expressions over multi-line if-else, Result over do-catch, native structured concurrency, atomic upserts rather than DELETE + INSERT, descriptive noun-style names, comments only for why.

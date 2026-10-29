## One-page summary of E-B (technical design: what will be built)

**The deliverable.** The Mystery City game, built by extending the existing llmHITL iPhone app. The Python back end (harnessd) is not changed: no new endpoint, no new data format, no database change. The only back-end call the app adds to its flow is the existing /llmclear.

**What the user will see (from E-A).** A full-screen map; a compact bottom panel with the latest LLM clue above a guess box with a Send button; a floating Clear button. A correct guess moves the map to the mystery city after Google sign-in and Face ID.

**What will be built, piece by piece (all in the existing tutorial files and type names).**
- **AgentApp.swift, `AppViewModel`:** a small game state machine (Starting, Ready, Sending, Error, Ended, Clearing) that holds the latest reply, a "game tool was called" flag, a retry record, the map camera and the pin. `sendTurn` and `resetGame` keep their names and roles.
- **ContentView.swift:** replaced by the map, the clue area, the guess box with `SubmitButton`, and `ClearButton` with a confirmation dialog.
- **Rein.swift:** `llmTools` now returns an explicit outcome instead of writing an error string, takes an optional resume (turn ID plus tool results) and applies a 30 s limit; `llmClear` gets the same limit. The stream reader and the secret-marker stripper are reused unchanged.
- **Toolbox.swift and tools/:** `get_auth` kept (Face ID read of the stored ticket, one read per user action); a new `recenter_map` tool (ticket, latitude, longitude) that checks the ticket and the coordinates, moves the map and drops a pin; schema file `recenter_map.json` beside `get_auth.json`.
- **Ticket.swift:** reads the Keychain ticket with Face ID, checks expiry without a prompt, saves by delete-then-add, no alert strings. **SigninView.swift:** always restores the Google sign-in (not the stale in-memory token) and shows no text.
- **Info.plist:** portrait only, location text reworded.

**How the game works (the flows).**
1. *Start.* Wipe the old conversation (/llmclear), then send the game rules plus "Begin". The LLM picks the city and begins its first reply with a hidden `[SECRET: city]` marker; the server stores and replays it, so the city stays fixed and secret; the app strips the marker before display.
2. *Guess.* The app sends the text; the reply replaces the clue. A give-up is only text; Clear restarts.
3. *Win.* The LLM calls `get_auth` (sign-in and Face ID, returns a ticket), then `recenter_map` with the ticket and coordinates, then writes the closing text: three requests. A denial at `get_auth` leaves the map still, the LLM reveals the city in text, and the game still ends.
4. *Errors.* Every call has a 30 s limit; one Retry resends, restarts or resumes depending on where the failure happened; Clear is the escape.

**Departures from E-A.** Fourteen, tabulated in E-B section 8, mainly: two tools instead of one, game end on any game tool call, a timer and error path for Clear, and Send disabled after certain errors.

**Limits accepted.** The secret is enforced by prompt only; the marker and the ticket sit in plain text in the harness database; the ticket lives at most 180 s; one tester at a time per back end.

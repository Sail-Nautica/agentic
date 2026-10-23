## One-page summary of E-B (technical design)

**What it is.** The plan for building the game on the existing llmHITL code with no back-end change. The iPhone app becomes a small state machine around the tutorial's network loop; the Python harness is untouched and keeps the whole conversation.

**Key ideas.**
- **Secret city.** The LLM picks the city and puts it in a hidden marker at the start of its first reply. The harness stores and replays that reply, so the model "remembers" the city; the app strips the marker before showing the text. Every start first wipes the old conversation.
- **Two device tools.** The LLM must obtain the token, so it calls `get_auth` (sign-in and Face ID, returns a ticket) and then `recenter_map` with the ticket and the city's coordinates. A win is therefore three back-end requests.
- **Win detection.** The app notices that a game tool was called; it cannot verify the guess or detect a give-up.
- **Timer and Retry.** Every back-end call, including the wipe, has a 30 s total limit. Retry has three behaviors: restart after a failed start or wipe, resend after a failed guess, and resume with the stored tool results after a failure that follows a tool call.
- **Map.** A SwiftUI map that follows the user once, then flies to the city and drops a pin on a win.

**Checked against the code.** The ticket lasts at most 180 s, so a win after three minutes needs a new sign-in. Clear deletes calls and turns but not stored tool schemas. Resending tool results is safe when the failed leg produced only text.

**Accepted limits.** The secret is enforced by prompt only; the marker and ticket sit in plain text in the harness database; a timeout right after the server stores a tool call can leave history damaged until Clear; one tester at a time.

**Departures from E-A.** Fourteen, listed in a table: for example two tools instead of one, Ended after any game tool, a timer and error path for Clear, and Send disabled after certain errors.

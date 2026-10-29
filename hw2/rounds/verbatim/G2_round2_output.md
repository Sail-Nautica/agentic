# Goldfish 2, round 2: verbatim output (critique of E-A v6)

AUDIT OF E-A v6

1. COVERAGE (requirements.md vs E-A)
- Screen 1, map centered on current location: PARTLY. 5.1 step 3 moves the map once when a fix arrives. But the map first shows a "default zoomed-out view" and only moves later, so it is not centered at launch. If location is denied it stays on the default with no notice (accepted, but it fails the requirement in that case). Also, after Clear/Play again the map stays put (5.4.8, 5.5.3), which is fine.
- Screen 2, hints above the text box, new overwrite old: FULL (sec 1, sec 2 order, 5.2.2).
- Screen 3, Send enabled only when there is something to send, shows work in progress: FULL (sec 3 table, 5.2.1 spinner and "Thinking..."). Enabled only in Ready/Error with non-space text, which is stricter than the requirement but consistent with it.
- Screen 4, Clear wipes history and prompts; Send disabled while clearing, Clear disabled while sending: FULL (sec 3 note, 5.5.3, sec 6). Clear is also disabled in Starting, which is stricter than asked but harmless.
- Game rule 1, rules sent on start, LLM picks city, city hidden until end: PARTLY. 5.1 covers picking and hiding. But "a session ends on a correct guess or give-up" is only half handled: sec 4 says give-up never reaches Ended and the game stays Ready. So the session does not formally end on give-up; the user just types again, or taps Clear.
- Game rule 2, recenter tool on correct guess, then invite to play again: PARTLY. 5.4 covers the tool and the Play again button. But the "invite" is a fixed button, not the LLM's invitation, and on denial the map does not move (see section 4 below for the conflict).
- Game rule 3, token from Google Sign-In, limited lifetime, reused, Keychain, Secure Enclave, biometric: FULL on paper (5.4 flowchart). Weak spots: the flowchart never says what happens when a stored token is expired AND the user cancels sign-in (goes to Denied, fine), and "limited lifetime" is not given a value or source.
- Constraint, no new endpoints, only /llmclear: FULL (5.5.3).
- Constraint, every required element fully visible, non-overlapping: PARTLY. The claim is made (sec 2) but not backed. See contradictions on keyboard and panel size.
- Constraint, exclude hardening/extras: PARTLY. See section 3.
- Constraint, Apple HIG: PARTLY. See section 2.

2. CONTRADICTIONS
- Preferences say map-dominant and few controls, yet the panel reserves a permanent 44 pt status row plus a 2-line minimum hints area plus input row. That is a large fixed block (target "about one third" of the screen). A permanently reserved, usually empty row works against map-dominant. Justified only to avoid layout jump; a usability prototype could instead show the row only when needed.
- Keyboard: "the panel sits above it; the map does not resize". With the keyboard up on a small iPhone, a one-third panel plus keyboard (about 40%) leaves little map and risks the floating Clear and status bar crowding. Also the win framing is computed with the keyboard down (5.4.4), but the keyboard is dismissed at win start (5.4.1) so this is okay; however "framed so the pin is above the panel" is never re-checked if the user rotates or text size grows. Dynamic Type is "system defaults" with "no special large-text layout" yet the panel is claimed to stay at most one third: at large text sizes that cannot be guaranteed, so the "fully visible, non-overlapping" requirement is untested.
- HIG: "Clear" as the visible label for an action that starts a new game is called out by the spec itself as unclear and patched with a VoiceOver label and a confirm title. HIG says labels should say what the control does. The requirement names the Clear button, so keeping it is defensible, but a user sees "Clear" and may expect to clear the text box.
- HIG: the Clear confirmation is called a "standard action sheet" with a destructive "Clear" button. On iPhone this is a confirmation dialog; fine. But Clear in Ended and Play again skip confirmation while Clear in Ready asks. Same visible button, different behavior depending on state: inconsistent and hard to predict. Spec acknowledges it.
- HIG: one tiny line of text ("Map not moved.") plus a button share the 44 pt status row; error text, spinner, and button all squeezed in one line risks truncation at larger text sizes.
- HIG/Preferences: the text field is disabled in Ended and the placeholder says "Guess, hint, or give up" even though the field is dead. Dimmed placeholder is fine, but inviting "give up" with a typed phrase is not discoverable (no button, and the hint is only in a placeholder that vanishes once typing begins).
- Requirement 3 says Send "shows that work is in progress". The spec disables Send but also replaces the whole status with a spinner; fine. However "Return does what Send does" is an extra behavior (see 3).
- Compass "when rotated" top-right and Clear top-left: standard, no conflict.
- Contradiction inside the spec: sec 3 table says the field is "Editable" in Clearing and Starting, yet Send is off; 5.2.1 says "keyboard stays" after sending. Meanwhile 5.4.1 dismisses the keyboard but the field stays editable in Sending, so the user can type during the win flow while Face ID/sign-in sheets appear. Minor.

3. UNREQUESTED FEATURES (justified or cut)
- Error state, Retry button, "Couldn't reach the game.", 30 s timeout: borderline. A network failure will occur in a real test, so some failure message is justified; but Retry keeping a hidden held guess, dropping it if the user sends something else, and distinguishing start/guess/final-reply retries is more machinery than a prototype needs. Cut to: show the message, let the user resend or Clear. Cut the held-guess logic.
- 30 s timeout: justified only if the LLM calls can hang; otherwise cut (a spinner that never ends is worse for a test, so keep, but as a single simple timer).
- Ended state with disabled field, Play again button, "Map not moved." text: the requirement only says "invites the user to play again". Play again is a reasonable reading. Disabling the field is an extra; "Map not moved." is an extra message. Cut "Map not moved." (the LLM already reveals the city in text). Play again duplicates Clear in Ended; keep one control (Clear) or keep Play again but do not also keep Clear enabled with different behavior.
- Skip-confirmation logic on Clear/Play again in Ended: extra branch. Cut: always confirm, or never confirm.
- Dimming old hints while sending: extra visual state; cut (spinner alone is enough).
- Return key = Send: standard text field behavior, justified, trivial.
- Tap map to dismiss keyboard: justified (HIG-standard), small.
- Compass: system default MapKit control; fine.
- Pin drop on win: not requested (requirement says recenter only). Small, helpful for the test; justified but flagged as an extra.
- Fly animation about 2 s with Reduce Motion fallback, plus framing "so the pin sits above the panel": the panel-aware framing is extra polish; requirement says layout polish is not graded. Cut or simplify to plain recenter.
- Longitude/latitude range check: reasonable guard, small; justified (LLM could return garbage and the map would break).
- Six status strings, floating-material Clear button, VoiceOver "Clear, starts a new game", two-line minimum hints with scroll after three lines: polish beyond need; keep scroll (long LLM text must be visible), the rest can be trimmed.
- Location denied/first-launch false-timeout note and "Starting" disabled Clear: acceptable notes, but the false failure on first launch is a known flaw left in on purpose; for a usability test this will hit every new tester. Should be fixed (delay the first request until the location prompt resolves) rather than accepted.
- Passcode fallback allowed for biometric: weakens "guarded by a biometric check". System default, but contradicts the requirement's literal wording; either state it as a deliberate relaxation or remove.

4. OTHER DISCREPANCIES
- The requirement says the recenter tool is called on a correct guess. The spec says the app can ONLY detect a win through that tool and cannot detect give-up. So if the LLM forgets to call the tool, the session never ends and the user is stuck until Clear (spec admits this in 5.5.4). The requirement's "session ends on correct guess or give-up" has no app-level implementation.
- Denial: requirement says on a correct guess the map recenters. The spec lets denial (cancelled Face ID, cancelled Google) end the game with the map not moving and the LLM then revealing the city. That is a behavior beyond the requirement and reveals the city without a successful win flow; acceptable but it should be stated as a decision.
- "Face ID on every token read" and "sign-in not repeated within lifetime" are fixed by the owner; the first win therefore shows Google then Face ID back to back. Fine, but the Secure Enclave and Keychain storage details in the flowchart (encrypted token, enclave key) are implementation notes inside a UX spec.
- Launch: Clear is disabled in Starting. If the first request hangs for 30 s the user cannot do anything but wait; no escape except the timeout.
- "Hints area shows the full latest LLM reply and nothing else" vs the Ended state showing "closing text" in the same area: consistent, but the closing text may itself contain the invitation to play again, which duplicates the Play again button.
- Section 1 says "app messages live only in the status row", but the Face ID reason string and the confirmation dialog also carry app messages; the claim is too strong.
- Spec header says "one screen"; it also lists four overlays, plus an action sheet. The "nothing else" claim is inaccurate (the action sheet is a fifth overlay).

VERDICT: Substantive. The spec covers the required elements but leaves the center-on-launch requirement and session-end logic partial, has a permanent panel that works against the map-dominant preference, and adds a lot of unrequested state machinery (retry, held guess, dimming, conditional confirmation, "Map not moved.") that should be cut.

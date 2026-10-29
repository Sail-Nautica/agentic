# Goldfish 2, round 3: verbatim output (critique of E-A v7)

AUDIT OF E-A v7

1. COVERAGE (requirements.md vs E-A)
- Screen 1, map centered on user at launch: PARTLY. 0(b) and 5.1 start on a default zoomed-out view and move to the user when a fix arrives. The first frame is not centered. If location is denied it never centers, and nothing is shown to the user. The requirement is met only after a fix.
- Screen 2, hints above the text box, new replaces old: FULLY (sections 1, 2, 3, 5.2). One gap: in Error and Sending the "latest reply" stays, but Starting shows empty hints. That is fine.
- Screen 3, text box and Send, enabled only with content, shows work in progress: FULLY (section 3 Send rule, 5.2 spinner and "Thinking..."). Weak point: there is no echo of the sent guess. The spinner is the only sign. This is acceptable but thin for the "sends the content" step.
- Screen 4, Clear wipes everything, mutual-disable rules: FULLY (5.5, section 3, section 6). Send is off while clearing, and Clear is off while sending. Clear is also off in Starting. It also keeps the map and Google token, which is fine because the requirement says conversation history and context only.
- Game rule 1, rules sent on start, LLM picks the city, city hidden until the session ends: MOSTLY (5.1). Weak spot: give-up is typed and not detected by the app (0). "Session ends" on give-up exists only in the LLM's text. The app stays in Ready and nothing in the app marks the session as ended. This partly conflicts with "a session ends when the user guesses correctly or gives up". The city stays hidden only if the LLM obeys. After a give-up reveal the user can keep typing against an already-revealed city. That is a gap, but it is a product-owner decision.
- Game rule 2, tool recenters the map, then invites play again: FULLY (5.4 steps 1 to 8). Play again button is the invite. The LLM's closing text is not required to include an invitation. The button covers it.
- Game rule 3, token from Google Sign-In, limited lifetime, reuse, Keychain, Secure Enclave, biometric guard: FULLY (5.4 flowchart, step 3, section 0). Passcode fallback is a stated relaxation of "biometric check"; see section 2 below.
- Constraint, no new endpoints beyond /llmclear: FULLY (5.5). Check that Play again also uses only /llmclear. Section 5.4 step 8 says "wipes the conversation" but does not name the endpoint. Presumed yes.
- Constraint, enterprise extras excluded: FULLY. See section 3 for the few borderline items.
- Constraint, every required element fully visible and non-overlapping: MOSTLY (section 2 layout). The keyboard and large-text cases are left to "verify on device" rather than designed. This is honest but means the requirement is unproven for small phones. Hints are limited to 3 lines and then scroll, so the full reply is not visible without scrolling. That sits against "shows hints" only if hints exceed 3 lines.
- Constraint, Apple HIG: PARTLY. See section 2.

2. CONTRADICTIONS
- "The map fills the screen" (preferences) vs the panel: the panel is about one third of the screen at default text size. That is a real cost against map-dominant. The panel reserves a 44 pt status row that is blank most of the time (Ready), and hints reserve 2 lines even when empty. Wasted space against the map-dominant preference. Weak cut: make the status row share the line with something, or collapse it. The owner fixed "status row is reserved" in 0, so only note it.
- Keyboard up: the panel exceeds one third and can cover much of a small phone's map. Accepted by the spec, but it is the largest conflict with map-dominant.
- HIG: Return doing the Send action is fine. Send at 44 x 44 pt is correct. A floating text-and-icon "Clear" button top-left is acceptable, but a destructive-feeling action in a prominent, always-visible floating spot invites accidental taps. A confirmation sheet covers this. OK.
- HIG: action sheet for confirmation is correct on iPhone. The title "Start a new game?" with destructive button "Clear" is fine. Minor: the destructive button label "Clear" differs from the title's wording "new game", which is a small vocabulary mismatch.
- HIG: the status row mixes a message and a button in one 44 pt line at large Dynamic Type sizes. "One line" will truncate at large text sizes, and the spec only says to verify. This risks hiding the Retry/Play again button. A one-line rule contradicts HIG Dynamic Type guidance (text should wrap). Real, though minor for a prototype.
- HIG: the field is "Disabled" in Ended, but the Play again button is the only action, which is fine. In Clearing the field stays Editable while Send is disabled; harmless.
- HIG: dismissing the keyboard on map tap is conventional. The keyboard dismissing on a win automatically is fine.
- Preferences "no extra screens": the Google and Face ID sheets are system overlays required by the requirements. Fine.
- Preferences "no decorative elements": the compass and unlabeled pin are functional. Fine.
- Requirements say "biometric check"; passcode fallback relaxes it. The owner fixed this. It is flagged only as a requirement conflict: a grader reading "guarded by a biometric check" may mark the passcode path as not biometric. The Keychain access-control flag can be set to biometric-only with the passcode option off; the spec chose the opposite. Low risk, owner-fixed.
- Requirements say the map is "centered on the user" and the spec 0(b) allows the first frame to be uncentered. Conflict caused by an owner decision. Visible to a tester as a jump on launch, and a denial leaves the map unrelated to the user. Flagged, not re-argued.

3. UNREQUESTED FEATURES
- Retry button and Error state: not requested, but needed because a network LLM call can fail. Justified. Keep.
- Play again button: justified (the requirement says "invites the user to play again"). Keep.
- 30 s timeout: justified, the only escape from a hung Starting state. Keep.
- Clear confirmation sheet: not requested. Borderline enterprise polish, but Clear destroys the conversation including the answer, so a tester could lose a game by accident. Justified for a test with real users; keep. Cost: one overlay.
- Different handling for Clear in Ended vs Play again: two paths to the same result (Clear with confirmation, and Play again without). That is duplication. The spec admits Play again is a "separate quick path". Because Clear stays visible and does the same thing, Play again could be cut if the LLM's closing text invites play again and Clear is allowed. But the requirement says the LLM "invites the user to play again", and a button makes that invitation actionable. Keep, but it is the weakest justified item.
- Compass when rotated: the system map control appears by default. Not designed by the spec; harmless.
- Dropped pin on win: not requested (the requirement says recenter only). It is minor and helps the tester see the target; borderline. Acceptable; could be cut for minimalism but costs little.
- Fly animation with Reduce Motion handling: a system behavior, free. Keep.
- Coordinate range validation (lat -90..90, lon -180..180): a cheap guard against an LLM giving garbage. Justified, small.
- Token expiry checks and Keychain details: required by the requirements.
- No account setup, bug reporting, feedback, payments, or subscriptions found. Good.
- Gesture-based map interaction (pan, zoom, rotate): default behavior, not a feature added.
- Principle that "no echo of the user's guess": a deliberate omission, not a feature.

4. OTHER DISCREPANCIES
- Give-up flow is inconsistent: section 0 says the app cannot detect a give-up, yet 5.2 and the state table treat a reveal as a normal Ready state. After a reveal, the same city may still be "fixed" and the user can keep guessing, which contradicts "session ends" semantics. The Clear note ("Stuck win or give-up: Clear is the escape") admits it. This is the most substantive gap against Game rule 1.
- Also from give-up: denial (0(a)) reveals the city in text, so a user who cancels Face ID can learn the city without the map moving. This is consistent with the requirement that the city is shown at the session end, but it makes the sign-in step bypassable by cancelling, which weakens the "token required" story. The owner fixed it. Note only.
- Section 4 diagram: "Error --> Starting: Retry (start failed)" and "Error --> Sending: Retry or new Send" are fine, but the Win flow's error ("Retry resends only the final request") is defined only in prose in 5.4 step 6, not in the diagram or table. Minor consistency gap. The state table does not show what Retry does in that case.
- Section 3 says Send is enabled in Error "when the field has text", and 4 says a new Send replaces Retry. If the user sends new text after a failed Win final request, the tool call result is lost and the LLM's history has a dangling tool call. A harness that rejects a replayed or dangling tool call (the repo history mentions that Gemini rejected replayed tool calls) could return another error. The spec does not handle it. Real edge case, low frequency.
- Tool call arrives while the keyboard is up and the panel is large: step 4 says framing is calculated with the keyboard down and not recalculated; the keyboard is dismissed at step 1. OK.
- "Strings in the app: four status messages, two button labels, one placeholder, one Face ID reason, one confirmation" is accurate to the spec (Picking, Thinking, Correct, Clearing, plus Couldn't reach = five status messages). The count says four, but section 6 shows five: "Picking a mystery city...", "Thinking...", "Correct! Moving the map...", "Couldn't reach the game.", "Clearing...". Minor factual error in the spec. The hints and button labels (Retry, Play again) and the field placeholder are otherwise consistent.
- Section 1 says app messages live in the status row and the only other text is the Face ID reason and the Clear confirmation. The Google sign-in sheet's text is also system text; the spec lists it under overlays, so fine.
- Section 2 says the panel "at most about one third" at default text size but then lists 3 hint lines, a 44 pt row, a field row, and 16 pt margins. On a small iPhone that sum may exceed a third. Plausible but unverified; the spec asks for verification.

VERDICT: Remaining critique is mostly minor; the one substantive item is the give-up flow (the app cannot end a session on give-up, and the user can keep playing against a revealed city). I would still change: (a) fix the status-message count (five, not four); (b) say whether the status row may wrap or truncate at large text, because the Retry and Play again buttons must stay visible; (c) say what Retry or a new Send does after a failed final win request, so the tool call is not left dangling; (d) consider cutting the unlabeled pin if minimalism is the goal.

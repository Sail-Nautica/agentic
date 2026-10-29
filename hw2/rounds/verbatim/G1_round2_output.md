# Goldfish 1, round 2: verbatim output (critique of E-A v2)

REVIEW OF E-A v2 (Mystery City iOS prototype), per screen/state. The app is one screen; "screens" below are the overlays plus the distinct states that change what the user sees.

A. MAIN SCREEN, READY (idle game)
1. Purpose: Player reads the latest LLM reply (a hint) and types a guess, a hint request, or "give up". The map is the backdrop and is only moved by the app.
2. Obvious interactive element: the guess field plus Send. Tap Send: clears the field, keeps the keyboard up, shows "Sent: <text>" in the status row, goes to Sending. Not ambiguous. Tapping the map dismisses the keyboard (fine). Clear (top-left) opens a confirmation sheet; clear.
3. Top three visuals: (1) the full-bleed map, (2) the hints panel text, (3) the input row. Mismatch: the map is the biggest thing but is only decoration until the win, and it shows the user's own neighbourhood, which is not the answer. The hints text should dominate; at 5 lines of Body text in a rounded panel it likely does, but the map's visual weight competes with it.
4. Confusing items:
 - The blank 44 pt status row sits between the hints and the input, so there is a dead gap on most of the screen's life.
 - The map shows the user's own location while the game is about guessing another city; testers may think the map is a hint or a clue.
 - "Give up" is only discoverable via a long placeholder that will truncate in a narrow field at Dynamic Type sizes; the spec also relies on the LLM to mention it in the first hint, which the app cannot guarantee.

B. STARTING (launch)
1. Purpose: Shows that the game is loading while location is fetched in parallel. Everything is locked.
2. Obvious element: none is usable. Disabled field, Send, Clear. The map is touchable. No ambiguity, but nothing to do for up to 30 s.
3. Top three: (1) map, (2) spinner and "Picking a mystery city..." (3) muted "Waiting for the first hint". Order is fine.
4. Confusing items:
 - Map flies to the user's position while the user is waiting; spec says it is skipped if the user touched the map, but "touched" is not defined (a pan, a tap, any touch?).
 - The location-permission alert appears over a spinning screen; if the user is slow, the 30 s timeout may fire in StartFailed while the alert is still up. Is the timer paused? Not stated (it is only paused for Google/Face ID sheets).
 - The "Location is off" message shares the one status row with the "Picking a mystery city..." spinner. Which wins? Section 5.1 says it shows "once" but the row holds one message.

C. STARTFAILED
1. Purpose: Tells the user the game could not start and offers a retry.
2. Obvious element: Retry (44 pt). Tap returns to Starting with a fresh conversation. Not ambiguous.
3. Top three: (1) map, (2) "Couldn't start the game." (3) Retry. The Retry button should arguably outrank the map; it is small inside a footnote-sized row.
4. Confusing items:
 - Hints area shows "Last text if any", which is odd after a fresh failure; probably the placeholder or empty.
 - Clear is disabled, so Retry is the only escape; fine, but there is no distinction between a network failure and a bad API key, so a tester cannot tell why.
 - Footnote text for the only error message is small for such a blocking state.

D. SENDING
1. Purpose: Waits for the LLM, with the guess echoed so the user knows what was sent.
2. Obvious element: field is still editable (for drafting). Typing does nothing visible except enabling nothing, since Send stays off. Tap on Send does nothing (disabled). Mildly ambiguous: an editable field with a disabled Send.
3. Top three: (1) dimmed stale hints text, (2) spinner plus "Sent: ..." (3) map. The dimmed hint becomes the heaviest area while being deliberately de-emphasized; the status row is the real focus and is small. Mismatch.
4. Confusing items:
 - The only echo of the user's message is one truncated line in a footnote-sized row; long guesses vanish, and after the reply the echo is gone. The user never sees the conversation, only the latest reply, so they cannot review earlier hints.
 - Return key behaviour: field says it "obeys the same rules" but the Return key labelled Send does nothing here; no feedback specified.
 - The field is cleared on send, but if the send fails the text is not restored; the user must retype or press Retry.

E. AUTHORIZING (win in progress)
1. Purpose: Warns that a Google sign-in and/or Face ID prompt is coming so the map can move.
2. Obvious element: none; field is editable but Send is off. The next thing the user sees is a system sheet, which is the real interaction.
3. Top three: (1) dimmed hints, (2) "Correct! Signing in to move the map" (3) the system sheet that follows. The win celebration is a small footnote line; the emotional payoff is weak.
4. Confusing items:
 - "Signing in" is wrong when the token exists and only Face ID appears.
 - The message appears and the sheet appears almost simultaneously; the user cannot read the warning, which the spec calls "the only warning".
 - The hints area is dimmed as stale, but the user has just won and the text still shows the previous hint. Reading it implies the game is not finished.

F. GOOGLE SIGN-IN SHEET (overlay)
1. Purpose: Gets a Google token the first time (or after expiry).
2. Obvious element: the Google account entry; cancel dismisses the sheet. Cancel leads to Denied, which is clear in the spec but not to the user: they may think they can retry.
3. Top three: it is the system sheet: (1) account fields, (2) Google branding, (3) cancel. Matches its purpose.
4. Confusing items:
 - Test-mode OAuth client shows an "unverified app" warning in Google's flow; testers may balk. Not mentioned.
 - Nothing says why the user must sign in to Google to see a city on a map; the one-line warning is vague.
 - Cancelling is irreversible for that game (no map move, no retry), with no warning that cancel forfeits the map move.

G. FACE ID / TOUCH ID PROMPT (overlay)
1. Purpose: Releases the stored token.
2. Obvious element: the biometric itself or Cancel. Cancel = denied.
3. Top three: reason string, Face ID glyph, Cancel. Fine.
4. Confusing items:
 - On the first win the user sees Google sign-in, then immediately Face ID; the spec admits this is odd.
 - Reason text says "saved sign-in", but on the first win the user just signed in and nothing was "saved" from their view.
 - Passcode fallback is allowed but denied on no passcode with message "Map not moved." which does not say why.

H. ENDED (won or gave up)
1. Purpose: Shows the closing text from the LLM and lets the player start over.
2. Obvious element: Play again in the status row. Tap restarts with no confirmation. Clear (top-left) does the same; two buttons, same effect, in different places.
3. Top three: (1) map (now moved, with pin, on a win) (2) closing text in hints (3) Play again. On a win, the map is the payoff, so correct; on a loss or denial the map did not move and the hints text should lead, which it does not.
4. Confusing items:
 - "Map not moved." beside Play again: the spec says "or ... beside it", so two messages in a single 44 pt row with a button could clip at large text sizes.
 - Clear is labelled "Clear" but acts as "Play again" here; the label and VoiceOver name ("Clear, start over") do not match the behaviour in mid-game vs ended states.
 - The pin, if any, stays visible until restart, but the next game starts on the map where it is, so the first location fly-to may be skipped (unspecified: does Starting re-center on the user?). 

I. CLEAR CONFIRMATION (action sheet)
1. Purpose: Prevents accidental loss of the game.
2. Obvious element: the destructive "Clear" button. Tap goes to Clearing then Starting. Cancel returns. Not ambiguous.
3. Top three: title, destructive button, Cancel. Fine.
4. Confusing items:
 - The sheet's button is called "Clear" while the screen's button is also "Clear"; the title says "Start a new game?" so the labels are inconsistent. "Start new game" would match.
 - Message says "forgets the conversation" but does not say the Google token is kept, which a tester may care about.
 - Clear is far from the thumb (top-left) and the sheet appears at the bottom; fine but it means a big thumb travel.

J. CLEARING and SENDFAILED (brief states)
- Clearing: purpose is to wipe state; hints blank, spinner "Clearing...". It flashes by almost instantly (a local wipe), so a spinner that exists only to be "testable" is a flicker; no minimum display time is given.
- SendFailed: purpose is to offer Retry. Obvious element is Retry; tap resends the failed message. The spec lets the user type a different draft and press Send, which silently discards the failed message. Confusing: two ways to continue, one silent loss; Retry vs. Send ordering is not visually cued.

OVERALL: IS THE SPEC SUFFICIENT TO BUILD WITHOUT QUESTIONS?
Mostly yes for layout and state flow, but not fully. It is strong on state tables and timing; it leaves these gaps:
- Colors, spacing beyond margins, the panel's corner radius, dim amount for stale text, and pin style are unspecified; fine for a prototype, builder will choose.
- Real gaps (would stop a builder):
 - Where does the Starting flow re-center for game 2? "Map stays where it is" vs. location fly-to on Starting: does 5.1 step 4 repeat on restart?
 - What counts as "user touched the map" (cancels the fly-to)?
 - 30 s timeout during the location permission alert: running or paused?
 - Status row can have two messages at once (location off plus start spinner, "Map not moved." plus Play again, echo plus a pending message). Priority order is undefined.
 - The status row echo and error text at large Dynamic Type: one line with ellipsis, but "Couldn't reach the game." plus Retry may not fit; no wrapping rule.
 - "Hints area: Last text if any" in StartFailed and the Clearing "Empty" state: conflicts with the placeholder text rule (empty vs. "Waiting for the first hint").
 - Ready + Return key when Send is disabled (empty/space-only field): behaviour not stated beyond "same rules".
 - Authorizing: spec lists the field as editable but the earlier text implies Send is off; what happens to Return? Also, the Authorizing->Sending transition label says the tool result is returned; the user-visible status line during that follow-up call is not specified (does "Sent: ..." come back?).
 - How is a "win" known? The LLM calls a recenter tool; the tool schema (name, arguments) and the system prompt are not specified here (maybe elsewhere), and the app has no fallback if the LLM never calls it, so a tester can win but stay in Ready forever. The spec acknowledges this but offers no way out except Clear.
 - Keyboard behaviour: tapping the map dismisses the keyboard, but there is no way to bring the keyboard back other than tapping the field; fine. Not blocking.
 - Pin: "dropped, no label"; what happens to a second game's pin (removed on Clear, fine).
 - Ended with Clear enabled: the spec says Clear in Ended restarts "at once", but Play again also exists; which one should be primary is unstated.
 - Offline detection: how does the app know "offline" vs. "couldn't reach"? Not defined (use system reachability? based on error code?).
- Contradictions to resolve:
 - Section 3 says Send is enabled only in Ready/SendFailed, while the field is editable in Sending/Authorizing; the placeholder text for those states ("shorter placeholders in other states (see section 6)") is promised but section 6 never lists the placeholders.
 - Section 2 says the panel is capped near 45 percent of screen height, while the keyboard-up case says hints shrink to 3 lines; at largest Dynamic Type with keyboard up, the three rows may exceed the visible area above the keyboard. The compass "top-right if rotated" could clash with a status bar and the floating Clear on small phones; the spec claims no overlap without a stated safe-area rule.
 - Section 5.4 step 7 says the camera is framed at 25 km across, yet a country-sized or tiny city answer may fit poorly; fine for prototype.
 - Section 1 says all app messages go in the status row, but the Ended state needs "Map not moved." and a button in the same row.

SUBSTANTIVE VS NITPICK
- Substantive (ask before building): status-row message priority and overflow; pause rules for the 30 s timer during the location alert; map behaviour on game 2 restart and the "touched" definition; missing placeholders for non-Ready states; how a stuck win (LLM never calls the tool) is escaped; Return-key behaviour in disabled-Send states; misleading "Signing in" copy when only Face ID appears; Clear/Play again duplicate and naming mismatch; hints area contents in StartFailed/Clearing.
- Nitpicks or out of scope: colours, radii, animation timings, the Google "unverified app" warning, Clearing flicker, cross-fade details, test-mode client note, VoiceOver wording, Reduce Motion details.
Verdict: the spec is about 85 percent buildable as-is; the substantive items are a short list of state-edge decisions, not structural problems.

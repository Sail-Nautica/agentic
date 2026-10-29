# Goldfish 1, round 1: verbatim output (critique of E-A v1)

REVIEW OF E-A_v1.md (Mystery City iOS prototype UX spec)

Overall verdict: NOT sufficient to build without questions. The single-screen layout is clear. But the spec has one hard contradiction (the Won/GaveUp states), several undefined behaviors (Play again, Retry, Clear confirm), and it never says what the hints look like. A builder would need roughly 10 answers before starting.

Note: the spec has one screen, one overlay (the Clear confirmation, as an action sheet), and two system sheets (Google sign-in, Face ID). Also treated as distinct states here: the status line variants and the end-of-game state.

==================================================
1. MAIN SCREEN (map + bottom panel), Ready state
==================================================
Purpose: A full-screen map with a bottom panel where the player reads the current hints and types guesses or questions. The map is the backdrop and the payoff, since it only moves when the player wins.

Most obvious interactive element: the Send button (filled, arrow.up), or the text field.
- Tap on Send: sends the text, clears the field, shows "Thinking...", disables Send and Clear until the reply arrives, then replaces the hints.
- Ambiguity: low for Send. But the keyboard stays up during Sending and the user can keep typing. Tapping the map or dismissing the keyboard is not specified.
- Ambiguity about the Clear icon: it is "trash-style OR arrow.counterclockwise". The spec does not pick one. Trash suggests permanent deletion. Counterclockwise suggests undo. This is a real build question.

Top three visual elements, ranked by what the spec implies:
1. Map (full bleed).
2. Hints block (the only LLM content shown).
3. Input row.
Does this match the purpose? Partly. The core task is read hints, then type. The hints should be the visual focus, but the spec gives them only "plain text" in a panel capped at about 4 lines, so the map visually dominates. The map is idle until a win, so it is mostly decoration for most of the session. In practice the user's eye goes to the input row and hints, and the spec never states typography or hierarchy for the hints.

Confusing, ambiguous, or badly placed items:
- The Principles section says "Everything else floats on top of it in a bottom panel", while the layout puts the status line above the hints. A status line that appears and disappears will push the hints up and down, which makes the layout jump on every send. The spec does not reserve space for it.
- Clear sits right next to Send in the same row, at the same size (44 pt). A mis-tap is the very reason for the confirmation sheet. Placing a destructive control beside the primary one is a design smell the spec patches with a dialog instead of moving it.
- Hints area: "one block per current hint" is never defined. How many hints are there? What does a hint look like? Where does the player's own guess appear? The transcript is hidden, so after Send the user's own message vanishes (the field clears) and there is no echo. The user cannot see what they asked while waiting, and cannot see whether the new hints answer their question.

==================================================
2. STARTING state (launch / new game)
==================================================
Purpose: The app asks the LLM to pick a secret city while the user waits. The first hints appear when it is ready.

Most obvious interactive element: the text field (Send is disabled).
- Tap on the field: opens the keyboard. Typing is allowed but nothing can be sent. Not ambiguous, but pointless for the user.

Top three visual elements:
1. Map (and the location permission prompt on first launch).
2. Status line with spinner "Picking a mystery city...".
3. Empty/placeholder hints area.
Does this match? Roughly. But the spec says the first hints "replace the placeholder text" in the hints area, and the placeholder text is never specified.

Confusing items:
- Location permission prompt and the game start run in parallel. The system prompt will cover the panel and the user may think the app is stuck.
- The text field placeholder says "Guess a city or ask for a hint" while Send is disabled and nothing has been revealed. It invites input that cannot be used.
- Clear is disabled in Starting (A4). If the start hangs, the user cannot clear, and only the (unspecified) timeout helps. The 30 s timeout is described only for Send, not for Starting.

==================================================
3. START FAILED state
==================================================
Purpose: Tells the user the game could not begin and offers a retry.

Most obvious interactive element: the inline Retry button in the status line. Tap returns to Starting. Not ambiguous.

Top three visual elements:
1. Status line error message with Retry.
2. Map.
3. Input row (disabled Send).
Does this match? Yes, but the error is a small secondary-text line ("Small secondary text"). An error that blocks the whole game is shown in the least prominent style in the panel.

Confusing items:
- Status line is "small secondary text", yet it carries the Retry button. Is the button 44 pt tall? The spec says all targets are 44 pt, but a small inline button in a one-line status row conflicts with that.
- The hints area is empty here and nothing says what is shown in it (blank gap?).
- Clear is enabled here and does a full wipe and restart. That duplicates Retry and confuses which one to tap.

==================================================
4. SENDING / THINKING state
==================================================
Purpose: Shows that the LLM is working on the reply, and locks Send and Clear.

Most obvious interactive element: none really; the text field remains active for drafting.
- Tap on the field: lets the user type the next message. Send stays off. This is a surprising rule (A5): the user can type but not send.

Top three visual elements:
1. Status line spinner "Thinking...".
2. The old hints (still showing).
3. Disabled buttons.
Does this match? Mostly. But old hints stay on screen until the reply, so the user may re-read stale hints and think nothing happened.

Confusing items:
- No Cancel for up to 30 s. A slow LLM call (with tool calls, sign-in, and Face ID) plausibly takes longer than 30 s, especially if the user is in the middle of Google sign-in. The spec does not say whether the timer pauses while the system sheets are up. If it does not pause, a slow sign-in causes a false timeout.
- The user's sent message disappears from the field and is not shown anywhere. They cannot confirm what was sent.
- Return key = Send, but the Return key stays active while Send is disabled. What does Return do while Sending? Presumably nothing, but it is not stated (the table says "same rules as Send", which implies ignoring it).

==================================================
5. SEND FAILED / OFFLINE state
==================================================
Purpose: Tells the user the request did not go through, and restores their text so it can be re-sent.

Most obvious interactive element: the inline Retry button.
- Tap on Retry: ambiguous. Does it resend the restored text automatically, or just clear the error so the user taps Send? The spec never says. Also, if the user typed a draft while waiting (A5), the restored text collides with the draft. Which wins, or are they concatenated?

Top three visual elements:
1. Status line error.
2. The text field with the restored text.
3. Hints (old).
Does this match? Yes.

Confusing items:
- Summary table says "Offline: You're offline." with no Retry and Send Off. But 5.2 says offline is detected only by a failed request, which is the Send-failed case with Retry and Send On. These two rows contradict each other.
- Send is "On if text present" in Send failed, but Offline says "Off". It is the same event and the two rows disagree.
- The game could have changed server-side before the failure (the LLM may have processed the message and the reply was lost). A retry could double-count a guess. Not addressed.

==================================================
6. AUTHORIZING state (status "Checking sign-in...")
==================================================
Purpose: After a correct guess, the app gets permission to move the map by checking a token, which may mean signing in with Google and/or Face ID.

Most obvious interactive element: none on the panel (everything is disabled); control passes to the system sheets.
- The user's only action is on the system sheets.

Top three visual elements:
1. System sheet (Google or Face ID).
2. Status line "Checking sign-in...".
3. Map.
Does this match? Yes.

Confusing items:
- The user has just typed a correct guess and gets "Checking sign-in..." with no sign that they won. A surprise Google login right after a winning guess, with no explanation, is the biggest usability risk in the flow. The spec gives no pre-sheet explanation.
- Face ID is required every time even when the Google token is valid (see 5.3 point 5 and Q2). Every win triggers a biometric prompt, which is heavy for a map move. The flowchart is also inconsistent: the diamond asks "valid token in Keychain" and routes Yes to Face ID, which matches, but "No biometrics enrolled" says to skip biometrics and use passcode only, which is itself a biometric-framework fallback, not "skip".
- The Face ID reason text "Allow the game to move the map" reads like it is about the map, not about account access. Fine, but a Google sign-in sheet shows nothing about what the game is.

==================================================
7. GOOGLE SIGN-IN SHEET (system overlay)
==================================================
Purpose: Gets a Google token the first time (or after expiry).

Most obvious interactive element: the account picker/consent buttons in the Google sheet (not controlled by the app).
- Tap on Cancel: returns to the game, status "Sign-in cancelled. Map not moved.", and the LLM is told the tool is denied. The LLM then reveals the city in text.

Top three visual elements: Google account list, consent text, Cancel/close. Matches, since it is a system sheet.

Confusing items:
- A cancel here ends the game as a win with no map move; "Won" state vs. GaveUp is not stated for the denied case. The state diagram goes Authorizing to Sending to Won, but does a denied path still reach Won? The diagram only shows "Won: correct guess, map recentered".
- The user cannot retry the map move after denying. Is there a way to try again? Not stated.
- "Cancelled" message vs. what the LLM then says may conflict (two messages: a status line and an LLM text).

==================================================
8. FACE ID / TOUCH ID PROMPT (system overlay)
==================================================
Purpose: Confirms it is the user before the stored token is used.

Most obvious interactive element: Cancel (and Use Passcode).
- Tap on Cancel: treated as denied, "Authorization cancelled. Map not moved."

Confusing items:
- Same win-with-no-map-move ending as above, not captured in the state model.
- Two distinct messages ("Sign-in cancelled" vs. "Authorization cancelled") are shown for similar things.
- "No passcode on device" shows "Set a device passcode to continue" then treats as denied. That text says "continue", but nothing continues.

==================================================
9. WON / GAVE UP state
==================================================
Purpose: Tells the user the answer and invites them to play again. The map flies to the city and drops a pin on a win.

Most obvious interactive element: the "Play again" button in the status line position.
- Tap: removes the pin, keeps the map where it is, goes to Starting. Not ambiguous in outcome, but see below.

Top three visual elements:
1. Map animation and pin (on a win only).
2. Hints area with the congratulation and city name.
3. Play again button.
Does this match? Partly. The win payoff is the map flight, but the hints panel covers the bottom part of the map where the city may land. The spec never says to offset the camera so the pin is not hidden behind the panel. This matters because the panel takes about a third of the screen.

Confusing items:
- Direct contradiction: 5.4 says "Sending any text while ended is treated as 'yes, play again'" but then says "the app starts a new game only through the button or Clear". Which is it? The state diagram says Won to Starting on "sends any text". Both cannot be true.
- Won and GaveUp: Send is "On", and typing a message sends it to the old LLM conversation, but the state diagram says it goes to Starting. Does the typed text get sent as the first message of the new game or discarded?
- Give up has no button (A1). A user who wants to quit must know to type "I give up". Nothing in the UI tells them. The placeholder text only says "Guess a city or ask for a hint". For a usability test this is a discoverability trap.
- A2: no recenter on give up, so the user's map stays on their own location. The pin text says the pin is dropped on a win only, so on give up there is no visual reveal at all. Fine, but flat.

==================================================
10. CLEAR CONFIRMATION (action sheet overlay)
==================================================
Purpose: Asks the user to confirm before wiping the session.

Most obvious interactive element: the red "Clear and restart" button.
- Tap: starts Clearing, empties hints, field and pin, then restarts at Starting. Not ambiguous.

Top three visual elements:
1. Destructive "Clear and restart".
2. Title "Start a new game?".
3. Cancel.
Matches.

Confusing items:
- On iPad, an action sheet becomes a popover anchored to the button. Spec says iPad is out of scope but says "same layout", so a builder must guess.
- Play again is described as "same as Clear without confirmation". But Clear fails with an error message while Play again has no failure path described.
- Clearing a Won game makes the confirmation arguably unnecessary, yet it is still shown for Clear from Won/GaveUp. Inconsistent with the stated reason (a mis-tap corrupts the session) because the session is already over.

==================================================
11. CLEARING state
==================================================
Purpose: Brief busy state while the conversation and pin are wiped, then a new game starts.

Most obvious interactive element: none (everything disabled).

Confusing items:
- The text field is "enabled except while Clearing", so it goes disabled and dismisses the keyboard (or does it?). Not stated.
- If Clear is only local (drop history), why would it need a failure state "Couldn't clear"? Unclear what can fail.
- Q4: map not moving back, but the old pin is gone and the user may be far from where they were.

==================================================
OVERALL: CAN IT BE BUILT WITHOUT QUESTIONS?
==================================================
No. Gaps and questions:

Contradictions to resolve
- Won/GaveUp: does typing text start a new game, or only the button/Clear? (5.4 contradicts itself and the state diagram.)
- Offline row vs. Send-failed row in the summary table.
- Clear icon: trash or counterclockwise?
- Authorizing: denied/cancelled path ends in Won? The state diagram has no arrow for it.
- Clear during Starting is disabled, but the Starting row in 5.1 lists no timeout, so a hung start locks the game forever except via Retry (which only exists after a failure).

Missing definitions
- What a hint is: count, formatting, how the first reply looks, what the "placeholder text" in the hints area is before the first reply.
- Whether the user's own message should be echoed anywhere.
- What Retry does after a send failure (resend automatically vs. restore only), and how it merges with a draft typed meanwhile.
- Whether the 30 s timeout pauses during Google/Face ID sheets, and whether it applies to Starting.
- Map camera framing on a win: offset so the pin is visible above the panel; default "city scale" and "default wide view" zoom values; default region when location is off.
- How the app discovers the city's lat/lon (tool arguments?) and what happens if the LLM returns bad coordinates.
- Panel visual details: corner radius, margins, padding, hint font size, spacing between status line and hints, and whether the panel collapses when the keyboard is up in landscape (bottom third minus keyboard leaves almost no room).
- How a user finds out they can type "I give up".
- Whether the map is interactive while the panel is open (tap on map to dismiss keyboard?).

Questions for the author
- Is Face ID on every win intended? It adds a prompt to the single most emotional moment of the game.
- Should there be a one-line explanation before the Google sheet ("Sign in to let the game move the map")?
- Is the sequence "sign-in → Face ID" clear enough for a test participant, or will they think they did something wrong?
- Should Clear be moved away from Send to cut mis-taps rather than relying on the confirmation?
- Should the hints area stay visible with a pending indicator rather than showing stale hints during Thinking?

Minor
- Spec says "one screen, one overlay, two system sheets", but the Face ID and Google sheets are part of one flow that can chain, and the status line states are effectively sub-screens. Count is fine, but a builder will need a per-state UI list; this spec offers it only as a table.
- Section 1 principle "user sees hints and nothing else from the LLM" conflicts with the congratulation text and the error "the LLM tells user the map could not move" being shown in the hints area. Those are not hints.

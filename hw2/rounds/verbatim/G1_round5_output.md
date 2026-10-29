# Goldfish 1, round 5: verbatim output (critique of E-A v5)

REVIEW OF E-A v5 (build-from-spec critique, native iOS view)

Scope note: states and overlays are reviewed one by one. States that share a layout (Ready/Sending/SendFailed, Finishing/FinishFailed) are grouped where the analysis is identical.

PER-SCREEN / STATE ANALYSIS

1. Main screen, Starting (launch)
- Purpose: The map shows while the app silently starts a game. The user waits for the first hint.
- Obvious interactive element: the map. Pan/zoom works, but nothing else is live. Field, Send and Clear are all dimmed. Nothing in this state has an ambiguous transition. Time-to-Ready is the only "transition", and it is automatic.
- Top 3 visuals: (1) the map, (2) the spinner plus "Picking a mystery city..." in the status row, (3) the muted hints placeholder. The order matches the purpose, but the map dominates while the user's real task is to wait for the text.
- Confusing items: (a) The user can't tell that the map is not the game. Nothing says "a city is hidden, you will guess". The first reply is the only explanation. (b) The fly-to to the user's location may happen while they read, and nothing explains it. (c) The status row is footnote-sized and secondary-colored, so the only "something is happening" signal is the weakest text on screen.

2. StartFailed
- Purpose: The game couldn't start. The user can only retry.
- Obvious element: Retry. It resends the rules to a fresh conversation and goes back to Starting. Clear. Unambiguous.
- Top 3: (1) the Retry button (prominent), (2) the error line, (3) the map. The map ranks third because the panel has no hint text, which fits.
- Confusing items: (a) Clear is dimmed here but visible, so the user sees a greyed button with no reason. (b) Error text says "Couldn't start the game." with no cause and no offline wording, unlike SendFailed's offline/unreachable split. Inconsistent. (c) The first-launch location prompt is delayed until the state leaves Starting, so on a failed start the permission prompt appears over an error screen with nothing to guess yet.

3. Ready (also after a give-up)
- Purpose: The user reads the latest hint and types a guess, a question or "give up".
- Obvious element: the text field. Tapping it opens the keyboard, and the panel rides above it. Send is the other candidate. It is enabled only with non-blank text, and with a blank field the Return key dismisses the keyboard. Not ambiguous.
- Top 3: (1) hints text (Body, large), (2) the text field with Send, (3) the map. Matches purpose. Clear is a floating button of the same visual weight as the map controls, so it is a risk to rank it above the content.
- Confusing items: (a) A given-up game looks identical to an active game. After the LLM reveals the city, the user sees "Guess, hint, or give up" again and has no cue that the game is over. The spec accepts this, but it is the most likely test confusion. The user keeps chatting with a finished game, and the only exit is the Clear button, whose label ("Clear") doesn't say "new game". (b) The give-up reminder depends entirely on the LLM's first reply. The placeholder vanishes when typing starts. If the LLM omits it, a first-time user may never learn the give-up phrase. The spec says "the app shows nothing extra", so a cheap fix is ignored. (c) The location-off notice disappears after 5 s or on first Send, but it occupies a reserved row. A tester might miss it and wonder why the map stays on the world view.

4. Sending
- Purpose: The message is in flight. The user can still draft the next message.
- Obvious element: the field, still editable with the keyboard up. Typing is the only action. Send is dimmed. Return does nothing. No ambiguous transition.
- Top 3: (1) the dimmed hints, (2) the status echo "Sent: <text>" with spinner, (3) the field. The dimmed old hint is the biggest thing on screen but is "stale", so the visual weight is on the wrong thing for a few seconds. The spec accepts it.
- Confusing items: (a) The field clears on send, but the user's own text then lives only in the footnote status echo (secondary color, cut at two lines). A long guess is not visible in full. The spec says the echo is only a confirmation, which is fine. (b) The user can type a draft during the wait, then Send is still dimmed, and Return does nothing silently (spec: "visibly dimmed and a spinner"). Silent no-op on Return is fine in a prototype. (c) A reply could take up to 30 s with no way to cancel. Clear is dimmed too, so the user is locked out for 30 s on a slow network.

5. SendFailed
- Purpose: The send failed, and the user can retry the same message or send something new.
- Obvious element: Retry (prominent, in the status row). It resends exactly the failed text and goes back to the "Sent:" echo. Unambiguous. Sending a new draft instead silently drops the failed message, which is explained only in the spec, not on screen.
- Top 3: (1) Retry button, (2) the error line (semibold, with triangle symbol), (3) the hints. Matches.
- Confusing items: (a) The dropped message is not recoverable once the user sends something else, and nothing warns them. (b) "Not sent: <text>" is cut to one line, so a long guess can't be verified. (c) Both Retry and Send are live and look similar, and the placeholder ("Type a new message, or tap Retry") is the only guidance, hidden once typing begins.

6. Authorizing (win in progress)
- Purpose: The LLM said the guess is right. The app must sign the user in and verify their identity before it moves the map.
- Obvious element: none in the main screen. Everything is disabled, and the system sheet (Google or Face ID) is the real interaction. A tap on the sheet's Cancel skips the map move. The "Cancel to skip it" clause is the only warning.
- Top 3: (1) the system sheet when it appears (full cover for Google), (2) the status line, (3) the dimmed hint. The status line is read before the sheet appears, then hidden behind it, as the spec admits. This is the weakest screen in the app.
- Confusing items: (a) The first win forces Google sign-in then Face ID back to back, with two different dialogs for what the user sees as "I won, show me the city". Users will cancel one by reflex, and the app treats a cancel as a denial. (b) The word "Correct!" appears in the status row before the hint (the LLM reply that said so) is visible. The hint is dimmed. A user may read "Correct!" with the hint not visibly confirming it. (c) Why a game would ask for Google sign-in at all is never explained to the tester. The text says "to move the map", which makes it sound optional, so a tester may cancel as the "safe" choice and miss the demo of the main feature.

7. Finishing / FinishFailed
- Purpose: The app returns the tool result and waits for the closing reply. If that fails, the user retries only that step.
- Obvious element: in Finishing, none (all dimmed). In FinishFailed, Retry. Unambiguous. Clear is live as the escape.
- Top 3: (1) status row (spinner or error plus Retry), (2) the map, which has just flown to the city, (3) the dimmed hint.
- Confusing items: (a) In FinishFailed the error begins "Correct!" and then "Couldn't load the final message." Two tones in one line. (b) Clear is live here with a confirmation that says the game's answer will be forgotten, but the user has just won, and the pin is visible. The message mismatches. (c) The hint shown is the old "Correct"-type reply while the closing text is missing, so the hints area is stale.

8. Ended (win)
- Purpose: The game is won. The user reads the closing text and taps Play again.
- Obvious element: Play again. It starts a new game with no confirmation, wipes the pin and the closing text, and goes through Clearing to Starting. Not ambiguous, and the spec argues the case well.
- Top 3: (1) hints (closing text), (2) Play again, (3) map with pin. The map with the pin is the win's reward and should arguably rank higher, but the panel covers up to 45 percent of it (the camera inset handles that).
- Confusing items: (a) "Map not moved." is a negative note in the status row with no reason (sign-in cancel, Face ID fail, bad coordinates, no passcode). The tester can't tell a bug from a deliberate cancel. (b) With the field disabled and no Clear button, the user can't ask follow-up questions or copy the closing text, which is fine, but the placeholder is the only instruction. (c) Play again is a one-tap destructive action next to the closing text the user might still be reading. Accepted in the spec, but one mis-tap loses the city name in the denied case, which is the only place the answer is written.

9. Clear confirmation sheet
- Purpose: Confirm a restart that destroys the current game.
- Obvious element: the destructive "Clear" button. It starts Clearing, then Starting. The Cancel button returns. Unambiguous.
- Top 3: (1) the title, (2) the destructive button, (3) the message. Matches.
- Confusing items: (a) The floating button and the sheet's destructive button are both called "Clear", while the user's intent is "new game". (b) The message says it "forgets ... the current game's answer", so a tester who has not given up will be warned correctly, but one who has will be confused about what was lost. (c) Reading the sheet doesn't say the map pin stays/leaves. The spec removes the pin on Clear but never tells the user.

10. Clearing
- Purpose: Wipe the conversation, then start a new game.
- Obvious element: none. Everything is disabled. The only possible interaction is a failure's Retry.
- Top 3: (1) status row spinner, (2) muted placeholder in the hints area, (3) map. Matches.
- Confusing items: (a) The spinner text changes from "Clearing..." to "Picking a mystery city..." in one step with no visible boundary, which is fine. (b) Clearing has an error path ("Couldn't clear." plus Retry) that is not in the state diagram or the state table and has no placeholder/hints definition. (c) Clearing has no 30 s timer defined.

11. Location permission prompt (overlay)
- Purpose: The system asks for location so the map can zoom to the user.
- Obvious element: Allow While Using / Don't Allow (system). Allow triggers a fly-to if the fix arrives before a gesture. Deny shows the location-off notice. Mildly ambiguous: the fly-to can happen under the user's eyes while they read the first hint.
- Top 3: all system-controlled.
- Confusing items: (a) The prompt appears on top of the first hint, per the spec, so the first hint is partly hidden while the user is deciding. (b) The prompt has no purpose string content in the spec. (c) After deny, the notice shows for 5 s only, and only if nothing else is showing.

12. Google sign-in sheet (overlay)
- Purpose: Get a token so the app can release it to the tool call.
- Obvious element: Google account choice or Cancel. Cancel means Denied (map not moved). Sign-in success leads straight to the Face ID prompt. The spec admits no custom text is possible.
- Confusing items: (a) A tester on a test-mode OAuth client must be on the allowed test-user list, or the sheet shows an error. The spec doesn't say what the app shows then (it is treated as Denied, but the user sees a Google error). (b) The warning appears only before the sheet. (c) The sheet is a second hop that has nothing to do with the user's goal.

13. Face ID prompt (overlay)
- Purpose: Confirm the user is present before the token is used.
- Obvious element: Face ID auto-scan; the Cancel button skips the map move. Passcode fallback is allowed. Cancel and failure are the same outcome (denied). Slightly ambiguous: the reason text says "Cancel skips the map move", which is fine.
- Confusing items: (a) The sheet is small, and the status row is visible behind it, so the two messages are redundant. (b) Failing Face ID twice looks the same as cancelling; the user who just mis-scanned loses the map move with no retry. (c) Simulator or devices without Face ID are not covered.

14. Clear button (floating) and compass, as always-present overlays
- Purpose: Clear is the only restart path except after a win.
- Obvious element: Clear itself; it opens the confirmation. Unambiguous.
- Confusing items: (a) The label "Clear" is misleading as a restart; a tester may expect it to clear the text field. The VoiceOver name "Clear, start over" is better than the visible one. (b) It is dimmed in Sending, Authorizing, Starting, which makes it look broken for up to 30 s. (c) Top-left placement beside the status bar is fine, but it is the only way out of a given-up game, and it looks like a map control.

OVERALL: IS THE SPEC SUFFICIENT TO BUILD WITHOUT QUESTIONS?
Mostly, yes for layout, state table and text strings. The status row rules, state table and per-state placeholders are exceptionally complete. A competent builder would still have to ask the questions below.

Gaps and questions (short bullets)
- Give-up has no on-screen cue. How would the tester know the game is over? Is "Clear" the right label, or "New game"?
- Clearing failure: no state, no hints text, no placeholder, no timer. Which state does Retry return to?
- Typing a new message in SendFailed drops the failed one silently. Is that really intended with no warning?
- No wording defined for why the map didn't move (cancel, Face ID fail, no passcode, bad coordinates). One generic "Map not moved." is the only text.
- Google sign-in for a test user not on the list, or no network during sign-in: what does the user see, and is the 30 s timer paused or running? Timer pause applies "while the sheet is on screen", but what about a sheet that never returns?
- Hints area: "up to 5 lines, then scrolls" while the panel cap is 45 percent. Can a long reply be scrolled to the end, and does the area reset to the top on each new reply? Not stated.
- Where exactly does the compass go, relative to the Clear button, on small phones (SE-size)? "Does not overlap" is stated but not shown.
- The hints area has no way to copy text or see an older hint. Fine for a prototype, but the user cannot refer back to a previous clue, which is the main game loop. Is that a deliberate test condition?
- After a win with a moved map, is the pin tappable or labeled? "Standard unlabeled pin" leaves the city name only in the hint text.
- Which iPhone sizes are in scope? Keyboard-up hints at 3 lines on the smallest screen can leave very little map.
- The "Cancel to skip it" clause is the only place the user learns the map move is optional; there is no way to retry the sign-in in the same game after cancelling.
- The first-launch location prompt appears over the first hint; the spec accepts it, but a tester may deny it by reflex and then see a world-view map for the whole session.
- Fly-to is skipped if the user gestures first, but "plain tap does not count" and the keyboard-dismiss tap leave the case of a pan during the Starting spinner undecided in practice (works, but untested).

CLASSIFICATION OF REMAINING ISSUES

Substantive
- Given-up game looks like an active game, and the only exit is a button labeled "Clear" with no on-screen cue. This is the biggest usability risk in the whole test.
- The give-up hint depends on an LLM reply with no app fallback.
- Win flow: two back-to-back system dialogs on the first win, where cancelling one by reflex loses the map move, and the only warning text is hidden behind the Google sheet.
- "Map not moved." gives no reason, so a tester can't tell a bug from their own cancel.
- Clearing failure path is missing from the state diagram, state table, and timer rules.
- Silent loss of the failed message when a new one is sent from SendFailed.
- Play again discards the closing text, which is the only place the city name appears when the map did not move. One mis-tap loses the answer.
- Clear in FinishFailed warns about forgetting "the answer" right after a win; the message doesn't fit.
- Up to a 30 s lockout (Clear and Send both dimmed during Sending) with no cancel.

Nitpick / out of scope
- Placeholder wording differences, the 5 s location notice duration, fonts for the notice.
- Clear dimmed versus hidden styling in StartFailed.
- Error wording inconsistency between start and send ("offline" split only on send).
- VoiceOver label differing from the visible label.
- Pin being unlabeled; compass placement on small phones; screen-size coverage.
- Accessibility-size rules (already thorough for a prototype).
- Copy-text or hint history absence.
- Face ID simulator coverage; Google test-user list errors (setup concerns, not UX).

VERDICT: Not mostly nitpicks yet. The layout, text and state rules are strong and the nitpick list is long, but about nine substantive issues remain, concentrated in three areas: how a user restarts after a give-up, the win/authorization flow's clarity, and the Play again/Clear data-loss edges. Fixing those would turn the critique into mostly nitpicks.

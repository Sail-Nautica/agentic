# Goldfish 1, round 4: verbatim output (critique of E-A v4)

# Critique of Exhibit E-A v4, "Mystery City" iOS prototype

Source read: only E-A_v4.md. I treat it as one screen with several states and four system overlays. The spec's own "Ready" and "Sending" states count as states of that one screen, so I group them.

## A. Per-screen and per-state review

### A1. Main screen, Starting (launch and after Clear)
1. **Purpose:** Show the map while the app asks the LLM to pick a city. The user waits.
2. **Obvious interactive element:** The map (pan, zoom, rotate). Everything else is dimmed. Tapping the map does nothing special, except that it dismisses a keyboard that isn't there. This is not ambiguous.
3. **Visual ranking:** (1) The map, (2) the status row spinner and text, (3) the hints placeholder. This matches a waiting screen. But the map is the dominant element on a screen where the user can do almost nothing, which is mildly odd.
4. **Confusing items:**
   - The hints area says "Waiting for the first hint" while the status row says "Picking a mystery city...". Two messages say nearly the same thing, and one of them is a fake "hint" slot.
   - A disabled field with the placeholder "Starting..." and a dimmed Clear button tell the user nothing about how long this takes. 30 s is a long time.
   - Spec 3.1's priority list mentions "Starting" as progress, but no text is defined for the location notice here. This is minor.

### A2. Main screen, Ready (including "after give-up")
1. **Purpose:** The core play state. The user reads a hint and types a guess.
2. **Obvious interactive element:** The text field. Tapping it raises the keyboard, and the panel rides above it. Send is the other candidate and is disabled until there is non-space text. The resulting transition (Ready to Sending) is clear.
3. **Visual ranking:** (1) The map (full bleed), (2) the hints text (Body, top of the panel), (3) the Send button (filled circle). For a hint-guessing game the hint should win. The order is roughly right, but the map's size makes it the loudest element while the hint is the actual content. A hint capped at 5 lines (3 with the keyboard up) is small relative to the map.
4. **Confusing items:**
   - A gave-up game is identical to Ready. The user sees a reveal in the hints area, with nothing marking the game as over, and the only restart is the small floating Clear. This is the biggest UX problem in the spec (see section C).
   - The placeholder "Guess, hint, or give up" is the only built-in clue to the give-up phrase. The spec never says what phrase counts as giving up, so the user doesn't know what to type.
   - The Clear button sits top-left and the Send button is bottom-right, far apart. A user whose game is over has to find a small control in a different part of the screen.

### A3. Sending
1. **Purpose:** Show that the guess has gone out and a reply is pending.
2. **Obvious interactive element:** The field. It stays editable so the user can draft the next message, but Send is dimmed and Return does nothing. A tap on the field raises the keyboard. This is not ambiguous, but it is odd: the field is editable while Send is dead.
3. **Visual ranking:** (1) The spinner and "Sent: <text>" echo, (2) the dimmed hints, (3) the map. This matches the purpose. The hints are dimmed, so the status row takes over as the focus.
4. **Confusing items:**
   - The keyboard stays up and the field clears, but the user's guess disappears from the text field and shows only in a small footnote-size echo that is cut at two lines. A long message cannot be seen in full.
   - The old hint stays on screen (dimmed) as though still current. Users may think it is the answer to their new guess.
   - Return does nothing, with no feedback beyond a dimmed Send. A user who taps Return repeatedly sees nothing happen.

### A4. SendFailed
1. **Purpose:** Tell the user the send failed and let them retry or send something else.
2. **Obvious interactive element:** The Retry button, filled and on the right of the status row. A tap resends the identical message and moves to Sending. This is clear.
3. **Visual ranking:** (1) The Retry button (prominent fill), (2) the error text (semibold with a warning symbol), (3) the hints text. This matches the purpose.
4. **Confusing items:**
   - The error block holds the error line, a "Not sent: <text>" line, and a Retry button in a row fixed at two lines. A long error or a large Dynamic Type size will clip it.
   - The field is still editable and Send is live. A user who types a new message silently drops the failed one. The spec says this but nothing on screen warns the user.
   - "Couldn't reach the game." is vague. The user can't tell whether the LLM is down or their network is.

### A5. Authorizing (win in progress)
1. **Purpose:** Tell the user they won and that the app needs sign-in or biometric confirmation before moving the map.
2. **Obvious interactive element:** None in the app. The field is disabled, and the system sheet (Google or Face ID) takes over. The transition is system-driven and clear.
3. **Visual ranking:** (1) The system sheet (Google, then Face ID), (2) the "Correct! ..." status message, (3) the dimmed hints. This matches the purpose, but the status row is hidden behind the sheet most of the time.
4. **Confusing items:**
   - The user is told "Correct!" and then immediately asked to sign in to Google just to move a map. The reason for the sign-in is not explained on screen, and a bare Google prompt looks like a login wall.
   - Back-to-back Google and Face ID prompts on the first win feel like a double login.
   - The spec says the LLM's tool call is the only win signal, so "Correct!" in the status row appears before the user has seen any hint text confirming a win. The hints area still shows the dimmed previous reply, which does not say anything about a win.

### A6. Finishing
1. **Purpose:** Wait for the LLM's closing message after the map has moved (or not).
2. **Obvious interactive element:** None. The map is moving or already moved, and the user can pan it. This is not ambiguous.
3. **Visual ranking:** (1) The map flight, (2) the "Finishing up..." spinner, (3) the dimmed hints. This matches the purpose.
4. **Confusing items:**
   - The user sees "Finishing up..." with no hint of what is being finished. It is a vague word for a game they have just won.
   - The map flight (2 s) and the final reply arriving may overlap, with the hints changing under the map's motion.
   - The panel covers the bottom of the map. The pin is centered in the visible part, which depends on the panel height. If the panel resizes (keyboard, larger text), the pin is no longer centered. The spec fixes the inset only at flight time.

### A7. FinishFailed
1. **Purpose:** Tell the user they won but the final message did not load, and let them retry.
2. **Obvious interactive element:** Retry (filled, right). A tap resends the final request and returns to Finishing. Clear is also active and is a competing exit. The Retry transition is clear.
3. **Visual ranking:** (1) Retry, (2) the "Correct! Couldn't load the final message." error, (3) the map. This matches the purpose.
4. **Confusing items:**
   - The error text is long: "Correct! Couldn't load the final message." plus a second line "Map not moved." The row is two lines tall, and it clips at larger text sizes.
   - Clear is enabled here, and the Clear dialog says "This forgets the conversation". Choosing it discards a win. The dialog does not say so.
   - "Map not moved." is a second line that appears without a clear referent, since the user has not been told the map was supposed to move.

### A8. Ended (win)
1. **Purpose:** Show the closing text and let the user start a new game.
2. **Obvious interactive element:** Play again (filled, right of the status row). A tap wipes the game and goes to Clearing then Starting, with no confirmation. This is clear.
3. **Visual ranking:** (1) The map with the pin, (2) the closing text in the hints area, (3) Play again. For an end screen, Play again should arguably outrank the map, but the pin on the map is a legitimate reward. The order is acceptable.
4. **Confusing items:**
   - The disabled field with the placeholder "Tap Play again to start a new game" duplicates the button's job in the most prominent place on the keyboard side of the panel.
   - "Map not moved." in the status row, with no explanation of why, may read as a bug.
   - Play again wipes the pin and the conversation with no confirmation, so an accidental tap loses the closing text and the pin the user may still want to look at. The spec says "nothing to lose", which is wrong: the user loses the city reveal.

### A9. Clearing
1. **Purpose:** Wipe the game and restart.
2. **Obvious interactive element:** None. All controls are dimmed. This is not ambiguous.
3. **Visual ranking:** (1) The spinner and "Clearing..." text, (2) the muted hints placeholder, (4) the map. This matches the purpose.
4. **Confusing items:**
   - It is a near-instant local wipe, yet it gets its own state, spinner and error ("Couldn't clear.") The spec itself says "somehow fails". This is state bloat for something that cannot really fail.
   - The text flips from "Clearing..." to "Picking a mystery city..." almost immediately, so the user will see a flicker.

### A10. StartFailed
1. **Purpose:** Tell the user the game could not start and offer a retry.
2. **Obvious interactive element:** Retry. A tap resends the game rules and goes back to Starting. This is clear.
3. **Visual ranking:** (1) Retry, (2) the error text, (3) the map. This matches the purpose.
4. **Confusing items:**
   - Clear is dimmed, but Retry does the same job. Fine, but a stuck user has only one control.
   - There is no cause given ("Couldn't start the game." covers offline, bad key, server down).
   - Still no way to differentiate offline from LLM down, unlike SendFailed.

### A11. Clear confirmation sheet (overlay)
1. **Purpose:** Confirm before discarding the game.
2. **Obvious interactive element:** The destructive "Clear" button. A tap starts Clearing. This is clear.
3. **Visual ranking:** (1) The destructive Clear action, (2) the title "Clear this game?", (3) Cancel. This matches the purpose.
4. **Confusing items:**
   - The title and the destructive button share the word "Clear", with the floating button using it too. This is fine, but there is no hint that the Google token stays.
   - The sheet appears over a possibly-open keyboard. The spec does not say whether the keyboard dismisses before the sheet shows.
   - On a gave-up game, the message "forgets the conversation" does not tell the user the city is lost.

### A12. Location permission prompt (overlay)
1. **Purpose:** Ask for location access so the map can fly to the user.
2. **Obvious interactive element:** The system "Allow While Using App" button. A tap grants location, and the map flies when the fix arrives. This is standard.
3. **Visual ranking:** System-controlled. The prompt is first, the first hint behind it second, the map third. The order is acceptable.
4. **Confusing items:**
   - The prompt appears on top of the first hint on first launch, which hides the content the user is waiting for.
   - The spec does not give the usage-description string for the prompt, and iOS requires one.
   - The map stays on the world view until the tester answers, and then flies a long distance with no explanation.

### A13. Google sign-in sheet (overlay)
1. **Purpose:** Get a Google token before the map moves.
2. **Obvious interactive element:** Google's own sign-in controls. Cancelling or failing means denial. The user cannot tell that cancelling costs them the map move.
3. **Visual ranking:** System-controlled.
4. **Confusing items:**
   - Nothing on screen warns the user that cancelling means the map will not move.
   - The user has just been told "Correct!" and now sees an account chooser with no connection to a map.
   - No scope or purpose text is specified for the OAuth consent.

### A14. Face ID prompt (overlay)
1. **Purpose:** Gate the token read.
2. **Obvious interactive element:** Face ID / Touch ID / passcode fallback. A failure or cancel means denial. This is standard.
3. **Visual ranking:** System-controlled.
4. **Confusing items:**
   - The prompt text, "Confirm it's you to move the map to the mystery city.", reveals that the city is about to be shown, which is fine, but the user cannot know a denial costs them the move.
   - A single failed scan can be a denial, depending on how the LAContext is evaluated. The spec does not say whether the user gets retries.
   - If Face ID is not enrolled but a passcode exists, the behavior is unclear, though "passcode fallback allowed" mostly covers it.

## B. Is the spec sufficient to build the app without questions?

**No, but it is close for the UI itself.** The layout, states, texts and transitions are unusually complete. The gaps are about the game contract and a few build details.

**Gaps and questions:**
- What is the give-up phrase? The spec says it is typed, but not which text, and whether the app or the LLM interprets it.
- Which LLM, endpoint, and API key handling? How are the game rules (system prompt) worded? What are the recenter tool's name and argument schema (latitude, longitude, anything else)?
- How does the LLM know a user is the same person as the Google sign-in? What does the Google token do at all? The spec never says what the token is used for besides gating the tool call. Is it sent anywhere? If not, why sign in?
- What does "unexpired" mean for the token, and how long is the lifetime?
- "Token released to tool call": is the tool call made with the token, or does the app use it locally? Is anything transmitted?
- What happens to a user's draft text on Clear or Play again? (Draft cleared when a new game starts, per 4, but Clear says "field empties".) Consistent, but confirm.
- What happens if the app is backgrounded or killed mid-game? Is the game lost on relaunch? The spec says launch always starts a new game, but never states it.
- What if the LLM calls the recenter tool during Starting (first reply)? The state diagram has no arrow.
- What if the LLM returns an empty reply, or a reply plus a tool call at once?
- Hints scroll: does it auto-scroll to the top of the new reply? Does the user's scroll position reset?
- Dim/disable rule for Sending: the field stays editable, but what happens to a draft typed in Sending when the reply arrives with Send "re-evaluating"? Presumably it enables. Confirm.
- Retry in SendFailed with a draft already typed: does Send (new text) and Retry coexist visually? Yes, but which wins on Return? The spec says Return does what Send does, so it sends the draft. Fine.
- Pin: which coordinates, any title, and does it get removed on Clear only?
- The map's initial region ("zoomed-out world view") needs coordinates and span.
- Dark mode and the map style: standard or satellite?
- Status row height formula "two lines of Subheadline, never less than 44 pt" vs Retry as a Body-size button with 44 pt minimum: confirm the button fits when the row is exactly 44 pt and the error is two lines.
- The Clear capsule "does not overlap the compass or panel": what happens on small phones (SE) with the compass at top-right and a long Clear label at large Dynamic Type?
- Network permission/ATS, and what counts as "offline" beyond the two named error codes.

## C. Remaining issues, classified

**Substantive:**
1. **Give-up is invisible to the app and the user.** A gave-up game looks like Ready, and the only restart is a small floating Clear that the user must discover. The spec acknowledges this and defers it to the LLM's wording, which the app cannot control. A usability test will likely show testers stuck here. This is a deliberate choice, but it is the highest-risk UX decision in the document.
2. **Google sign-in has no stated purpose.** Nothing in the spec says what the token is for. If it only gates a map move, then the first win shows two security prompts for a cosmetic action, and the "Correct!" status gives the user no reason for it. If it is a study variable, the spec should say so.
3. **Denial costs the user the reward with no warning.** Cancelling Google or Face ID silently means "map not moved". Neither prompt tells the user.
4. **Win detection depends solely on the LLM calling the tool.** If it forgets, the user has won and nothing happens ("Stuck win", item 9). The spec accepts this, but a tester will read it as a broken app.
5. **Missing tool and game contract.** The tool schema, system prompt, give-up phrase and model are not in this document. A builder cannot finish without them.
6. **Missing state arrow:** a tool call during Starting, or a tool call combined with a normal reply, is undefined.
7. **Play again claims "nothing to lose", but it discards the closing text and the pin** with no confirmation, while Clear in a given-up game asks for one. The inconsistency is deliberate but the justification is wrong.
8. **Status row overload.** One fixed two-line row has to carry errors with a second detail line, a button, echoes of user text, and Dynamic Type growth. Clipping at large sizes is likely. The spec's own rule (button never shrinks, block wraps to two lines then ellipsis) can truncate the "Correct!" win error to near nothing at accessibility sizes.
9. **Pin and camera centering relies on the panel height at flight time only.** It will be off after the keyboard or a text size change.

**Nitpick or out of scope for a prototype:**
- The Clearing state and its failure message (a local wipe cannot really fail).
- The "Couldn't clear." error.
- Cross-fade timing, Reduce Motion details, and VoiceOver strings.
- The duplicate messaging in Starting (hints placeholder plus status row).
- The "Finishing up..." wording.
- The 5 s auto-hide of the location notice.
- Offline versus unreachable error wording.
- Device-passcode requirement and Secure Enclave details.
- Clear and Retry both dimmed in StartFailed.
- The keyboard-dismiss order relative to the confirmation sheet.
- Small-phone layout of Clear versus compass.

**Verdict:** The critique is **not yet mostly nitpicks**. Items 1 to 6 are real design or contract gaps that would stop a builder or distort a usability test. Items 7 to 9 are moderate. The long tail of wording, animation and error-state polish is nitpick territory, and that tail is where the spec has spent most of its length. The UI itself is well specified. The game contract and the purpose of sign-in are not.

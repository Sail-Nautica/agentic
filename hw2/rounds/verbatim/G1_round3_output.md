# Goldfish 1, round 3: verbatim output (critique of E-A v3)

REVIEW OF E-A_v3 (read only that file; nothing written)

The spec is one screen with a map, a bottom panel and a floating Clear button. Plus four overlays and ten states. Below, each part gets its purpose, main control, top three visuals, and problems.

## A. Per-screen / per-state review

### 1. Main screen (map + panel + floating Clear)
1. Purpose: a map-based guessing game where the player chats with an LLM to identify a mystery city. On a win the map flies to the city.
2. Obvious control: the text field with the Send button. Tap Send and the text goes to the LLM with no ambiguity. The one unclear transition is Return. It acts as Send only if Send is enabled and otherwise does nothing, so the user gets no feedback (see issues).
3. Top three visuals: (1) the map, which is full bleed; (2) the hints area, which holds the clues; (3) the input row. The panel is much smaller than the map, so the map dominates. But the game's real content is the hints, and the map does nothing useful until a win. The hierarchy is "map first" while the purpose is "hints first." Hints at Body size and up to 5 lines is a reasonable fix. The match is partial.
4. Issues:
 - Clear (top-left) sits far from the thumb and the panel, and is far from the other controls. Its position is arbitrary but acceptable.
 - The map is non-functional for play until a win, yet the player may pan it and fly-to may be cancelled by accident.
 - Which element is "the answer"? Nothing says how to win. The only instruction is a placeholder that disappears once typing starts, plus the LLM's first reply.

### 2. Starting (launch)
1. Purpose: waits for the LLM's first clue while the map shows the world. The user can do nothing except look.
2. Obvious control: none. Everything is disabled, and Clear is dimmed. The map is the only active thing, so the user will likely pan it. No ambiguity, but no affordance either.
3. Top three: (1) map; (2) status row spinner "Picking a mystery city..."; (3) muted "Waiting for the first hint". Matches the purpose.
4. Issues:
 - The location fly-to can happen during Starting and cancel/fight with user touch. Well specified, but the map moving while the user waits is a surprise.
 - The iOS location prompt appears on top while the 30 s timer runs. The user can spend more than 30 s reading the prompt and trigger a false StartFailed.
 - Dimmed Clear with no explanation.

### 3. StartFailed
1. Purpose: tells the user the game could not start and offers Retry.
2. Obvious control: Retry in the status row. It resends and returns to Starting. Clear transition. The "Retry" label is not given an explicit position other than "right".
3. Top three: (1) status row error and Retry; (2) the map; (3) muted "No game running". Matches, though the map is visually bigger than the error. The error is only a Footnote-sized line in a panel; it is easy to miss.
4. Issues:
 - Error text is Footnote size, the smallest on the screen, yet it carries the only action.
 - Why is the user not told what the problem is (no key, offline)? The message is generic.
 - Three different muted texts across Starting, StartFailed, Clearing.

### 4. Ready
1. Purpose: the user guesses cities or asks for hints. The latest LLM reply is shown above the input.
2. Obvious control: Send. Sends the text, field clears, keyboard stays, state goes to Sending. Unambiguous.
3. Top three: (1) hints area; (2) text field; (3) map. Good match, since the user's attention should be on the hint and the input.
4. Issues:
 - Placeholder "Guess a city, ask for a hint, or type 'give up'" is long and will be truncated on a narrow phone and at large Dynamic Type. The give-up phrase is the one thing that must be seen.
 - Only the latest reply shows. The user cannot re-read earlier hints (their own prior guesses and the answers vanish). For a guessing game that is a real memory burden.
 - The location notice shows here and vanishes after 5 s, which the user can easily miss.

### 5. Sending
1. Purpose: waiting for the LLM's reply. The user's message is echoed.
2. Obvious control: none except the field, which is editable for drafting. Nothing happens on Return. Send is dimmed.
3. Top three: (1) status row echo "Sent: <text>"; (2) dimmed hints; (3) the field. Matches. 
4. Issues:
 - The user's sent text vanishes from the field and survives only as a truncated echo in a Footnote line. If the user cannot see their own guess in full, they cannot tell which guess the answer refers to.
 - No Cancel for a request that may take 30 s. Clear is disabled too, so the user is stuck.
 - Return silently does nothing.

### 6. Authorizing (win)
1. Purpose: tells the player they guessed right while the app gets permission to move the map.
2. Obvious control: none in the panel. The user acts in the system sheets (Google, Face ID).
3. Top three: (1) the system sheet; (2) status "Correct! Getting access to move the map"; (3) dimmed hints. Matches.
4. Issues:
 - First win means Google sign-in then Face ID back to back. The spec admits this. The user was told "Correct!" and then is asked for a Google account with no reason given.
 - The Face ID reason text mentions "saved sign-in", but the user just signed in, which is odd.
 - "Getting access" is vague jargon for a user who does not know a token is involved. 

### 7. Finishing
1. Purpose: waiting for the final congratulation or reveal text.
2. Obvious control: none. The field is editable but Send is off.
3. Top three: (1) status "Finishing up..."; (2) the map (which has just moved, or not); (3) dimmed hints. Mostly matches, but the map flight is the payoff and happens at the same time as the sheet dismissal.
4. Issues:
 - The map flight starts here, with the panel and "Finishing up" competing.
 - Editable field with Send disabled invites typing that goes nowhere.
 - The user sees the old hint (dimmed) for the whole time, not the congratulation.

### 8. SendFailed (normal)
1. Purpose: tells the user the last message did not go and lets them retry or send something else.
2. Obvious control: Retry. It resends the same message. Clear.
3. Top three: (1) status error + Retry; (2) hints; (3) field. Matches.
4. Issues:
 - The failed message is not shown anywhere. The user does not know what Retry will send because the echo has gone and the field is empty or holds a different draft.
 - Draft handling: Send sends the draft and drops the failed message silently.
 - The placeholder "Type a new message, or tap Retry" only appears with an empty field.

### 9. SendFailed (final request)
1. Purpose: the win already happened but the closing message failed.
2. Obvious control: Retry. Clear and unambiguous.
3. Top three: same as above. Matches.
4. Issues:
 - Field is editable and Return does nothing, with Send off and no explanation why. Not communicated.
 - "Couldn't get the final message." does not tell the user they won.
 - Clear is the escape but wipes a won game.

### 10. Ended
1. Purpose: the game is over (win, win without map move, or give up). The user can start again.
2. Obvious control: Play again, in the status row. It wipes everything with no confirmation, goes to Clearing then Starting. Clear to the user.
3. Top three: (1) hints closing text; (2) map; (3) Play again button in a Footnote-height row. The key action (Play again) is the third and smallest; it should rank higher. Mismatch.
4. Issues:
 - Play again is a small button in the status row at the far right, not a prominent button.
 - The give-up path depends on an unresolved question (Q1) about an "end game" signal. If no signal, Ended never appears.
 - A disabled field plus placeholder is the only other cue.

### 11. Clearing
1. Purpose: briefly wipes state before restarting.
2. Obvious control: none.
3. Top three: spinner "Clearing...", muted hint, the map. Matches.
4. Issues: it flashes by (local wipe) and then "Starting"; two spinner states in a row is flicker. "Couldn't clear" error path is speculative.

### 12. Clear confirmation sheet
1. Purpose: confirms the user wants to throw away the current game.
2. Obvious control: destructive "Clear" button. Starts Clearing. Cancel returns. Clear.
3. Top three: title, destructive button, Cancel. Matches (standard).
4. Issues:
 - Action sheet on iPhone is fine; but "Clear" appears as button, title word and floating label. The word "Clear" also reads as "clear the text field." The spec says one name per action is a virtue; it is, but the name itself is weak. "New game" would be clearer, and Play again is a different name for the same effect.
 - The message is accurate but does not mention that the answer city is lost.

### 13. Location permission prompt (system)
1. Purpose: asks to use location to fly the map to the user.
2. Obvious control: system Allow/Don't Allow. Allow triggers fly-to; deny shows the notice.
3. Matches (system).
4. Issues: why would a mystery-city game need your location? There is no purpose string given. The map flying to the user also gives away nothing, but it is pointless for the game and adds a permission prompt before the first clue. The 30 s timer runs under it.

### 14. Google sign-in sheet (system)
1. Purpose: gets a token so the tool can move the map.
2. Obvious control: the Google account choice; Cancel leads to Denied.
3. Matches (system).
4. Issues: user is signing in after having won, to see an animation. The value to the user is low and the cost high. Cancel is a silent denial.

### 15. Face ID prompt (system)
1. Purpose: unlock the stored token.
2. Obvious control: Face ID / passcode fallback. Cancel leads to Denied.
3. Matches (system).
4. Issues: same as above; on first win it comes right after Google.

## B. Is the spec sufficient to build without questions?
Mostly, for layout and the state table. No, there are real gaps:

- Q1 is open: how the app learns the game ended on give-up ("end game" signal). The whole Ended path for give-up depends on it. Without the signal Play again never shows. The spec says "open question Q1" but nothing else defines the signal (tool call? special text?).
- No definition of the recenter tool's inputs (city name? coordinates?) or the LLM's rules/system prompt text. The app builder needs to know the format of coordinates and the "end game" tool.
- No conversation history display. Only the latest reply is shown; confirm that is really intended.
- Where does the failed message text live for Retry (kept in memory, not displayed)? Not shown anywhere.
- Hints area while Sending: "latest reply of the current game" but at Ready after a failed Starting, etc. Fine, but what shows after Retry from SendFailed while sending? (State table says Sending shows dimmed latest reply; Retry from SendFailed goes to Sending. OK.)
- Retry in the Finishing-failed case: returns to Finishing, but the state diagram only shows Finishing to SendFailed. SendFailed to Finishing is missing. The diagram lists "SendFailed --> Sending: Send new text or Retry" only, so a final-request retry has no arrow.
- Authorizing and Finishing are labelled "Editable" for the field, but Return and Send do nothing, yet the field editing during Authorizing while system sheets are up is moot.
- Timer: "paused only while the Google or Face ID sheet is on screen" but the 30 s limit per request applies to the LLM; there are two LLM requests around the tool call. Clear when the timer covers Authorizing is undefined (is there a timeout on Authorizing itself if a sheet is never answered? No: paused indefinitely, with Clear disabled. The user can be stuck only by their own choice, fine).
- Placeholder text during SendFailed final request says "Type a new message" but Send is off.
- Hints when Ready after a successful location: what if the LLM reply is longer than 5 lines (scroll)? Defined. What about the first reply taller than the capped panel? Defined at 45 percent.
- Pin and fly-to camera: "about 25 km across" for every city, including small or huge ones; fine for a prototype.
- Whether the keyboard auto-opens at Ready: not stated.
- Return key "Send" label while Send is disabled: the key looks active but does nothing.
- Fixed decision conflict: "Biometric check on every token read; Google sign-in not repeated within token lifetime," plus "Sign-in happens just in time at the win." Consistent, but token lifetime length is not given.
- Whether the Google sheet needs scopes at all. The token is "never shown" and used for what? Its purpose in the game is not stated; the user (and builder) cannot tell what the token unlocks.
- The "denied" flow when coordinates are out of range: map not moved, the LLM reveals the city. OK.
- Dim vs hidden Clear: Hidden in Ended, dimmed otherwise. Fine.

## C. Classification of all issues

SUBSTANTIVE (would change the build or the test result)
1. Open question Q1: no defined "end game" signal; give-up path may never reach Ended or Play again. Blocks building a core path.
2. No state arrow for retrying the final request (SendFailed to Finishing missing from the diagram).
3. Recenter tool and end-game tool formats (arguments, names) and the LLM rules text are not specified.
4. Only the latest reply is visible, so players cannot review earlier clues or their own guesses; the user's sent text is lost after a truncated echo. This hurts the actual game.
5. Failed message is not displayed, so Retry's effect is invisible.
6. 30 s timer runs behind the location prompt and can produce a false StartFailed on first launch.
7. First win forces Google sign-in then Face ID with a vague "Getting access" message and no explanation of why; likely to confuse and abort in a usability test, and the Face ID reason text ("saved sign-in") is inaccurate right after signing in.
8. Play again is ranked third and Footnote-sized; the sole way forward is easy to miss. Same for the Retry button and error text living in a Footnote row.
9. Return key that does nothing when Send is off, with no feedback (including the long editable-but-dead field during Authorizing/Finishing).
10. The give-up hint lives only in a long placeholder that is truncated or hidden once typing starts.

NITPICK / OUT OF SCOPE
- "Clear" naming versus "New game" (wording preference).
- Two fast spinner states in Clearing then Starting (flicker).
- Dimmed Clear with no explanation.
- Action sheet message not mentioning loss of the answer.
- Location fly-to relevance and permission purpose string (product choice, fixed decision).
- Why location at all; keyboard auto-open at Ready; 25 km zoom for all cities; token lifetime length; Clearing error path.
- Muted-text wording variety across states.
- Compass/location dot overlap with Clear (already addressed in the spec).
- Dynamic Type edge cases and 45 percent cap.

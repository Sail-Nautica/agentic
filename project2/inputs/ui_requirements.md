# Design Requirements (HW2: Where on the Map?)

A native iOS prototype (SwiftUI, MapKit) built on the existing llmChat/llmTools/llmHITL app. It is a usability-test prototype, not a release.

## Screen elements
1. Map on launch, centered on the user's current location.
2. Mystery-city hints, shown above the guess text box. New hints overwrite old ones; only current hints show.
3. Guess text box with a Send button. Send is enabled only when there is something to send. Tapping it sends the content and shows that work is in progress.
4. Clear button. Tapping it clears all conversation history and context, including system and user prompts. While clearing, Send is disabled; while sending, Clear is disabled; until each finishes.

## Game rules
1. On start, the app sends the game rules to the LLM. The LLM itself chooses the mystery city; the app never picks it from a list. The city stays fixed and is never shown to the user until the session ends. A session ends when the user guesses correctly or gives up.
2. On a correct guess, the LLM calls a tool that recenters the on-device map to the mystery city's latitude and longitude, then invites the user to play again.
3. The recenter tool call requires an authorization token the LLM must obtain from the front end. The token comes from Google Sign-In (OAuth), has a limited lifetime, and can be reused within it without revalidation. It is stored encrypted in the Keychain, accessed through the Secure Enclave, and guarded by a biometric check.

## Constraints
- No new back-end endpoints beyond /llmclear; no change to the harness API, data formats, or SQLite schema.
- Layout polish is not graded; every required element must be fully visible, non-overlapping, and work as specified.
- Exclude enterprise hardening and standard extras: account setup, bug reporting, reviews, payments, subscriptions.
- iOS follows Apple Human Interface Guidelines.

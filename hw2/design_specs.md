# Design Specs for Technical Design (Stage B)

Project: HW2 "Where on the Map?", built on the existing llmChat, llmTools and llmHITL tutorial code in this repository (iOS front end in Agent/, Python back end "harnessd" in harnessd/).

## Fixed constraints from the assignment
- Architecture, separation of concerns, code structure and naming must match the tutorials. Code with a different structure or naming scheme is not graded.
- The tutorial front ends must keep working with this project's back end, and the staff tutorial front ends must work with the cloud-hosted back end.
- The API and data format used to talk to the harness may not be modified. No new endpoints beyond /llmclear from Project 1. The SQLite database schema may not change.
- iOS: MapKit (no key needed) is the chosen map. Prototype, not a release: this is a Minimal Reproducible Example, so exclude enterprise hardening and standard extras.
- Back end is a bare-metal Ubuntu deployment (no containers).

## Game mechanics
1. Initialization: the app sends the game rules to the LLM. The LLM itself picks the mystery city; the app may not pick it from a static list. The choice stays fixed and is never shown to the user until the session ends. A session ends when the user guesses correctly or gives up.
2. On a correct guess the LLM calls a tool that recenters the map on the device to the mystery city's latitude and longitude. The LLM then invites the user to play again.
3. Authorization: the recenter tool call requires an authorization token that the LLM must obtain from the front end. The token is generated through Google Sign-In (OAuth), has a limited lifetime and can be reused within it without revalidation. It is stored encrypted in the Keychain, accessed through the Secure Enclave, guarded by a biometric check.

## Decisions already made in the UX spec (E-A)
- There is no "end game" tool. The recenter tool is the only game-state signal the app receives; the app cannot detect a give-up.
- The LLM reveals the city in text when sign-in or biometrics fail; the map does not move.
- Clear uses the existing /llmclear endpoint.
- See E-A for everything else (states, status messages, timeouts, layout).

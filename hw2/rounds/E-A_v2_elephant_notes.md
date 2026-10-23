# Elephant notes after v2 (not shown to Goldfish)

## Not adopted from G1 round 1
1. Retry of the map move after denial: adds a second authorization path; testers can start a new game.
2. Chat transcript / message history: contradicts "only current hints show"; one-line echo in status row instead.
3. Explanation screen before Google sheet: adds a screen; one-line status message used.
4. iPad popover and landscape: test is on iPhone; portrait lock.
5. Parsing LLM text to detect wins/give-ups: LLM owns game logic; app reacts only to the tool call and final reply.
6. Pausing the Starting timeout during the location prompt: requests are independent.

## Open questions for the product owner
1. Is the LLM API stateless, with the app holding history? (no-double-count rule depends on it)
2. Is Google sign-in then Face ID back to back on the first win acceptable?
3. In Ended, field disabled and Play again button required: acceptable?
4. 44 pt always-reserved status row vs map-dominant preference?
5. Clear top-left floating vs in the input row?
6. 30 s timeout; 5 km at launch / 25 km on a win?
7. Testers on physical iPhone with passcode + biometrics and on the Google test-user list?

# Elephant notes after v4 (not shown to Goldfish)

## Not adopted from G1 round 3
1. Showing the whole sent message when long: fixed-height row; only current hints may show; two-line echo is the compromise.
2. Excluding the location prompt from the timer: delaying the first-launch location request is simpler.
3. Visible give-up hint/banner/button when the first reply omits the reminder: adds chrome.
4. Detecting give-ups by parsing text or an extra tool: ruled out by product-owner decision.
5. Play again after a give-up: impossible without detection; Clear is the path.
6. Out-of-scope nitpicks from the reviewer.

## Open questions for the product owner
1. After a give-up the only restart is Clear; acceptable that testers learn this only from the LLM's reveal text?
2. Is the LLM API stateless, app holds history?
3. First launch only: map stays on world view until the tester answers the location prompt (appears after first hint); acceptable?
4. 30 s, 5 km launch, 25 km win acceptable?
5. Testers on a physical iPhone with passcode and biometrics, on the Google test-user list?

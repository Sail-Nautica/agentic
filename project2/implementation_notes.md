# Implementation notes (E-C steps done so far)

Done and compiled (`xcodebuild`, Debug, iPhone 18 Pro simulator destination: BUILD SUCCEEDED):
- B1 `handlers.llmclear`: third delete of the app's row in the tools table (after calls, then turns). Checked on a scratch SQLite database built from db_schema.sql (the statistics-table line removed because SQLite reserves that name): turns-first delete is refused by the foreign key; the three deletes remove app A's rows and leave app B's rows and the tickets untouched. No live write.
- B2 `handlers.TICKET_MAX_LIFETIME` now `int(os.environ.get("TICKET_LIFETIME_SECONDS", 180))`, with `import os`. Not run: the handlers module cannot be imported locally (aiosqlite is not installed); it compiles. The live check (E-B2) needs the deployed server.
- F2 camera state: `LocManagerViewModel.camera`, `isPositioned`, `centerOnFirstFix`, `recenter` (two camera assignments), `startUpdates` calls `centerOnFirstFix` after `setLocation`.
- F3 `recenter_map`: `tools/recenter_map.json`, `ticketRejection(for:)` shared guard (baseline 401 sentence moved unchanged), `recenterMap` (finite, valid, not (0,0)), registered in `Toolbox.init`.
- F4a rules text for Guess the City in `Game.rules` (20 Questions rules unchanged).
- F5 screen: picker disabled while busy; `MapArea` (progress indicator until `isPositioned`, then `Map` bound to the camera with `UserAnnotation` for the system location dot); computed `AppViewModel.hint`; hint above the input row (capped, scrollable); toolbar button swaps the map area with `ConversationView`; tap dismisses the keyboard only, attached to the hint and input group (not the map); `SubmitButton` whitespace-aware.
- F6 launch task: `guard conversation.isEmpty, !isBusy`, then `resetGame()` (wipe, then rules).
- F7 location permission text changed in both build configurations.

F8 sweep on added lines (grep of the diff): zero hits for DispatchQueue, Task.sleep, Thread.sleep, RunLoop, ObservableObject, @Published, @StateObject, @ObservedObject, @EnvironmentObject, @MainActor, ZStack, GeometryReader, foregroundColor, do {, catch, as?, as!, Optional, typing., .format(, threading, time.sleep, get_event_loop. One hit: `cornerRadius` on the existing `.cornerRadius(20)` line of the text field, which only moved (re-indented) into an inner stack; per the plan's definition re-indentation is not a touched line. Baseline offenders are unchanged and not fixed.

Not done, blocked on the owner or a person:
- B4 deploy of `handlers.py` and restart of `harnessd` (needs the owner's go-ahead), hence no B3 check and none of the F9 tests; the app was not run, because launching it wipes this app's conversation on the shared server.
- F1a stale-token investigation (a person must sign in and wait over an hour on a frozen baseline build); F1b only if it reproduces.
- E-D phases, the reference city table, device observations.

## B4 deploy (done 2026-11-02, with the owner's go-ahead)
- Server: copied only `harnessd/handlers.py` (backup at /home/ubuntu/handlers.py.bak-20261102; the server's git tree is otherwise unchanged and shows handlers.py as modified). The diff against the backup is exactly the three edits (import os, tools-row delete, lifetime knob).
- harnessd is a systemd service (harnessd.service, EnvironmentFile /home/ubuntu/.env.sys). Restarted: active, listening on 443.
- Single test runner: a systemd drop-in /etc/systemd/system/harnessd.service.d/test-runner.conf sets RUNNERS_CONFIG=/home/ubuntu/runners.groq.toml (the repo's runners.toml with only the Groq runner; the local fallback stays as the last resort). The API keys and /home/ubuntu/.env.sys were not touched. To revert: delete the drop-in, `sudo systemctl daemon-reload`, `sudo systemctl restart harnessd`.
- Lifetime knob left unset (default 180).
- Check: POST /llmclear for a throwaway app ID returned 200 and the server log shows it, so the new third statement runs on the live schema (no rows existed for that ID).
- NOT done: any run of the app. This Mac lists the iOS 27.0 simulator runtime but `simctl boot` fails with "runtime path not found: download the iOS 27.0 simulator runtime from Xcode Settings", so E-PRE-B, E-T1 and every other runtime test are blocked until the runtime is installed or a device is used.

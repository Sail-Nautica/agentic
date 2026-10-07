# Where in the World? — Project 1

EECS 498-008. "Guess the City" / "20 Questions" LLM game, built on the llmPrompt/llmChat tutorials.

## Team

Individual submission — one member.

| Name      | Uniqname  | Email                   |
|-----------|-----------|-------------------------|
| Amit Sail | amitsail  | amitsail@umich.edu      |

## llmTools

Extends the game with LLM tool calling: "What's the weather at my location?" chains two tools.

- `get_location` runs on the device (`Agent/Agent/Toolbox.swift`, `LocManager.swift`, schema in `Agent/Agent/tools/get_location.json`).
- `get_weather` runs on the backend against Open-Meteo (`harnessd/toolbox.py`, schema in `harnessd/tools/get_weather.json`).
- `POST /llmtools/` (`harnessd/handlers.py`) streams the LLM reply, runs backend tools itself, and forwards device tools to the app as a `tool_calls` SSE event carrying `turnID`; the app replies with the tool results and the same `turnID`.
- `POST /weather` returns the temperature at `lat`/`lon` as `text/plain`.
- Tool calls and results are stored in the `calls` table and the app's tool schemas in `tools`, both in `harnessd.db`.

## Code Ownership

Solo project — Amit Sail wrote/owns all code in this repository (`Agent/`, `harnessd/`).

## Honor Code Pledge

"I HAVE received aid from an LLM or automated coding
assistant on this submitted work. If I received aid, the specific
tool used was [claude-sonnet-5].
Regardless of assistance, I fully understand and can defend all code
and design choices within this submission, and I have not concealed
any violations of the Honor Code."

Signed: AMIT SAIL Date: 2026-09-29

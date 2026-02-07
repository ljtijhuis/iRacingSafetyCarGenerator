# What is in this folder?

When you start the SCG in dev mode, an option becomes available to record SDK data. This records a full dump of the SDK values every second and writes it to a `ndjson` (Newline Delimited JSON) file. This is helpful for a number of things:

1. Have AI analyse it for useful fields to leverage in our heuristic based detection mechanisms
2. Validate how values change in different situations
3. Create a mock SDK that replays those same values to build test cases around real-sim-life events.

Note that these dumps can become quite big. If you want to record longer sessions, you may want to alter the recording logic in `src\util\sdk_dump.py`.

The names of the files included here should indicate what scenarios we have recorded.
# Postmortem

analysis/31 and analysis/32 are both tied to PR 346
https://github.com/PlanExeOrg/PlanExe/pull/346

analysis/31 outputted junk for anthropic and llama.

Here in analysis/32, it compared with analysis/31, and got the impression that the output had improved.
Here Claude forgot the big picture, that analysis/31 was a disaster, and should be comparing against something older.

I'm wondering how to keep track of the current best solution, or a ranked list of best solutions.
This way it's always possible to compare against earlier runs, and not comparing against a crappy run.


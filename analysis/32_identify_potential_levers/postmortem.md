# Postmortem

analysis/31 and analysis/32 are both tied to PR 346
https://github.com/PlanExeOrg/PlanExe/pull/346

analysis/31 outputted junk for anthropic and llama.

Here in analysis/32, it compared with analysis/31, and got the impression that the output had improved.
Here Claude forgot the big picture, that analysis/31 was a disaster, and should be comparing against something older.

When the AI's attempt to auto-detect what dir to compare with, it often happens that it's the wrong dir, 
making some crappy analysis and flawed conclusions. By keep track of the current best solutions, 
it's always possible to compare against earlier runs, and not comparing against crap.
I have added an `analysis/best.json` that points at the best experiments.
That way it's possible to determine what to compare with.


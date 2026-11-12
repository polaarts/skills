# Fast command-line tools: start small, measure, then cache

In this fictional demo talk, an example speaker argues that most slow command-line tools are slow for two boring reasons: they do work nobody asked for, and they repeat work they already did.

## Key ideas

### 1. Do less before doing it faster

The speaker's first rule is to remove work before optimizing it. Startup imports, eager config loading and network checks on every run are the usual suspects.

![Chart slide: run time before and after caching](images/0130.jpg)
*Screenshot 01:30 · Run time of the tool before and after adding a cache (placeholder slide).*

### 2. Measure the cold start

Time the tool from a cold cache, not only the second run. The difference between the two is the budget a cache can win back.

### 3. Cache what is expensive and stable

Cache results that are slow to compute and rarely change, keyed by their inputs, and make the cache easy to clear.

## Resources

| Resource | What it is |
|---|---|
| `time` | Shell built-in to measure how long a command takes |
| `--no-cache` | Flag the speaker recommends every cached tool should offer |

The talk gives no links for these resources.

## Source

- Video: Demo talk, Example Channel, 10:00 (fictional, used only to test and preview the skill).
- The text is a rewritten summary of the talk's transcript.

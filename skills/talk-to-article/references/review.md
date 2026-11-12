# Fidelity review

Run after `article.md` is written. A reviewer who did not write the article catches more, so
use a subagent when available. Give it file paths, not your conclusions.

## Prompt for the reviewer

```
You are checking an article against the talk it was written from.

Files:
- Transcript (source of truth; auto-captions may misspell names): <pkg>/transcript.md
- Article: <pkg>/article.md
- Screenshots referenced by the article: <pkg>/images/ (you may view them)

Report, as a numbered list with the article's exact sentence and the transcript timestamp:
1. Claims, numbers or names in the article that the talk does not support or contradicts.
2. Important points from the talk that the article omits (only ones a reader would miss).
3. Captions whose timestamp or description doesn't match the image or the moment.
4. Anything presented as fact that the speaker framed as opinion.
Do not rewrite the article and do not comment on style. If everything checks out, say so.
```

## After the review

Fix confirmed issues in `article.md`. Where the reviewer and you disagree, check the
transcript and the frame at that second; the talk wins over both of you.

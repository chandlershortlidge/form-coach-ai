# Model Observations & Known Shortcomings

## Observation Biases

### Wrist stacking is over-prioritized
The model flags wrist stacking/extension as the primary issue in nearly every analysis, regardless of whether more significant problems are present. While wrist position is a genuinely common issue, it often gets mentioned before more critical observations like missing arch, dangerous foot placement, or failed reps.

### Default positive framing regardless of lift quality
The model tends to lead with "you look solid overall" or similar praise even when the lift has serious issues. This reduces the impact of the feedback and may give users a false sense of security on lifts that need significant correction.

### Nitpicking on solid lifts (partially resolved)
The model previously invented minor issues to fill space when the lift was actually good. This has improved with the updated response style — likely due to removing "Cover all significant issues you observe" from the prompt, and the shorter output giving less room for filler. Worth monitoring.

## Vision & Context Limitations

### Safety issues not in training data are invisible
The model cannot identify safety concerns that fall outside its RAG context. Examples observed:
- Pressing heavy adjustable dumbbells next to a window in loose footwear — not flagged
- Failing a final rep and rolling the bar down the body with no spotter or safety pins — not flagged as a safety concern

This is a fundamental limitation of the RAG-only approach: if the vector store doesn't contain content about a topic, the model won't coach on it even when it can visually observe the problem.

### Camera angle limitations
The model generally handles this well — it acknowledges when it can't fully assess form from a given angle. However, it sometimes still makes confident claims about body positions it can't actually see clearly.

## Next Steps & Improvement Ideas

- Consider adding safety-focused content to the vector store (spotter usage, equipment hazards, environment awareness)
- Explore prompt adjustments to reduce the "you look solid" default opener on lifts with clear issues
- Track whether wrist stacking over-prioritization persists with the concise prompt
- Consider adding a severity ranking instruction so the model leads with the most impactful issue rather than the most common one

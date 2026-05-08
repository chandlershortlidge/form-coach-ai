# Correctness Judge Prompt (Original)

You are evaluating a fitness coaching AI assistant.
Your job is to assess the quality of its response against a reference answer. 

Question: {question}
Reference answer: {reference}
Generated answer: {generated}

Scoring criteria:

Score 0 — The generated answer contains incorrect or potentially harmful advice that contradicts the reference answer. This is the worst outcome.
Score 1 — The generated answer is incomplete or omits important details from the reference, but contains nothing incorrect or harmful.
Score 2 — The generated answer is correct and captures the key facts from the reference answer.

Important: Penalize incorrect advice more harshly than omission. A response that says nothing is better than one that says something wrong.

Reply with only the number: 0, 1, or 2.

# Correctness Judge Prompt (test2)

You are evaluating a fitness coaching AI assistant.
Your job is to assess the quality of its response against a reference answer. 
The reference answer contains the minimum key observations. The generated answer may expand on these with additional coaching advice and this should not be penalized. <-----

Question: {question}
Reference answer: {reference}
Generated answer: {generated}

Scoring criteria:

Score 0 — The generated answer contains incorrect or potentially harmful advice that contradicts the reference answer. This is the worst outcome.
Score 1 — The generated answer is incomplete or omits important details from the reference, but contains nothing incorrect or harmful.
Score 2 — The generated answer is correct and captures the key facts from the reference answer.

Important: Penalize incorrect advice more harshly than omission. A response that says nothing is better than one that says something wrong.

Reply with only the number: 0, 1, or 2.
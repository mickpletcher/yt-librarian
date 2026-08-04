# Classification

Rules are evaluated by descending priority. A rule can match title, description, channel, transcript, regular expressions, or keyword lists. Every matching rule may emit multiple category assignments. The engine keeps the highest-confidence result per category and records the rule name and explanation.

Assignments above the review threshold can be approved automatically when they do not conflict. Lower-confidence results enter the review queue. Manual decisions always remain distinguishable from rule, AI, imported, and learned assignments.

AI classification is optional and disabled by default. The provider receives only the configured local metadata and category descriptions. The OpenAI adapter requires `OPENAI_API_KEY` in the process environment and validates structured JSON before storing a run record. Raw provider responses, token counts, estimated cost, prompt version, and errors are auditable in `classification_runs`.

Manual reviews do not silently rewrite rules. The learning module can summarize repeated manual choices into draft suggestions for the user to add to the YAML file.

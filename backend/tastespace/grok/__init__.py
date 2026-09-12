"""Everything TasteSpace does with xAI's Grok API lives in this package. OWNER: engine (P2).

Grok is the interface; the engine is the judge:
  * agent.py             - "Ask TasteSpace": Grok tool-calls engine functions (search / twins / shift /
                           explain) and replies ONLY with numbers those tools returned (grounding.py).
  * ingredient_mapper.py - maps recipe ingredients our parser could not match onto the CLOSED list of
                           ontology ids (structured output with an enum of ids).
  * client.py            - the xai_sdk wrapper + a provider-neutral chat protocol (fakes in tests).
Offline prior drafting lives in tools/data/grok_draft_ingredients.py (P1): drafts go to
data/drafts/ and only become canonical after human review.
Grok never computes similarity and never supplies runtime sensory values.
"""

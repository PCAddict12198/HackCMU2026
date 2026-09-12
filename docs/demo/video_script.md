# Demo video script (~2:30). OWNER: data (P1)

Every number below is live output from core build `3eaa61b000dc` — re-run the three calls if `data/**`
changes before you record. Say nothing the engine cannot show on screen.

**Recording notes:** `make dev`, browser at 100% zoom, galaxy already rotating before you hit record.
Have the Ask panel question typed but not sent, so there is no dead air while Grok thinks (~5 s).
`XAI_API_KEY` must be set or the Ask panel is hidden.

---

## 0:00 – 0:18 · The hook

> *[rotating galaxy, no clicks]*
>
> "Every food app organizes the world by cuisine. Italian here, Thai there, Japanese over there.
> But cuisine is geography — it isn't flavor.
>
> This is TasteSpace. Seventy dishes from ten cuisines, placed by how they actually taste:
> seventeen sensory dimensions, built up from a hundred and fifty-five ingredients."

## 0:18 – 0:50 · Flavor Twins — the claim

> *[click **Pho Bo** → Flavor Twins panel]*
>
> "Pick Vietnamese pho. Its closest flavor twin isn't Vietnamese, or even Asian —
> it's Mexican **pozole rojo**, at the 98th percentile of all dish pairs. Then **French onion soup** at 97.7.
>
> Which makes sense the moment you see why: all three are long-simmered beef broth bowls.
> Brothy, umami, earthy, roasted, rich."
>
> *[click **Why?** → attribution bars + provenance chips]*
>
> "And we can show our work. Every bar is an ingredient, a cooking process, or the dish format.
> The sodium came from USDA. The lime's sourness is cited food chemistry. Nothing here is a vibe —
> and the attributions sum to the dish value exactly."

## 0:50 – 1:12 · Taste Shift

> *[Shift panel, preset **L**]*
>
> "You can also move through the space. 'What I love about pho, but lighter and more sour' —
> less rich, more acidic. The engine lands on **tom yum goong** at 87.7.
>
> Still a hot aromatic broth. Less fat, much more acid. That's a recommendation engine that can
> explain itself in the language of taste."

## 1:12 – 2:05 · Ask TasteSpace — the Grok beat *(the important one)*

> *[open **Ask TasteSpace**, send: "like pho bo but spicier"]*
>
> "This is Ask TasteSpace, and it runs on **xAI's Grok — model `grok-4.6`**, through the xAI SDK.
>
> But we gave Grok a specific job. It does **not** compute flavor similarity. Instead it gets four
> typed engine tools — search dishes, find twins, shift taste, explain a pair — and it decides which
> ones to call."
>
> *[point at the tool trace as it fills in]*
>
> "You can watch it work. For 'like pho but spicier' Grok resolved the dish, then called shift_taste
> with spicy turned up — and the engine came back with **mapo tofu at 99.2**.
>
> Here's the part I'm proud of. *[point at the **grounded** badge]* Before we show you that reply, we
> pull every number out of it and check each one against the tool results. If Grok states a figure the
> engine never returned, the answer is flagged ungrounded and we swap in a templated reply instead.
> The galaxy fly-to is driven off the same tool trace, so the model can't send you to a dish it
> didn't actually look up.
>
> Our rule is: **Grok is the interface, the engine is the judge.**"
>
> *[optional, if time — terminal or editor on screen]*
>
> "Grok does two more jobs here. It maps messy pasted recipe text onto our ingredient list — and its
> structured output is an enum of our actual ingredient IDs, so it physically cannot invent one.
> And it drafted sensory priors for the corpus — but those land in a drafts folder and a person has to
> review each value before it becomes canonical. A hundred and thirty-six values are marked
> grok-reviewed, and raw Grok drafts are rejected by the validator.
>
> Pull the API key out and everything except Ask still works."

## 2:05 – 2:30 · Validation, honestly

> *[validation slide or `build/report.md`]*
>
> "Last thing, because it matters. We froze a sanity set before we had results: four of ten pairs we
> expected to be similar clear the 90th percentile, nine of ten we expected to be different sit below
> the 50th. We never tuned an ingredient to move those numbers.
>
> We also rated twenty pairs by hand against the engine — Spearman rho **0.90**. But we'll be straight
> with you: that rater was an AI, not a human panel, and it's the same agent that wrote much of the
> data. So call it an upper bound, not validation.
>
> Every one of our six hundred and sixty-five sensory values carries a source. That's the project."

---

## 60-second cut

Drop Taste Shift and the validation beat. Keep:

1. **0:00–0:12** hook — "cuisine is geography, not flavor" + galaxy
2. **0:12–0:30** pho → pozole 98.1 + French onion 97.7, one line on *why* (beef broth bowls)
3. **0:30–0:55** Ask TasteSpace: send "like pho bo but spicier", show the tool trace, mapo tofu 99.2,
   and say the grounding rule — *"we check every number in Grok's reply against the engine's tool
   results; if it isn't traceable, we don't show it"*
4. **0:55–1:00** "Grok is the interface, the engine is the judge."

## If you are cutting for the Grok prize specifically

Lead with Ask, not the galaxy. The judge needs to see, in order: the question typed in plain English →
the **tool trace** naming the engine tools Grok chose → the **grounded** badge → the galaxy flying to
the dish Grok actually looked up. Say the model id out loud (`grok-4.6`) and name the three distinct
jobs — tool-calling agent, closed-vocabulary ingredient mapper, review-gated data drafter. The
differentiator is not that you called an LLM; it's that you constrained it and then verified it.

## Numbers cheat-sheet (build `3eaa61b000dc`)

| claim | value |
|---|---|
| corpus | 70 core dishes · 10 cuisines · 155 ingredients · 17 dims |
| pho_bo twins | pozole_rojo **98.1**, french_onion_soup **97.7**, osso_buco 97.2 (relaxation level 0) |
| shift L (rich −0.8σ, sour +1.2σ) | tom_yum_goong **87.7** |
| shift S (spicy +1.4σ) | mapo_tofu **99.2** |
| sanity (frozen) | **4/10** positive ≥90th pct · **9/10** negative <50th pct |
| rater panel | rho **0.90**, 20 pairs — **AI rater, not a human panel** |
| provenance | **665/665** values sourced: usda 213, team 245, grok_reviewed 136, literature 66, scoville 5 |
| PCA | creamy↔umami 24.8%, rich↔fruity 16.9%, brothy↔roasted 12.5% (54.2% in 3 axes) |
| Grok | `grok-4.6` via xAI SDK · 4 engine tools · reply numbers verified against the tool trace |

## Do not say

- "Validated against human taste" — the rho 0.90 rater was an AI. Say AI baseline.
- "Grok figures out which dishes are similar" — it never computes similarity; the engine does.
- Any number not in the table above or visibly on screen.

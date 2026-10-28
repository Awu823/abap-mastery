# Sources — Deep-Dive Research Trail

Research conducted 2026-07-14 for the ABAP dev skill enrichment initiative (`artifacts/scratchpads/scratchpad_abap-dev-skill-enrichment.md`, Phase 2). `sap-docs-extend-mcp` was confirmed down for this entire session — did not attempt it. Fell back directly to `curl`-fetching the official SAP-samples cheat sheet from GitHub (public repo, no auth).

## Primary source retrieved

- `https://raw.githubusercontent.com/SAP-samples/abap-cheat-sheets/main/30_Generative_AI.md` (247 lines, fetched in full) — the exact topical match for this skill; the entire file was read, not grepped, since it's short. All code/method-name claims in the deep-dive are transcribed directly from this file's two code blocks (lines 41-49 short example; lines 59-247 full `zcl_demo_abap` executable example with 6 numbered sections).

## Verified findings (all method/class names transcribed verbatim from the fetched file)

| Finding | Source location (line range in `30_Generative_AI.md`) |
|---|---|
| `ai_api->get_parameter_setter( )` → `set_maximum_tokens( 500 )`, `set_temperature( '0.5' )` | Lines 127-144, section "3) Setting parameters" |
| `create_message_container( )` → `set_system_role`, `add_user_message`, `add_assistant_message`, `get_messages`, `execute_for_messages` | Lines 191-213, section "5) Calling the LLM completion API with a prompt as message list" |
| `get_completion_token_count( )`, `get_prompt_token_count( )`, `get_total_token_count( )`, `get_runtime_ms( )` on `IF_AIC_COMPLETION_API_RESULT` | Lines 150-181, section "4) Retrieving information regarding the result" |
| `cl_aic_islm_prompt_tpl_factory=>get( )->create_instance( islm_scenario = ... template_id = ... )` → `->get_prompt( )` | Lines 219-245, section "6) Calling the prompt library API to use prompt templates" |
| `CX_AIC_PROMPT_TEMPLATE` exception (catch alongside `CX_AIC_API_FACTORY`/`CX_AIC_COMPLETION_API`) | Line 242 |
| Type elements `aic_islm_scenario_id=>type`, `aic_islm_prompt_template_id=>type` | Lines 69-70 |

## Correction applied to the skill's live content

The live `.claude/skills/abap-generative-ai/SKILL.md` stated under "What the SDK does NOT (yet) offer": *"Fine-grained sampling parameters (temperature, max tokens) are governed by the ISLM scenario/model configuration, not ad-hoc setters."* This was directly contradicted by the fetched source's section 3 (lines 127-144 above), which shows `get_parameter_setter( )->set_maximum_tokens( )`/`->set_temperature( )` as real, working ad-hoc setters in the official example class. **Applied to the live SKILL.md body itself** (new "Setting Parameters" section replacing the incorrect bullet), not just appended to this deep-dive — an unresolved factual reversal left in place would have misinformed future use of the skill.

## Negative findings (absence checked and confirmed, not just assumed)

- Grepped `30_Generative_AI.md` (full text) for "embed" (case-insensitive): zero matches. Confirms — via an independent source read, not just repetition of the existing SKILL.md claim — that no embeddings API is documented for the ABAP AI SDK.
- Grepped `30_Generative_AI.md` for "orchestrat": zero matches. The SKILL.md's existing suggestion to route embeddings/RAG needs "via the Generative AI Hub orchestration service" is **not itself sourced from this file** — it predates this research pass and should be treated as a reasonable architectural inference, not a verified citation from this source.
- Grepped `33_ABAP_Release_News.md` (8,016 lines, the same digest used for every release-number claim in the `modern-abap-syntax`/`rap` pilot deep-dives) case-insensitively for `aic_`, `islm`, and `generative ai`: **zero matches for all three**. This is why the deep-dive's Version Safety section reports an honest absence rather than a release/quarter number.

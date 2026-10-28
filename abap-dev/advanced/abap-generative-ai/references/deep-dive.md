# ABAP Generative AI — Deep Dive

Read this for the full multi-turn/message-container API (missing from the SKILL.md body until this pass), the parameter-setter correction now folded into the SKILL.md body itself, and decision criteria for picking a call pattern. Sources/citation trail: [references/sources-deep-dive.md](sources-deep-dive.md).

## Multi-Turn / Message-Container API (missing from SKILL.md entirely before this deep-dive)

For anything beyond a single string prompt — system role instructions, few-shot examples, or an actual back-and-forth — use the message container instead of `execute_for_string`:

```abap
"Creating another instance of the ISLM completion API
ai_api = cl_aic_islm_compl_api_factory=>get( )->create_instance( islm_scenario ).

"Creating a message container instance and adding messages
FINAL(message_container) = ai_api->create_message_container( ).
message_container->set_system_role( `You are a professional translator` ).
message_container->add_user_message( `Can you translate German into English?` ).
message_container->add_assistant_message( `Yes` ).
message_container->add_user_message(
  `Translate the following German sentence into English: "Entschuldigung, wie komme ich zum Bahnhof?"` ).

llm_answer = ai_api->execute_for_messages( message_container )->get_completion( ).

"The container can be inspected/replayed
FINAL(messages) = message_container->get_messages( ).
```

Decision cue: reach for the message container the moment the prompt needs a **system role** (persona/instructions distinct from the user's actual ask) or **conversation history** (multi-turn, or few-shot examples via alternating `add_user_message`/`add_assistant_message`). Use plain `execute_for_string` only for a genuine one-shot prompt with no role separation — it's the simpler call, don't default to the message container out of habit.

## Prompt Templates — the actual retrieval code

The SKILL.md body names `CL_AIC_ISLM_PROMPT_TPL_FACTORY` but doesn't show working code. The verified pattern retrieves the template's stored prompt text, then feeds it into the message container as the system role:

```abap
FINAL(prompt_temp) = cl_aic_islm_prompt_tpl_factory=>get( )->create_instance(
                        islm_scenario = islm_scenario
                        template_id   = prompt_template ).

"Retrieving the prompt from the template
"Note: depending on the template's setup, there may be input parameters
"('parameters' importing parameter) to assign in this call.
FINAL(prompt) = prompt_temp->get_prompt( ).

FINAL(msg_container) = ai_api->create_message_container( ).
msg_container->set_system_role( prompt ).
msg_container->add_user_message( `... some user message ...` ).
llm_answer = ai_api->execute_for_messages( msg_container )->get_completion( ).
```

`CX_AIC_PROMPT_TEMPLATE` is the exception to catch alongside the two already documented in the SKILL.md.

## Result Metadata (missing from SKILL.md — useful for cost/perf logging)

`IF_AIC_COMPLETION_API_RESULT` exposes more than `get_completion( )`:

| Method | Returns |
|---|---|
| `get_completion_token_count( )` | Tokens in the LLM output |
| `get_prompt_token_count( )` | Tokens in the LLM input |
| `get_total_token_count( )` | Sum of both |
| `get_runtime_ms( )` | Call runtime in milliseconds |

Decision cue: log these alongside the completion whenever the call sits in a workflow with cost/latency sensitivity (batch processing, a RAP determination invoking an LLM per instance) — token counts are the direct lever for the SKILL.md's existing "consider token limits" best practice, and `get_runtime_ms( )` is the concrete number to check before deciding an LLM call is safe to run synchronously inside a RAP save sequence versus needing to move to a background job.

## Decision Criteria: which call shape to use

| Situation | Use |
|---|---|
| One-shot prompt, no role/persona needed, no reuse | `execute_for_string( )` — simplest call, don't over-engineer |
| Prompt needs a system role/persona, or few-shot examples, or true multi-turn | Message container (`create_message_container` → `set_system_role`/`add_user_message`/`add_assistant_message` → `execute_for_messages`) |
| Same prompt shape reused across multiple call sites, or the business wants prompt text editable without a code change | Prompt template (`CL_AIC_ISLM_PROMPT_TPL_FACTORY`) feeding its `get_prompt( )` output into a message container's system role |
| Requirement is embeddings/RAG vector search, semantic similarity, or anything the SDK's completion API doesn't expose | **Not this SDK** — route via Generative AI Hub orchestration service directly (HTTP, outbound communication arrangement); say explicitly this is outside the AI SDK, don't fabricate an embeddings class |

## Version Safety — honestly-scoped negative finding

`33_ABAP_Release_News.md` (the ABAP language/RAP release-news digest used for every version-gating claim in the `modern-abap-syntax` and `rap` pilot deep-dives) contains **zero matches** for `AIC`, `ISLM`, or "Generative AI" anywhere in its ~8,000 lines. This means: **no verified release/quarter number can be cited for when `CL_AIC_ISLM_*`/`IF_AIC_*` became usable in ABAP Cloud** — the feature area isn't tracked in that particular digest (it's a newer, separately-announced capability, likely tracked only via SAP Help/blogs, not the ABAP Keyword Documentation release-news channel). Rather than invent a release number, this is flagged as **absent evidence** — if a TS depends on this SDK being available on a specific target release, verify directly against that system (ADT API State tab on `CL_AIC_ISLM_COMPL_API_FACTORY`), don't infer a date from this source family.

Confirmed (not contradicted): `30_Generative_AI.md` — the canonical source for this skill — has no mention of an embeddings API anywhere in its text, reinforcing the SKILL.md's existing "no documented embeddings API" claim from a second independent check.

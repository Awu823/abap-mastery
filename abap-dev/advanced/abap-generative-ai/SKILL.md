---
name: abap-generative-ai
version: 1.0
description: Help with implementing Generative AI within ABAP Cloud using ISLM (Intelligent Scenario Lifecycle Management) and the official ABAP AI SDK (CL_AIC_ISLM_* / IF_AIC_* family). Use when users ask about Generative AI, AI SDK, ISLM, LLM calls from ABAP, Generative AI Hub, prompt templates, or completions in ABAP. Triggers include "generative ai", "ai sdk", "islm", "llm", "tích hợp ai", "openai abap", "completion api".
---

# ABAP Generative AI

Guide for calling Large Language Models from ABAP Cloud using the **ABAP AI SDK powered by ISLM**. The SDK's real, released surface is the `CL_AIC_ISLM_*` factory + `IF_AIC_*` interface family — do not invent other class names; if unsure, verify against the References below before emitting code.

## Prerequisites

- An **ISLM Intelligent Scenario** of type Generative AI exists and is published (this is what maps your code to a concrete model/deployment — never hardcode model names like `gpt-4`).
- Generative AI Hub / provider connectivity is configured with active Communication Arrangements.

## Completion API (the core pattern)

```abap
TRY.
    " Factory → instance bound to the ISLM scenario
    DATA(lo_api) = cl_aic_islm_compl_api_factory=>get( )->create_instance(
                     islm_scenario = 'ZMY_LLM_SCENARIO' ).

    " Execute a completion for a plain-text prompt
    DATA(lo_result) = lo_api->execute_for_string(
                        `Explain the difference between VALUE and REDUCE in ABAP.` ).

    DATA(lv_completion) = lo_result->get_completion( ).
    out->write( lv_completion ).

  CATCH cx_aic_api_factory cx_aic_completion_api INTO DATA(lx_error).
    " Network/quota/config issues are common with LLM calls — always handle
    out->write( |AI Error: { lx_error->get_text( ) }| ).
ENDTRY.
```

Key types: `CL_AIC_ISLM_COMPL_API_FACTORY` (entry point), `IF_AIC_COMPLETION_API` (instance), `IF_AIC_COMPLETION_API_RESULT` (result), exceptions `CX_AIC_API_FACTORY` / `CX_AIC_COMPLETION_API`.

## Prompt Templates

For reusable prompts with placeholders, use `CL_AIC_ISLM_PROMPT_TPL_FACTORY` to create/fill a prompt template bound to the scenario, then execute it via the completion API (exception: `CX_AIC_PROMPT_TEMPLATE`). Prefer templates over string concatenation when the same prompt shape is used in multiple places — they keep prompt text out of code and versionable.

## Setting Parameters (correction: ad-hoc setters DO exist)

Sampling parameters are settable per-call from code via the instance's parameter setter — this is NOT locked to ISLM scenario/model configuration alone:

```abap
FINAL(params) = lo_api->get_parameter_setter( ).
params->set_maximum_tokens( 500 ).
params->set_temperature( '0.5' ). "Value must be between 0 and 1
```

The ISLM scenario still governs which *models* are reachable and the governance/lifecycle boundary — but temperature/max-tokens themselves are ad-hoc, per-call settings, not something frozen by scenario config. See [references/deep-dive.md](references/deep-dive.md) for the full multi-turn/message-container API, prompt-template retrieval code, and result-metadata methods (token counts, runtime).

## What the SDK does NOT (yet) offer

- **No documented embeddings API** in the ISLM-based ABAP AI SDK. If a requirement needs embeddings/RAG vectors, do not fabricate `*_embedding_*` classes — route via the Generative AI Hub orchestration service (HTTP, outbound communication arrangement) and say explicitly that this is outside the AI SDK.

## Best Practices

- Always indirect through the ISLM scenario — it is the lifecycle/governance boundary (model swaps, deployments) and the reason the SDK exists.
- Consider token limits when assembling prompt context; truncate/summarize inputs deliberately rather than letting calls fail.

## References

- [references/deep-dive.md](references/deep-dive.md) — multi-turn/message-container API, prompt-template retrieval code, result-metadata methods, call-shape decision criteria
- SAP ABAP Cheat Sheets — [30_Generative_AI.md](https://github.com/SAP-samples/abap-cheat-sheets/blob/main/30_Generative_AI.md) (canonical code patterns)
- SAP Help — [API Reference Guide for ABAP AI SDK](https://help.sap.com/docs/abap-ai/generative-ai-in-abap-cloud/api-reference-guide-for-abap-ai-sdk)

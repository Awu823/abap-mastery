# OO Design Patterns in ABAP — Deep Dive

Read this for short, real skeletons of the 4 realizations the SKILL.md body's "ABAP-Specific Realization Notes" section already flags as non-obvious but states without code. This file does **not** turn into a GoF implementation cookbook — per the SKILL.md's own framing, pattern selection judgment lives in the body; this file only fleshes out the ABAP-specific mechanics for the patterns already called out as needing them. Sources/citation trail: [references/sources-deep-dive.md](sources-deep-dive.md).

## Version Safety

Classic ABAP Objects constructs used below (`CREATE PRIVATE`, interfaces, inheritance, `CLASS-DATA`) all predate the ABAP Cloud documentation window entirely — no version risk, same baseline reasoning as `modern-abap-syntax`'s deep-dive. One genuine exception, tied directly to the Observer replacement below:

| Feature | Introduced | Practical impact if unavailable |
|---|---|---|
| RAP business events — native event-driven architecture support (`RAISE ENTITY EVENT`) | Release 789 (2208 / 2022 Q3) | Fall back to a hand-rolled Observer (register/notify table + interface) inside the behavior pool |
| `FOR ENTITY EVENT`/`FOR EVENTS OF` local event-handler-class syntax, `CL_ABAP_BEHAVIOR_EVENT_HANDLER` | Release 792 (2305) | Business events can still be *raised*, but a local in-app reaction needs a different mechanism until this release — check with `[Skill: rap]`'s own deep-dive before assuming a local handler is available |

Don't assume RAP business events are available on every RAP-capable system just because RAP itself is much older — this is exactly the kind of "foundational-feeling but actually recent" gap the `rap` skill's own deep-dive already flags for other BDL constructs (`with additional save`, `numbering:managed`, etc., all 2019–2022).

## Singleton — Scoping in ABAP Cloud

The SKILL.md body's note ("`CREATE PRIVATE` + `CLASS-DATA go_instance` + `CLASS-METHODS get_instance`. In ABAP Cloud there is no cross-session shared memory — a 'singleton' lives per internal session only") in skeleton form:

```abap
CLASS lcl_singleton DEFINITION CREATE PRIVATE.
  PUBLIC SECTION.
    CLASS-METHODS get_instance RETURNING VALUE(instance) TYPE REF TO lcl_singleton.
    METHODS get_config RETURNING VALUE(config) TYPE ztconfig.
  PRIVATE SECTION.
    CLASS-DATA go_instance TYPE REF TO lcl_singleton.
    DATA config TYPE ztconfig.
    METHODS constructor.  "loads config once
ENDCLASS.

CLASS lcl_singleton IMPLEMENTATION.
  METHOD get_instance.
    IF go_instance IS NOT BOUND.
      go_instance = NEW lcl_singleton( ).
    ENDIF.
    instance = go_instance.
  ENDMETHOD.

  METHOD constructor.
    " Expensive one-time load (e.g., customizing/config read) happens here,
    " exactly once per internal session — not once per system/user as
    " "singleton" might suggest outside ABAP.
  ENDMETHOD.

  METHOD get_config.
    config = me->config.
  ENDMETHOD.
ENDCLASS.
```

The `IF go_instance IS NOT BOUND` guard, not a `class_constructor`, is what makes this lazy — a `class_constructor` would run at class-load time regardless of whether anyone ever calls `get_instance`. Reach for `class_constructor` only when the one-time setup must happen unconditionally before first use (e.g., initializing a constant lookup table the class always needs), not for the instance-creation guard itself.

## Factory — the Testability Seam

The SKILL.md body's note ("return an interface type; give the factory an injectable seam ... this is the seam `[Skill: abap-unit-testing]` relies on for dependency isolation") as a concrete pattern — this is the same shape `abap-unit-testing`'s constructor-injection guidance depends on, shown here from the factory/consumer side rather than the test side:

```abap
CLASS zcl_processor DEFINITION.
  PUBLIC SECTION.
    METHODS constructor
      IMPORTING io_provider TYPE REF TO zif_data_provider OPTIONAL.
    METHODS process RETURNING VALUE(rv_result) TYPE string.
  PRIVATE SECTION.
    DATA mo_provider TYPE REF TO zif_data_provider.
ENDCLASS.

CLASS zcl_processor IMPLEMENTATION.
  METHOD constructor.
    " The seam: caller gets the real provider by default, but a test
    " can substitute a double via the same constructor parameter —
    " no separate test-only entry point needed.
    mo_provider = COND #( WHEN io_provider IS BOUND THEN io_provider
                           ELSE NEW zcl_default_provider( ) ).
  ENDMETHOD.

  METHOD process.
    DATA(lt_data) = mo_provider->get_data( ).
    " ...
  ENDMETHOD.
ENDCLASS.
```

The "factory" here is the optional constructor parameter's default branch, not necessarily a separate `Factory` class — for a single concrete production implementation, the constructor-default form above is enough; only promote it to a dedicated `CREATE PRIVATE` + static `create( )` factory class when a second concrete implementation (a real variant, not just a test double) needs selecting by type/config at runtime, per the SKILL.md body's own Factory row ("variant selection by type code").

## Strategy / State — the Class-Explosion Warning, Concretely

The SKILL.md body's warning ("in ABAP each class is a repository object with TR overhead — before splitting per-state/per-strategy classes, confirm the variability is real and in the TS") applies to both Strategy and State because they share the same realization shape — one interface, N concrete classes, one context class holding a reference:

```abap
INTERFACE lif_pricing_strategy.
  METHODS calculate IMPORTING base_amount    TYPE p
                     RETURNING VALUE(result) TYPE p.
ENDINTERFACE.

CLASS lcl_strategy_standard DEFINITION.
  PUBLIC SECTION. INTERFACES lif_pricing_strategy.
ENDCLASS.
" ... one more CLASS ... ENDCLASS per variant — this is the TR-overhead cost:
" each variant is its own repository object, not a branch in one method.

CLASS lcl_pricing_context DEFINITION.
  PUBLIC SECTION.
    METHODS set_strategy IMPORTING strategy TYPE REF TO lif_pricing_strategy.
    METHODS calculate IMPORTING base_amount TYPE p
                       RETURNING VALUE(result) TYPE p.
  PRIVATE SECTION.
    DATA strategy_ref TYPE REF TO lif_pricing_strategy.
ENDCLASS.

CLASS lcl_pricing_context IMPLEMENTATION.
  METHOD set_strategy.
    strategy_ref = strategy.
  ENDMETHOD.
  METHOD calculate.
    result = strategy_ref->calculate( base_amount ).
  ENDMETHOD.
ENDCLASS.
```

The concrete number to weigh against TR overhead: **2 stable branches is a `COND`/`CASE`, not a pattern** — the SKILL.md body already says this for Strategy ("the 'strategies' are 2 branches of a stable IF"); the same threshold applies to State. The pattern starts earning its indirection once a 3rd variant is confirmed in the TS, or the per-variant logic is complex enough that a `CASE` branch would itself be multiple non-trivial statements — not before.

## Observer — RAP Business Events Replace Hand-Rolled Registries

The SKILL.md body's note ("`RAISE ENTITY EVENT` + event handler class replaces hand-rolled observer registries") — the exact syntax (verified against this workspace's own `rap-business-events` skill, which is sourced from the dedicated RAP Business Events cheat sheet, so it is not re-derived here):

In the behavior definition:

```
define behavior for ZR_Travel ...
{
  event travel_created;
  ...
}
```

```abap
"Raising it — in a determination or the saver, after the state change is committed-safe
RAISE ENTITY EVENT zr_travel~travel_created FROM VALUE #( ( %key = travel-%key ) ).
```

```abap
"Local reaction — a class implementing the generated event-handler interface
"(FOR ENTITY EVENT addition, release 792/2305+ — see Version Safety above)
CLASS lcl_travel_event_handler DEFINITION.
  PUBLIC SECTION.
    METHODS on_travel_created
      FOR ENTITY EVENT
      travel_created FOR Travel~travel_created.
ENDCLASS.
```

Don't hand-roll a register/notify table (the classic ABAP OO Observer shape shown for plain classes) inside a RAP behavior pool — the framework's own commit-coupled event queue (the event is only delivered after a successful `COMMIT`, never for a rolled-back change) already gives correctness a hand-rolled registry would have to reimplement. Reserve the classic register/notify Observer shape for plain, non-RAP classes where no BDEF/behavior pool exists to hang an event off of. Full producer/consumer wiring (event bindings, Event Mesh, external subscribers): `[Skill: rap-business-events]`.

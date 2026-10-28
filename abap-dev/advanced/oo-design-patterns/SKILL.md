---
name: oo-design-patterns
version: 1.0
description: Help with Object-Oriented Design Patterns (GoF) implemented in ABAP. Use when users ask about design patterns, Singleton, Factory, Observer, Strategy, Decorator, Builder, State, Command, Adapter, Facade, Composite, Iterator, Proxy, or OOP best practices. Triggers include "design pattern", "singleton", "factory", "observer", "strategy", "mẫu thiết kế", "oop abap".
---

# OO Design Patterns in ABAP

The build workflows need pattern *selection judgment*, not textbook implementations — you already know how to code every GoF pattern. **Never force a pattern the TS doesn't call for** (workspace rule §6: patterns are justified by the TS's Coding Implementation Plan, not aesthetics). A pattern that isn't earning its indirection is worse than a plain class.

## When Is Which Pattern Warranted

| Pattern | Use in ABAP/RAP context when... | Avoid when... |
|---|---|---|
| **Singleton** | One shared config/cache/connection holder per session | It's hiding global state that makes tests order-dependent; RAP handlers are stateless anyway |
| **Factory** | Callers must not know the concrete class — test injection (interface + `create object` behind a static `create( )`), variant selection by type code | There's exactly one implementation and no test seam needed |
| **Strategy** | An algorithm varies by config/customizing (pricing rule, validation policy) chosen at runtime | The "strategies" are 2 branches of a stable IF — COND is enough |
| **Observer** | Decoupled reaction to a change; in RAP prefer **business events** ([Skill: rap-business-events]) over hand-rolled observers | A direct method call is clearer and the coupling is fine |
| **Decorator** | Layering optional behavior (logging, caching) over an interface without touching implementations | Subclassing or a plain wrapper method does the job |
| **Builder** | Constructing an object with many optional parts stepwise (test-data builders are the classic ABAP use) | A `VALUE #( )` constructor expression covers it |
| **State** | A status machine where behavior per state is complex enough to warrant one class per state | Status logic fits in a determination/validation + CASE — typical for most RAP BOs |
| **Command** | Queue/undo/audit of operations as objects (e.g., batch job step lists) | You're just calling a method |
| **Adapter** | Wrapping an unreleased/legacy API behind a clean released interface — the Tier-2 wrapper pattern IS an adapter ([Skill: abap-cloud-migration]) | Signatures already match |
| **Facade** | One entry point over a subsystem (e.g., a supporting class hiding several I_* view reads from a behavior pool) | It would be a one-method pass-through |
| **Composite** | Uniform treatment of tree structures (BOM explosions, org hierarchies) | The hierarchy is fixed at 2 levels — just loop |
| **Iterator** | Custom traversal order/lazy paging over a non-table source | It's an internal table — LOOP/FOR already iterate |
| **Proxy** | Lazy loading or access control in front of an expensive resource (RFC destination, HTTP client) | The resource is cheap to create |

## ABAP-Specific Realization Notes

Only where the ABAP realization is non-obvious:

- **Singleton**: `CREATE PRIVATE` + `CLASS-DATA go_instance` + `CLASS-METHODS get_instance`. In ABAP Cloud there is no cross-session shared memory — a "singleton" lives per internal session only.
- **Factory for testability**: return an interface type; give the factory an injectable seam (`CLASS-METHODS set_instance FOR TESTING` or constructor injection in the consumer) — this is the seam [Skill: abap-unit-testing] relies on for dependency isolation.
- **Strategy/State class explosion**: in ABAP each class is a repository object with TR overhead — before splitting per-state/per-strategy classes, confirm the variability is real and in the TS.
- **Observer in RAP**: `RAISE ENTITY EVENT` + event handler class replaces hand-rolled observer registries.

## Deep Dive

For real, short skeletons of the 4 realizations above (Singleton, Factory, Strategy/State, Observer) and the one genuine version-gating finding (RAP business events are newer than RAP itself), read [references/deep-dive.md](references/deep-dive.md) — this does not turn into a full GoF cookbook, only the 4 already flagged as non-obvious.

## Output Format

When recommending a pattern: name it, state the forces that justify it (one sentence, tied to the TS/FS requirement), then give the ABAP skeleton. If no pattern is warranted, say so explicitly — "plain class, no pattern" is a valid recommendation.

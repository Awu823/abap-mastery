---
name: abap-workflows
description: |
  Orchestration workflows for the abap-mastery skills library. Chains the merged sub-skills into
  end-to-end, phased, gate-checked pipelines for the four canonical ABAP delivery scenarios:
  (A) Functional-Spec -> Fiori app (document-driven), (B) RAP business object (greenfield),
  (C) code quality & release gate, (D) ABAP Cloud migration / clean core. Load this skill when
  the task spans multiple sub-skills or needs a defined sequence with checkpoints. Triggers include
  "workflow", "pipeline", "end-to-end abap", "from FS to Fiori", "greenfield RAP app", "release
  gate", "cloud migration workflow", "how do I deliver this step by step", "orchestrate abap".
---

# abap-mastery Workflows

> Orchestration layer over `abap-mastery`. Each workflow is a **phased pipeline** where every phase
> loads one or more sub-skills, and gates (checkpoints) must pass before advancing.
> Sub-skills are referenced by **relative path** from `abap-dev/workflows/` (e.g. `../core/rap`).

## How to run a workflow

1. Pick the workflow matching the task: **A** (FS→Fiori), **B** (RAP greenfield), **C** (quality/release), **D** (cloud migration).
2. Execute phases **in order**. Each phase lists the sub-skill(s) to load and the deliverable to produce.
3. Run the **gate** at the end of each phase; do NOT advance on a failed gate — fix, re-run, then continue.
4. Use `../productivity/scratchpad` to track multi-phase progress, and `../productivity/handoff` to
   hand off context if the session is interrupted.
5. Cross-cutting helpers available in any phase: `../productivity/grill-me` (clarify ambiguity),
   `../productivity/caveman` (terse progress narration), `../productivity/activation-guard` (verify activation).

---

## Workflow A — FS 文档 → Fiori 应用（文档驱动开发）

**Goal:** turn a Functional Specification (FS) into a deployable Fiori app on ABAP Cloud.

| Phase | Load sub-skill(s) | Deliverable / action | Gate |
|---|---|---|---|
| A1 预处理 | `../productivity/document-markdown-converter` (PDF/DOCX→MD), `../fs-analysis/fs-vision-extractor` (图片/表格→结构化) | 干净的 FS 文本 + 结构化表格 | 文档可检索 |
| A2 澄清 | `../productivity/grill-me` | 需求/范围/接口确认 | 无未决问题 |
| A3 数据模型 | `../fs-analysis/fs-data-model-extractor` | 表/CDS/join/key 清单 | 实体齐全 |
| A4 UI 规格 | `../fs-analysis/fs-fiori-ui-elements-mapper` | Fiori Elements 注解规格 | 字段映射完成 |
| A5 API/集成 | `../fs-analysis/fs-integration-api-analyzer` | OData/REST/JSON payload 规格 | 接口契约定稿 |
| A6 业务逻辑 | `../fs-analysis/fs-logic-behavior-translator` | 规则/权限/状态机 → 实现策略 | 行为已定 |
| A7 领域校验 | `../process/sap-process-*`（按模块，如 `sap-process-o2c-sell-from-stock`） | 核对 scope item 语义 | 与标准流程一致 |
| A8 复用 | `../fs-analysis/find-released-cds-view` | 选中 released CDS/文本/值帮助 | 无重复造轮子 |
| A9 设计 | `../core/cds-view-entities`, `../advanced/cds-analytical-views`, `../advanced/cds-data-model-analysis`, `../core/rap`, `../advanced/naming-convention` | CDS/BDEF 设计稿 | 命名/建模评审 |
| A10 实现 | `../core/abap`, `../advanced/modern-abap-syntax`, `../advanced/lean-abap`, `../core/abap-sql-amdp` | 代码 + 最小实现 | 编译通过 |
| A11 暴露 | `../core/odata`, `../advanced/sap-fiori-apps-reference` | 服务绑定 + FLP URL | 服务可访问 |
| A12 激活 | `../productivity/activation-guard` | 激活校验（无 error/warning） | 激活干净 |
| A13 测试 | `../core/abap-unit-testing` | 单元测试（CDS/RAP 环境） | 测试通过 |
| A14 交付 | `../productivity/handoff`, `../productivity/scratchpad` | 交接记录 | 上下文完整 |

---

## Workflow B — RAP 业务对象（Greenfield）

**Goal:** build a managed/unmanaged RAP BO with draft, events, authorization, and OData exposure.

| Phase | Load sub-skill(s) | Deliverable / action | Gate |
|---|---|---|---|
| B1 环境 | `../core/btp-abap-environment`, `/sap-project-init` (commands) | 服务实例/包结构/软件组件 | 环境就绪 |
| B2 数据模型 | `../core/cds-view-entities` | 根/子 CDS 视图实体 | 模型一致 |
| B3 行为 | `../core/rap` | BDEF（managed/unmanaged、draft、action、validation、determination） | 行为合法 |
| B4 查询 | `../advanced/rap-query-provider`（如需自定义实体） | `IF_RAP_QUERY_PROVIDER` 实现 | 无 "Query not fully covered" |
| B5 服务 | `../core/odata` | 服务定义/绑定（V4） | 绑定激活 |
| B6 事件 | `../core/rap-business-events` | 事件定义 + `RAISE ENTITY EVENT` | 事件绑定 |
| B7 授权 | `../core/authorization-iam` | DCL + 实例/全局授权 | 权限闭环 |
| B8 增强 | `../core/badi-enhancement`（可选） | 客户扩展点 | — |
| B9 激活 | `../productivity/activation-guard` | 激活链校验 | 激活干净 |
| B10 测试 | `../core/abap-unit-testing` | RAP BO test doubles / EML 测试 | 测试通过 |
| B11 暴露 | `../core/sap-fiori-url-generator` | FLP URL | 可预览 |

---

## Workflow C — 代码质量与发布门禁

**Goal:** take authored ABAP code through static analysis, review, and release readiness.

| Phase | Load sub-skill(s) | Deliverable / action | Gate |
|---|---|---|---|
| C1 静态检查 | `../core/abap` (abaplint) | 语法/类型/规则报告 | 无 Error |
| C2 干净代码 | `../advanced/clean-abap`, `../core/abap` (Clean ABAP 审查) | 15 类目问题清单 | 无 Critical |
| C3 单元测试 | `../core/abap-unit-testing` | 覆盖率/断言 | 全绿 |
| C4 代码审查 | `../../code-review/abap-code-review`（或 `../../code-review/abap-guardian`） | 9 维 / 企业级 GO-NO-GO | GO |
| C5 ATC 合规 | `../core/atc-cloudification` | Clean Core / Cloud Readiness 检查 | 无 P1 |
| C6 传输就绪 | `../../code-review/sap-transport-gate` | 传输请求就绪评估 | READY |
| C7 对象读写 | `../../code-review/sap-adt-cli`（如需自动化） | ADT 读/写 | 一致 |

---

## Workflow D — ABAP Cloud 迁移（Brownfield → Clean Core）

**Goal:** migrate classic ABAP custom code toward clean core Level A.

| Phase | Load sub-skill(s) | Deliverable / action | Gate |
|---|---|---|---|
| D1 评估 | `../core/atc-cloudification` | Cloud Readiness 发现清单 | 发现完成 |
| D2 定位替代 | `../core/released-abap-classes`, `../fs-analysis/find-released-cds-view` | 已发布替代候选 | 候选就绪 |
| D3 替换 | `../core/abap-cloud-migration` | 替换表 + wrapper 类 | 无未替换 |
| D4 合规 | `../core/abap-cloud` | Clean Core 级别核对（A/B/C/D） | 达目标级 |
| D5 复检 | `../core/abap-unit-testing`, `../core/atc-cloudification` | 回归测试 + ATC 复检 | 全绿 |

---

## Cross-cutting guidance

- **Always** end each phase by verifying the gate; a skipped gate is the #1 cause of cascading failures.
- **Prefer reuse before writing:** climb the reuse ladder (existing Z-object → released SAP content →
  declarative CDS/RAP feature → language built-in → minimum code) per `../advanced/lean-abap`.
- **Log deliberate shortcuts** with the `shortcut:` convention (collected by `/sap-debt`).
- **Multi-session work:** keep a `../productivity/scratchpad` ledger; use `../productivity/handoff` before compaction.
- **Domain grounding:** when a FS touches Finance/SCM/PP/PS, load the matching `../process/sap-process-*`
  skill in phase A7 to avoid inventing non-standard semantics.

## Related artifacts

- `SKILL_INDEX.md` — full 107-skill index · `SKILL.md` (root) — entry router · `commands/` — Claude slash commands

# Clean ABAP & Enterprise Architecture

## Clean ABAP Principles
- **Use Object-Oriented ABAP**: Prefer Classes (`CL_`) and Interfaces (`IF_`) over function modules and subroutines (`FORM`).
- **Small Methods**: Methods should do exactly one thing. Keep them short (under 50 lines).
- **Naming Conventions**: 
  - Use descriptive English names (e.g., `calculate_total` instead of `calc_tot`).
  - Avoid obsolete prefixes like `lt_` or `ls_` for local variables if the scope is small enough, though many legacy systems still enforce them. Follow the project's specific convention, but prefer semantic names.
- **Error Handling**: Use class-based exceptions (`CX_`) instead of `SY-SUBRC` and classic exceptions.

## Enterprise Architecture & Frameworks
- **Separation of Concerns**: Never mix UI logic, business logic, and database access in the same class.
- **Dependency Injection**: Pass dependencies (APIs, database adapters) into constructors as interfaces (`IF_`) rather than instantiating hardcoded classes inside business logic. This enables seamless unit testing with test doubles.
- **RAP (RESTful Application Programming)**: 
  - Use Behavior Definitions (BDEF) and Behavior Implementations (ABAP for RAP) for transactional logic.
  - Implement EML (Entity Manipulation Language) safely (`MODIFY ENTITIES`).
- **CDS View Entities (7.55+ / ABAP Cloud)**: 
  - Replace classic `DEFINE VIEW` (which generates obsolete SQL DB views `@AbapCatalog.sqlViewName`) with `DEFINE VIEW ENTITY`.
  - Push data-intensive logic to SAP HANA using CDS view entities rather than doing heavy lifting in ABAP application server memory.

## ABAP Cloud Compliance Auditing
When reviewing code targeted at **ABAP Cloud** (SAP BTP ABAP Environment or S/4HANA Cloud):
- **Prohibited Statements**: Flag legacy statements like `WRITE`, `MOVE...TO`, `DESCRIBE TABLE`, `CALL FUNCTION`, and `FORM...ENDFORM`.
- **Released APIs Only**: Flag unreleased SAP SAP-internal function modules or tables. Mandate released APIs (e.g. `cl_system_uuid` for UUIDs, `xco_cp` for system date/time).
- **Prohibited System Fields**: Flag direct access to unreleased system fields (e.g. `sy-datum`, `sy-uzeit`) in favor of released time abstractions.
- **Strict Interface Contracts**: Mandate explicit interface exposure (`IF_`) for cross-package APIs.

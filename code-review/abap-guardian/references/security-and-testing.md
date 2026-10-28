# Security & Testing

## Security Standards
- **Authorization Checks**: Every entry point (OData service, report, transaction) must have an `AUTHORITY-CHECK` or CDS Access Control (DCL).
- **Dynamic Programming Risk**: When using dynamic `WHERE` conditions or dynamic `(table_name)`, validate the input to prevent SQL injection. Use `cl_abap_dyn_prg` methods (e.g., `check_table_name_str`).
- **Directory Traversal**: Validate file paths when working with the application server file system (`OPEN DATASET`).

## Testing Standards (ABAP Unit)
- **Unit Test Classes**: Every business logic class must have a corresponding local test class (`FOR TESTING`).
- **Test Seams**: Use `TEST-SEAM` to mock database accesses or external API calls if modern mocking frameworks (OSQL Test Environment) are not available.
- **Mocking Frameworks**:
  - Use `cl_abap_testdouble` to create test doubles for interface dependencies without writing manual mock classes.
  - Use `cl_osql_test_environment` to mock database tables and `cl_cds_test_environment` to mock CDS views during unit tests.
- **Assertions**: Use `cl_abap_unit_assert` for validating expected outcomes.

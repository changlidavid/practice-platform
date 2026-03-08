# Engineering Constitution

## Purpose
This constitution defines mandatory engineering principles for planning, implementing, reviewing, and releasing software.

## 1. Code Quality
- Code MUST be readable, maintainable, and intentionally structured.
- Every change MUST be small enough to review effectively and SHOULD avoid unrelated refactors.
- Public interfaces MUST be documented with clear behavior, inputs, outputs, and failure modes.
- Linters and formatters MUST pass before merge.
- New dependencies MUST be justified in the change description and approved by maintainers.

### Code Quality Gates
- No unresolved TODO/FIXME in production code unless linked to a tracked issue.
- No duplicated logic when a shared abstraction is practical.
- No dead code paths in modified areas.

## 2. Testing Standards
- All new features MUST include tests covering expected behavior and key edge cases.
- All bug fixes MUST include a regression test that fails before and passes after the fix.
- Test suites MUST be deterministic and runnable in CI.
- Critical paths (auth, billing, data integrity, security boundaries) MUST include integration or end-to-end coverage.
- Flaky tests MUST be fixed or quarantined immediately; recurring flakes block release.

### Testing Gates
- Unit and integration test pipelines MUST pass on every merge.
- Code coverage for changed files MUST NOT decrease; high-risk modules SHOULD maintain >=90% line coverage.
- Negative-path tests (invalid input, network/service failure, permission failure) MUST be present for external-facing behavior.

## 3. User Experience Consistency
- UI and interaction behavior MUST follow the established design system and content style.
- Similar user actions MUST produce consistent controls, feedback, and error messaging.
- Accessibility MUST be built in by default: semantic structure, keyboard navigation, focus visibility, contrast, and screen-reader labels.
- Loading, empty, success, and error states MUST be designed and tested for each user-facing flow.
- Breaking UX changes MUST include migration notes and stakeholder sign-off.

### UX Gates
- No new UI component is merged without responsive behavior for supported viewport ranges.
- No user-facing error is merged without actionable guidance.
- Accessibility checks (automated + manual keyboard pass) MUST pass for changed screens.

## 4. Performance Requirements
- Performance budgets MUST be defined and tracked for key user journeys and service endpoints.
- Changes MUST NOT regress page load, interaction latency, memory use, or API response time beyond budget.
- Expensive operations MUST be measured, optimized, or deferred using caching, batching, streaming, or pagination where appropriate.
- Performance-critical code paths MUST include metrics and observability hooks.
- Capacity-impacting changes MUST include load-test evidence before release.

### Performance Gates
- Frontend: Core interactions SHOULD remain within target latency budgets on representative devices/network profiles.
- Backend: P95 and P99 latency for critical endpoints MUST remain within SLO targets.
- Any performance regression above agreed thresholds blocks release unless explicitly waived.

## 5. Governance and Enforcement
- Pull requests MUST include: scope, rationale, test evidence, UX impact, and performance impact.
- Reviewers MUST verify all gates relevant to the change; missing evidence is grounds for rejection.
- Exceptions MUST be time-bound, documented, and approved by a maintainer.
- This constitution MAY be amended via pull request with maintainer approval and versioned changelog updates.

## 6. Definition of Done
A change is done only when:
- Implementation is complete and reviewed.
- All applicable tests pass in CI.
- UX states and accessibility are verified.
- Performance impact is measured and within budget.
- Documentation and runbooks are updated as needed.

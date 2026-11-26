# 0001: Business hours do not change priority

## Context

A customer-facing incident opened at night was assigned a lower priority than the same incident opened during the
day, contrary to the documented rule that the customer-facing uplift applies at any hour.
([Issue #12](https://github.com/termidy/incidentdesk-rehearsal/issues/12))

## Decision

Apply the customer-facing uplift independently of business hours; a major incident on the customer-facing
login service is P1 on Tuesday night and on Saturday morning.
([PR #57](https://github.com/termidy/incidentdesk-rehearsal/pull/57))
Business hours continue to determine who responds first, without changing routing.
([Issue #12](https://github.com/termidy/incidentdesk-rehearsal/issues/12))
Apply the maintenance adjustment after the customer-facing uplift, clamping each adjustment to the P1–P4 range.
([Commit 37bc99b](https://github.com/termidy/incidentdesk-rehearsal/commit/37bc99b0136b341c473b7a1c65d3c99fbf1e589e))

## Consequences

New customer-facing incidents no longer miss their uplift merely because they open outside business hours.
([Commit feb21b6](https://github.com/termidy/incidentdesk-rehearsal/commit/feb21b68846a030f0277cb8afe9bf41b92fc0bdc))
Re-prioritizing incidents already stored was outside the scope of the fix.
([Issue #12](https://github.com/termidy/incidentdesk-rehearsal/issues/12))
Gap: the issue and fix do not specify a procedure for correcting previously stored priorities.

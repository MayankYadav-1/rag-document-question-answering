# Northwind Robotics — Engineering On-Call Handbook

## Rotation

Each engineering team runs a weekly on-call rotation. An on-call shift begins on
Monday at 10:00 AM and ends the following Monday at 10:00 AM. No engineer should
be scheduled for on-call more than one week in any four-week period.

Engineers who are on-call receive an on-call stipend of $500 per week in addition
to their regular salary.

## Severity Levels

Incidents are classified into three severity levels:

- **SEV1**: Complete outage or data loss affecting many customers. Must be
  acknowledged within 5 minutes at any hour.
- **SEV2**: Major functionality degraded for some customers. Must be acknowledged
  within 15 minutes during business hours.
- **SEV3**: Minor issue with a workaround available. Must be acknowledged within
  one business day.

## Escalation

If the primary on-call engineer does not acknowledge a SEV1 within 5 minutes, the
alert automatically escalates to the secondary on-call engineer. If the secondary
does not respond within a further 5 minutes, the engineering manager is paged.

## Service Level Agreements

Northwind's customer-facing SLA guarantees 99.9% uptime measured monthly, which
allows for approximately 43 minutes of downtime per month. Breaching the SLA
triggers service credits to affected customers as described in the master service
agreement.

## Postmortems

Every SEV1 and SEV2 incident requires a written, blameless postmortem published
within 5 business days. Postmortems are stored in the engineering wiki and are
reviewed in a weekly reliability meeting.

## Deploy Freeze

There is a company-wide deploy freeze from December 20 through January 2 each
year. Deploys during the freeze require VP of Engineering approval.

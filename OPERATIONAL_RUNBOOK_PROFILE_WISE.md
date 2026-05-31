# KarthikAi-OMS Operational Runbook (Profile-Wise)

This runbook defines the minimum end-to-end operating model for running KarthikAi-OMS in a live organizational environment.

## 1) Operating Objective

Run platform, tenant, delivery, people, finance, and client-visibility workflows with:

- clear ownership by user profile,
- strict RBAC and data-scope boundaries,
- repeatable daily/weekly/monthly execution cycles,
- measurable handoffs between teams.

---

## 2) User Profiles and Core Responsibilities

## Super Admin (Platform Owner)

Owns platform governance and tenant lifecycle, not tenant execution work.

1. Sign in and monitor platform dashboard.
2. Create company tenant and assign package/subscription.
3. Generate company admin invite and monitor acceptance.
4. Track tenant health:
   - active/inactive status
   - user/client/project counts
   - support and subscription summary
5. Activate/deactivate tenants when required.
6. Review platform-level reports and exceptions.
7. Confirm privacy boundary:
   - must not run tenant operational modules (tasks, timesheets, leave, invoices execution).

## Company Admin (Tenant Operator)

Owns company setup, governance, and all tenant-wide operations.

1. Accept invite and complete first login.
2. Configure company workspace:
   - profile, timezone, currency, working calendar.
3. Configure master data:
   - departments, designations, roles, permissions.
4. Create and activate users by function:
   - PM, employee, finance, HR, management, account roles.
5. Validate role-wise menus and access.
6. Oversee all company modules:
   - clients, projects, delivery, people ops, finance, risks/issues, reports.
7. Run data-governance checks:
   - no cross-company leakage
   - stale records and exception review.

## Project Manager (Delivery Owner)

Owns project delivery flow and project-linked operational coordination.

1. Create/manage clients and projects.
2. Build project structure:
   - team members, milestones, deliverables, tasks.
3. Assign tasks to employees with due dates/priority/status.
4. Track execution and update project/task state.
5. Run collaboration workflows:
   - meetings and documents.
6. Manage delivery controls:
   - issues, risks, change requests, support tickets.
7. Review employee timesheets and project evidence.
8. Feed delivery KPI status into reporting/governance.

## Employee / Staff (Execution User)

Executes assigned work and submits self-scoped operational records.

1. View assigned projects/tasks only.
2. Execute and update tasks (status/progress/notes).
3. Submit personal operations:
   - timesheets (with entries),
   - attendance,
   - leave,
   - expenses.
4. Access project-linked meetings/documents only.
5. Complete weekly close:
   - task updates + timesheet + attendance/leave correctness.

## Finance User (Billing Operator)

Owns billing lifecycle and payment reconciliation.

1. Create invoices linked to client/project.
2. Record payments against invoices.
3. Verify invoice state transitions:
   - draft -> partial -> paid.
4. Reconcile balances and exceptions.
5. Publish finance metrics for admin/reporting.

## Client User / Client Admin (External Stakeholder)

Portal-only visibility of own client data.

1. Sign in to client portal.
2. View own project summaries/status.
3. View permitted client-facing artifacts.
4. No internal create/edit/delete access.
5. No access to other clients’ projects/data.

## Functional Oversight Roles (Management, Delivery Manager, Account Manager, HR Manager)

Role-specific oversight and controlled intervention.

1. Access only assigned modules per role permissions.
2. Review delivery/people/finance/risk indicators.
3. Perform approvals/interventions where enabled.
4. Maintain company-only data boundary.

---

## 3) End-to-End Operational Lifecycle

## Phase A: Platform and Tenant Onboarding

1. Super Admin creates company.
2. Company admin invite is generated.
3. Company Admin accepts invite and tenant activates.

## Phase B: Company Enablement

1. Company Admin configures workspace and master data.
2. Company Admin creates operational users/roles.
3. RBAC/menu/scope checks are completed for all roles.

## Phase C: Delivery Setup and Execution

1. PM creates client and project.
2. PM adds team, milestones, deliverables, tasks.
3. PM assigns tasks to employees.
4. Employees execute work and update tasks.
5. PM reviews progress and adjusts delivery.

## Phase D: People Operations

1. Employees submit timesheets, leave, attendance, expenses.
2. PM/Admin review relevant records per scope.

## Phase E: Collaboration and Control

1. PM runs meetings and documents.
2. PM manages issues, risks, change requests, support tickets.

## Phase F: Commercial Operations

1. Finance creates invoices.
2. Finance records payments.
3. Invoice balances and statuses reconcile correctly.

## Phase G: Client Transparency and Reporting

1. Client users view own project data in portal.
2. Role-based reports render scoped metrics.
3. Admin and Super Admin complete governance review.

---

## 4) Role Handoff Matrix

1. Super Admin -> Company Admin:
   tenant created, invite accepted, company active.
2. Company Admin -> PM/Employees/Finance:
   users created, roles assigned, module access validated.
3. PM -> Employee:
   assignments issued with required details.
4. Employee -> PM:
   task progress and timesheet entries submitted.
5. PM/Company Admin -> Finance:
   billable project state ready for invoicing.
6. Finance -> Company Admin/Reports:
   billing/payment status available for governance.
7. Internal Ops -> Client Portal:
   approved visibility data reflected for client users.

---

## 5) Live Readiness Acceptance Checklist

System is considered live-operational only if all pass:

1. Authentication and role landing pages are correct.
2. Profile-wise menu visibility matches permissions.
3. Restricted modules are denied (403/hidden) for unauthorized roles.
4. Cross-company isolation works for all data-bearing modules.
5. Core flow records link correctly:
   - client -> project -> task
   - invoice -> payment
   - timesheet -> timesheet entries
6. People ops forms work with required seed prerequisites:
   - leave policy
   - expense category
7. Document upload and retrieval works.
8. Reports are role-scoped and consistent with source records.
9. Client portal remains view-only and client-scoped.
10. Super Admin privacy boundary is enforced for tenant staff operations.

---

## 6) Daily / Weekly / Monthly Cadence

## Daily

1. PM reviews task progress and blockers.
2. Employees update task status and submit activity records.
3. Finance monitors unpaid/partial invoices.
4. Company Admin checks exceptions (access, data integrity, overdue items).

## Weekly

1. PM validates timesheets and delivery status.
2. Company Admin reviews people ops and delivery health.
3. Finance performs payment reconciliation.
4. Client-facing status refresh for portal visibility.

## Monthly

1. Tenant governance review (Company Admin).
2. Platform governance review (Super Admin).
3. Access-role audit and cleanup.
4. Reporting sign-off for delivery + people + finance.

---

## 7) Current Operational Preconditions

For stable production usage, keep these guaranteed:

1. Seed data exists for leave policies and expense categories.
2. RBAC module access checks are active on custom + generic views.
3. Timesheet flow captures entries, not only parent timesheet headers.
4. Generic list templates keep header/row column counts consistent.
5. Invite acceptance flow and tenant activation remain functional.

---

## 8) Go-Live Verification Order (Recommended)

1. Super Admin creates company.
2. Company Admin accepts invite and configures workspace.
3. Company Admin creates PM/Employee/Finance users.
4. PM creates client + project + team + tasks.
5. Employee executes task + submits timesheet/leave/attendance.
6. PM runs meeting/document/issue/risk workflows.
7. Finance runs invoice/payment workflows.
8. Client user validates portal view-only access.
9. Company Admin validates company-wide reporting.
10. Super Admin validates platform monitoring + privacy boundary.


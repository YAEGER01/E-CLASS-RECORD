Legend:

- ⏳ Pending
- 🚧 Ongoing
- ✅ Done
- 🏁 Finished (phase fully complete)

🧩 PHASE 1 — DATA FOUNDATION 🏁

Status: 🏁 Finished (tables, versioning, JSON schema validation)

Goal: Establish consistent data flow and database schema.

✅ Confirm existing tables — DONE (present in db/\*.sql)

grade_structures (already exists)

students

classes

student_classes (pivot table)

grade_assessments (optional, extracted from JSON)

student_scores

🛠️ Define JSON schema standards — ✅ Done (server-side validation in app.py: validate_structure_json)

Every structure in grade_structures.structure_json follows:

{
"LABORATORY": [
{
"name": "LAB TINGS",
"weight": 50,
"assessments": [
{"name": "Wan Ting", "max_score": 50}
]
}
],
"LECTURE": []
}

Ensure all categories follow same field names (name, weight, assessments, etc.)

🔄 Create versioning strategy — ✅ Done

Add or use version column (already present).

Implement auto-increment or timestamp versioning for edits.

⚙️ PHASE 2 — NORMALIZATION API 🏁

Status: 🏁 Finished (API + flatten + caching)

Goal: Flatten structure_json for easier access and manipulation.

Create route: /api/classes/<id>/normalized — ✅ Done (see app.py: api_get_normalized)

Process:

Load structure_json from DB. — ✅ Done (app.py: api_get_normalized & test_grade_normalizer)

Flatten structure into a list of objects. — ✅ Done (server: app.py: normalize_structure; client also in template for UI)

Example output:

[
{"category": "LABORATORY", "name": "LAB TINGS", "weight": 50, "assessment": "Wan Ting", "max_score": 50},
{"category": "LABORATORY", "name": "LAB TINGS", "weight": 50, "assessment": "Tu Ting", "max_score": 50}
]

Store or cache normalized data temporarily (Redis, or memory). — ✅ Done (in-memory cache keyed by /live-version; see app.py)

🧮 PHASE 3 — GROUPER / SEPARATOR API 🏁

Status: 🏁 Finished (API + grouping + caching)

Goal: Separate string vs numeric values for easier grade computation.

Create route: /api/classes/<id>/grouped — ✅ Done (see app.py: api_get_grouped)

Input: Normalized data from /normalized.

Process:

Split keys into:

Strings: name, category, assessment

Numbers: weight, max_score

Output Example:

{
"strings": [
{"category": "LABORATORY", "name": "LAB TINGS", "assessment": "Wan Ting"}
],
"numbers": [
{"weight": 50, "max_score": 50}
]
}

Purpose: Provide consistent format for the grade calculator.

🧮 PHASE 4 — GRADE CALCULATION LAYER 🚧

Status: 🚧 Ongoing (dynamic templates + calculate API)

Goal: Perform dynamic, weight-based, and score-based computations with editable calculation templates.

What’s implemented now:

- Database tables: grade_calculation_templates, professor_calculation_overrides (see db/2025-10-31-grade-calculation-templates.sql)
- Routes (templates management):
  - GET /grade-calculations — list default templates (page)
  - GET /grade-calculations/<id> — view single template (page)
  - POST /grade-calculations/<id>/clone — clone a default for the current instructor (class-specific optional)
  - GET /grade-calculations/professor/<prof_id> — list professor overrides (JSON; self or admin)
- Calculate API:
  - GET /api/classes/<id>/calculate — resolves active formula (professor override for class → professor-level override → default), computes per-student totals and equivalent
  - Helpers: perform_grade_computation(), get_equivalent(), \_resolve_active_formula_for_class()

Assumptions (v1):

- We scale category contributions from the structure weights to match the formula’s total per-category weight (sum of parts like major/minor). Detailed part-to-assessment mapping will come next.
- Assessment matching uses names from grade_assessments joined with student_scores; normalized structure provides max_score.

Next steps to finish the phase:

- Add override edit/save UI for instructors (JSON editor) and activation toggles
- Optional: per-class override toggle and deactivation of older overrides
- Weight validation (must total 100%) and richer formula interpreter
- Student-scoped access in /calculate (Phase 7)

Output Example:

[
{"student_id": 1, "final_grade": 89.4, "equivalent": "1.75"},
{"student_id": 2, "final_grade": 91.2, "equivalent": "1.50"}
]

🔐 PHASE 5 — ACCESS CONTROL (ROLE-BASED) 🚧

Status: 🚧 Ongoing (route guards implemented; calculators pending)

Goal: Allow data reuse for multiple roles with scoped visibility.

Implement user roles: instructor, student, admin. — ✅ Done (session role checks + login_required in app.py)

Guard routes: — ✅ Done (role-checked routes across /api/admin, /api/instructor, /api/student)

Instructor: can view all students. — 🚧 Ongoing (e.g., /api/instructor/classes/<id>/members)

Student: can only view self. — 🚧 Ongoing (e.g., /api/student/joined-classes filters by current user)

Shared computation: same /calculate logic reused. — ⏳ Pending

Decorator example:

@role_required(['instructor', 'student'])

Add student filter:

if current_user.role == 'student':
limit results to current_user.id

🧑‍🏫 PHASE 6 — INSTRUCTOR MODULE 🚧

Status: 🚧 Ongoing

Goal: Manage grade structures and run computations.

Routes:

/api/instructor/classes

/api/instructor/class/<id>/grades — ⏳ Pending (API) | ✅ Done (Page route: /instructor/class/<id>/grades)

/api/instructor/class/<id>/calculate — ⏳ Pending

Features:

Create / edit / version grade structures. — ✅ Done (/api/gradebuilder/save, /history, /restore, /delete)

Run calculations. — ⏳ Pending

View all student results. — 🚧 Ongoing (members list available; computed grades not yet)

🎓 PHASE 7 — STUDENT MODULE ⏳

Status: ⏳ Pending (core grade view missing)

Goal: Allow students to view their computed grades.

Route: /api/student/classes/<class_id>/grades — ⏳ Pending

Internally calls: /api/classes/<id>/calculate

Auto-filters: by current logged-in student ID.

Frontend:

Read-only grade view.

Display computations breakdown (optional).

🧱 PHASE 8 — SYSTEM REUSE & OPTIMIZATION 🚧

Status: 🚧 Ongoing (version hash endpoint exists)

Goal: Centralize and optimize logic for maintainability.

Extract shared logic: — ⏳ Pending

normalize_structure(structure_json)

group_structure(normalized)

perform_grade_computation(grouped, scores)

Cache heavy operations. — 🚧 Ongoing (normalized cache in-memory; consider Redis)

Version check: — ✅ Done (see /api/classes/<id>/live-version)

Invalidate cached normalized/grouped data when version changes.

Add API versioning: — ⏳ Pending

/api/v1/...

🧰 PHASE 9 — TESTING & VALIDATION ⏳

Status: ⏳ Pending

Unit test each helper function:

Normalizer

Grouper

Calculator

Integration test:

End-to-end grade flow (instructor → compute → student view).

Edge cases:

No scores yet

Incomplete weights

Version mismatch

🚀 PHASE 10 — FRONTEND CONNECTION 🚧

Status: 🚧 Ongoing (gradebuilder wired; compute pipeline pending)

Goal: Connect Flask APIs to your frontend (Vue, React, or vanilla JS).

Instructor view:

Load normalized + computed data for class dashboard.

Student view:

Display own grades with breakdown.

UI considerations:

Dynamic recalculation preview when weights change.

Loading indicators for grouped/normalized data.

✅ SUMMARY FLOW
[MariaDB]
↓
/api/classes/<id>/normalized
↓
/api/classes/<id>/grouped
↓
/api/classes/<id>/calculate
↓
┌───────────────────┐
│ Role-based Layer │
├───────────────────┤
│ Instructor → All │
│ Student → Self │
└───────────────────┘
↓
Frontend (Instructor / Student)

Notes (what already exists):

- Grade structures CRUD + version history: /api/gradebuilder/\* in app.py
- Instructor endpoints: /api/instructor/classes, /api/instructor/classes/<id>/members, /details
- Student endpoints: /api/student/join-class, /api/student/joined-classes, /api/student/leave-class/<id>
- Version hash endpoint: /api/classes/<id>/live-version (useful for cache invalidation)
- Dev-only view for structure visualization/testing: /test-grade-normalizer/<class_id>

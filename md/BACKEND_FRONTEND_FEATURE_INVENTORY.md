# AptiFy Backend ↔ Frontend Feature Inventory

**Generated after integration.** Backend is source of truth; frontend exposes it.

---

## Task 1 — Backend Audit

### Django apps scanned
- **users**: User, Profile, Achievement, Goal, Course, CourseResource, CourseEnrollment
- **assignments**: Assignment, Skill, Question, QuizQuestion, OutputGuessQuestion, CodingQuestion, AssignmentAttempt, QuizSubmission, OutputGuessSubmission, CodingSubmission
- **analysis**: GapAnalysisReport, SkillAnalysis

### Services
- **assignments**: `SubmissionService` (start, quiz/output/code submit, finalize_attempt), `ScoringService`
- **analysis**: `InferenceEngine.analyze_attempt`

### APIs (django-ninja)
| Endpoint | Auth | Purpose |
|----------|------|---------|
| `GET /api/assignments/list` | Yes | List assignments |
| `GET /api/assignments/attempts` | Yes | List user's attempts |
| `GET /api/assignments/skills` | Yes | List skills |
| `POST /api/assignments/start` | Yes | Start assignment |
| `POST /api/assignments/quiz/submit` | Yes | Quiz submission |
| `POST /api/assignments/output/submit` | Yes | Output guess submission |
| `POST /api/assignments/code/submit` | Yes | Coding submission |
| `GET /api/assignments/{id}/summary` | Yes | Get/finalize attempt summary |
| `GET /api/analysis/reports` | Yes | List user's gap reports |
| `POST /api/analysis/generate/{attempt_id}` | Yes | Generate report for attempt |
| `GET /api/analysis/report/{attempt_id}` | Yes | Get report by attempt |
| `GET /api/users/profile` | Yes | Current user profile |

---

## Task 2 — Frontend Audit

### Pages
- **Landing / Login**: `landing.html`, `login.html`, `account/login.html`, `account/signup.html`
- **Dashboard**: `dashboard.html` — now loads real scores + report via API
- **Profile**: `profile.html` — now loads profile + skills via API
- **Intelligence**: `intelligence.html` — now loads reports + attempt scores via API
- **Assignments**: `assignments/start.html`, `quiz.html`, `output_guess.html`, `coding.html`, `summary.html` — use APIs for start/submit; start lists assignments from API
- **Analysis**: `analysis/report.html` — server-rendered report (view can trigger generate)

### API usage
- **Dashboard**: `GET /api/assignments/attempts`, `GET /api/analysis/reports`
- **Profile**: `GET /api/users/profile`, `GET /api/assignments/skills`
- **Intelligence**: `GET /api/analysis/reports`, `GET /api/assignments/attempts`
- **Start**: `GET /api/assignments/list`, `POST /api/assignments/start` (via `AssignmentAPI.start`)
- **Quiz/Output/Coding**: `AssignmentAPI.submitQuiz`, `submitOutput`, `submitCode` (same-origin, session auth)

---

## Task 3 — Feature Mapping

| Feature | Backend | API | Frontend | User Accessible |
|--------|---------|-----|----------|-----------------|
| View student profile | Yes | Yes `/users/profile` | Yes | Yes |
| Skill overview | Yes (Skill model) | Yes `/assignments/skills` | Yes (profile) | Yes |
| Start assignment | Yes | Yes | Yes (start page + list) | Yes |
| Quiz submission | Yes | Yes | Yes | Yes |
| Output guess submission | Yes | Yes | Yes | Yes |
| Coding submission | Yes | Yes | Yes | Yes |
| View assignment summary | Yes | Yes + view finalizes | Yes | Yes |
| Generate intelligence report | Yes | Yes | Yes (summary → report) | Yes |
| Display concept/logic/execution scores | Yes | Yes (attempts/summary) | Dashboard, Summary, Intelligence | Yes |
| Display AI insight / gaps | Yes | Yes (reports) | Dashboard, Intelligence, report.html | Yes |
| List assignments | Yes | Yes | Yes (start page) | Yes |
| List attempts | Yes | Yes | Yes (dashboard data) | Yes |

---

## Fixes applied (integration only)

1. **Backend**
   - Added read-only APIs: list assignments, list attempts, list skills, list reports, get profile.
   - Secured APIs: attempt/report access restricted to owner; assignment views `@login_required`; attempt ownership checks on submit/summary.

2. **Assignment flow**
   - Pass parent `question_id` (Question.id) in quiz, output_guess, and coding views/templates so submissions use correct ID.
   - Summary view calls `SubmissionService.finalize_attempt` before render so scores are correct.

3. **Frontend**
   - Dashboard: fetch `/api/assignments/attempts` and `/api/analysis/reports`; show latest attempt scores and latest report insight; loading/empty handled.
   - Intelligence: fetch reports + attempts; show latest report (recommendation, gaps) and strength labels from latest attempt; list of report links when multiple.
   - Profile: fetch `/api/users/profile` and `/api/assignments/skills`; show name, email, skills overview, bio.
   - Start: fetch `/api/assignments/list`; show assignment list or single “Start” button; no hardcoded assignment ID.

4. **Auth**
   - All assignment and analysis views require login; attempt/report ownership enforced in API and views.

---

## Flow verification

- **Login** → allauth (existing).
- **Dashboard** → shows real latest attempt scores and AI insight from latest report (or empty state).
- **Profile** → shows real profile and skills from API.
- **Assignment** → Start lists assignments → Start → Quiz → Output Guess → Coding → Summary (scores finalized) → “Generate Intelligence Report” → report page.
- **Intelligence** → shows latest report + gaps and list of report links.

No backend algorithms, scoring, or schema were changed; only exposure and wiring.

# Medical Transportation Network Recovery Optimizer — Project Handoff

**Snapshot inspected:** `optimizer.zip`, uploaded October 16, 2026.  
**Companion source archive:** `optimizer_source_only.zip` (a direct copy of the project-authored files; excludes `node_modules`, `.venv`, caches).  
**Purpose:** A reliable technical reference for future coding, debugging, handoffs, and a 36-hour hackathon. This document reports what exists *in this exact source snapshot*, not what has been validated in production.

## 1. Project in one paragraph

This is a **synthetic, scenario-based medical transportation recovery prototype** aimed particularly at trips to dialysis facilities. It generates patients, drivers/vehicles, locations, appointments, and estimated travel times; checks accessibility, eligibility, availability, and deadlines; globally assigns patients to available transportation resources; and responds to disruptions by rerunning the assignment optimizer. A Python FastAPI backend provides scenario-generation and optimization endpoints. A React/Vite/Leaflet dashboard displays assignments, routes, explanations for failure, and the effects of a simulated vehicle breakdown. The solver uses Google OR-Tools **CP-SAT**, not SciPy SLSQP. It currently permits **at most two sequential patient trips per vehicle**.

## 2. Source tree and ownership

```text
backend/
  main.py                   FastAPI application, API request schemas and endpoints
  __init__.py
optimization/
  schemas.py                Pydantic patient, vehicle, event and assignment schemas
  scenario_generator.py     Synthetic Boston / NYC network and travel-time generation
  facility_schedules.py    Facility appointment window generation
  travel.py                Trip/transition arrival-time calculations
  eligibility.py           Compatibility, first-trip and sequential feasibility matrices
  costs.py                 Initial and follow-on trip cost matrices
  solver.py                CP-SAT assignment and two-trip routing formulation
  state.py                 Reassignment state and onboard locks
  events.py                Disruption transformations
  recovery.py              Integration of feasibility, costs, state and solver
  reasons.py               Reasons why a vehicle can't serve a given patient
  metrics.py               Basic assignment/service-rate and score calculations
  baseline.py              Greedy first-trip-only baseline
  scenarios.py             Historical standalone testing/demo script; outdated
  data/
    boston_land.geojson    Land polygons for synthetic point generation
    nyc_land.geojson       Land polygons for synthetic point generation
frontend/
  src/App.jsx              React controls, API requests, disruption workflow and panels
  src/NetworkMap.jsx       React-Leaflet network map, markers, paths, analysis
  src/App.css              Dashboard styling
  src/index.css            Global styling
  src/main.jsx             React mount
  package.json             React, Leaflet, Vite and frontend tooling
  package-lock.json
  vite.config.js
  index.html
  public/...
  src/assets/...
```

The original ZIP also contains `.venv`, `frontend/node_modules`, and compiled Python files. They are **generated dependencies**, not the source of truth, and are excluded from the source-only archive. No top-level `requirements.txt` or Python packaging file was present.

## 3. End-to-end application behavior

1. The user selects a **region** (`BOSTON` or `NYC`), mode (`NORMAL`, `STRESSED`, `CRISIS`), number of patients/resources, and random seed in `frontend/src/App.jsx`. The defaults there are **Boston, Normal, 30 patients, 40 resources, seed 67**.
2. The frontend POSTs to **`/generate-scenario`**. The backend calls `optimization.scenario_generator.generate_scenario` and returns requests, resources, time matrices, dialysis centers, current time, and a summary.
3. The frontend POSTs those generated objects to **`/optimize`**, with empty prior assignments and events.
4. `backend/main.py` optionally applies network events via `optimization.events.apply_event`, then invokes `optimization.recovery.reoptimize_network`.
5. Recovery derives assignment locks; builds direct and sequential feasibility/cost matrices; calls the OR-Tools solver; and returns assignments, ordered per-resource routes, unserved requests, feasibility, and failure explanations.
6. The backend adds basic metrics. The React dashboard renders service-rate cards, a map, assignment details and escalation/failure explanation views.
7. In the main frontend demo, selecting an assigned patient and clicking **Simulate Vehicle Breakdown** marks the assigned vehicle unavailable, sends an event and prior `CONFIRMED` assignments to `/optimize`, then highlights assignments and changes in the map.

**Important:** This is simulated operational recovery; there is no evidence in this snapshot of live dispatch, real patient records, external transportation booking, a database, or a working mobile app. Although dashboard copy says “real-time,” scenario timestamps are synthetic and currently fixed for the demo.

## 4. API contract

### `GET /`
Returns an `ok` status and service identifier.

### `POST /generate-scenario`
JSON request keys:

```json
{
  "region": "BOSTON",
  "num_patients": 30,
  "num_resources": 40,
  "seed": 67,
  "scenario_mode": "NORMAL"
}
```

Returns `region`, `scenario_mode`, `seed`, `current_time`, `requests`, `resources`, `dialysis_centers`, `pickup_travel_times`, `patient_trip_times`, `transition_travel_times`, and `summary`.

### `POST /optimize`
Inputs:

- `requests`: list of `TransportRequest` (including appointment, target, and latest-arrival timestamps).
- `resources`: list of `TransportResource`.
- `current_time`: a scenario timestamp.
- `pickup_travel_times[request_id][resource_id]`: minutes to reach pickup from the resource's starting location.
- `patient_trip_times[request_id]`: patient pickup to destination minutes.
- `transition_travel_times[first_request_id][next_request_id]`: first patient's destination to next patient's pickup, in minutes. **Required for practical sequential routing**, despite defaulting to an empty dictionary in the API schema.
- Optional `current_assignment_states`, `events`, and `reassignment_penalty` (default `30`).

Response keys: `events_applied`, `assignments` (request ID → resource ID), `resource_routes` (resource ID → ordered one- or two-request list), `unserved_requests`, `metrics`, `feasibility_matrix`, `infeasibility_reasons`.

**Entrypoint:** from the repository root, with compatible Python dependencies installed, `uvicorn backend.main:app --reload`. The frontend uses hard-coded `http://127.0.0.1:8000` endpoints and permits local frontend origins on port 5173. Frontend startup is usually `cd frontend && npm ci && npm run dev`. These are **instructions inferred from the implementation**, not a verified end-to-end startup in this environment.

## 5. Data model and rules

### `TransportRequest`

Fields: `request_id`, `patient_id`, `patient_name`, `pickup_lat`, `pickup_lon`, `destination_lat`, `destination_lon`, `appointment_time`, `target_arrival`, `latest_arrival`, `rideshare_allowed`, `uses_wheelchair`, `wheelchair_folds`, `requires_wav`, `can_transfer`, and `transfer_assistance_required`.

### `TransportResource`

Fields: `resource_id`, `resource_type`, current coordinates, `available`, optional `available_from`, `wav_capable`, `folding_wheelchair_storage`, `transfer_assistance_capable`, approved patient IDs, and declined request IDs.

### Compatibility (`optimization/eligibility.py`)

Reject when a resource is unavailable, has declined the request, is rideshare without consent, is a caregiver not approved for this patient, lacks required wheelchair-accessible-vehicle capability, lacks folding wheelchair storage when needed, or lacks transfer assistance when needed. Time feasibility also checks arrival no later than `latest_arrival`.

### Timing (`optimization/travel.py`)

First-trip arrival = `max(current_time, resource.available_from if set)` + pickup minutes + patient trip minutes. Follow-on arrival = first patient's predicted dropoff + travel to the next pickup + next patient trip minutes. Each trip must meet its `latest_arrival` threshold. `target_arrival` is used to calculate lateness cost rather than a hard limit. The `can_transfer` attribute is present in the schema but is **not enforced in `eligibility.is_compatible`**.

### Synthetic scenarios (`optimization/scenario_generator.py`)

- Regions: **Boston** and **NYC**; land polygons help place synthetic coordinates on land.
- Boston uses a list of named dialysis centers in the scenario code; NYC uses explicitly synthetic centers. These names/locations are reference/demo data, not an active integration with the facilities.
- Normal → Stressed → Crisis adjusts patient need, WAV scarcity, resource availability, rideshare consent rates, and timing slack.
- Travel times are **estimated synthetically from approximate distances and random variation**; they are not live road-navigation or traffic API travel times.
- The generator fixes the scenario's starting timestamp to **October 16, 2026 at 1:00 PM**. Changing the real wall clock does not change that timestamp.

## 6. The optimization model — exact conceptual formulation

**Solver:** `optimization/solver.py`, `optimize_assignments`, OR-Tools `cp_model.CpModel()`/`CpSolver()`.

Binary decisions:

- `start[p, r]` = resource `r` serves patient/request `p` **first**.
- `follow[p, q, r]` = resource `r` serves `q` **immediately after** serving `p`.
- `unserved[p]` = request `p` is not served.

Constraints:

1. A first trip is forbidden if its direct feasibility matrix value is zero.
2. A follow-on trip is forbidden if its sequential feasibility matrix value is zero.
3. A follow-on trip requires `start[first_patient, same_resource] = 1`.
4. Every request must be **exactly one** of: first trip, second trip, or unserved.
5. Every resource starts **at most one** route.
6. Every resource has **at most one** follow-on patient. Maximum route length = **two** patient trips.
7. A patient who was previously assigned to a still directly feasible resource cannot become unserved, subject to the exact formulation.
8. `PASSENGER_ONBOARD` patients are assigned a fixed resource (see caveats below).

Objective minimized:

```text
sum(first_trip_cost[p,r] * start[p,r])
+ sum(follow_on_cost[p,q,r] * follow[p,q,r])
+ 30 * number_of_reassignments   [configurable coefficient]
+ 10000 * number_of_unserved_requests  [solver default coefficient]
```

Costs include trip travel minutes plus **10 × positive minutes after `target_arrival`**. Follow-on costs include travel from the first destination through the next destination. This is a **weighted operational score**, not a demonstrated dollar cost.

**Distinguish metrics:** `optimization/metrics.py` calculates a post-hoc `total_score`, but its formula does **not** match this complete CP-SAT objective for two-trip routes (see issues). Do not claim that displayed `total_score` is the exact solver objective.

### State and disruptions

Assignment states: `FLEXIBLE`, `CONFIRMED`, `EN_ROUTE_TO_PICKUP`, `PASSENGER_ONBOARD`, `COMPLETED`.

`optimization/state.py` excludes `COMPLETED` from current assignments; it locks `PASSENGER_ONBOARD` to their existing resource. `optimization/events.py` supports:

- `TRAFFIC_DELAY`: adds minutes to a specified request/resource pickup estimate.
- `DRIVER_DECLINED`: records that resource's refusal of one request.
- `RESOURCE_UNAVAILABLE`: marks a resource unavailable.
- `VEHICLE_BREAKDOWN`: likewise marks a resource unavailable.
- `RESOURCE_AVAILABLE`: marks it available again.

`optimization/recovery.py` reruns the optimization after applying state changes. The main UI currently exposes a vehicle-breakdown demonstration rather than separate controls for every available event type.

## 7. Frontend and demonstrable UX

Built with **React 19, Vite 8, React-Leaflet 5, and Leaflet 1.9** (from the supplied `package.json`). Main UI:

- network generator settings for region, mode, patients, resources, and seed;
- generation and automatic optimization flow;
- assigned/total, service rate, and unserved cards;
- selection of an assigned patient/ride to trigger a vehicle breakdown;
- before/after recovery details and revised assignments;
- interactive map with patient/resource/facility markers and colored assignment paths;
- route order for sequential two-patient trips;
- infeasibility explanations and an escalation panel.

**Map paths are straight Leaflet polylines between resource, pickup, and destination coordinates**, not verified street-level routing. OpenStreetMap tiles are requested externally, so map tiles need connectivity.

There is no separate patient-facing mobile app in the supplied source. The UI includes a hard-coded older three-patient `recoveryPayload`/sample data section; the main scenario generation pipeline is a separate workflow.

## 8. Verification actually performed on this snapshot

**Passed:**

- Inspected the ZIP manifest, separated 35 project files from bundled third-party dependencies and caches.
- `python -m compileall -q` on backend and optimization source completed without Python syntax errors.
- Successfully invoked `generate_scenario`, `build_operational_feasibility_matrix`, and `build_assignment_costs` for three six-patient/eight-resource combinations:
  - Boston / Normal: 29 feasible first-trip patient-resource pairs;
  - Boston / Stressed: 27 feasible pairs;
  - NYC / Crisis: 10 feasible pairs.
- Parsed `frontend/src/App.jsx` and `frontend/src/NetworkMap.jsx` with the Babel JSX parser without syntax errors.

**Not verified:**

- An end-to-end OR-Tools solution; `ortools` is not installed in the verification environment.
- A successful Vite production build. The supplied node dependencies contain native dependencies from a different platform; an attempted build failed at missing platform-specific `rolldown` native binding, not at a reported source-code syntax error.
- Browser rendering, integration, actual solver outputs for the default 30×40 scenario, run times, deterministic numerical correctness, or judge-ready demo quality.

## 9. Priority issues discovered from code inspection

| Priority | File(s) | Problem | Why it matters |
|---|---|---|---|
| P0 | `optimization/scenarios.py` | Historical script uses `TransportRequest` without current required `appointment_time`; several calls unpack `optimize_assignments` into 2 return values even though it now returns 3. | **Do not use this script as the regression test or demo runner without updating it.** |
| P0 | `optimization/metrics.py` | Metric calculation sums direct-trip costs for every assignment, including the second patient, while the solver prices second patients using `sequential_assignment_costs`; also omits reassignment penalties. | Any “total optimization cost” or comparison can misrepresent the actual optimized objective. The **service count/rate** calculation is comparatively straightforward. |
| P0 | `optimization/solver.py` | If `CpSolver` returns neither `FEASIBLE` nor `OPTIMAL`, extraction currently returns empty assignments, empty unserved list, and empty routes; no solver status is surfaced. | An infeasible model can appear as a zero-assignment/zero-unserved network. Return explicit solver status and handle failure. |
| P1 | `optimization/solver.py`, `optimization/state.py` | The onboard lock keeps a request on its resource but treats it as an ordinary first/second decision; if that resource becomes unavailable, the full model may be infeasible. | Real onboard trips need preserved in-progress state and special disruption handling, not a generic reallocation. |
| P1 | `optimization/recovery.py` | Defaults `transition_travel_times` to `{}`, but sequential feasibility/cost creation directly indexes `transition_travel_times[first][second]` for multiple requests. | Calling `/optimize` with multiple requests but omitted transitions may raise a `KeyError`. Validate matrices or explicitly disable follow-on trips when no transition data exist. |
| P1 | `backend/main.py` / frontend | Frontend API URL is hard-coded to localhost; no deployment configuration or environment-based API URL is present. | A hosted demo cannot call `127.0.0.1` on judges' computers. Configure `VITE_API_BASE_URL` / backend origins before deployment. |
| P1 | Entire repo | No captured Python dependency manifest, automated tests, CI, or controlled environment setup visible. | A cold startup/deployment is fragile. Add a known-good installation/run procedure and tests. |
| P1 | `optimization/travel.py`, `scenario_generator.py` | Travel-time estimates are synthetic; dates are fixed in generated examples. | Describe as a simulation or decision-support prototype; do not imply real-time clinical dispatch or live navigation. |
| P2 | `optimization/schemas.py`, `eligibility.py` | `can_transfer` exists but is not used in compatibility. Some clinical/transit rules are simplified. | No claim of complete patient-handling safety or regulatory/commercial readiness. |
| P2 | `frontend/src/NetworkMap.jsx` | Displays straight segments, not turn-by-turn driving routes. | Be transparent in demo and judging presentation. |
| P2 | `optimization/baseline.py` | Greedy comparator only assigns one patient per resource, while CP-SAT can assign two sequential patients. | Raw service-rate improvement against this baseline may partly reflect extra capacity rather than global optimization alone; make comparisons fair. |

**Note:** These are code-inspection findings, not claims that every scenario triggers each issue.

## 10. Best 36-hour hackathon path for a three-person team

**Subject to the hackathon's rules on using pre-existing code:**

**MVP scope**: One coherent story — generate a patient/vehicle network → display baseline assignments → cause one vehicle breakdown → show which patients are affected → find alternative legal assignments → explain why other options cannot work. Use Boston and a fixed, tested seed for the final demonstration. Preserve the strongest existing dashboard/optimizer/backend flows. Do **not** try to build a second mobile application unless the core demo is already finished.

**Recommended division of labor:**

1. **Optimization/backend lead:** resolve solver-status/metric issues, test disruption safety and frozen onboard assignments, validate selected sample data, own core algorithm explanations.
2. **Frontend/map lead:** make the before/after narrative and failed-ride recovery clear, ensure visible loading/errors, improve accessibility, implement a reliable demo preset.
3. **Integration/testing/pitch lead:** write automated API tests and deployment scripts, verify cross-browser live demo, prepare demo cases and a short judge presentation.

**Sequencing:** Establish one deterministic end-to-end passing run before adding features; fix broken paths; create a polished before/after visual; deploy or prepare local/demo-video fallback; rehearse a 90–180 second explanation.

**Compliance:** AI-allowed does **not** necessarily equal pre-event-code-allowed. Check the hackathon's rules/organizers about the uploaded codebase, and distinguish clearly between pre-existing components and work completed during the event. Do not manipulate Git history to hide origin.

## 11. Next-step checklist

- [ ] Confirm competition rules for pre-existing code and AI.
- [ ] Make a repeatable Python environment (`requirements.txt` or `pyproject.toml`) with tested Python/OR-Tools/Shapely/FastAPI/Pydantic versions.
- [ ] Reinstall dependencies for the host platform; don't copy the zipped `.venv` or `node_modules` to another OS.
- [ ] Add an end-to-end test for `POST /generate-scenario` followed by `POST /optimize` with a small deterministic seed.
- [ ] Record actual solver status, selected objective, run time, routes and assignments.
- [ ] Add explicit verification of request uniqueness, all-one-of service invariant, no repeated first trip, vehicle type/consent/time compatibility, sequential route order and second-trip arrival deadlines.
- [ ] Correct `metrics.py` for the actual solver objective, including follow-on route costs and reassignment costs.
- [ ] Fix or archive `optimization/scenarios.py`.
- [ ] Validate missing matrices and contradictory locked/current-resource states.
- [ ] Ensure a default, reproducible example: saved seed + expected service count + a predictable failure/recovery outcome.
- [ ] Make the backend URL configurable and test deployment.
- [ ] Rehearse the map's explanation of direct vs sequential routes and why certain assignments are infeasible.

## 12. Rules for using this handoff in future ChatGPT conversations

1. Upload **both** `optimizer_source_only.zip` and this document to the new conversation (or provide access to their saved originals). This keeps the implementation verifiable; a summary alone cannot reproduce exact functions.
2. Tell the assistant: *“Use this exact ZIP as the source of truth. Read `OPTIMIZER_PROJECT_HANDOFF.md` first, then inspect relevant source files before editing.”*
3. After major changes, upload the **new source snapshot** and request an updated document; old snapshots are not automatically synchronized with edited local files.
4. For precise code changes, request **file-by-file diffs, tests, and actual solver output**, rather than assuming the assistant automatically remembers all lines from previous chats.
5. Do not assume ChatGPT Memory stores the complete source. This handoff saves the **architecture and current state**; the ZIP preserves the precise files.

---

### Snapshot source hashes (SHA-256, first 16 hexadecimal characters)

```text
backend/main.py                         8265cd863cb14cda
optimization/solver.py                  99b6ad3342a3f0e6
optimization/scenario_generator.py      7c26e9b4a11df41b
frontend/src/App.jsx                    3d44bdc9d9a07c9a
frontend/src/NetworkMap.jsx             46e6be02ee5bb9fc
```

**Bottom line:** The technical core, API and dashboard **exist**. The remaining gap is confidence in *correctness, reporting, reproducibility and the final demo*, not an absence of a project. This document and the archived source together provide a much more reliable basis for continuing than memory alone.

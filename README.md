# Medical Transportation Network Recovery Optimizer

A simulated medical transportation dispatch and recovery system. It assigns patients to eligible vehicles using network-wide constrained optimization, then recalculates assignments when a vehicle becomes unavailable or another disruption occurs.

The project consists of a Python **OR-Tools CP-SAT** optimizer, a **FastAPI** backend, and a **React/Vite** operations dashboard.

## What it does

- Generates synthetic Boston or New York City patient, vehicle, and dialysis-facility networks in Normal, Stressed, and Crisis modes.
- Assigns patients subject to vehicle availability, wheelchair access, transfer assistance, patient consent, caregiver approval, and arrival deadlines.
- Supports up to **two sequential patient trips per vehicle**.
- Reoptimizes assignments following disruptions such as vehicle breakdowns, driver declines, and travel-time delays.
- Shows assignments, unserved patients, route order, and recovery results on an interactive map.

## Requirements

Install these before starting:

- **Git** — to clone this private repository (or use GitHub's **Code → Download ZIP**).
- **Python 3.10** — the version used by the original development environment. The pinned dependencies have not been verified here with other Python versions.
- **Node.js 22.13 or newer (22.x), or Node.js 24.x** — required by the frontend tooling. Includes npm.

Check your installations:

```bash
git --version
python --version
node --version
npm --version
```

On Windows, `py -3.10 --version` can check Python 3.10 specifically. On macOS/Linux, use `python3 --version` if `python` is not recognized.

## 1. Get the code

Clone the repository (GitHub may ask you to authenticate because it is private):

```bash
git clone https://github.com/jackfusheridan19281/medical-transport-optimizer.git
cd medical-transport-optimizer
```

Alternatively, download the repository ZIP from GitHub, extract it, and open a terminal **inside the extracted repository folder**.

The repository root should contain `backend/`, `frontend/`, `optimization/`, and `requirements.txt`.

## 2. Start the Python backend

Open a terminal **at the repository root**. Use the instructions for your operating system.

### Windows PowerShell

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn backend.main:app --reload
```

If PowerShell prevents activation, you can skip activation and run the virtual environment directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn backend.main:app --reload
```

**Leave this terminal running.** The API should be at:

- Health check: <http://127.0.0.1:8000/>
- Interactive API documentation: <http://127.0.0.1:8000/docs>

The health check should return JSON with `"status": "ok"`. This verifies that the API started, **not** that the optimizer has completed a solve.

## 3. Start the React dashboard

Open a **second terminal** at the repository root (keep the backend running):

```bash
cd frontend
npm ci
npm run dev
```

Open the URL printed by Vite, normally <http://localhost:5173/>.

**Important:** The frontend currently calls the backend at `http://127.0.0.1:8000`. Both servers must run on the **same computer** for the current local setup. Port **5173** must be available; if Vite switches to another port, the backend's current CORS configuration may reject requests.

## 4. Try the optimizer

1. In the dashboard, choose a region, scenario mode, patient count, and resource count.
2. Click **Generate Network**. The dashboard calls `/generate-scenario`, then `/optimize`.
3. Check that the network, assignments, and service statistics appear.
4. Select an assigned patient and use **Simulate Vehicle Breakdown** to see the recovery workflow.

If the API health check works but optimization fails, check the backend terminal for the error. A successful health check alone does not verify the solver.

## Repository layout

```text
backend/
  main.py                    FastAPI routes: /, /generate-scenario, /optimize
optimization/
  solver.py                  OR-Tools CP-SAT assignment and two-trip model
  eligibility.py             Compatibility and timing constraints
  costs.py                   Direct and sequential assignment costs
  recovery.py                Reoptimization workflow
  events.py                  Disruption handling
  scenario_generator.py      Synthetic network generation
  schemas.py                 Pydantic request/resource models
  metrics.py                 Solution summary metrics
  baseline.py                Greedy baseline comparator
  data/                      Boston and NYC geographic reference data
  ...                        Other scheduling, travel, and state modules
frontend/
  src/App.jsx                Dashboard and API calls
  src/NetworkMap.jsx         Interactive Leaflet map
  package.json               Frontend dependencies and scripts
  package-lock.json          Locked frontend dependency versions
requirements.txt             Pinned direct Python dependencies
README.md                    Setup and project overview
```

## API

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/` | Basic API health check |
| POST | `/generate-scenario` | Generate a synthetic network |
| POST | `/optimize` | Optimize assignments and apply recovery events |

For request/response schemas, use <http://127.0.0.1:8000/docs> while the backend is running.

## Troubleshooting

- **`No module named 'ortools'` or `No module named 'fastapi'`:** Install with `python -m pip install -r requirements.txt` in the same environment used to start Uvicorn.
- **`No module named 'optimization'`:** Start the backend **from the repository root**, not from inside `backend/`.
- **PowerShell says scripts are disabled:** Use the direct `.venv\Scripts\python.exe` commands above; no execution-policy change is necessary.
- **`npm ci` fails:** Confirm Node.js and npm versions, run the command inside `frontend/`, and keep the committed `package-lock.json`.
- **Dashboard shows a network/API error:** Make sure the backend is still running at `127.0.0.1:8000` and Vite is serving on port 5173.
- **Port already in use:** Stop the conflicting process before starting the backend or frontend. Changing ports also requires updating the hard-coded frontend API address and/or backend CORS settings.

## Current limitations

This is a **synthetic decision-support prototype**, not a live medical dispatch system. Travel times are estimated rather than obtained from a live routing service, and map lines are not street-level routes. The current optimizer limits each vehicle to two sequential trips. The reporting metrics and some disruption edge cases still need additional validation.

The versions in `requirements.txt` were taken from the original Python 3.10 development environment. **A fresh cross-platform install and full end-to-end optimization run have not yet been verified.**

from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from optimization.scenario_generator import generate_scenario

from optimization.schemas import (
    TransportRequest,
    TransportResource,
    CurrentAssignment,
    NetworkEvent,
)

from optimization.events import apply_event
from optimization.recovery import reoptimize_network
from optimization.metrics import calculate_solution_metrics


app = FastAPI(
    title="Medical Transportation Recovery API",
    version="0.2.0",
)



# CORS


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# REQUEST BODY


class RecoveryRequest(BaseModel):
    requests: list[TransportRequest]

    resources: list[TransportResource]

    current_time: datetime

    pickup_travel_times: dict[str, dict[str, int]]

    patient_trip_times: dict[str, int]

    transition_travel_times: dict[str, dict[str, int]] = Field(
    default_factory=dict
    )

    current_assignment_states: list[CurrentAssignment] = Field(
        default_factory=list
    )

    events: list[NetworkEvent] = Field(
        default_factory=list
    )

    reassignment_penalty: int = 30

class ScenarioGenerationRequest(BaseModel):
    region: str = "BOSTON"
    num_patients: int = 12
    num_resources: int = 16
    seed: int = 42
    scenario_mode: str = "NORMAL"


# HEALTH CHECK


@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "medical-transport-recovery",
    }


# GENERATE SYNTHETIC TRANSPORTATION NETWORK


@app.post("/generate-scenario")
def generate_network(
    payload: ScenarioGenerationRequest,
):

    scenario = generate_scenario(
        region=payload.region,
        num_patients=payload.num_patients,
        num_resources=payload.num_resources,
        seed=payload.seed,
        scenario_mode=payload.scenario_mode,
    )

    return {
        "region": scenario["region"],
        "scenario_mode": scenario["scenario_mode"],
        "seed": scenario["seed"],   
        "current_time": scenario["current_time"],

        "requests": [
            request.model_dump()
            for request in scenario["requests"]
        ],

        "resources": [
            resource.model_dump()
            for resource in scenario["resources"]
        ],

        "dialysis_centers": scenario["dialysis_centers"],

        "pickup_travel_times": scenario[
            "pickup_travel_times"
        ],

        "patient_trip_times": scenario[
            "patient_trip_times"
        ],

        "transition_travel_times": scenario[
            "transition_travel_times"
        ],

        "summary": {
            "num_patients": len(
                scenario["requests"]
            ),
            "num_resources": len(
                scenario["resources"]
            ),
        },
    }


# OPTIMIZATION ENDPOINT


@app.post("/optimize")
def optimize_recovery(
    payload: RecoveryRequest,
):
    updated_resources = payload.resources
    updated_pickup_travel_times = payload.pickup_travel_times


    # Apply real-world events first


    for event in payload.events:
        (
            updated_resources,
            updated_pickup_travel_times,
        ) = apply_event(
            event=event,
            resources=updated_resources,
            pickup_travel_times=updated_pickup_travel_times,
        )


    # Reoptimize after events change network state


    result = reoptimize_network(
        requests=payload.requests,
        resources=updated_resources,
        current_time=payload.current_time,
        pickup_travel_times=updated_pickup_travel_times,
        patient_trip_times=payload.patient_trip_times,
        transition_travel_times=payload.transition_travel_times,
        current_assignment_states=payload.current_assignment_states,
        reassignment_penalty=payload.reassignment_penalty,
    )

    metrics = calculate_solution_metrics(
        requests=payload.requests,
        assignments=result["assignments"],
        unserved_requests=result["unserved_requests"],
        assignment_costs=result["assignment_costs"],
    )

    return {
        "events_applied": [
            event.event_type.value
            for event in payload.events
        ],
        "assignments": result["assignments"],
        "resource_routes": result["resource_routes"],
        "unserved_requests": result["unserved_requests"],
        "metrics": metrics,
        "feasibility_matrix": result["feasibility_matrix"],
        "infeasibility_reasons": result[
            "infeasibility_reasons"
        ],
    }
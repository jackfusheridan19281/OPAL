from datetime import datetime

from optimization.metrics import calculate_solution_metrics
from optimization.baseline import greedy_assignments
from optimization.schemas import NetworkEvent, EventType
from optimization.events import apply_event
from optimization.recovery import reoptimize_network
from optimization.travel import calculate_estimated_arrival
from optimization.costs import build_assignment_costs
from optimization.solver import optimize_assignments
from optimization.state import derive_solver_state
from optimization.schemas import (
    TransportRequest,
    TransportResource,
    CurrentAssignment,
    AssignmentStatus,
)

from optimization.eligibility import (
    is_compatible,
    get_feasible_resources,
    build_feasibility_matrix,
    build_operational_feasibility_matrix,
)



# 1. DEFINE PATIENT REQUESTS


margaret = TransportRequest(
    request_id="REQ-001",
    patient_id="PATIENT-001",
    patient_name="Margaret",

    pickup_lat=42.9956,
    pickup_lon=-71.4548,
    destination_lat=43.2081,
    destination_lon=-71.5376,

    target_arrival=datetime(2026, 10, 16, 13, 45),
    latest_arrival=datetime(2026, 10, 16, 13, 55),

    rideshare_allowed=True,

    uses_wheelchair=True,
    wheelchair_folds=True,
    requires_wav=False,
    can_transfer=True,
    transfer_assistance_required=True,
)


john = TransportRequest(
    request_id="REQ-002",
    patient_id="PATIENT-002",
    patient_name="John",

    pickup_lat=43.0050,
    pickup_lon=-71.4500,
    destination_lat=43.2081,
    destination_lon=-71.5376,

    target_arrival=datetime(2026, 10, 16, 14, 5),
    latest_arrival=datetime(2026, 10, 16, 14, 20),

    rideshare_allowed=False,

    uses_wheelchair=False,
    wheelchair_folds=False,
    requires_wav=False,
    can_transfer=True,
    transfer_assistance_required=False,
)

sarah = TransportRequest(
    request_id="REQ-003",
    patient_id="PATIENT-003",
    patient_name="Sarah",

    pickup_lat=43.0500,
    pickup_lon=-71.5000,

    destination_lat=43.2081,
    destination_lon=-71.5376,

    target_arrival=datetime(
        2026, 10, 16, 14, 10
    ),

    latest_arrival=datetime(
        2026, 10, 16, 14, 20
    ),

    rideshare_allowed=False,

    uses_wheelchair=True,
    wheelchair_folds=False,
    requires_wav=True,

    can_transfer=False,
    transfer_assistance_required=True,
)


# 2. DEFINE TRANSPORTATION RESOURCES


uber_x = TransportResource(
    resource_id="UBER-X-01",
    resource_type="RIDESHARE",

    current_lat=43.0100,
    current_lon=-71.4600,

    available=True,

    wav_capable=False,
    folding_wheelchair_storage=True,
    transfer_assistance_capable=False,
)


uber_assist = TransportResource(
    resource_id="UBER-ASSIST-01",
    resource_type="RIDESHARE",

    current_lat=43.0200,
    current_lon=-71.4700,

    available=True,

    wav_capable=False,
    folding_wheelchair_storage=True,
    transfer_assistance_capable=True,
)


approved_caregiver = TransportResource(
    resource_id="CAREGIVER-01",
    resource_type="CAREGIVER",

    current_lat=43.0150,
    current_lon=-71.4650,

    available=True,

    wav_capable=False,
    folding_wheelchair_storage=True,
    transfer_assistance_capable=True,

    approved_patient_ids=["PATIENT-001"],
)


john_caregiver = TransportResource(
    resource_id="CAREGIVER-02",
    resource_type="CAREGIVER",

    current_lat=43.0120,
    current_lon=-71.4620,

    available=True,

    wav_capable=False,
    folding_wheelchair_storage=True,
    transfer_assistance_capable=True,

    approved_patient_ids=["PATIENT-002"],
)


nemt_wav = TransportResource(
    resource_id="NEMT-WAV-01",
    resource_type="NEMT",

    current_lat=43.0180,
    current_lon=-71.4680,

    available=True,

    wav_capable=True,
    folding_wheelchair_storage=True,
    transfer_assistance_capable=True,
)



# 3. CREATE NETWORK LISTS


all_resources = [
    uber_x,
    uber_assist,
    approved_caregiver,
    john_caregiver,
    nemt_wav,
]


all_requests = [
    margaret,
    john,
    sarah,
]



# 4. BASIC COMPATIBILITY TESTS


print("Individual compatibility checks:")

print("UberX:", is_compatible(margaret, uber_x))
print("Uber Assist:", is_compatible(margaret, uber_assist))
print("Approved Caregiver:", is_compatible(margaret, approved_caregiver))
print("John Caregiver:", is_compatible(margaret, john_caregiver))
print("NEMT WAV:", is_compatible(margaret, nemt_wav))



# 5. FIND MARGARET'S FEASIBLE RESOURCES


feasible_resources = get_feasible_resources(
    margaret,
    all_resources
)

print("\nFeasible resources for Margaret:")

for resource in feasible_resources:
    print(
        resource.resource_id,
        "-",
        resource.resource_type
    )



# 6. BUILD FEASIBILITY MATRIX


feasibility_matrix = build_feasibility_matrix(
    all_requests,
    all_resources
)


print("\nPatient x Resource Feasibility Matrix:\n")

for request in all_requests:

    print(request.patient_name)

    for resource in all_resources:

        feasible = feasibility_matrix[
            request.request_id
        ][
            resource.resource_id
        ]

        print(
            "  ",
            resource.resource_id,
            ":",
            feasible
        )

    print()



# 8. SIMULATED CURRENT TIME + TRAVEL TIMES


current_time = datetime(
    2026,
    10,
    16,
    13,
    10
)


# Minutes from each resource's current location
# to each patient's pickup location
pickup_travel_times = {
    "REQ-001": {
        "UBER-X-01": 8,
        "UBER-ASSIST-01": 12,
        "CAREGIVER-01": 15,
        "CAREGIVER-02": 10,
        "NEMT-WAV-01": 25,
    },

    "REQ-002": {
        "UBER-X-01": 7,
        "UBER-ASSIST-01": 11,
        "CAREGIVER-01": 14,
        "CAREGIVER-02": 9,
        "NEMT-WAV-01": 16,
    },

    "REQ-003": {
        "UBER-X-01": 10,
        "UBER-ASSIST-01": 12,
        "CAREGIVER-01": 14,
        "CAREGIVER-02": 15,
        "NEMT-WAV-01": 12,
    },
}


# Minutes from patient pickup location
# to dialysis facility
patient_trip_times = {
    "REQ-001": 25,
    "REQ-002": 30,
    "REQ-003": 30,
}

operational_feasibility_matrix = build_operational_feasibility_matrix(
    requests=all_requests,
    resources=all_resources,
    current_time=current_time,
    pickup_travel_times=pickup_travel_times,
    patient_trip_times=patient_trip_times,
)

assignment_costs = build_assignment_costs(
    current_time=current_time,
    requests=all_requests,
    resources=all_resources,
    pickup_travel_times=pickup_travel_times,
    patient_trip_times=patient_trip_times,
)

print("\nOperational Feasibility Matrix:\n")

for request in all_requests:

    print(request.patient_name)

    for resource in all_resources:

        feasible = operational_feasibility_matrix[
            request.request_id
        ][
            resource.resource_id
        ]

        print(
            "  ",
            resource.resource_id,
            ":",
            feasible
        )

    print()

print("\nCalculated Assignment Costs:\n")

for request in all_requests:

    print(request.patient_name)

    for resource in all_resources:

        if feasibility_matrix[
            request.request_id
        ][
            resource.resource_id
        ] == 1:

            print(
                "  ",
                resource.resource_id,
                "->",
                assignment_costs[
                    request.request_id
                ][
                    resource.resource_id
                ]
            )

    print()


# 9. RUN INITIAL OPTIMIZER


assignments, unserved_requests = optimize_assignments(
    all_requests,
    all_resources,
    operational_feasibility_matrix,
    assignment_costs,
)


print("\nOptimized Assignments:\n")

for request in all_requests:

    resource_id = assignments.get(
        request.request_id
    )

    print(
        request.patient_name,
        "->",
        resource_id
    )


print("\nUnserved Requests:")

if unserved_requests:

    for request_id in unserved_requests:
        print(request_id)

else:
    print("None")



# 10. CALCULATE ETAs FOR FEASIBLE ASSIGNMENTS


print("\nEstimated Arrival Times:\n")

for request in all_requests:

    print(request.patient_name)

    for resource in all_resources:

        feasible = feasibility_matrix[
            request.request_id
        ][
            resource.resource_id
        ]

        if feasible == 1:

            eta = calculate_estimated_arrival(
                current_time=current_time,
                request=request,
                resource=resource,
                pickup_travel_minutes=pickup_travel_times[
                    request.request_id
                ][
                    resource.resource_id
                ],
                patient_trip_minutes=patient_trip_times[
                    request.request_id
                ],
            )

            print(
                "  ",
                resource.resource_id,
                "->",
                eta.strftime("%I:%M %p")
            )

    print()



# 11. SHOW REUSABLE FEASIBILITY MATRIX


print("\nReusable Feasibility Matrix:\n")

for request_id, resource_options in feasibility_matrix.items():

    print(request_id)

    for resource_id, feasible in resource_options.items():

        print(
            "  ",
            resource_id,
            ":",
            feasible
        )

    print()



# 12. SIMULATE TRANSPORTATION FAILURE


print("\n--- SIMULATING TRAFFIC DELAY ---\n")

traffic_event = NetworkEvent(
    event_type=EventType.TRAFFIC_DELAY,
    occurred_at=current_time,
    request_id="REQ-001",
    resource_id="UBER-ASSIST-01",
    delay_minutes=12,
)


traffic_resources, traffic_pickup_travel_times = apply_event(
    event=traffic_event,
    resources=all_resources,
    pickup_travel_times=pickup_travel_times,
)


# Keep this temporary test condition so we can still test
# reassignment stability for John.
traffic_pickup_travel_times[
    "REQ-002"
][
    "NEMT-WAV-01"
] = 5

# Rebuild operational feasibility using the delayed travel time
traffic_feasibility_matrix = build_operational_feasibility_matrix(
    requests=all_requests,
    resources=all_resources,
    current_time=current_time,
    pickup_travel_times=traffic_pickup_travel_times,
    patient_trip_times=patient_trip_times,
)


# Recalculate costs because ETAs changed
traffic_assignment_costs = build_assignment_costs(
    current_time=current_time,
    requests=all_requests,
    resources=all_resources,
    pickup_travel_times=traffic_pickup_travel_times,
    patient_trip_times=patient_trip_times,
)


# GREEDY BASELINE


greedy_traffic_assignments, greedy_traffic_unserved = greedy_assignments(
    requests=all_requests,
    resources=traffic_resources,
    feasibility_matrix=traffic_feasibility_matrix,
    assignment_costs=traffic_assignment_costs,
)


print("\n--- GREEDY BASELINE VS GLOBAL OPTIMIZER ---\n")

print("Greedy sequential assignments:")

for request in all_requests:

    resource_id = greedy_traffic_assignments.get(
        request.request_id
    )

    if resource_id:
        print(
            request.patient_name,
            "->",
            resource_id
        )
    else:
        print(
            request.patient_name,
            "-> UNSERVED"
        )


print("\nGreedy unserved count:", len(greedy_traffic_unserved))

greedy_metrics = calculate_solution_metrics(
    requests=all_requests,
    assignments=greedy_traffic_assignments,
    unserved_requests=greedy_traffic_unserved,
    assignment_costs=traffic_assignment_costs,
)


# TEST 1: Reoptimize WITHOUT protecting existing assignments


traffic_assignments_no_stability, _ = optimize_assignments(
    all_requests,
    all_resources,
    traffic_feasibility_matrix,
    traffic_assignment_costs,
    current_assignments=assignments,
    reassignment_penalty=0,
)



# TEST 2: Reoptimize WITH reassignment/disruption protection


traffic_assignments, traffic_unserved = optimize_assignments(
    all_requests,
    all_resources,
    traffic_feasibility_matrix,
    traffic_assignment_costs,
    current_assignments=assignments,
    reassignment_penalty=30,
)



# TEST 3: Derive locking automatically from trip state


current_assignment_states = [
    CurrentAssignment(
        request_id="REQ-001",
        resource_id=assignments["REQ-001"],
        status=AssignmentStatus.CONFIRMED,
    ),

    CurrentAssignment(
        request_id="REQ-002",
        resource_id=assignments["REQ-002"],
        status=AssignmentStatus.PASSENGER_ONBOARD,
    ),
]


# INTEGRATED RECOVERY PIPELINE TEST


integrated_recovery_result = reoptimize_network(
    requests=all_requests,
    resources=traffic_resources,
    current_time=current_time,
    pickup_travel_times=traffic_pickup_travel_times,
    patient_trip_times=patient_trip_times,
    current_assignment_states=current_assignment_states,
    reassignment_penalty=30,
)

global_metrics = calculate_solution_metrics(
    requests=all_requests,
    assignments=integrated_recovery_result["assignments"],
    unserved_requests=integrated_recovery_result["unserved_requests"],
    assignment_costs=integrated_recovery_result["assignment_costs"],
)

print("\n--- INTEGRATED RECOVERY PIPELINE ---\n")

print("Assignments:")

for request in all_requests:

    resource_id = integrated_recovery_result[
        "assignments"
    ].get(
        request.request_id
    )

    if resource_id:
        print(
            request.patient_name,
            "->",
            resource_id
        )

    else:
        print(
            request.patient_name,
            "-> NO FEASIBLE RECOVERY"
        )


print("\nUnserved Requests:")

if integrated_recovery_result["unserved_requests"]:

    for request_id in integrated_recovery_result[
        "unserved_requests"
    ]:
        print(request_id)

else:
    print("None")

print("\n--- PERFORMANCE COMPARISON ---\n")

print("Greedy:")
print(
    "Served:",
    greedy_metrics["served_count"],
    "/",
    greedy_metrics["total_requests"]
)
print(
    "Unserved:",
    greedy_metrics["unserved_count"]
)
print(
    "Service rate:",
    f'{greedy_metrics["served_rate"]:.0%}'
)
print(
    "Total score:",
    greedy_metrics["total_score"]
)


print("\nGlobal Optimizer:")
print(
    "Served:",
    global_metrics["served_count"],
    "/",
    global_metrics["total_requests"]
)
print(
    "Unserved:",
    global_metrics["unserved_count"]
)
print(
    "Service rate:",
    f'{global_metrics["served_rate"]:.0%}'
)
print(
    "Total score:",
    global_metrics["total_score"]
)

print("\nWhy each option is or is not feasible for Margaret:")

margaret_reasons = integrated_recovery_result[
    "infeasibility_reasons"
][
    margaret.request_id
]

for resource in all_resources:

    reasons = margaret_reasons[
        resource.resource_id
    ]

    if reasons:
        print(
            resource.resource_id,
            "->",
            ", ".join(reasons)
        )

    else:
        print(
            resource.resource_id,
            "-> FEASIBLE"
        )

state_current_assignments, state_locked_request_ids = derive_solver_state(
    current_assignment_states
)


traffic_assignments_locked, _ = optimize_assignments(
    all_requests,
    all_resources,
    traffic_feasibility_matrix,
    traffic_assignment_costs,
    current_assignments=state_current_assignments,
    locked_request_ids=state_locked_request_ids,
    reassignment_penalty=0,
)



# PRINT THE THREE DIFFERENT BEHAVIORS


print("Without reassignment protection:")

for request in all_requests:
    print(
        request.patient_name,
        "->",
        traffic_assignments_no_stability.get(
            request.request_id
        )
    )


print("\nWith reassignment protection:")

for request in all_requests:
    print(
        request.patient_name,
        "->",
        traffic_assignments.get(
            request.request_id
        )
    )


print("\nWith John LOCKED because he is PASSENGER_ONBOARD:")

for request in all_requests:
    print(
        request.patient_name,
        "->",
        traffic_assignments_locked.get(
            request.request_id
        )
    )

print("\nTraffic-adjusted ETAs for Margaret:")

for resource in all_resources:

    if is_compatible(margaret, resource):

        eta = calculate_estimated_arrival(
            current_time=current_time,
            request=margaret,
            resource=resource,
            pickup_travel_minutes=traffic_pickup_travel_times[
                margaret.request_id
            ][
                resource.resource_id
            ],
            patient_trip_minutes=patient_trip_times[
                margaret.request_id
            ],
        )

        operationally_feasible = traffic_feasibility_matrix[
            margaret.request_id
        ][
            resource.resource_id
        ]

        print(
            resource.resource_id,
            "->",
            eta.strftime("%I:%M %p"),
            "| feasible:",
            operationally_feasible
        )

print("\n--- SIMULATING RECOVERY FAILURE ---\n")



# CREATE FAILURE EVENTS


failure_events = [
    NetworkEvent(
        event_type=EventType.DRIVER_DECLINED,
        occurred_at=current_time,
        request_id="REQ-001",
        resource_id="UBER-ASSIST-01",
),

    NetworkEvent(
        event_type=EventType.RESOURCE_UNAVAILABLE,
        occurred_at=current_time,
        resource_id="CAREGIVER-01",
    ),

    NetworkEvent(
        event_type=EventType.VEHICLE_BREAKDOWN,
        occurred_at=current_time,
        resource_id="NEMT-WAV-01",
    ),
]



# START FROM THE STATE AFTER THE TRAFFIC EVENT


failure_resources = traffic_resources
failure_pickup_travel_times = traffic_pickup_travel_times



# APPLY EACH FAILURE EVENT


for event in failure_events:

    failure_resources, failure_pickup_travel_times = apply_event(
        event=event,
        resources=failure_resources,
        pickup_travel_times=failure_pickup_travel_times,
    )



# REOPTIMIZE AFTER THE FAILURE EVENTS


failure_recovery_result = reoptimize_network(
    requests=all_requests,
    resources=failure_resources,
    current_time=current_time,
    pickup_travel_times=failure_pickup_travel_times,
    patient_trip_times=patient_trip_times,
    current_assignment_states=current_assignment_states,
    reassignment_penalty=30,
)



# PRINT FAILURE EVENTS


print("Events applied:")

for event in failure_events:
    print(
        event.event_type.value,
        "->",
        event.resource_id
    )



# PRINT RECOVERY RESULT


print("\nAssignments after transportation failures:\n")

for request in all_requests:

    resource_id = failure_recovery_result[
        "assignments"
    ].get(
        request.request_id
    )

    if resource_id:

        print(
            request.patient_name,
            "->",
            resource_id
        )

    else:

        print(
            request.patient_name,
            "-> NO FEASIBLE RECOVERY"
        )


print("\nUnserved Requests:")

if failure_recovery_result["unserved_requests"]:

    for request_id in failure_recovery_result[
        "unserved_requests"
    ]:
        print(request_id)

else:
    print("None")



# EXPLAIN WHY MARGARET HAS NO FEASIBLE RECOVERY


print("\nWhy Margaret has no feasible recovery:")

failure_reasons = failure_recovery_result[
    "infeasibility_reasons"
][
    margaret.request_id
]

for resource in failure_resources:

    reasons = failure_reasons[
        resource.resource_id
    ]

    if reasons:

        print(
            resource.resource_id,
            "->",
            ", ".join(reasons)
        )

    else:

        print(
            resource.resource_id,
            "-> FEASIBLE"
        )
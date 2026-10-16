from datetime import datetime

from optimization.schemas import (
    TransportRequest,
    TransportResource,
    CurrentAssignment,
)

from optimization.eligibility import (
    build_operational_feasibility_matrix,
    build_sequential_feasibility_matrix,
)

from optimization.costs import (
    build_assignment_costs,
    build_sequential_assignment_costs,
)

from optimization.state import (
    derive_solver_state,
)

from optimization.solver import (
    optimize_assignments,
)

from optimization.reasons import (
    build_infeasibility_reason_matrix,
)


def reoptimize_network(
    requests: list[TransportRequest],
    resources: list[TransportResource],
    current_time: datetime,
    pickup_travel_times: dict[str, dict[str, int]],
    patient_trip_times: dict[str, int],
    transition_travel_times: dict[str, dict[str, int]] | None = None,
    current_assignment_states: list[CurrentAssignment] | None = None,
    reassignment_penalty: int = 30,
):

    if transition_travel_times is None:
        transition_travel_times = {}

    
    # 1. Determine current assignment / locking state
    

    if current_assignment_states is None:
        current_assignments = {}
        locked_request_ids = set()

    else:
        (
            current_assignments,
            locked_request_ids,
        ) = derive_solver_state(
            current_assignment_states
        )


    
    # 2. Determine operational feasibility
    

    feasibility_matrix = build_operational_feasibility_matrix(
        requests=requests,
        resources=resources,
        current_time=current_time,
        pickup_travel_times=pickup_travel_times,
        patient_trip_times=patient_trip_times,
    )


    
    # 3. Build explanation / reason matrix
    

    infeasibility_reasons = build_infeasibility_reason_matrix(
        requests=requests,
        resources=resources,
        current_time=current_time,
        pickup_travel_times=pickup_travel_times,
        patient_trip_times=patient_trip_times,
    )

    
    # 4. Determine sequential trip feasibility
    #
    # first patient → next patient → resource
    

    sequential_feasibility_matrix = (
        build_sequential_feasibility_matrix(
            requests=requests,
            resources=resources,
            current_time=current_time,
            pickup_travel_times=pickup_travel_times,
            patient_trip_times=patient_trip_times,
            transition_travel_times=transition_travel_times,
        )
    )

    
    # 5. Calculate assignment costs
    

    assignment_costs = build_assignment_costs(
        current_time=current_time,
        requests=requests,
        resources=resources,
        pickup_travel_times=pickup_travel_times,
        patient_trip_times=patient_trip_times,
    )

    
    # 6. Calculate sequential assignment costs
    #
    # first patient → next patient → resource
    

    sequential_assignment_costs = (
        build_sequential_assignment_costs(
            current_time=current_time,
            requests=requests,
            resources=resources,
            pickup_travel_times=pickup_travel_times,
            patient_trip_times=patient_trip_times,
            transition_travel_times=transition_travel_times,
        )
    )

    
    # 7. Solve global transportation allocation
    

    assignments, unserved_requests, resource_routes = optimize_assignments(
        requests=requests,
        resources=resources,
        feasibility_matrix=feasibility_matrix,
        assignment_costs=assignment_costs,
        sequential_feasibility_matrix=sequential_feasibility_matrix,
        sequential_assignment_costs=sequential_assignment_costs,
        current_assignments=current_assignments,
        locked_request_ids=locked_request_ids,
        reassignment_penalty=reassignment_penalty,
    )


    
    # 8. Return complete recovery result
    

    return {
        "assignments": assignments,
        "resource_routes": resource_routes,
        "unserved_requests": unserved_requests,
        "feasibility_matrix": feasibility_matrix,
        "sequential_feasibility_matrix": sequential_feasibility_matrix,
        "infeasibility_reasons": infeasibility_reasons,
        "assignment_costs": assignment_costs,
        "sequential_assignment_costs": sequential_assignment_costs,
    }
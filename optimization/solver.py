from ortools.sat.python import cp_model

from optimization.schemas import (
    TransportRequest,
    TransportResource,
)


def optimize_assignments(
    requests: list[TransportRequest],
    resources: list[TransportResource],
    feasibility_matrix: dict[str, dict[str, int]],
    assignment_costs: dict[str, dict[str, int]],
    sequential_feasibility_matrix: (
        dict[str, dict[str, dict[str, int]]] | None
    ) = None,
    sequential_assignment_costs: (
        dict[str, dict[str, dict[str, int]]] | None
    ) = None,
    current_assignments: dict[str, str] | None = None,
    locked_request_ids: set[str] | None = None,
    reassignment_penalty: int = 30,
    unserved_penalty: int = 10000,
):

    model = cp_model.CpModel()

    if current_assignments is None:
        current_assignments = {}

    if locked_request_ids is None:
        locked_request_ids = set()

    if sequential_feasibility_matrix is None:
        sequential_feasibility_matrix = {}

    if sequential_assignment_costs is None:
        sequential_assignment_costs = {}


    
    # DECISION VARIABLES
    #
    # start[(patient, resource)]
    #
    #     Resource serves this patient FIRST.
    #
    #
    # follow[(first_patient, second_patient, resource)]
    #
    #     Resource serves second_patient immediately after
    #     first_patient.
    #
    #
    # unserved[patient]
    #
    #     Patient receives no transportation.
    

    start = {}
    follow = {}
    unserved = {}


    
    # 1. FIRST-TRIP VARIABLES
    

    for request in requests:

        request_id = request.request_id

        unserved[request_id] = model.new_bool_var(
            f"unserved_{request_id}"
        )

        for resource in resources:

            resource_id = resource.resource_id

            key = (
                request_id,
                resource_id,
            )

            start[key] = model.new_bool_var(
                f"start_{request_id}_{resource_id}"
            )

            # A patient can only be the first trip if the
            # resource can reach them directly from its
            # current starting position.
            if (
                feasibility_matrix[
                    request_id
                ][
                    resource_id
                ]
                == 0
            ):

                model.add(
                    start[key] == 0
                )


    
    # 2. SEQUENTIAL FOLLOW-ON VARIABLES
    

    for first_request in requests:

        first_id = first_request.request_id

        for next_request in requests:

            next_id = next_request.request_id

            if first_id == next_id:
                continue

            for resource in resources:

                resource_id = resource.resource_id

                key = (
                    first_id,
                    next_id,
                    resource_id,
                )

                follow[key] = model.new_bool_var(
                    f"follow_{first_id}_{next_id}_{resource_id}"
                )

                sequence_feasible = (
                    sequential_feasibility_matrix
                    .get(
                        first_id,
                        {}
                    )
                    .get(
                        next_id,
                        {}
                    )
                    .get(
                        resource_id,
                        0
                    )
                )

                # Physically impossible sequence
                if sequence_feasible == 0:

                    model.add(
                        follow[key] == 0
                    )

                # A second patient can only follow a first
                # patient that this same resource actually
                # serves first.
                model.add(
                    follow[key]
                    <= start[
                        (
                            first_id,
                            resource_id,
                        )
                    ]
                )


    
    # 3. EACH PATIENT IS SERVED EXACTLY ONCE OR UNSERVED
    #
    # A patient may be:
    #
    #   A. first/only patient on a resource
    #   B. second patient on a resource
    #   C. unserved
    #
    # But never more than one of those.
    

    for request in requests:

        request_id = request.request_id

        service_terms = []

        # Patient is first / only trip
        for resource in resources:

            service_terms.append(
                start[
                    (
                        request_id,
                        resource.resource_id,
                    )
                ]
            )

        # Patient is second trip
        for first_request in requests:

            first_id = first_request.request_id

            if first_id == request_id:
                continue

            for resource in resources:

                service_terms.append(
                    follow[
                        (
                            first_id,
                            request_id,
                            resource.resource_id,
                        )
                    ]
                )

        model.add(
            sum(service_terms)
            + unserved[request_id]
            == 1
        )


    
    # 4. EACH RESOURCE CAN BEGIN AT MOST ONE ROUTE
    

    for resource in resources:

        resource_id = resource.resource_id

        model.add(
            sum(
                start[
                    (
                        request.request_id,
                        resource_id,
                    )
                ]
                for request in requests
            )
            <= 1
        )


    
    # 5. EACH RESOURCE CAN HAVE AT MOST ONE FOLLOW-ON PATIENT
    #
    # Current milestone:
    #
    #     Resource → A
    #
    # or
    #
    #     Resource → A → B
    #
    # We intentionally stop at two patients for now.
    

    for resource in resources:

        resource_id = resource.resource_id

        follow_terms = []

        for first_request in requests:

            first_id = first_request.request_id

            for next_request in requests:

                next_id = next_request.request_id

                if first_id == next_id:
                    continue

                follow_terms.append(
                    follow[
                        (
                            first_id,
                            next_id,
                            resource_id,
                        )
                    ]
                )

        model.add(
            sum(follow_terms) <= 1
        )


    
    # HELPER:
    #
    # Expression indicating whether a particular patient is
    # served by a particular resource, regardless of whether
    # the patient is first or second.
    

    def assigned_to_resource_expression(
        request_id: str,
        resource_id: str,
    ):

        terms = [
            start[
                (
                    request_id,
                    resource_id,
                )
            ]
        ]

        for first_request in requests:

            first_id = first_request.request_id

            if first_id == request_id:
                continue

            terms.append(
                follow[
                    (
                        first_id,
                        request_id,
                        resource_id,
                    )
                ]
            )

        return sum(terms)


    
    # 6. PREVIOUSLY SERVED, UNAFFECTED PATIENTS
    #    CANNOT BECOME UNSERVED
    #
    # Preserve the collateral-service protection we already
    # added earlier.
    

    for request in requests:

        request_id = request.request_id

        if request_id not in current_assignments:
            continue

        current_resource_id = (
            current_assignments[
                request_id
            ]
        )

        current_assignment_still_feasible = (
            feasibility_matrix[
                request_id
            ].get(
                current_resource_id,
                0,
            )
            == 1
        )

        if current_assignment_still_feasible:

            model.add(
                unserved[
                    request_id
                ] == 0
            )


    
    # 7. LOCKED PATIENTS MUST REMAIN ON THEIR CURRENT RESOURCE
    

    for request_id in locked_request_ids:

        if request_id not in current_assignments:
            continue

        current_resource_id = (
            current_assignments[
                request_id
            ]
        )

        model.add(
            assigned_to_resource_expression(
                request_id=request_id,
                resource_id=current_resource_id,
            )
            == 1
        )


    
    # 8. OBJECTIVE — INITIAL TRIP COSTS
    

    initial_assignment_cost_term = sum(
        assignment_costs[
            request.request_id
        ][
            resource.resource_id
        ]
        * start[
            (
                request.request_id,
                resource.resource_id,
            )
        ]
        for request in requests
        for resource in resources
    )


    
    # 9. OBJECTIVE — SEQUENTIAL TRIP COSTS
    #
    # Charges:
    #
    # first patient's destination
    #       →
    # second patient's pickup
    #       →
    # second patient's destination
    

    sequential_cost_terms = []

    for first_request in requests:

        first_id = first_request.request_id

        for next_request in requests:

            next_id = next_request.request_id

            if first_id == next_id:
                continue

            for resource in resources:

                resource_id = resource.resource_id

                sequence_cost = (
                    sequential_assignment_costs
                    .get(
                        first_id,
                        {}
                    )
                    .get(
                        next_id,
                        {}
                    )
                    .get(
                        resource_id,
                        0
                    )
                )

                sequential_cost_terms.append(
                    sequence_cost
                    * follow[
                        (
                            first_id,
                            next_id,
                            resource_id,
                        )
                    ]
                )

    sequential_assignment_cost_term = sum(
        sequential_cost_terms
    )


    
    # 10. OBJECTIVE — REASSIGNMENT PENALTY
    #
    # A patient keeps their assignment if they remain on the
    # same resource, whether they become the first or second
    # trip on that resource.
    

    reassignment_terms = []

    for request in requests:

        request_id = request.request_id

        if request_id not in current_assignments:
            continue

        original_resource_id = (
            current_assignments[
                request_id
            ]
        )

        for resource in resources:

            resource_id = resource.resource_id

            if resource_id == original_resource_id:
                continue

            reassignment_terms.append(
                reassignment_penalty
                * assigned_to_resource_expression(
                    request_id=request_id,
                    resource_id=resource_id,
                )
            )

    reassignment_cost_term = sum(
        reassignment_terms
    )


    
    # 11. OBJECTIVE — UNSERVED PENALTY
    

    unserved_cost_term = sum(
        unserved_penalty
        * unserved[
            request.request_id
        ]
        for request in requests
    )


    model.minimize(
        initial_assignment_cost_term
        + sequential_assignment_cost_term
        + reassignment_cost_term
        + unserved_cost_term
    )


    
    # 12. SOLVE
    

    solver = cp_model.CpSolver()

    status = solver.solve(model)


    
    # 13. EXTRACT RESULTS
    

    assignments = {}

    unserved_requests = []

    resource_routes = {}


    if status in (
        cp_model.OPTIMAL,
        cp_model.FEASIBLE,
    ):

        
        # Record unserved patients
        

        for request in requests:

            request_id = request.request_id

            if (
                solver.value(
                    unserved[
                        request_id
                    ]
                )
                == 1
            ):

                unserved_requests.append(
                    request_id
                )


        
        # Recover each resource's ordered route
        

        for resource in resources:

            resource_id = resource.resource_id

            first_request_id = None

            for request in requests:

                request_id = request.request_id

                if (
                    solver.value(
                        start[
                            (
                                request_id,
                                resource_id,
                            )
                        ]
                    )
                    == 1
                ):

                    first_request_id = request_id

                    break


            if first_request_id is None:
                continue


            route = [
                first_request_id
            ]

            assignments[
                first_request_id
            ] = resource_id


            # Look for a second patient
            for next_request in requests:

                next_id = next_request.request_id

                if next_id == first_request_id:
                    continue

                key = (
                    first_request_id,
                    next_id,
                    resource_id,
                )

                if (
                    key in follow
                    and solver.value(
                        follow[key]
                    )
                    == 1
                ):

                    route.append(
                        next_id
                    )

                    assignments[
                        next_id
                    ] = resource_id

                    break


            resource_routes[
                resource_id
            ] = route


    return (
        assignments,
        unserved_requests,
        resource_routes,
    )
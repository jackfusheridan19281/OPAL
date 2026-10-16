from datetime import datetime

from optimization.schemas import (
    TransportRequest,
    TransportResource,
)

from optimization.travel import (
    calculate_estimated_arrival,
    calculate_transition_arrival,
)


# ============================================================
# INITIAL ASSIGNMENT COST
#
# Resource start → patient pickup → patient destination
# ============================================================

def calculate_assignment_cost(
    current_time: datetime,
    request: TransportRequest,
    resource: TransportResource,
    pickup_travel_minutes: int,
    patient_trip_minutes: int,
) -> int:

    eta = calculate_estimated_arrival(
        current_time=current_time,
        request=request,
        resource=resource,
        pickup_travel_minutes=pickup_travel_minutes,
        patient_trip_minutes=patient_trip_minutes,
    )

    # Total travel burden
    total_travel_minutes = (
        pickup_travel_minutes
        + patient_trip_minutes
    )

    # Minutes after the patient's preferred arrival time
    lateness_minutes = max(
        0,
        int(
            (
                eta - request.target_arrival
            ).total_seconds()
            / 60
        )
    )

    # Lateness matters much more than ordinary travel time
    cost = (
        total_travel_minutes
        + 10 * lateness_minutes
    )

    return cost


# ============================================================
# SEQUENTIAL ASSIGNMENT COST
#
# Previous patient destination
# → next patient pickup
# → next patient destination
# ============================================================

def calculate_transition_assignment_cost(
    previous_dropoff_time: datetime,
    next_request: TransportRequest,
    transition_travel_minutes: int,
    patient_trip_minutes: int,
) -> int:

    eta = calculate_transition_arrival(
        previous_dropoff_time=previous_dropoff_time,
        next_request=next_request,
        transition_travel_minutes=transition_travel_minutes,
        patient_trip_minutes=patient_trip_minutes,
    )

    # Only count travel associated with the next leg.
    #
    # The first patient's trip is already counted by
    # calculate_assignment_cost().
    total_travel_minutes = (
        transition_travel_minutes
        + patient_trip_minutes
    )

    lateness_minutes = max(
        0,
        int(
            (
                eta - next_request.target_arrival
            ).total_seconds()
            / 60
        )
    )

    cost = (
        total_travel_minutes
        + 10 * lateness_minutes
    )

    return cost


# ============================================================
# INITIAL ASSIGNMENT COST MATRIX
# ============================================================

def build_assignment_costs(
    current_time: datetime,
    requests: list[TransportRequest],
    resources: list[TransportResource],
    pickup_travel_times: dict[str, dict[str, int]],
    patient_trip_times: dict[str, int],
) -> dict[str, dict[str, int]]:

    costs = {}

    for request in requests:

        costs[request.request_id] = {}

        for resource in resources:

            costs[
                request.request_id
            ][
                resource.resource_id
            ] = calculate_assignment_cost(
                current_time=current_time,
                request=request,
                resource=resource,
                pickup_travel_minutes=(
                    pickup_travel_times[
                        request.request_id
                    ][
                        resource.resource_id
                    ]
                ),
                patient_trip_minutes=(
                    patient_trip_times[
                        request.request_id
                    ]
                ),
            )

    return costs


# ============================================================
# SEQUENTIAL ASSIGNMENT COST MATRIX
#
# first patient → next patient → resource
# ============================================================

def build_sequential_assignment_costs(
    current_time: datetime,
    requests: list[TransportRequest],
    resources: list[TransportResource],
    pickup_travel_times: dict[str, dict[str, int]],
    patient_trip_times: dict[str, int],
    transition_travel_times: dict[str, dict[str, int]],
) -> dict[str, dict[str, dict[str, int]]]:

    costs = {}

    for first_request in requests:

        costs[first_request.request_id] = {}

        for next_request in requests:

            costs[
                first_request.request_id
            ][
                next_request.request_id
            ] = {}

            for resource in resources:

                # A request cannot follow itself.
                if (
                    first_request.request_id
                    == next_request.request_id
                ):

                    costs[
                        first_request.request_id
                    ][
                        next_request.request_id
                    ][
                        resource.resource_id
                    ] = 0

                    continue


                # Determine when the vehicle finishes
                # serving the first patient.
                first_dropoff_time = (
                    calculate_estimated_arrival(
                        current_time=current_time,
                        request=first_request,
                        resource=resource,
                        pickup_travel_minutes=(
                            pickup_travel_times[
                                first_request.request_id
                            ][
                                resource.resource_id
                            ]
                        ),
                        patient_trip_minutes=(
                            patient_trip_times[
                                first_request.request_id
                            ]
                        ),
                    )
                )


                # Price only the additional travel and
                # lateness caused by serving the next patient.
                transition_cost = (
                    calculate_transition_assignment_cost(
                        previous_dropoff_time=(
                            first_dropoff_time
                        ),
                        next_request=next_request,
                        transition_travel_minutes=(
                            transition_travel_times[
                                first_request.request_id
                            ][
                                next_request.request_id
                            ]
                        ),
                        patient_trip_minutes=(
                            patient_trip_times[
                                next_request.request_id
                            ]
                        ),
                    )
                )

                costs[
                    first_request.request_id
                ][
                    next_request.request_id
                ][
                    resource.resource_id
                ] = transition_cost

    return costs
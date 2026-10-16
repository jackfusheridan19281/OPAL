
from optimization.schemas import TransportRequest, TransportResource
from optimization.travel import (
    calculate_estimated_arrival,
    is_time_feasible,
    is_transition_time_feasible,
)

def is_compatible(
    request: TransportRequest,
    resource: TransportResource
) -> bool:

    # Resource must currently be available
    if not resource.available:
        return False

    if request.request_id in resource.declined_request_ids:
        return False

    # Rideshare can only be used if the patient opted in
    if (
        resource.resource_type == "RIDESHARE"
        and not request.rideshare_allowed
    ):
        return False

    # Caregivers must be specifically approved for the patient
    if (
        resource.resource_type == "CAREGIVER"
        and request.patient_id not in resource.approved_patient_ids
    ):
        return False

    # A patient who requires a WAV must be assigned a WAV-capable resource
    if request.requires_wav and not resource.wav_capable:
        return False

    # If the patient uses a folding wheelchair but does not require a WAV,
    # the vehicle still needs somewhere to safely store the wheelchair
    if (
        request.uses_wheelchair
        and request.wheelchair_folds
        and not request.requires_wav
        and not resource.folding_wheelchair_storage
    ):
        return False

    # Required physical transfer assistance must be available
    if (
        request.transfer_assistance_required
        and not resource.transfer_assistance_capable
    ):
        return False

    return True


def get_feasible_resources(
    request: TransportRequest,
    resources: list[TransportResource]
) -> list[TransportResource]:

    feasible_resources = []

    for resource in resources:
        if is_compatible(request, resource):
            feasible_resources.append(resource)

    return feasible_resources


def build_feasibility_matrix(
    requests: list[TransportRequest],
    resources: list[TransportResource]
) -> dict[str, dict[str, int]]:

    matrix = {}

    for request in requests:
        matrix[request.request_id] = {}

        for resource in resources:
            matrix[request.request_id][resource.resource_id] = int(
                is_compatible(request, resource)
            )

    return matrix


def build_operational_feasibility_matrix(
    requests: list[TransportRequest],
    resources: list[TransportResource],
    current_time,
    pickup_travel_times: dict[str, dict[str, int]],
    patient_trip_times: dict[str, int],
) -> dict[str, dict[str, int]]:

    matrix = {}

    for request in requests:

        matrix[request.request_id] = {}

        for resource in resources:

            compatible = is_compatible(
                request,
                resource
            )

            if not compatible:

                matrix[
                    request.request_id
                ][
                    resource.resource_id
                ] = 0

                continue

            time_feasible = is_time_feasible(
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

            matrix[
                request.request_id
            ][
                resource.resource_id
            ] = int(time_feasible)

    return matrix

def build_sequential_feasibility_matrix(
    requests: list[TransportRequest],
    resources: list[TransportResource],
    current_time,
    pickup_travel_times: dict[str, dict[str, int]],
    patient_trip_times: dict[str, int],
    transition_travel_times: dict[str, dict[str, int]],
) -> dict[str, dict[str, dict[str, int]]]:

    matrix = {}

    for first_request in requests:

        matrix[first_request.request_id] = {}

        for next_request in requests:

            matrix[
                first_request.request_id
            ][
                next_request.request_id
            ] = {}

            for resource in resources:

                # ------------------------------------------------
                # A patient cannot follow themselves.
                # ------------------------------------------------

                if (
                    first_request.request_id
                    == next_request.request_id
                ):

                    matrix[
                        first_request.request_id
                    ][
                        next_request.request_id
                    ][
                        resource.resource_id
                    ] = 0

                    continue


                # ------------------------------------------------
                # Resource must be compatible with BOTH patients.
                # ------------------------------------------------

                first_compatible = is_compatible(
                    first_request,
                    resource,
                )

                next_compatible = is_compatible(
                    next_request,
                    resource,
                )

                if (
                    not first_compatible
                    or not next_compatible
                ):

                    matrix[
                        first_request.request_id
                    ][
                        next_request.request_id
                    ][
                        resource.resource_id
                    ] = 0

                    continue


                # ------------------------------------------------
                # First patient must be reachable from the
                # resource's starting location.
                # ------------------------------------------------

                first_time_feasible = is_time_feasible(
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

                if not first_time_feasible:

                    matrix[
                        first_request.request_id
                    ][
                        next_request.request_id
                    ][
                        resource.resource_id
                    ] = 0

                    continue


                # ------------------------------------------------
                # Determine when the first trip finishes.
                # ------------------------------------------------

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


                # ------------------------------------------------
                # Determine whether the SAME resource can travel
                # from Patient A's destination to Patient B's
                # pickup and still get B to dialysis on time.
                # ------------------------------------------------

                sequence_feasible = (
                    is_transition_time_feasible(
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

                matrix[
                    first_request.request_id
                ][
                    next_request.request_id
                ][
                    resource.resource_id
                ] = int(sequence_feasible)

    return matrix
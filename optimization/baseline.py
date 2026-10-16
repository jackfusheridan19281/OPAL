from optimization.schemas import (
    TransportRequest,
    TransportResource,
)


def greedy_assignments(
    requests: list[TransportRequest],
    resources: list[TransportResource],
    feasibility_matrix: dict[str, dict[str, int]],
    assignment_costs: dict[str, dict[str, int]],
):
    """
    Simple sequential baseline.

    Processes patients one at a time and assigns the cheapest
    currently available feasible resource.

    It does NOT look ahead at the needs of future patients.
    """

    assignments = {}
    unserved_requests = []

    used_resource_ids = set()

    for request in requests:

        feasible_options = []

        for resource in resources:

            if resource.resource_id in used_resource_ids:
                continue

            if (
                feasibility_matrix[
                    request.request_id
                ][
                    resource.resource_id
                ]
                == 0
            ):
                continue

            cost = assignment_costs[
                request.request_id
            ][
                resource.resource_id
            ]

            feasible_options.append(
                (
                    cost,
                    resource.resource_id,
                )
            )

        if not feasible_options:

            unserved_requests.append(
                request.request_id
            )

            continue

        # Pick cheapest option for THIS patient only.
        # No consideration of later patients.
        feasible_options.sort()

        _, chosen_resource_id = feasible_options[0]

        assignments[
            request.request_id
        ] = chosen_resource_id

        used_resource_ids.add(
            chosen_resource_id
        )

    return assignments, unserved_requests
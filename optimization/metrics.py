from optimization.schemas import TransportRequest


def calculate_solution_metrics(
    requests: list[TransportRequest],
    assignments: dict[str, str],
    unserved_requests: list[str],
    assignment_costs: dict[str, dict[str, int]],
    unserved_penalty: int = 10000,
):
    total_requests = len(requests)

    served_count = len(assignments)

    unserved_count = len(
        unserved_requests
    )

    served_rate = (
        served_count / total_requests
        if total_requests > 0
        else 0
    )

    total_assignment_cost = 0

    for request_id, resource_id in assignments.items():

        total_assignment_cost += assignment_costs[
            request_id
        ][
            resource_id
        ]

    penalty_cost = (
        unserved_count
        * unserved_penalty
    )

    total_score = (
        total_assignment_cost
        + penalty_cost
    )

    return {
        "total_requests": total_requests,
        "served_count": served_count,
        "unserved_count": unserved_count,
        "served_rate": served_rate,
        "assignment_cost": total_assignment_cost,
        "unserved_penalty_cost": penalty_cost,
        "total_score": total_score,
    }
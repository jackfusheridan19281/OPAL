

from optimization.schemas import CurrentAssignment, AssignmentStatus


def derive_solver_state(
    assignments: list[CurrentAssignment],
) -> tuple[dict[str, str], set[str]]:

    current_assignments = {}
    locked_request_ids = set()

    for assignment in assignments:

        # Completed trips no longer need to participate
        # in the active optimization problem.
        if assignment.status == AssignmentStatus.COMPLETED:
            continue

        current_assignments[
            assignment.request_id
        ] = assignment.resource_id

        # If the patient is already onboard,
        # the optimizer is not allowed to move them.
        if assignment.status == AssignmentStatus.PASSENGER_ONBOARD:
            locked_request_ids.add(
                assignment.request_id
            )

    return current_assignments, locked_request_ids
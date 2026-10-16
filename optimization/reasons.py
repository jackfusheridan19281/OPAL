from datetime import datetime

from optimization.schemas import (
    TransportRequest,
    TransportResource,
)

from optimization.travel import (
    calculate_estimated_arrival,
)


def get_infeasibility_reasons(
    request: TransportRequest,
    resource: TransportResource,
    current_time: datetime,
    pickup_travel_minutes: int,
    patient_trip_minutes: int,
) -> list[str]:

    reasons = []

    
    # Resource availability
    

    if not resource.available:
        reasons.append("RESOURCE_UNAVAILABLE")

    if request.request_id in resource.declined_request_ids:
        reasons.append("DRIVER_DECLINED")

    
    # Patient consent / permission
    

    if (
        resource.resource_type == "RIDESHARE"
        and not request.rideshare_allowed
    ):
        reasons.append("RIDESHARE_NOT_ALLOWED")


    
    # Caregiver approval
    

    if (
        resource.resource_type == "CAREGIVER"
        and request.patient_id
        not in resource.approved_patient_ids
    ):
        reasons.append("CAREGIVER_NOT_APPROVED")


    
    # Wheelchair accessibility
    

    if (
        request.requires_wav
        and not resource.wav_capable
    ):
        reasons.append("WAV_REQUIRED")


    if (
        request.uses_wheelchair
        and request.wheelchair_folds
        and not request.requires_wav
        and not resource.folding_wheelchair_storage
    ):
        reasons.append(
            "FOLDING_WHEELCHAIR_STORAGE_REQUIRED"
        )


    
    # Transfer assistance
    

    if (
        request.transfer_assistance_required
        and not resource.transfer_assistance_capable
    ):
        reasons.append(
            "TRANSFER_ASSISTANCE_REQUIRED"
        )


    
    # Time feasibility
    

    eta = calculate_estimated_arrival(
        current_time=current_time,
        request=request,
        resource=resource,
        pickup_travel_minutes=pickup_travel_minutes,
        patient_trip_minutes=patient_trip_minutes,
    )

    if eta > request.latest_arrival:
        reasons.append("ARRIVES_AFTER_DEADLINE")


    return reasons

def build_infeasibility_reason_matrix(
    requests: list[TransportRequest],
    resources: list[TransportResource],
    current_time: datetime,
    pickup_travel_times: dict[str, dict[str, int]],
    patient_trip_times: dict[str, int],
) -> dict[str, dict[str, list[str]]]:

    reason_matrix = {}

    for request in requests:

        reason_matrix[request.request_id] = {}

        for resource in resources:

            reasons = get_infeasibility_reasons(
                request=request,
                resource=resource,
                current_time=current_time,
                pickup_travel_minutes=pickup_travel_times[
                    request.request_id
                ][
                    resource.resource_id
                ],
                patient_trip_minutes=patient_trip_times[
                    request.request_id
                ],
            )

            reason_matrix[
                request.request_id
            ][
                resource.resource_id
            ] = reasons

    return reason_matrix
from datetime import datetime, timedelta

from optimization.schemas import (
    TransportRequest,
    TransportResource,
)



# RESOURCE START TIME


def get_resource_start_time(
    current_time: datetime,
    resource: TransportResource,
) -> datetime:

    # If no future availability time is specified,
    # the resource can begin at the scenario's current time.
    if resource.available_from is None:
        return current_time

    # A resource cannot begin before either:
    #
    # 1. the scenario's current time
    # 2. its own available_from time
    #
    # Example:
    #
    # current_time   = 1:00 PM
    # available_from = 1:25 PM
    #
    # The vehicle cannot begin until 1:25 PM.
    return max(
        current_time,
        resource.available_from,
    )



# INITIAL RESOURCE → PATIENT → DESTINATION


def calculate_estimated_arrival(
    current_time: datetime,
    request: TransportRequest,
    resource: TransportResource,
    pickup_travel_minutes: int,
    patient_trip_minutes: int,
) -> datetime:

    start_time = get_resource_start_time(
        current_time=current_time,
        resource=resource,
    )

    total_minutes = (
        pickup_travel_minutes
        + patient_trip_minutes
    )

    return start_time + timedelta(
        minutes=total_minutes
    )


def is_time_feasible(
    current_time: datetime,
    request: TransportRequest,
    resource: TransportResource,
    pickup_travel_minutes: int,
    patient_trip_minutes: int,
) -> bool:

    eta = calculate_estimated_arrival(
        current_time=current_time,
        request=request,
        resource=resource,
        pickup_travel_minutes=pickup_travel_minutes,
        patient_trip_minutes=patient_trip_minutes,
    )

    return eta <= request.latest_arrival



# PATIENT A DESTINATION → PATIENT B → DESTINATION


def calculate_transition_arrival(
    previous_dropoff_time: datetime,
    next_request: TransportRequest,
    transition_travel_minutes: int,
    patient_trip_minutes: int,
) -> datetime:

    # Example:
    #
    # Patient A dropoff:
    #       1:30 PM
    #
    # A destination → B pickup:
    #       12 minutes
    #
    # B pickup → B destination:
    #       20 minutes
    #
    # B estimated arrival:
    #       2:02 PM

    total_minutes = (
        transition_travel_minutes
        + patient_trip_minutes
    )

    return previous_dropoff_time + timedelta(
        minutes=total_minutes
    )


def is_transition_time_feasible(
    previous_dropoff_time: datetime,
    next_request: TransportRequest,
    transition_travel_minutes: int,
    patient_trip_minutes: int,
) -> bool:

    eta = calculate_transition_arrival(
        previous_dropoff_time=previous_dropoff_time,
        next_request=next_request,
        transition_travel_minutes=transition_travel_minutes,
        patient_trip_minutes=patient_trip_minutes,
    )

    return eta <= next_request.latest_arrival
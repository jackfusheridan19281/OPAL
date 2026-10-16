from copy import deepcopy

from optimization.schemas import (
    TransportResource,
    NetworkEvent,
    EventType,
)


def apply_event(
    event: NetworkEvent,
    resources: list[TransportResource],
    pickup_travel_times: dict[str, dict[str, int]],
):
    """
    Apply a real-world event to the current transportation state.

    Returns NEW copies of the resources and travel times so that
    the previous state is preserved.
    """

    updated_resources = deepcopy(resources)

    updated_pickup_travel_times = deepcopy(
        pickup_travel_times
    )


    # ============================================================
    # TRAFFIC DELAY
    # ============================================================

    if event.event_type == EventType.TRAFFIC_DELAY:

        if event.request_id is None:
            raise ValueError(
                "TRAFFIC_DELAY requires request_id"
            )

        if event.resource_id is None:
            raise ValueError(
                "TRAFFIC_DELAY requires resource_id"
            )

        updated_pickup_travel_times[
            event.request_id
        ][
            event.resource_id
        ] += event.delay_minutes


    # ============================================================
    # DRIVER DECLINES A SPECIFIC REQUEST
    # ============================================================

    elif event.event_type == EventType.DRIVER_DECLINED:

        if event.request_id is None:
            raise ValueError(
                "DRIVER_DECLINED requires request_id"
            )

        if event.resource_id is None:
            raise ValueError(
                "DRIVER_DECLINED requires resource_id"
            )

        for resource in updated_resources:

            if resource.resource_id == event.resource_id:

                if (
                    event.request_id
                    not in resource.declined_request_ids
                ):
                    resource.declined_request_ids.append(
                        event.request_id
                    )

                break


    # ============================================================
    # RESOURCE IS GLOBALLY UNAVAILABLE
    # ============================================================

    elif event.event_type in {
        EventType.RESOURCE_UNAVAILABLE,
        EventType.VEHICLE_BREAKDOWN,
    }:

        if event.resource_id is None:
            raise ValueError(
                f"{event.event_type.value} requires resource_id"
            )

        for resource in updated_resources:

            if resource.resource_id == event.resource_id:

                resource.available = False
                break


    # ============================================================
    # RESOURCE BECOMES AVAILABLE AGAIN
    # ============================================================

    elif event.event_type == EventType.RESOURCE_AVAILABLE:

        if event.resource_id is None:
            raise ValueError(
                "RESOURCE_AVAILABLE requires resource_id"
            )

        for resource in updated_resources:

            if resource.resource_id == event.resource_id:

                resource.available = True
                break


    # ============================================================
    # RETURN UPDATED NETWORK STATE
    # ============================================================

    return (
        updated_resources,
        updated_pickup_travel_times,
    )
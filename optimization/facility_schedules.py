from datetime import datetime, time, timedelta
import random


# ============================================================
# DEFAULT MODELED DIALYSIS SCHEDULING RULES
#
# These are simulation defaults, NOT claims about the actual
# operating hours of any real facility.
#
# Individual facilities can override these values later.
# ============================================================

DEFAULT_DIALYSIS_SCHEDULE = {
    "opening_time": "06:00",
    "closing_time": "18:00",
    "slot_interval_minutes": 30,
    "arrival_buffer_minutes": 15,
    "minimum_booking_lead_minutes": 30,
}


def parse_clock_time(
    clock_time: str,
) -> time:

    return datetime.strptime(
        clock_time,
        "%H:%M",
    ).time()


def build_facility_appointment_slots(
    scenario_time: datetime,
    opening_time: str,
    closing_time: str,
    slot_interval_minutes: int,
    minimum_booking_lead_minutes: int,
) -> list[datetime]:

    opening = datetime.combine(
        scenario_time.date(),
        parse_clock_time(opening_time),
    )

    closing = datetime.combine(
        scenario_time.date(),
        parse_clock_time(closing_time),
    )

    earliest_allowed_appointment = (
        scenario_time
        + timedelta(
            minutes=minimum_booking_lead_minutes
        )
    )

    slots = []

    slot_time = opening

    while slot_time <= closing:

        if slot_time >= earliest_allowed_appointment:

            slots.append(
                slot_time
            )

        slot_time += timedelta(
            minutes=slot_interval_minutes
        )

    return slots


def generate_facility_appointment(
    scenario_time: datetime,
    facility: dict,
    rng: random.Random,
) -> dict:

    schedule = {
        **DEFAULT_DIALYSIS_SCHEDULE,
        **facility.get(
            "schedule",
            {},
        ),
    }

    appointment_slots = (
        build_facility_appointment_slots(
            scenario_time=scenario_time,
            opening_time=schedule[
                "opening_time"
            ],
            closing_time=schedule[
                "closing_time"
            ],
            slot_interval_minutes=schedule[
                "slot_interval_minutes"
            ],
            minimum_booking_lead_minutes=schedule[
                "minimum_booking_lead_minutes"
            ],
        )
    )

    if not appointment_slots:

        raise ValueError(
            f"No valid appointment slots remain for "
            f"{facility.get('name', 'facility')}."
        )

    appointment_time = rng.choice(
        appointment_slots
    )

    target_arrival = (
        appointment_time
        - timedelta(
            minutes=schedule[
                "arrival_buffer_minutes"
            ]
        )
    )

    latest_arrival = appointment_time

    return {
        "appointment_time": appointment_time,
        "target_arrival": target_arrival,
        "latest_arrival": latest_arrival,
    }
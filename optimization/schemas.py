

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field



# TRANSPORT REQUEST


class TransportRequest(BaseModel):
    request_id: str
    patient_id: str
    patient_name: str

    pickup_lat: float
    pickup_lon: float

    destination_lat: float
    destination_lon: float

    appointment_time: datetime

    target_arrival: datetime
    latest_arrival: datetime

    rideshare_allowed: bool

    uses_wheelchair: bool
    wheelchair_folds: bool
    requires_wav: bool

    can_transfer: bool
    transfer_assistance_required: bool



# TRANSPORT RESOURCE


class TransportResource(BaseModel):
    resource_id: str
    resource_type: str

    current_lat: float
    current_lon: float

    available: bool
    available_from: datetime | None = None

    wav_capable: bool
    folding_wheelchair_storage: bool
    transfer_assistance_capable: bool

    approved_patient_ids: list[str] = Field(
        default_factory=list
    )

    declined_request_ids: list[str] = Field(
        default_factory=list
    )


# ASSIGNMENT STATE


class AssignmentStatus(str, Enum):
    FLEXIBLE = "FLEXIBLE"
    CONFIRMED = "CONFIRMED"
    EN_ROUTE_TO_PICKUP = "EN_ROUTE_TO_PICKUP"
    PASSENGER_ONBOARD = "PASSENGER_ONBOARD"
    COMPLETED = "COMPLETED"


class CurrentAssignment(BaseModel):
    request_id: str
    resource_id: str
    status: AssignmentStatus



# NETWORK EVENTS


class EventType(str, Enum):
    TRAFFIC_DELAY = "TRAFFIC_DELAY"
    RESOURCE_UNAVAILABLE = "RESOURCE_UNAVAILABLE"
    RESOURCE_AVAILABLE = "RESOURCE_AVAILABLE"
    DRIVER_DECLINED = "DRIVER_DECLINED"
    VEHICLE_BREAKDOWN = "VEHICLE_BREAKDOWN"


class NetworkEvent(BaseModel):
    event_type: EventType
    occurred_at: datetime

    request_id: str | None = None
    resource_id: str | None = None

    delay_minutes: int = 0
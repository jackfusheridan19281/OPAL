

import json
import math
import random

from optimization.facility_schedules import (
    generate_facility_appointment,
)

from functools import lru_cache
from pathlib import Path

from shapely.geometry import Point, shape
from shapely.ops import unary_union

from datetime import datetime, timedelta

from optimization.schemas import (
    TransportRequest,
    TransportResource,
)



# DEMO REGION PRESETS
#
# These are only geographic centers for synthetic scenarios.
# Later, real locations can come from a database / mapping API.


REGIONS = {
    "BOSTON": {
        "center_lat": 42.3601,
        "center_lon": -71.0589,
        "spread": 0.07,
    },

    "NYC": {
        "center_lat": 40.7580,
        "center_lon": -73.9855,
        "spread": 0.09,
    },
}


# REAL BOSTON DIALYSIS DESTINATIONS
#
# Publicly listed dialysis facilities.
# Patient and vehicle locations remain synthetic.


BOSTON_DIALYSIS_CENTERS = [
    {
        "name": "Brigham and Women's Hospital Dialysis",
        "address": "75 Francis St, Boston, MA 02115",
        "lat": 42.335680,
        "lon": -71.106044,
    },
    {
        "name": "DaVita Boston Dialysis",
        "address": "660 Harrison Ave, Boston, MA 02118",
        "lat": 42.338826,
        "lon": -71.069919,
    },
    {
        "name": "DCI Boston",
        "address": "35 Kneeland St, Boston, MA 02111",
        "lat": 42.350596,
        "lon": -71.061942,
    },
    {
        "name": "Fresenius Kidney Care Boston - The Kidney Center",
        "address": "888 Commonwealth Ave, Boston, MA 02215",
        "lat": 42.350935,
        "lon": -71.115315,
    },
    {
        "name": "Massachusetts General Hospital Dialysis",
        "address": "55 Fruit St, Boston, MA 02114",
        "lat": 42.362417,
        "lon": -71.068937,
    },
]

SCENARIO_MODES = {
    "NORMAL": {
        "wheelchair_probability": 0.22,
        "wav_given_wheelchair_probability": 0.35,
        "transfer_assistance_probability": 0.25,
        "rideshare_allowed_probability": 0.70,

        "wav_resource_share": 0.22,
        "extra_wav_probability": 0.25,
        "resource_unavailable_probability": 0.00,

        "target_minutes_min": 50,
        "target_minutes_max": 150,

        "deadline_slack_min": 20,
        "deadline_slack_max": 35,
    },

    "STRESSED": {
        "wheelchair_probability": 0.32,
        "wav_given_wheelchair_probability": 0.55,
        "transfer_assistance_probability": 0.40,
        "rideshare_allowed_probability": 0.50,

        "wav_resource_share": 0.14,
        "extra_wav_probability": 0.10,
        "resource_unavailable_probability": 0.08,

        "target_minutes_min": 30,
        "target_minutes_max": 110,

        "deadline_slack_min": 10,
        "deadline_slack_max": 20,
    },

    "CRISIS": {
        "wheelchair_probability": 0.42,
        "wav_given_wheelchair_probability": 0.68,
        "transfer_assistance_probability": 0.55,
        "rideshare_allowed_probability": 0.35,

        "wav_resource_share": 0.08,
        "extra_wav_probability": 0.03,
        "resource_unavailable_probability": 0.15,

        "target_minutes_min": 20,
        "target_minutes_max": 85,

        "deadline_slack_min": 5,
        "deadline_slack_max": 15,
    },
}

FIRST_NAMES = [
    "Margaret", "John", "Sarah", "James", "Maria",
    "Robert", "Linda", "Michael", "Patricia", "David",
    "Jennifer", "William", "Elizabeth", "Richard", "Susan",
    "Joseph", "Jessica", "Thomas", "Karen", "Charles",
    "Nancy", "Daniel", "Lisa", "Matthew", "Betty",
    "Anthony", "Sandra", "Mark", "Ashley", "Donald",
    "Emily", "Steven", "Kimberly", "Paul", "Donna",
    "Andrew", "Michelle", "Joshua", "Carol", "Kenneth",
    "Amanda", "Kevin", "Melissa", "Brian", "Deborah",
    "George", "Stephanie", "Edward", "Rebecca", "Jason",
]


LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones",
    "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
    "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris",
    "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson",
    "Walker", "Young", "Allen", "King", "Wright",
    "Scott", "Torres", "Nguyen", "Hill", "Flores",
    "Green", "Adams", "Nelson", "Baker", "Hall",
    "Rivera", "Campbell", "Mitchell", "Carter", "Roberts",
]

def generate_patient_names(
    count: int,
    rng: random.Random,
) -> list[str]:

    possible_names = [
        f"{first} {last}"
        for first in FIRST_NAMES
        for last in LAST_NAMES
    ]

    rng.shuffle(possible_names)

    if count <= len(possible_names):
        return possible_names[:count]

    # Fallback for extremely large simulations
    names = possible_names.copy()

    while len(names) < count:
        number = len(names) + 1

        first = rng.choice(FIRST_NAMES)
        last = rng.choice(LAST_NAMES)

        names.append(
            f"{first} {last} {number}"
        )

    return names


# APPROXIMATE DISTANCE


def approximate_distance_miles(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:

    latitude_miles = (
        lat2 - lat1
    ) * 69.0

    average_latitude = math.radians(
        (lat1 + lat2) / 2
    )

    longitude_miles = (
        lon2 - lon1
    ) * (
        69.0 * math.cos(average_latitude)
    )

    return math.sqrt(
        latitude_miles ** 2
        + longitude_miles ** 2
    )



# SYNTHETIC TRAVEL TIME
#
# Temporary replacement for Google Routes / real road data.


def estimate_travel_minutes(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
    rng: random.Random,
) -> int:

    distance = approximate_distance_miles(
        lat1,
        lon1,
        lat2,
        lon2,
    )

    # Rough city driving speed
    average_speed_mph = rng.uniform(
        16,
        28,
    )

    traffic_multiplier = rng.uniform(
        1.0,
        1.35,
    )

    minutes = (
        distance
        / average_speed_mph
        * 60
        * traffic_multiplier
    )

    # Avoid unrealistically tiny travel times
    return max(
        4,
        round(minutes),
    )



# GENERATE RANDOM LOCATION INSIDE REGION


def random_location(
    region_data: dict,
    rng: random.Random,
) -> tuple[float, float]:

    lat = (
        region_data["center_lat"]
        + rng.uniform(
            -region_data["spread"],
            region_data["spread"],
        )
    )

    lon = (
        region_data["center_lon"]
        + rng.uniform(
            -region_data["spread"],
            region_data["spread"],
        )
    )

    return lat, lon


# REAL CITY LAND GEOMETRY
#
# Boston and NYC synthetic locations are constrained to
# official land polygons so patients/resources are not
# generated in water.


LAND_GEOJSON_FILES = {
    "BOSTON": "boston_land.geojson",
    "NYC": "nyc_land.geojson",
}


@lru_cache(maxsize=None)
def load_city_land(
    region: str,
):

    filename = LAND_GEOJSON_FILES.get(
        region
    )

    if not filename:

        raise ValueError(
            f"No land geometry configured for {region}"
        )


    geojson_path = (
        Path(__file__).resolve().parent
        / "data"
        / filename
    )


    with open(
        geojson_path,
        "r",
        encoding="utf-8",
    ) as file:

        geojson_data = json.load(file)


    geometries = [
        shape(feature["geometry"])
        for feature in geojson_data["features"]
        if feature.get("geometry")
    ]


    return unary_union(
        geometries
    )


def random_city_land_location(
    region: str,
    rng: random.Random,
) -> tuple[float, float]:

    city_land = load_city_land(
        region
    )


    min_lon, min_lat, max_lon, max_lat = (
        city_land.bounds
    )


    for _ in range(10000):

        lon = rng.uniform(
            min_lon,
            max_lon,
        )

        lat = rng.uniform(
            min_lat,
            max_lat,
        )


        point = Point(
            lon,
            lat,
        )


        if city_land.contains(point):

            return lat, lon


    raise RuntimeError(
        f"Unable to generate a location on {region} land."
    )


def random_scenario_location(
    region: str,
    region_data: dict,
    rng: random.Random,
) -> tuple[float, float]:

    if region in {
        "BOSTON",
        "NYC",
    }:

        return random_city_land_location(
            region,
            rng,
        )


    return random_location(
        region_data,
        rng,
    )


# MAIN SCENARIO GENERATOR


def generate_scenario(
    region: str = "BOSTON",
    num_patients: int = 30,
    num_resources: int = 40,
    seed: int = 67,
    scenario_mode: str = "NORMAL",
):

    region = region.upper()

    scenario_mode = scenario_mode.upper()

    if scenario_mode not in SCENARIO_MODES:
        raise ValueError(
            f"Unknown scenario mode: {scenario_mode}"
        )

    mode = SCENARIO_MODES[scenario_mode]

    if region not in REGIONS:
        raise ValueError(
            f"Unknown region: {region}"
        )

    if num_patients < 1:
        raise ValueError(
            "num_patients must be at least 1"
        )

    if num_resources < 1:
        raise ValueError(
            "num_resources must be at least 1"
        )

    rng = random.Random(seed)

    region_data = REGIONS[region]

    current_time = datetime(
        2026,
        10,
        16,
        13,
        0,
    )


    
    # DIALYSIS DESTINATIONS
    

    if region == "BOSTON":

        dialysis_centers = [
            center.copy()
            for center in BOSTON_DIALYSIS_CENTERS
        ]

    else:

        # NYC remains synthetic for now.

        dialysis_centers = []

        for i in range(1, 4):

            center_lat, center_lon = random_scenario_location(
                region,
                region_data,
                rng,
            )

            dialysis_centers.append(
                {
                    "name": f"Synthetic Dialysis Center {i}",
                    "address": "Synthetic demo location",
                    "lat": center_lat,
                    "lon": center_lon,
                }
            )


    
    # GENERATE PATIENTS
    

    requests = []

    patient_names = generate_patient_names(
        num_patients,
        rng,
    )

    for i in range(
        1,
        num_patients + 1,
    ):

        request_id = f"REQ-{i:03d}"
        patient_id = f"PATIENT-{i:03d}"

        pickup_lat, pickup_lon = random_scenario_location(
            region,
            region_data,
            rng,
        )

        destination_center = rng.choice(
            dialysis_centers
        )

        destination_lat = destination_center["lat"]
        destination_lon = destination_center["lon"]


        
        # Accessibility characteristics
        

        uses_wheelchair = (
            rng.random()
            < mode["wheelchair_probability"]
        )

        requires_wav = (
            uses_wheelchair
            and rng.random()
            < mode["wav_given_wheelchair_probability"]
        )

        if uses_wheelchair:

            wheelchair_folds = (
                not requires_wav
                and rng.random() < 0.75
            )

        else:

            wheelchair_folds = False


        can_transfer = (
            not requires_wav
        )

        transfer_assistance_required = (
            uses_wheelchair
            and rng.random()
            < mode["transfer_assistance_probability"]
        )


        
        # Transportation consent
        

        rideshare_allowed = (
            rng.random()
            < mode["rideshare_allowed_probability"]
        )


        
        # Facility-based appointment scheduling
        #
        # The patient's appointment is generated from the
        # destination dialysis facility's scheduling window.
        #
        # Transportation timing is then derived backward:
        #
        # appointment_time
        #       ↓
        # target arrival = appointment - arrival buffer
        #       ↓
        # latest arrival = appointment time
        

        appointment = (
            generate_facility_appointment(
                scenario_time=current_time,
                facility=destination_center,
                rng=rng,
            )
        )

        appointment_time = (
            appointment[
                "appointment_time"
            ]
        )

        target_arrival = (
            appointment[
                "target_arrival"
            ]
        )

        latest_arrival = (
            appointment[
                "latest_arrival"
            ]
        )

        request = TransportRequest(
            request_id=request_id,
            patient_id=patient_id,
            patient_name=patient_names[i - 1],
            pickup_lat=pickup_lat,
            pickup_lon=pickup_lon,
            destination_lat=destination_lat,
            destination_lon=destination_lon,

            appointment_time=appointment_time,
            target_arrival=target_arrival,
            latest_arrival=latest_arrival,
            rideshare_allowed=rideshare_allowed,
            uses_wheelchair=uses_wheelchair,
            wheelchair_folds=wheelchair_folds,
            requires_wav=requires_wav,
            can_transfer=can_transfer,
            transfer_assistance_required=(
                transfer_assistance_required
            ),
        )

        requests.append(
            request
        )


    
    # GENERATE RESOURCES
    

    resources = []

    # Guarantee at least some specialized capacity
    guaranteed_wav_count = max(
        1,
        round(
            num_resources
            * mode["wav_resource_share"]
        ),
    )

    for i in range(
        1,
        num_resources + 1,
    ):

        resource_lat, resource_lon = random_scenario_location(
            region,
            region_data,
            rng,
        )


        
        # Choose resource type
        

        if i <= guaranteed_wav_count:

            resource_type = "NEMT"
            wav_capable = True

        else:

            type_roll = rng.random()

            if type_roll < 0.40:

                resource_type = "NEMT"

            elif type_roll < 0.68:

                resource_type = "CAREGIVER"

            else:

                resource_type = "RIDESHARE"


            wav_capable = (
                resource_type == "NEMT"
                and rng.random()
                < mode["extra_wav_probability"]
            )


        
        # Capabilities
        

        folding_storage = (
            resource_type != "RIDESHARE"
            or rng.random() < 0.80
        )

        transfer_assistance = (
            resource_type in {
                "NEMT",
                "CAREGIVER",
            }
        )


        
        # Caregiver approvals
        

        approved_patient_ids = []

        if resource_type == "CAREGIVER":

            number_approved = min(
                rng.randint(
                    1,
                    3,
                ),
                len(requests),
            )

            approved_patients = rng.sample(
                requests,
                number_approved,
            )

            approved_patient_ids = [
                patient.patient_id
                for patient
                in approved_patients
            ]


        resource = TransportResource(
            resource_id=f"RESOURCE-{i:03d}",
            resource_type=resource_type,
            current_lat=resource_lat,
            current_lon=resource_lon,
            available=(
                rng.random()
                >= mode["resource_unavailable_probability"]
            ),
            available_from=current_time,
            wav_capable=wav_capable,
            folding_wheelchair_storage=(
                folding_storage
            ),
            transfer_assistance_capable=(
                transfer_assistance
            ),
            approved_patient_ids=(
                approved_patient_ids
            ),
            declined_request_ids=[],
        )

        resources.append(
            resource
        )


    
    # BUILD TRAVEL TIME MATRICES
    

    pickup_travel_times = {}

    patient_trip_times = {}

    transition_travel_times = {}


    for request in requests:

        pickup_travel_times[
            request.request_id
        ] = {}


        
        # Resource → patient pickup
        

        for resource in resources:

            pickup_minutes = estimate_travel_minutes(
                resource.current_lat,
                resource.current_lon,
                request.pickup_lat,
                request.pickup_lon,
                rng,
            )

            pickup_travel_times[
                request.request_id
            ][
                resource.resource_id
            ] = pickup_minutes


        
        # Patient pickup → dialysis center
        

        patient_trip_minutes = estimate_travel_minutes(
            request.pickup_lat,
            request.pickup_lon,
            request.destination_lat,
            request.destination_lon,
            rng,
        )

        patient_trip_times[
            request.request_id
        ] = patient_trip_minutes

    
    # BUILD PATIENT-TO-PATIENT TRANSITION TRAVEL TIMES
    #
    # This represents:
    #
    # Patient A dialysis dropoff
    #           ↓
    # Patient B pickup
    #
    # It allows the optimizer to determine whether the same
    # vehicle can finish one trip and then serve another.
    

    for first_request in requests:

        transition_travel_times[
            first_request.request_id
        ] = {}

        for next_request in requests:

            # A patient does not transition to themselves
            if (
                first_request.request_id
                == next_request.request_id
            ):

                transition_travel_times[
                    first_request.request_id
                ][
                    next_request.request_id
                ] = 0

                continue

            transition_minutes = estimate_travel_minutes(
                first_request.destination_lat,
                first_request.destination_lon,
                next_request.pickup_lat,
                next_request.pickup_lon,
                rng,
            )

            transition_travel_times[
                first_request.request_id
            ][
                next_request.request_id
            ] = transition_minutes

    
    # RETURN COMPLETE SYNTHETIC NETWORK
    

    return {
        "region": region,
        "scenario_mode": scenario_mode,
        "seed": seed,
        "current_time": current_time,

        "requests": requests,
        "resources": resources,

        "dialysis_centers": dialysis_centers,

        "pickup_travel_times": (
            pickup_travel_times
        ),

        "patient_trip_times": (
            patient_trip_times
        ),

        "transition_travel_times": (
        transition_travel_times
        ),
    }
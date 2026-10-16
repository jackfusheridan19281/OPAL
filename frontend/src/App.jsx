
import { useState } from "react";
import NetworkMap from "./NetworkMap";
import "./App.css";


const resourceNames = {
  "UBER-X-01": "UberX",
  "UBER-ASSIST-01": "Uber Assist",
  "CAREGIVER-01": "Caregiver 1",
  "CAREGIVER-02": "Caregiver 2",
  "NEMT-WAV-01": "NEMT WAV",
};


const initialPatients = [
  {
    requestId: "REQ-001",
    name: "Margaret",
    currentRide: "Uber Assist",
    status: "At Risk",
    recoveredRide: null,
  },
  {
    requestId: "REQ-002",
    name: "John",
    currentRide: "Caregiver 2",
    status: "Stable",
    recoveredRide: null,
  },
  {
    requestId: "REQ-003",
    name: "Sarah",
    currentRide: "NEMT WAV",
    status: "Stable",
    recoveredRide: null,
  },
];


const recoveryPayload = {
  requests: [
    {
      request_id: "REQ-001",
      patient_id: "PATIENT-001",
      patient_name: "Margaret",
      pickup_lat: 42.9956,
      pickup_lon: -71.4548,
      destination_lat: 43.2081,
      destination_lon: -71.5376,
      target_arrival: "2026-10-16T13:45:00",
      latest_arrival: "2026-10-16T13:55:00",
      rideshare_allowed: true,
      uses_wheelchair: true,
      wheelchair_folds: true,
      requires_wav: false,
      can_transfer: true,
      transfer_assistance_required: true,
    },

    {
      request_id: "REQ-002",
      patient_id: "PATIENT-002",
      patient_name: "John",
      pickup_lat: 43.02,
      pickup_lon: -71.48,
      destination_lat: 43.2081,
      destination_lon: -71.5376,
      target_arrival: "2026-10-16T14:05:00",
      latest_arrival: "2026-10-16T14:20:00",
      rideshare_allowed: false,
      uses_wheelchair: false,
      wheelchair_folds: false,
      requires_wav: false,
      can_transfer: true,
      transfer_assistance_required: false,
    },

    {
      request_id: "REQ-003",
      patient_id: "PATIENT-003",
      patient_name: "Sarah",
      pickup_lat: 43.05,
      pickup_lon: -71.5,
      destination_lat: 43.2081,
      destination_lon: -71.5376,
      target_arrival: "2026-10-16T14:10:00",
      latest_arrival: "2026-10-16T14:20:00",
      rideshare_allowed: false,
      uses_wheelchair: true,
      wheelchair_folds: false,
      requires_wav: true,
      can_transfer: false,
      transfer_assistance_required: true,
    },
  ],

  resources: [
    {
      resource_id: "UBER-X-01",
      resource_type: "RIDESHARE",
      current_lat: 43.0,
      current_lon: -71.46,
      available: true,
      wav_capable: false,
      folding_wheelchair_storage: true,
      transfer_assistance_capable: false,
      approved_patient_ids: [],
      declined_request_ids: [],
    },

    {
      resource_id: "UBER-ASSIST-01",
      resource_type: "RIDESHARE",
      current_lat: 43.01,
      current_lon: -71.47,
      available: true,
      wav_capable: false,
      folding_wheelchair_storage: true,
      transfer_assistance_capable: true,
      approved_patient_ids: [],
      declined_request_ids: [],
    },

    {
      resource_id: "CAREGIVER-01",
      resource_type: "CAREGIVER",
      current_lat: 43.03,
      current_lon: -71.49,
      available: true,
      wav_capable: false,
      folding_wheelchair_storage: true,
      transfer_assistance_capable: true,
      approved_patient_ids: ["PATIENT-001"],
      declined_request_ids: [],
    },

    {
      resource_id: "CAREGIVER-02",
      resource_type: "CAREGIVER",
      current_lat: 43.04,
      current_lon: -71.48,
      available: true,
      wav_capable: false,
      folding_wheelchair_storage: true,
      transfer_assistance_capable: true,
      approved_patient_ids: ["PATIENT-002"],
      declined_request_ids: [],
    },

    {
      resource_id: "NEMT-WAV-01",
      resource_type: "NEMT",
      current_lat: 43.06,
      current_lon: -71.51,
      available: true,
      wav_capable: true,
      folding_wheelchair_storage: true,
      transfer_assistance_capable: true,
      approved_patient_ids: [],
      declined_request_ids: [],
    },
  ],

  current_time: "2026-10-16T13:10:00",

  pickup_travel_times: {
    "REQ-001": {
      "UBER-X-01": 8,
      "UBER-ASSIST-01": 12,
      "CAREGIVER-01": 15,
      "CAREGIVER-02": 10,
      "NEMT-WAV-01": 25,
    },

    "REQ-002": {
      "UBER-X-01": 7,
      "UBER-ASSIST-01": 11,
      "CAREGIVER-01": 14,
      "CAREGIVER-02": 9,
      "NEMT-WAV-01": 5,
    },

    "REQ-003": {
      "UBER-X-01": 10,
      "UBER-ASSIST-01": 12,
      "CAREGIVER-01": 14,
      "CAREGIVER-02": 15,
      "NEMT-WAV-01": 12,
    },
  },

  patient_trip_times: {
    "REQ-001": 25,
    "REQ-002": 30,
    "REQ-003": 30,
  },

  current_assignment_states: [
    {
      request_id: "REQ-001",
      resource_id: "UBER-ASSIST-01",
      status: "CONFIRMED",
    },
    {
      request_id: "REQ-002",
      resource_id: "CAREGIVER-02",
      status: "PASSENGER_ONBOARD",
    },
  ],

  events: [
  {
    event_type: "TRAFFIC_DELAY",
    occurred_at: "2026-10-16T13:10:00",
    request_id: "REQ-001",
    resource_id: "UBER-ASSIST-01",
    delay_minutes: 12,
  },
],

  reassignment_penalty: 30,
};

function formatReason(reason) {
  const labels = {
    RESOURCE_UNAVAILABLE: "Resource unavailable",
    DRIVER_DECLINED: "Driver declined this patient",
    RIDESHARE_NOT_ALLOWED: "Patient does not allow rideshare",
    CAREGIVER_NOT_APPROVED: "Caregiver not approved for this patient",
    WAV_REQUIRED: "Wheelchair-accessible vehicle required",
    FOLDING_WHEELCHAIR_STORAGE_REQUIRED:
      "Folding wheelchair storage required",
    TRANSFER_ASSISTANCE_REQUIRED:
      "Transfer assistance required",
    ARRIVES_AFTER_DEADLINE:
      "Would arrive after latest acceptable time",
  };

  return labels[reason] || reason;
}

function summarizeFailureReasons(
  reasonMap,
  resources,
  assignments,
  requests,
  requestId
) {
  const counts = {
    RESOURCE_UNAVAILABLE: 0,
    DRIVER_DECLINED: 0,
    RIDESHARE_NOT_ALLOWED: 0,
    CAREGIVER_NOT_APPROVED: 0,
    WAV_REQUIRED: 0,
    FOLDING_WHEELCHAIR_STORAGE_REQUIRED: 0,
    TRANSFER_ASSISTANCE_REQUIRED: 0,
    ARRIVES_AFTER_DEADLINE: 0,
    ALLOCATED_ELSEWHERE: 0,
    FEASIBLE_UNUSED: 0,
  };

  resources.forEach((resource) => {
    const reasons =
      reasonMap[resource.resource_id] || [];

    if (reasons.length > 0) {
      reasons.forEach((reason) => {
        if (counts[reason] !== undefined) {
          counts[reason] += 1;
        }
      });

      return;
    }

    const assignedRequestId =
      Object.entries(assignments || {}).find(
        ([, assignedResource]) =>
          assignedResource === resource.resource_id
      )?.[0];

    if (
      assignedRequestId &&
      assignedRequestId !== requestId
    ) {
      counts.ALLOCATED_ELSEWHERE += 1;
    } else {
      counts.FEASIBLE_UNUSED += 1;
    }
  });

  return counts;
}

function App() {
  const [patients, setPatients] = useState(initialPatients);

  const [message, setMessage] = useState(
    "Network stable. No disruption detected."
  );

const [metrics, setMetrics] = useState(null);

  const [region, setRegion] = useState("BOSTON");
  const [numPatients, setNumPatients] = useState(30);
  const [numResources, setNumResources] = useState(40);
  const [seed, setSeed] = useState(67);

  const [scenarioMode, setScenarioMode] = useState("NORMAL");

  const [generatedScenario, setGeneratedScenario] = useState(null);

  const [generatedSolution, setGeneratedSolution] = useState(null);

  const [loading, setLoading] = useState(false);

  const [selectedDisruptionRequest, setSelectedDisruptionRequest] =
    useState("");

  const [activeDisruption, setActiveDisruption] =
    useState(null);

  const [preDisruptionSolution, setPreDisruptionSolution] =
    useState(null);

  const [recoveryDetails, setRecoveryDetails] = useState(null);

  async function generateNetwork() {
  setLoading(true);

  setGeneratedScenario(null);
  setGeneratedSolution(null);
  setMetrics(null);
  setSelectedDisruptionRequest("");
  setActiveDisruption(null);
  setPreDisruptionSolution(null);

  setMessage(
    "Generating and optimizing transportation network..."
  );

  try {

    // STEP 1: GENERATE NETWORK


    const generationResponse = await fetch(
      "http://127.0.0.1:8000/generate-scenario",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          region: region,
          num_patients: Number(numPatients),
          num_resources: Number(numResources),
          seed: Number(seed),
          scenario_mode: scenarioMode,
        }),
      }
    );

    if (!generationResponse.ok) {
      throw new Error(
        `Scenario generation failed: ${generationResponse.status}`
      );
    }

    const scenario =
      await generationResponse.json();

    setGeneratedScenario(scenario);


    // STEP 2: SEND GENERATED NETWORK TO OPTIMIZER


    const optimizationResponse = await fetch(
      "http://127.0.0.1:8000/optimize",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },

        body: JSON.stringify({
          requests: scenario.requests,
          resources: scenario.resources,
          current_time: scenario.current_time,
          pickup_travel_times:
            scenario.pickup_travel_times,
          patient_trip_times:
            scenario.patient_trip_times,
          transition_travel_times:
            scenario.transition_travel_times,

          current_assignment_states: [],
          events: [],
          reassignment_penalty: 30,
        }),
      }
    );

    if (!optimizationResponse.ok) {
      throw new Error(
        `Optimization failed: ${optimizationResponse.status}`
      );
    }

    const solution =
      await optimizationResponse.json();

    setGeneratedSolution(solution);

    setMetrics(solution.metrics);



    // STEP 3: UPDATE MESSAGE


    setMessage(
      `Generated and optimized ${scenario.summary.num_patients} patients and ${scenario.summary.num_resources} resources in ${scenario.region}.`
    );

  } catch (error) {

    console.error(error);

    setMessage(
      "Unable to generate or optimize transportation network."
    );

  } finally {

    setLoading(false);

  }
}

async function simulateVehicleBreakdown() {


  // SAFETY CHECKS


  if (
    !selectedDisruptionRequest ||
    !generatedScenario ||
    !generatedSolution
  ) {
    return;
  }


  const failedResourceId =
    generatedSolution.assignments?.[
      selectedDisruptionRequest
    ];


  if (!failedResourceId) {

    setMessage(
      "The selected patient does not currently have an assigned ride."
    );

    return;
  }


  const selectedPatient =
    generatedScenario.requests.find(
      (request) =>
        request.request_id ===
        selectedDisruptionRequest
    );



  // SAVE THE BEFORE STATE


  setPreDisruptionSolution(
    generatedSolution
  );


  setLoading(true);


  setMessage(
    `${failedResourceId} has broken down. Reoptimizing the transportation network...`
  );


  try {


    // MARK THE FAILED VEHICLE UNAVAILABLE


    const disruptedResources =
      generatedScenario.resources.map(
        (resource) => {

          if (
            resource.resource_id ===
            failedResourceId
          ) {

            return {
              ...resource,
              available: false,
            };

          }

          return resource;
        }
      );


// CONVERT CURRENT ASSIGNMENTS INTO CURRENT STATE
//
// This tells the optimizer what the network looked like
// immediately before the breakdown.


const currentAssignmentStates =
  Object.entries(
    generatedSolution.assignments || {}
  ).map(
    ([requestId, resourceId]) => ({
      request_id: requestId,
      resource_id: resourceId,
      status: "CONFIRMED",
    })
  );


    // CREATE BREAKDOWN EVENT


    const breakdownEvent = {
      event_type: "VEHICLE_BREAKDOWN",

      occurred_at:
        generatedScenario.current_time,

      request_id:
        selectedDisruptionRequest,

      resource_id:
        failedResourceId,
    };



    // SEND DISRUPTED NETWORK BACK TO OR-TOOLS


    const optimizationResponse =
      await fetch(
        "http://127.0.0.1:8000/optimize",
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json",
          },

          body: JSON.stringify({

            requests:
              generatedScenario.requests,

            resources:
              disruptedResources,

            current_time:
              generatedScenario.current_time,

            pickup_travel_times:
              generatedScenario.pickup_travel_times,

            patient_trip_times:
              generatedScenario.patient_trip_times,
            
            transition_travel_times:
              generatedScenario.transition_travel_times,

            current_assignment_states:
              currentAssignmentStates,

            events: [
              breakdownEvent,
            ],

            reassignment_penalty: 30,
          }),
        }
      );


    if (!optimizationResponse.ok) {

      throw new Error(
        `Recovery optimization failed: ${optimizationResponse.status}`
      );

    }


    const recoveredSolution =
      await optimizationResponse.json();



    // FIND WHAT HAPPENED TO THE AFFECTED PATIENT


    const replacementResourceId =
      recoveredSolution.assignments?.[
        selectedDisruptionRequest
      ] || null;



    // UPDATE FRONTEND NETWORK STATE


    setGeneratedScenario(
      (previousScenario) => ({
        ...previousScenario,
        resources:
          disruptedResources,
      })
    );


    setGeneratedSolution(
      recoveredSolution
    );


    setMetrics(
      recoveredSolution.metrics
    );


    setActiveDisruption({
      event_type:
        "VEHICLE_BREAKDOWN",

      request_id:
        selectedDisruptionRequest,

      patient_name:
        selectedPatient?.patient_name ||
        selectedDisruptionRequest,

      failed_resource_id:
        failedResourceId,

      replacement_resource_id:
        replacementResourceId,
    });



    // UPDATE STATUS MESSAGE


    if (replacementResourceId) {

      setMessage(
        `${failedResourceId} broke down. ${selectedPatient?.patient_name || selectedDisruptionRequest} was recovered with ${replacementResourceId}.`
      );

    } else {

      setMessage(
        `${failedResourceId} broke down. No feasible replacement was found for ${selectedPatient?.patient_name || selectedDisruptionRequest}.`
      );

    }

  } catch (error) {

    console.error(error);

    setMessage(
      "Unable to recover the transportation network after the vehicle breakdown."
    );

  } finally {

    setLoading(false);

  }
}

  return (
    <div className="app">

      <header>
        <div>
          <p className="eyebrow">
            Recovery Control Center
          </p>

          <h1>
            Medical Transportation Network
          </h1>

          <p className="subtitle">
            Real-time recovery optimization for critical
            medical transportation.
          </p>
        </div>
      </header>


      <section className="alert">
        {message}
      </section>

<section className="scenario-controls">

  <div>
    <label>Region</label>

    <select
      value={region}
      onChange={(e) =>
        setRegion(e.target.value)
      }
    >
      <option value="BOSTON">
        Boston
      </option>

      <option value="NYC">
        New York City
      </option>
    </select>
  </div>

<div>
  <label>Scenario Mode</label>

  <select
    value={scenarioMode}
    onChange={(e) =>
      setScenarioMode(e.target.value)
    }
  >
    <option value="NORMAL">
      Normal
    </option>

    <option value="STRESSED">
      Stressed
    </option>

    <option value="CRISIS">
      Crisis
    </option>
  </select>
</div>

  <div>
    <label>Patients</label>

    <input
      type="number"
      min="1"
      value={numPatients}
      onChange={(e) =>
        setNumPatients(e.target.value)
      }
    />
  </div>

  <div>
    <label>Resources</label>

    <input
      type="number"
      min="1"
      value={numResources}
      onChange={(e) =>
        setNumResources(e.target.value)
      }
    />
  </div>


  <div>
    <label>Seed</label>

    <input
      type="number"
      value={seed}
      onChange={(e) =>
        setSeed(e.target.value)
      }
    />
  </div>

  <button
    onClick={generateNetwork}
    disabled={loading}
  >
    Generate Network
  </button>

</section>

{generatedScenario && (
  <section className="generated-network">

    <div>
      <span>Region</span>
      <strong>
        {generatedScenario.region}
      </strong>
    </div>

    <div>
      <span>Patients</span>
      <strong>
        {generatedScenario.summary.num_patients}
      </strong>
    </div>

    <div>
      <span>Resources</span>
      <strong>
        {generatedScenario.summary.num_resources}
      </strong>
    </div>

    <div>
      <span>Seed</span>
      <strong>
        {generatedScenario.seed}
      </strong>
    </div>

    <div>
      <span>Mode</span>
      <strong>
        {generatedScenario.scenario_mode}
      </strong>
    </div>

  </section>
)}

{generatedScenario && generatedSolution && (
  <section className="disruption-panel">

    <div>
      <p className="eyebrow">
        Live Operations
      </p>

      <h2>
        Simulate Network Disruption
      </h2>

      <p>
        Select an active transportation assignment
        and inject a real-time operational failure.
      </p>
    </div>


    <div className="disruption-controls">

      <div>
        <label>
          Active Ride
        </label>

        <select
          value={selectedDisruptionRequest}
          onChange={(e) =>
            setSelectedDisruptionRequest(
              e.target.value
            )
          }
        >

          <option value="">
            Select an assigned patient
          </option>

          {Object.entries(
            generatedSolution.assignments || {}
          )
            .map(
              ([requestId, resourceId]) => {

                const patient =
                  generatedScenario.requests.find(
                    (request) =>
                      request.request_id ===
                      requestId
                  );

                return {
                  requestId,
                  resourceId,
                  patientName:
                    patient?.patient_name ||
                    requestId,
                };
              }
            )
            .sort(
              (a, b) =>
                a.patientName
                  .split(" ")
                  .slice(-1)[0]
                  .localeCompare(
                    b.patientName
                      .split(" ")
                      .slice(-1)[0]
                  )
            )
            .map(
              ({
                requestId,
                resourceId,
                patientName,
              }) => (

                <option
                  key={requestId}
                  value={requestId}
                >
                  {patientName}
                  {" — "}
                  {resourceId}
                </option>

              )
            )}

        </select>

      </div>


      <button
        type="button"

        onClick={
          simulateVehicleBreakdown
        }

        disabled={
          !selectedDisruptionRequest ||
          loading
        }
      >
        {loading
          ? "Reoptimizing..."
          : "Simulate Vehicle Breakdown"}
      </button>

    </div>

  </section>
)}

  {generatedScenario && generatedSolution && metrics && (
    <section className="metrics">

      <div className="metric-card">
        <span>Patients Served</span>

        <strong>
          {metrics.served_count}
          {" / "}
          {metrics.total_requests}
        </strong>
      </div>

      <div className="metric-card">
        <span>Service Rate</span>

        <strong>
          {Math.round(
            metrics.served_rate * 100
          )}
          %
        </strong>
      </div>

      <div className="metric-card">
        <span>Unserved</span>

        <strong>
          {metrics.unserved_count}
        </strong>
      </div>

    </section>
  )}

{generatedScenario && generatedSolution && (
  <NetworkMap
    scenario={generatedScenario}
    solution={generatedSolution}
    activeDisruption={activeDisruption}
    preDisruptionSolution={preDisruptionSolution}
  />
)}

{generatedScenario && generatedSolution && (
  <>
    {/* =====================================================
        PATIENTS REQUIRING ESCALATION
    ====================================================== */}

    <section className="escalation-section">

      <div className="section-heading">
        <div>
          <p className="eyebrow">
            Requires Attention
          </p>

          <h2>
            {generatedSolution.unserved_requests.length}
            {" "}
            patient
            {generatedSolution.unserved_requests.length === 1
              ? ""
              : "s"}
            {" "}
            require escalation
          </h2>
        </div>
      </div>


      {generatedSolution.unserved_requests.length === 0 ? (

        <div className="all-served-message">
          <strong>
            All generated patients have feasible transportation.
          </strong>

          <p>
            No dispatcher escalation is currently required.
          </p>
        </div>

      ) : (

        <div className="escalation-grid">

          {generatedSolution.unserved_requests.map(
            (requestId) => {

              const patient =
                generatedScenario.requests.find(
                  (request) =>
                    request.request_id === requestId
                );

              if (!patient) {
                return null;
              }


              const reasonMap =
                generatedSolution.infeasibility_reasons?.[
                  requestId
                ] || {};

              const failureSummary =
                summarizeFailureReasons(
                  reasonMap,
                  generatedScenario.resources,
                  generatedSolution.assignments,
                  generatedScenario.requests,
                  requestId
                );


              return (
                <article
                  className="escalation-card"
                  key={requestId}
                >

                  <div className="escalation-header">

                    <div>
                      <p className="alert-label">
                        Requires Escalation
                      </p>

                      <h3>
                        {patient.patient_name}
                      </h3>

                      <span className="patient-id">
                        {patient.patient_id}
                      </span>
                    </div>

                    <span className="escalation-badge">
                      NO FEASIBLE RECOVERY
                    </span>

                  </div>


                  <div className="patient-details">

                    <div>
                      <span>Target arrival</span>

                      <strong>
                        {new Date(
                          patient.target_arrival
                        ).toLocaleTimeString(
                          [],
                          {
                            hour: "numeric",
                            minute: "2-digit",
                          }
                        )}
                      </strong>
                    </div>


                    <div>
                      <span>Latest arrival</span>

                      <strong>
                        {new Date(
                          patient.latest_arrival
                        ).toLocaleTimeString(
                          [],
                          {
                            hour: "numeric",
                            minute: "2-digit",
                          }
                        )}
                      </strong>
                    </div>


                    <div>
                      <span>WAV required</span>

                      <strong>
                        {patient.requires_wav
                          ? "Yes"
                          : "No"}
                      </strong>
                    </div>


                    <div>
                      <span>Transfer assistance</span>

                      <strong>
                        {patient.transfer_assistance_required
                          ? "Yes"
                          : "No"}
                      </strong>
                    </div>

                  </div>


                    <div className="failure-reasons">

                      <p className="label">
                        Why recovery failed
                      </p>

                      <div className="failure-summary-grid">

                        {failureSummary.WAV_REQUIRED > 0 && (
                          <div className="failure-summary-item">
                            <strong>
                              {failureSummary.WAV_REQUIRED}
                            </strong>
                            <span>
                              resources were not WAV capable
                            </span>
                          </div>
                        )}

                        {failureSummary.ARRIVES_AFTER_DEADLINE > 0 && (
                          <div className="failure-summary-item">
                            <strong>
                              {failureSummary.ARRIVES_AFTER_DEADLINE}
                            </strong>
                            <span>
                              resources would arrive too late
                            </span>
                          </div>
                        )}

                        {failureSummary.CAREGIVER_NOT_APPROVED > 0 && (
                          <div className="failure-summary-item">
                            <strong>
                              {failureSummary.CAREGIVER_NOT_APPROVED}
                            </strong>
                            <span>
                              caregivers were not approved
                            </span>
                          </div>
                        )}

                        {failureSummary.RIDESHARE_NOT_ALLOWED > 0 && (
                          <div className="failure-summary-item">
                            <strong>
                              {failureSummary.RIDESHARE_NOT_ALLOWED}
                            </strong>
                            <span>
                              rideshares were not permitted
                            </span>
                          </div>
                        )}

                        {failureSummary.TRANSFER_ASSISTANCE_REQUIRED > 0 && (
                          <div className="failure-summary-item">
                            <strong>
                              {failureSummary.TRANSFER_ASSISTANCE_REQUIRED}
                            </strong>
                            <span>
                              resources lacked transfer assistance
                            </span>
                          </div>
                        )}

                        {failureSummary.RESOURCE_UNAVAILABLE > 0 && (
                          <div className="failure-summary-item">
                            <strong>
                              {failureSummary.RESOURCE_UNAVAILABLE}
                            </strong>
                            <span>
                              resources were unavailable
                            </span>
                          </div>
                        )}

                        {failureSummary.ALLOCATED_ELSEWHERE > 0 && (
                          <div className="failure-summary-item">
                            <strong>
                              {failureSummary.ALLOCATED_ELSEWHERE}
                            </strong>
                            <span>
                              feasible resources were allocated elsewhere
                            </span>
                          </div>
                        )}

                      </div>


                      <details className="resource-details">

                        <summary>
                          View all resource-level decisions
                        </summary>

                        <div className="resource-detail-list">

                          {generatedScenario.resources.map(
                            (resource) => {

                              const reasons =
                                reasonMap[
                                  resource.resource_id
                                ] || [];

                              const assignedRequestId =
                                Object.entries(
                                  generatedSolution.assignments || {}
                                ).find(
                                  ([, assignedResource]) =>
                                    assignedResource ===
                                    resource.resource_id
                                )?.[0];

                              const assignedPatient =
                                generatedScenario.requests.find(
                                  (request) =>
                                    request.request_id ===
                                    assignedRequestId
                                );

                              let explanation;

                              if (reasons.length > 0) {

                                explanation =
                                  reasons
                                    .map(formatReason)
                                    .join(", ");

                              } else if (
                                assignedRequestId &&
                                assignedRequestId !== requestId
                              ) {

                                explanation =
                                  `Feasible, but allocated to ${
                                    assignedPatient?.patient_name ||
                                    assignedRequestId
                                  }`;

                              } else {

                                explanation =
                                  "Feasible resource, but not selected";
                              }

                              return (
                                <div
                                  className="resource-reason"
                                  key={resource.resource_id}
                                >

                                  <div>
                                    <strong>
                                      {resource.resource_id}
                                    </strong>

                                    <span>
                                      {resource.resource_type}
                                    </span>
                                  </div>

                                  <p>
                                    {explanation}
                                  </p>

                                </div>
                              );
                            }
                          )}

                        </div>

                      </details>

                    </div>

                </article>
              );
            }
          )}

        </div>

      )}

    </section>


    {/* =====================================================
        SUCCESSFUL PATIENTS
    ====================================================== */}

    <details className="served-patients">

      <summary>
        View successful assignments (
        {generatedSolution.metrics.served_count}
        )
      </summary>


      <div className="served-grid">

        {generatedScenario.requests
          .filter(
            (patient) =>
              !generatedSolution.unserved_requests.includes(
                patient.request_id
              )
          )
          .map((patient) => {

            const assignedResourceId =
              generatedSolution.assignments?.[
                patient.request_id
              ];


            const resource =
              generatedScenario.resources.find(
                (item) =>
                  item.resource_id ===
                  assignedResourceId
              );


            return (
              <article
                className="served-card"
                key={patient.request_id}
              >

                <div>
                  <h3>
                    {patient.patient_name}
                  </h3>

                  <span>
                    {patient.patient_id}
                  </span>
                </div>


                <div className="served-assignment">

                  <span>Assigned transportation</span>

                  <strong>
                    {assignedResourceId || "Unknown"}
                  </strong>

                  <small>
                    {resource?.resource_type || ""}
                  </small>

                </div>


                {patient.requires_wav && (
                  <span className="requirement-tag">
                    WAV Required
                  </span>
                )}

              </article>
            );
          })}

      </div>

    </details>

  </>
)}


{recoveryDetails && (
  <section className="decision-panel">

    <div className="decision-column">
      <p className="label">
        Event Detected
      </p>

      <h3>Traffic Delay</h3>

      <p>
        Margaret's Uber Assist route experienced
        a 12-minute delay.
      </p>
    </div>


    <div className="decision-column">
      <p className="label">
        Why Recovery Was Needed
      </p>

      <div className="reason-row">
        <span>Uber Assist</span>

        <strong>
          {recoveryDetails.reasons[
            "UBER-ASSIST-01"
          ]?.includes("ARRIVES_AFTER_DEADLINE")
            ? "Arrives after deadline"
            : "Feasible"}
        </strong>
      </div>

      <div className="reason-row">
        <span>Caregiver 1</span>

        <strong>
          {recoveryDetails.reasons[
            "CAREGIVER-01"
          ]?.length
            ? recoveryDetails.reasons[
                "CAREGIVER-01"
              ].join(", ")
            : "Feasible"}
        </strong>
      </div>
    </div>


    <div className="decision-column">
      <p className="label">
        Recovery Decision
      </p>

      <h3>
        Uber Assist → Caregiver 1
      </h3>

      <p>
        Sarah keeps the scarce NEMT WAV.
        John's existing ride remains unchanged.
      </p>
    </div>

  </section>
)}


</div>
  );
}

export default App;
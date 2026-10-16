

import { useState } from "react";

import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Polyline,
} from "react-leaflet";

import "leaflet/dist/leaflet.css";

import { divIcon } from "leaflet";

function createMapIcon({
  symbol,
  background,
  size = 34,
  border = "#ffffff",
  statusSymbol = null,
  statusBackground = "#111827",
  opacity = 1,
}) {

  const statusBadge =
    statusSymbol
      ? `
        <span
          class="map-icon-status"
          style="background: ${statusBackground};"
        >
          ${statusSymbol}
        </span>
      `
      : "";


  return divIcon({
    className: "custom-map-icon-wrapper",

    html: `
      <div
        class="map-icon-badge"
        style="
          --marker-background: ${background};
          --marker-border: ${border};
          --marker-size: ${size}px;
          --marker-opacity: ${opacity};
        "
      >
        <span class="map-icon-symbol">
          ${symbol}
        </span>

        ${statusBadge}
      </div>
    `,

    iconSize: [
      size,
      size,
    ],

    iconAnchor: [
      size / 2,
      size / 2,
    ],

    popupAnchor: [
      0,
      -(size / 2 + 8),
    ],
  });
}

function getResourceDisplayName(resource) {

  const resourceNumber =
    resource.resource_id
      ?.replace("RESOURCE-", "") || "";

  if (resource.resource_type === "NEMT") {
    return `NEMT Vehicle ${resourceNumber}`;
  }

  if (resource.resource_type === "RIDESHARE") {
    return `Rideshare ${resourceNumber}`;
  }

  if (resource.resource_type === "CAREGIVER") {
    return `Caregiver ${resourceNumber}`;
  }

  return resource.resource_id;
}

function formatReason(reason) {
  const labels = {
    RESOURCE_UNAVAILABLE:
      "Resource unavailable",

    DRIVER_DECLINED:
      "Driver declined this patient",

    RIDESHARE_NOT_ALLOWED:
      "Patient does not allow rideshare",

    CAREGIVER_NOT_APPROVED:
      "Caregiver not approved for this patient",

    WAV_REQUIRED:
      "Wheelchair-accessible vehicle required",

    FOLDING_WHEELCHAIR_STORAGE_REQUIRED:
      "Folding wheelchair storage required",

    TRANSFER_ASSISTANCE_REQUIRED:
      "Transfer assistance required",

    ARRIVES_AFTER_DEADLINE:
      "Would arrive after the patient's deadline",
  };

  return labels[reason] || reason;
}

function NetworkMap({
  scenario,
  solution,
  activeDisruption,
  preDisruptionSolution,
}) {
  const [selectedRequestId, setSelectedRequestId] =
    useState(null);


  if (!scenario || !solution) {
    return null;
  }


  // ========================================================
  // UNSERVED PATIENTS
  // ========================================================

  const unservedPatients = new Set(
    solution.unserved_requests || []
  );

  const resourceRoutes =
    solution.resource_routes || {};

  // ========================================================
  // MAP CENTER
  // ========================================================

  const mapCenter =
    scenario.region === "NYC"
      ? [40.758, -73.9855]
      : [42.3601, -71.0589];


  // ========================================================
  // SUCCESSFUL ASSIGNMENT PATHS
  // ========================================================

const assignmentPaths = scenario.requests
  .map((patient) => {

    const resourceId =
      solution.assignments?.[
        patient.request_id
      ];

    if (!resourceId) {
      return null;
    }


    const resource =
      scenario.resources.find(
        (item) =>
          item.resource_id === resourceId
      );

    if (!resource) {
      return null;
    }


    // ====================================================
    // DETERMINE THIS PATIENT'S POSITION IN THE
    // RESOURCE'S ORDERED ROUTE
    // ====================================================

    const route =
      resourceRoutes[
        resourceId
      ] || [
        patient.request_id
      ];


    const routeIndex =
      route.indexOf(
        patient.request_id
      );


    const routeLength =
      route.length;


    const previousRouteRequestId =
      routeIndex > 0
        ? route[
            routeIndex - 1
          ]
        : null;


    const previousRoutePatient =
      previousRouteRequestId
        ? scenario.requests.find(
            (request) =>
              request.request_id ===
              previousRouteRequestId
          )
        : null;


    const isSequentialFollowOn =
      Boolean(
        previousRoutePatient
      );


    // ====================================================
    // DISRUPTION / RECOVERY STATE
    // ====================================================

      const previousResourceId =
        preDisruptionSolution?.assignments?.[
          patient.request_id
        ] || null;


      const previousResource =
        scenario.resources.find(
          (item) =>
            item.resource_id ===
            previousResourceId
        );


      const assignmentChangedAfterDisruption =
        Boolean(
          activeDisruption &&
          previousResourceId &&
          resourceId &&
          previousResourceId !== resourceId
        );


      const directlyRecoveredAfterDisruption =
        Boolean(
          assignmentChangedAfterDisruption &&
          patient.request_id ===
            activeDisruption?.request_id
        );


      const reassignedForNetworkRecovery =
        Boolean(
          assignmentChangedAfterDisruption &&
          patient.request_id !==
            activeDisruption?.request_id
        );


      // ====================================================
      // BUILD THE ACTUAL PHYSICAL ROUTE
      //
      // FIRST PATIENT:
      //
      // resource start
      // → patient pickup
      // → dialysis
      //
      // FOLLOW-ON PATIENT:
      //
      // previous dialysis
      // → next patient pickup
      // → next dialysis
      // ====================================================

      const positions =
        isSequentialFollowOn
          ? [
              [
                previousRoutePatient.destination_lat,
                previousRoutePatient.destination_lon,
              ],

              [
                patient.pickup_lat,
                patient.pickup_lon,
              ],

              [
                patient.destination_lat,
                patient.destination_lon,
              ],
            ]
          : [
              [
                resource.current_lat,
                resource.current_lon,
              ],

              [
                patient.pickup_lat,
                patient.pickup_lon,
              ],

              [
                patient.destination_lat,
                patient.destination_lon,
              ],
            ];


      return {

        requestId:
          patient.request_id,

        patientName:
          patient.patient_name,

        resourceId:
          resource.resource_id,

        resourceName:
          getResourceDisplayName(
            resource
          ),

        routeIndex,

        routeLength,

        isSequentialFollowOn,

        previousRoutePatientName:
          previousRoutePatient?.patient_name ||
          null,

        previousResourceId,

        previousResourceName:
          previousResource
            ? getResourceDisplayName(
                previousResource
              )
            : previousResourceId,

        directlyRecoveredAfterDisruption,

        reassignedForNetworkRecovery,

        positions,
      };

    })
    .filter(Boolean);


  // ========================================================
  // SELECTED FAILED PATIENT
  // ========================================================

  const selectedReasonMap =
    selectedRequestId
      ? solution.infeasibility_reasons?.[
          selectedRequestId
        ] || {}
      : {};


  const resourceAssignments =
    Object.entries(
      solution.assignments || {}
    );

const selectedPatient =
  scenario.requests.find(
    (patient) =>
      patient.request_id === selectedRequestId
  );

const allAnalysisPaths =
  selectedPatient
    ? scenario.resources.map((resource) => {

        const reasons =
          selectedReasonMap[
            resource.resource_id
          ] || [];

        const assignedRequestId =
          resourceAssignments.find(
            ([, resourceId]) =>
              resourceId ===
              resource.resource_id
          )?.[0];

        const pickupMinutes =
          scenario.pickup_travel_times?.[
            selectedRequestId
          ]?.[
            resource.resource_id
          ] ?? Infinity;


        let status = "FEASIBLE";
        let color = "#16a34a";
        let opacity = 0.9;
        let weight = 4;
        let dashArray = null;


        if (reasons.length > 0) {

          status = "INCOMPATIBLE";
          color = "#dc2626";
          opacity = 0.18;
          weight = 2;
          dashArray = "5 8";

        } else if (
          assignedRequestId &&
          assignedRequestId !==
            selectedRequestId
        ) {

          status = "ALLOCATED";
          color = "#f59e0b";
          opacity = 0.75;
          weight = 3;
          dashArray = "8 6";

        }


        return {
          resourceId:
            resource.resource_id,

          status,

          pickupMinutes,

          color,

          opacity,

          weight,

          dashArray,

          positions: [
            [
              resource.current_lat,
              resource.current_lon,
            ],

            [
              selectedPatient.pickup_lat,
              selectedPatient.pickup_lon,
            ],
          ],
        };
      })
    : [];


const analysisCounts = {
  feasible: allAnalysisPaths.filter(
    (path) => path.status === "FEASIBLE"
  ).length,

  allocated: allAnalysisPaths.filter(
    (path) => path.status === "ALLOCATED"
  ).length,

  incompatible: allAnalysisPaths.filter(
    (path) => path.status === "INCOMPATIBLE"
  ).length,
};


let primaryBottleneck = "";

if (selectedPatient) {

  if (
    analysisCounts.feasible === 0 &&
    analysisCounts.allocated > 0
  ) {
    primaryBottleneck =
      "Compatible transportation capacity is already committed.";
  }

  else if (
    analysisCounts.feasible === 0 &&
    analysisCounts.allocated === 0
  ) {
    primaryBottleneck =
      "No currently feasible transportation resource exists.";
  }

  else {
    primaryBottleneck =
      "Feasible transportation remains available.";
  }

}

const analysisPaths = [

  ...allAnalysisPaths
    .filter(
      (path) =>
        path.status === "FEASIBLE"
    )
    .sort(
      (a, b) =>
        a.pickupMinutes -
        b.pickupMinutes
    )
    .slice(0, 3),

  ...allAnalysisPaths
    .filter(
      (path) =>
        path.status === "ALLOCATED"
    )
    .sort(
      (a, b) =>
        a.pickupMinutes -
        b.pickupMinutes
    )
    .slice(0, 5),

  ...allAnalysisPaths
    .filter(
      (path) =>
        path.status === "INCOMPATIBLE"
    )
    .sort(
      (a, b) =>
        a.pickupMinutes -
        b.pickupMinutes
    )
    .slice(0, 3),

];

  return (
    <section className="network-map-section">

      <div className="network-map-header">

        <p className="eyebrow">
          Network View
        </p>

        <h2>
          {scenario.region} Transportation Network
        </h2>

        <p>
          Generated patient pickup locations
        </p>

       {!selectedRequestId && (

  <div className="map-legend">

    <div className="map-legend-item">
      <span className="legend-map-icon legend-patient-assigned">
        👤
        <small>✓</small>
      </span>

      <span>
        Patient — transportation assigned
      </span>
    </div>


    <div className="map-legend-item">
      <span className="legend-map-icon legend-patient-alert">
        !
      </span>

      <span>
        Patient — requires escalation
      </span>
    </div>


    <div className="map-legend-item">
      <span className="legend-map-icon legend-patient-recovered">
        ♥
      </span>

      <span>
        Patient successfully recovered
      </span>
    </div>

    <div className="map-legend-item">

    <span className="legend-map-icon legend-patient-reassigned">
        ↻
    </span>

    <span>
        Patient reassigned to support network recovery
    </span>

    </div>

    <div className="map-legend-item">
      <span className="legend-map-icon legend-nemt-icon">
        🚐
      </span>

      <span>
        NEMT vehicle
      </span>
    </div>


    <div className="map-legend-item">
      <span className="legend-map-icon legend-rideshare-icon">
        🚗
      </span>

      <span>
        Rideshare
      </span>
    </div>


    <div className="map-legend-item">
      <span className="legend-map-icon legend-caregiver-icon">
        🤲
      </span>

      <span>
        Approved caregiver
      </span>
    </div>


    <div className="map-legend-item">
      <span className="legend-map-icon legend-unavailable-icon">
        ×
      </span>

      <span>
        Unavailable resource
      </span>
    </div>


    <div className="map-legend-item">
      <span className="legend-map-icon legend-facility-icon">
        🏥
      </span>

      <span>
        Dialysis facility
      </span>
    </div>


    <div className="map-legend-item">

      <span className="legend-line" />

      <span>
        Optimized assignment
      </span>

    </div>

<div className="map-legend-item">

  <span
    style={{
      display: "inline-block",
      width: "28px",
      borderTop:
        "3px dashed #0f766e",
    }}
  />

  <span>
    Sequential vehicle reuse
  </span>

</div>

  </div>

)}

        {selectedRequestId && selectedPatient && (
        <div className="failure-analysis-panel">

            <div>
            <strong>
                Failure Analysis: {selectedPatient.patient_name}
            </strong>

            <span>
                {selectedPatient.patient_id}
            </span>
            </div>

            <div className="analysis-summary">

            <span>
                <strong>
                {analysisCounts.feasible}
                </strong>
                {" "}
                immediately feasible
            </span>

            <span>
                <strong>
                {analysisCounts.allocated}
                </strong>
                {" "}
                feasible but allocated
            </span>

            <span>
                <strong>
                {analysisCounts.incompatible}
                </strong>
                {" "}
                incompatible
            </span>

            <p>
                <strong>
                Primary bottleneck:
                </strong>
                {" "}
                {primaryBottleneck}
            </p>

            </div>

            <div className="analysis-legend">

            <span>
                <i className="analysis-dot incompatible-dot" />
                Cannot serve
            </span>

            <span>
                <i className="analysis-dot allocated-dot" />
                Feasible but allocated
            </span>

            <span>
                <i className="analysis-dot feasible-dot" />
                Feasible
            </span>

            </div>

            <button
            type="button"
            className="exit-analysis-button"
            onClick={() =>
                setSelectedRequestId(null)
            }
            >
            Exit Analysis
            </button>

        </div>
        )}

      </div>


      <MapContainer
        center={mapCenter}
        zoom={11}
        style={{
          height: "500px",
          width: "100%",
          borderRadius: "12px",
        }}
      >

        <TileLayer
          attribution="&copy; OpenStreetMap contributors"
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />


        {/* ====================================================
            OPTIMIZED ASSIGNMENT PATHS
            ==================================================== */}

        {assignmentPaths.map((path) => (

          <Polyline
            key={path.requestId}
            positions={path.positions}
            pathOptions={{
              color:
                path.directlyRecoveredAfterDisruption
                  ? "#db2777"
                  : path.reassignedForNetworkRecovery
                    ? "#2563eb"
                    : path.isSequentialFollowOn
                      ? "#0f766e"
                      : "#64748b",

              weight:
                path.directlyRecoveredAfterDisruption
                  ? 6
                  : path.reassignedForNetworkRecovery
                    ? 4
                    : path.isSequentialFollowOn
                      ? 3
                      : 2,

              opacity:
                selectedRequestId
                  ? 0.08
                  : path.directlyRecoveredAfterDisruption
                    ? 1
                    : path.reassignedForNetworkRecovery
                      ? 0.9
                      : path.isSequentialFollowOn
                        ? 0.85
                        : 0.55,

              dashArray:
                path.directlyRecoveredAfterDisruption
                  ? "12 7"
                  : path.reassignedForNetworkRecovery
                    ? "4 6"
                    : path.isSequentialFollowOn
                      ? "10 6"
                      : null,
            }}
          >

            <Popup>

            <strong>
                {path.patientName}
            </strong>

            <br />
            <br />

            {path.directlyRecoveredAfterDisruption && (
            <>

                <strong>
                RECOVERED AFTER DISRUPTION
                </strong>

                <br />

                Previous transportation:{" "}
                {path.previousResourceName}

                <br />

            </>
            )}


            {path.reassignedForNetworkRecovery && (
            <>

                <strong>
                REASSIGNED TO SUPPORT NETWORK RECOVERY
                </strong>

                <br />

                Previous transportation:{" "}
                {path.previousResourceName}

                <br />

            </>
            )}

            Assigned transportation:{" "}
            {path.resourceName}

            {path.routeLength > 1 && (
              <>
                <br />
                <br />

                <strong>
                  Sequential vehicle route
                </strong>

                <br />

                Stop{" "}
                {path.routeIndex + 1}
                {" "}of{" "}
                {path.routeLength}

                {path.isSequentialFollowOn &&
                  path.previousRoutePatientName && (
                    <>
                      <br />

                      Previous stop:{" "}
                      {
                        path.previousRoutePatientName
                      }
                    </>
                  )}
              </>
            )}

            </Popup>

          </Polyline>

        ))}

        {/* ====================================================
                SELECTED PATIENT RESOURCE ANALYSIS
            ==================================================== */}

            {analysisPaths.map((path) => (

            <Polyline
                key={`analysis-${path.resourceId}`}

                positions={path.positions}

                pathOptions={{
                color: path.color,
                opacity: path.opacity,
                weight: path.weight,
                dashArray: path.dashArray,
                }}
            >

                <Popup>

                <strong>
                    {path.resourceId}
                </strong>

                <br />

                {path.status === "INCOMPATIBLE"
                    ? "Cannot serve selected patient"
                    : path.status === "ALLOCATED"
                    ? "Feasible, but allocated elsewhere"
                    : "Feasible for selected patient"}

                </Popup>

            </Polyline>

            ))}

        {/* ====================================================
            PATIENTS
            ==================================================== */}

{scenario.requests.map((patient) => {

  const unserved =
    unservedPatients.has(
      patient.request_id
    );


  const isSelected =
    patient.request_id ===
    selectedRequestId;


  const shouldDim =
    selectedRequestId &&
    !isSelected;


  const previousResourceId =
    preDisruptionSolution?.assignments?.[
      patient.request_id
    ] || null;


  const currentResourceId =
    solution.assignments?.[
      patient.request_id
    ] || null;


const assignmentChangedAfterDisruption =
  Boolean(
    activeDisruption &&
    previousResourceId &&
    currentResourceId &&
    previousResourceId !==
      currentResourceId
  );


const directlyRecoveredAfterDisruption =
  Boolean(
    assignmentChangedAfterDisruption &&
    patient.request_id ===
      activeDisruption?.request_id
  );


const reassignedForNetworkRecovery =
  Boolean(
    assignmentChangedAfterDisruption &&
    patient.request_id !==
      activeDisruption?.request_id
  );


  let patientIcon;


  // ----------------------------------------------------
  // PATIENT REQUIRES ESCALATION
  // ----------------------------------------------------

  if (unserved) {

    patientIcon = createMapIcon({
      symbol: "!",
      background: "#dc2626",
      size: isSelected
        ? 42
        : 36,
      opacity: shouldDim
        ? 0.2
        : 1,
    });

  }


// ----------------------------------------------------
// DIRECTLY DISRUPTED PATIENT WAS RECOVERED
// ----------------------------------------------------

else if (
  directlyRecoveredAfterDisruption
) {

  patientIcon = createMapIcon({
    symbol: "♥",
    background: "#db2777",
    size: 38,

    opacity: shouldDim
      ? 0.2
      : 1,
  });

}


// ----------------------------------------------------
// PATIENT REASSIGNED TO SUPPORT NETWORK RECOVERY
// ----------------------------------------------------

else if (
  reassignedForNetworkRecovery
) {

  patientIcon = createMapIcon({
    symbol: "↻",
    background: "#2563eb",
    size: 36,

    opacity: shouldDim
      ? 0.2
      : 1,
  });

}


// ----------------------------------------------------
// PATIENT HAS NORMAL TRANSPORTATION
// ----------------------------------------------------

else {

  patientIcon = createMapIcon({
    symbol: "👤",
    background: "#16a34a",
    size: 34,

    statusSymbol: "✓",
    statusBackground: "#166534",

    opacity: shouldDim
      ? 0.2
      : 1,
  });

}


  return (

    <Marker
      key={patient.request_id}

      position={[
        patient.pickup_lat,
        patient.pickup_lon,
      ]}

      icon={patientIcon}

        zIndexOffset={
        isSelected ||
        directlyRecoveredAfterDisruption ||
        reassignedForNetworkRecovery
            ? 1000
            : 0
        }

      eventHandlers={{
        click: () => {

          if (unserved) {

            setSelectedRequestId(
              patient.request_id
            );

          }

        },
      }}
    >

      <Popup>

        <strong>
          {patient.patient_name}
        </strong>

        <br />

        {patient.patient_id}

        <br />
        <br />

        WAV required:{" "}
        {patient.requires_wav
          ? "Yes"
          : "No"}

        <br />

        Transfer assistance:{" "}
        {patient.transfer_assistance_required
          ? "Yes"
          : "No"}

        <br />
        <br />


    {unserved ? (

    <strong>
        NO FEASIBLE RECOVERY
    </strong>

    ) : directlyRecoveredAfterDisruption ? (

    <>

        <strong>
        RECOVERED AFTER DISRUPTION
        </strong>

        <br />
        <br />

        Previous ride:{" "}
        {previousResourceId}

        <br />

        Replacement ride:{" "}
        {currentResourceId}

    </>

    ) : reassignedForNetworkRecovery ? (

    <>

        <strong>
        REASSIGNED TO SUPPORT NETWORK RECOVERY
        </strong>

        <br />
        <br />

        Previous ride:{" "}
        {previousResourceId}

        <br />

        New ride:{" "}
        {currentResourceId}

    </>

    ) : (

    <strong>
        Transportation assigned
    </strong>

    )}

      </Popup>

    </Marker>

  );
})}

        {/* ====================================================
            TRANSPORTATION RESOURCES
            ==================================================== */}

{scenario.resources.map((resource) => {

  const reasons =
    selectedReasonMap[
      resource.resource_id
    ] || [];


  const assignedRequestId =
    resourceAssignments.find(
      ([, resourceId]) =>
        resourceId ===
        resource.resource_id
    )?.[0];


  const assignedRoute =
    resourceRoutes[
      resource.resource_id
    ] || [];


  const assignedPatients =
    assignedRoute
      .map(
        (requestId) =>
          scenario.requests.find(
            (request) =>
              request.request_id ===
              requestId
          )
      )
      .filter(Boolean);


  const allocatedElsewhere =
    selectedRequestId &&
    reasons.length === 0 &&
    assignedRequestId &&
    assignedRequestId !==
      selectedRequestId;


  const feasibleForSelected =
    selectedRequestId &&
    reasons.length === 0 &&
    !allocatedElsewhere;


  // ==================================================
  // RESOURCE TYPE ICON
  // ==================================================

  let resourceSymbol = "🚐";
  let resourceBackground = "#0f766e";


  if (
    resource.resource_type ===
    "RIDESHARE"
  ) {

    resourceSymbol = "🚗";
    resourceBackground = "#f59e0b";

  }


  else if (
    resource.resource_type ===
    "CAREGIVER"
  ) {

    resourceSymbol = "🤲";
    resourceBackground = "#7c3aed";

  }


  // ==================================================
  // RESOURCE STATUS BADGE
  // ==================================================

  let statusSymbol = null;
  let statusBackground = "#111827";


  // Unavailable resource
  if (!resource.available) {

    resourceBackground = "#64748b";

    statusSymbol = "×";

    statusBackground = "#991b1b";

  }


  // --------------------------------------------------
  // FAILURE ANALYSIS MODE
  // --------------------------------------------------

  if (selectedRequestId) {

    if (reasons.length > 0) {

      statusSymbol = "×";

      statusBackground = "#dc2626";

    }

    else if (allocatedElsewhere) {

      statusSymbol = "•";

      statusBackground = "#f59e0b";

    }

    else if (feasibleForSelected) {

      statusSymbol = "✓";

      statusBackground = "#16a34a";

    }

  }


  const resourceIcon =
    createMapIcon({
      symbol:
        resourceSymbol,

      background:
        resourceBackground,

      size: 36,

      statusSymbol,

      statusBackground,
    });


  return (

    <Marker
      key={resource.resource_id}

      position={[
        resource.current_lat,
        resource.current_lon,
      ]}

      icon={resourceIcon}
    >

      <Popup>

        <strong>
          {getResourceDisplayName(
            resource
          )}
        </strong>

        <br />

        <span>
          {resource.resource_id}
        </span>

        <br />
        <br />

    <strong>
      Assigned route:
    </strong>

    <br />

    {assignedPatients.length > 0 ? (

      assignedPatients.map(
        (assignedPatient, index) => (

          <div
            key={
              assignedPatient.request_id
            }
          >

            <strong>
              {index + 1}.{" "}
              {
                assignedPatient.patient_name
              }
            </strong>

          </div>

        )
      )

    ) : (

      <strong>
        None
      </strong>

    )}

    {assignedPatients.length > 1 && (
      <>
        <br />

        <strong>
          Sequential reuse: Yes
        </strong>
      </>
    )}

    <br />
    <br />

        Available:{" "}
        {resource.available
          ? "Yes"
          : "No"}

        <br />

        WAV capable:{" "}
        {resource.wav_capable
          ? "Yes"
          : "No"}

        <br />

        Transfer assistance:{" "}
        {resource.transfer_assistance_capable
          ? "Yes"
          : "No"}


        {selectedRequestId && (

          <>

            <br />
            <br />


            {reasons.length > 0 ? (

              <>

                <strong>
                  Cannot serve selected patient
                </strong>

                <br />

                {reasons
                  .map(formatReason)
                  .join(", ")}

              </>

            ) : allocatedElsewhere ? (

              <strong>
                Feasible, but allocated to another patient
              </strong>

            ) : (

              <strong>
                Feasible for selected patient
              </strong>

            )}

          </>

        )}

      </Popup>

    </Marker>

  );
})}

        {/* ====================================================
            DIALYSIS CENTERS
        ==================================================== */}

    {(scenario.dialysis_centers || []).map(
        (center) => {

            const facilityIcon =
            createMapIcon({
                symbol: "🏥",
                background: "#5b21b6",
                size: 42,
            });


            return (

            <Marker
                key={center.name}

                position={[
                center.lat,
                center.lon,
                ]}

                icon={facilityIcon}

                zIndexOffset={500}
            >

                <Popup>

                <strong>
                    {center.name}
                </strong>

                <br />
                <br />

                {center.address}

                <br />
                <br />

                <strong>
                    Dialysis Facility
                </strong>

                </Popup>

            </Marker>

            );
        }
        )}

      </MapContainer>

    </section>
  );
}


export default NetworkMap;
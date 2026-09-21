# eVTOL Flight Simulator — Senior Design 2025

A Python-based flight simulation environment integrating a custom graphical interface, JSBSim-based physics, and a modular architecture designed to support hybrid AI-copilot development.

---

## Overview

This project provides a lightweight but extensible simulation framework developed for the AEM Senior Design program at the University of Minnesota. The system is structured to support:

- eVTOL flight dynamics simulation using JSBSim
- Evaluation of human–machine interface concepts
- Prototyping and testing of AI-assisted pilot support tools
- General research involving new flight-control or autonomy concepts

The implementation uses Python, PyQt6, and JSBSim, with an emphasis on clean separation of concerns between physics, UI, and shared state management.

---



## System Architecture

```text
/FlightSim
│
├── run_sim.py                # Entry point
│
├── simcore/                  # Simulation backend
│   ├── physics_engine.py     # JSBSim wrapper (initialization, loading, stepping)
│   ├── simulation_core.py    # Main simulation loop (fixed-step physics)
│   ├── shared_state.py       # Thread-safe global state container
│   ├── user_input.py         # Maps UI inputs to JSBSim control properties
│   ├── state_json.py         # Converts JSBSim state to structured JSON
│   └── __init__.py
│
└── ui/                       # PyQt6 application
    ├── main_window.py        # Assembles UI layout and connects callbacks
    ├── ui_update_loop.py     # Periodic refresh of UI from shared state
    ├── widgets.py            # Custom flight instruments and controls
    └── __init__.py
```

---



# Simulation Logic Flow



## Initialization (`run_sim.py`)

- Loads configuration and aircraft model
- Creates shared state
- Launches:
  - **Simulation Core Thread**
  - **PyQt6 Graphical Interface**

These subsystems run concurrently and communicate via a global, thread-safe `SharedState` object.

---



## Physics Engine (`simcore/physics_engine.py`)

The physics engine is powered by **JSBSim**, an open-source, high-fidelity flight dynamics model.

### Responsibilities:

- Initialize FDMExec
- Load the eVTOL aircraft XML definition
- Bind JSBSim properties (orientation, position, rates, thrust, etc.)
- Apply control inputs from the UI
- Run the simulation at a fixed timestep
- Output updated state to `SharedState`



### Core Loop:

1. Read pilot inputs via `user_input.py`
2. Apply throttle/rotor/cyclic commands to JSBSim
3. Execute `Step()`
4. Store updated state

---



## Simulation Core (`simcore/simulation_core.py`)

Runs at a fixed frequency (e.g., 100 Hz), independent of the UI.

### Responsibilities:

- Coordinate physics updates
- Maintain stable timing
- Package important flight variables via `state_json.py`
- Update shared state for UI access

This ensures that rendering speed never interferes with physics update stability.

---



## Shared Global State (`simcore/shared_state.py`)

A thread-safe object used for:

- Publishing physics results → UI
- Receiving user inputs → physics
- Preventing race conditions between threads



### Features:

- Atomic updates
- Non-blocking reads for UI
- Safe expansion for future AI modules

---



## User Input Mapping (`simcore/user_input.py`)

This file inputs pilot commands into JSBSim. [More info](FlightSim/simcore/ReadMe.md)

---



## State Encoding (`simcore/state_json.py`)

Converts raw JSBSim property values into a structured dictionary for UI consumption.

---



## Graphical User Interface (`ui/`)



### Built using:

- **PyQt6**
- Custom flight gauges and tapes



### `main_window.py`

- Builds panels, gauges, and flight instruments
- Connects UI events → SharedState



### `ui_update_loop.py`

Runs a QTimer:

1. Pulls latest JSON flight state
2. Refreshes widgets smoothly
3. Handles interpolation and filtering



### `widgets.py`

Contains:

- Attitude indicator
- Speed and altitude tapes
- [Map](FlightSim/ui/Map/ReadMe.md)
- [SyntheticVision](FlightSim/ui/SyntheticVision/ReadMe.md)
- Gauges
- and more

---



# Running the Simulator



## Install Python:

Install [Python 3.12.10](https://www.python.org/downloads/), check add to path.  
It may be necessary to restart your computer after this.

## Install Requirements:

```bash
pip install -r requirements.txt
```



## Visual Studio Code

With VSCode or another IDE, install Python extension.

In VSCode, open the folder `/Flightsim/` Do not open `/AcronAEMSeniorDesign/` unless editing the ReadMe or Requirements, the program will not run from this folder.

## Run:

```bash
python FlightSim/run_sim.py
```

---



## License

...

---




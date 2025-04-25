# TRANSIT

## Introduction

**Tr**affic **An**omaly **Si**mulation **T**ool (TRANSIT) is a simulation tool which aims to generate cross-scale unified, reproducible, and controllable urban road traffic anomaly scenarios, with detailed multimodal traffic anomlay simulation datasets. TRANSIT can be used in vaious urban road network scenarios, including real-world road networks, and supports diverse types of traffic anomalies.

## Installation

* TRANSIT is developed based on SUMO—a widely used, open source traffic simulation tool. SUMO environment should be prepared firstly, you can follow the instruction of the following page:
  [Downloads - SUMO Documentation
  ](https://sumo.dlr.de/docs/Downloads.php)Please note that TRANSIT utilizes the system variable SUMO_HOME to call SUMO, therefore the **SUMO_HOME** must be set to the correct SUMO installation path. You can follow the instructions to add the system variable:
  [Computer Skills - SUMO Documentation
  ](https://sumo.dlr.de/docs/Basics/Basic_Computer_Skills.html#sumo_home)
* TRANSIT is a python program, python>=3.8 environment should be installed. You can download python or using Anaconda is recommended.
  [Download Python | Python.org](https://www.python.org/downloads/)
  [Download Anaconda Distribution | Anaconda](https://www.anaconda.com/download)
* Packages like traci, numpy should be installed, which are listed in *requirements.txt .* You can install these third-party packages using the following command:
  ```bash
  pip install -r requirements.txt
  ```

## Usage

TRANSIT's entrypont is at `src/run.py`. You can simply run the following command line to get a demo:

```bash
python src/run.py
```

To customize the simulation, you may:

1. Adjust the **scenario and anomaly names** in `src/run.py`
2. Modify or create the corresponding **configuration files** (`.ini`) in the `config` folder.

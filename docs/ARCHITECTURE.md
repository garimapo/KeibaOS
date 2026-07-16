# KeibaOS Architecture

## Overview

KeibaOS is a modular horse racing analysis system.

The system separates:

- Data acquisition
- HTML parsing
- Data modeling
- Database storage
- AI analysis

to maintain long-term scalability and maintainability.


## System Flow


External Racing Site

↓

Provider Layer

↓

Parser Layer

↓

Model Layer

↓

Database Layer

↓

AI Analysis



## Directory Structure


KeibaOS

config/
    settings.json

database/
    keiba.db

docs/
    ROADMAP.md
    ARCHITECTURE.md
    CHANGELOG.md

logs/

prompts/

scripts/
    database.py
    fetch_races.py
    fetch_local.py
    fetch_jra.py
    models.py
    logger.py

    providers/
        nar_provider.py

    parsers/
        nar_parser.py

main.py



# Module Responsibilities


## main.py

Application entry point.

Responsibilities:

- Start system
- Initialize database
- Execute race acquisition


## Fetch Layer

Files:


fetch_races.py
fetch_local.py
fetch_jra.py


Responsibilities:

- Decide race source
- Control acquisition flow
- Connect Provider and Parser


## Provider Layer

Example:


providers/nar_provider.py


Responsibilities:

- External site communication
- HTTP requests
- HTML acquisition

Provider does not parse HTML.


## Parser Layer

Example:


parsers/nar_parser.py

Responsibilities:

- Convert HTML into models
- Extract required data

Parser does not access network.


## Model Layer

File:

models.py

Responsibilities:

Define data structures.

Current models:

- RaceMeeting
- Race
- Horse
- Prediction
- Bet
- Result
- Analysis


## Database Layer

File:

database.py

Responsibilities:

- SQLite connection
- Table management
- Data persistence
# KeibaOS Ver0.8 Horse Engine Design


## Overview

Ver0.8 adds horse entry information acquisition.

Current:

Race data acquisition completed.
Race
|
v
SQLite
Ver0.8:
Race
|
v
Horse
|
v
SQLite
The goal is to store individual horse information required for AI prediction.


---

# Goal

Acquire and store horse entry data from NAR DebaTable pages.


Target data:

- Frame number
- Horse number
- Horse name
- Jockey
- Trainer
- Odds
- Popularity
- Horse weight


---

# Data Flow

Race

↓

deba_table_url

↓

NARProvider

↓

DebaTable HTML

↓

HorseParser

↓

Horse Model

↓

SQLite horses table

---

# New Components


## HorseParser

File:
scripts/parsers/horse_parser.py

Responsibilities:

- Parse DebaTable HTML
- Extract horse information
- Convert HTML data into Horse models


Parser does not access network.


---

## NARProvider Extension

File:
scripts/providers/nar_provider.py

Add:
fetch_deba_table()

Responsibilities:

- Access DebaTable URL
- Return HTML


Provider does not parse HTML.


---

# Database Design


New table:

## horses


Columns:

id

race_id

frame_no

horse_no

horse_name

jockey

trainer

odds

popularity

weight

Relationship:

races

1

|

many

|

horses

---

# Model Design


Horse model:

Horse

race_id
frame_no
horse_no
horse_name
jockey
trainer
odds
popularity
weight

---

# Modified Files


## scripts/models.py

Update Horse model if required.


## scripts/database.py

Add horses table.

Add horse save functions.


## scripts/providers/nar_provider.py

Add DebaTable acquisition.


## scripts/parsers/horse_parser.py

New file.

Horse HTML parser.


## scripts/fetch_local.py

Connect Race acquisition and Horse acquisition.


---

# Development Rules


Follow:
Design

↓

Implementation

↓

Self Review

↓

Release

Do not:

- Mix network and parsing logic
- Store incomplete data
- Add temporary code to production


---

# Completion Criteria


Ver0.8 is complete when:


- DebaTable HTML can be acquired
- HorseParser can extract horses
- Horse data is stored in SQLite
- Duplicate horse entries are prevented
- Existing Ver0.7 functions continue working


---

# Release

Target:
Release Ver0.8 Horse Engine
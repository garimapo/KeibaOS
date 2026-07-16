# KeibaOS Changelog


## Ver0.7 Race Engine

Release:

- Release Ver0.7 Race Engine
- Commit: 9da9a2c


### Added

- NAR RaceList acquisition
- RaceParser implementation
- Race model expansion
- SQLite race data storage
- Duplicate race detection


### Data Flow
NAR Website

↓

RaceMeeting

↓

RaceList

↓

RaceParser

↓

Race Model

↓

SQLite


### Database

Added support for:

- race_date
- organization
- place
- race_no
- race_name
- start_time
- distance
- track
- weather
- track_condition
- horse_count
- deba_table_url



---

## Ver0.6 Meeting Engine


### Added

- NAR connection
- HTML fetching
- BeautifulSoup integration
- RaceMeeting model
- Today's racecourse acquisition


### Completed

Supported racecourses:

- 門別
- 浦和
- 名古屋
- 園田



---

## Ver0.5 Data Foundation


### Added

- Logger
- SQLite database
- Database layer
- Race model
- Fetch foundation
- Git management



---

# Future Versions


## Ver0.8 Horse Engine

Planned:

- Horse data acquisition
- Frame number
- Horse number
- Horse name
- Jockey
- Trainer
- Odds
- Popularity
- Horse weight



## Ver0.9 Result Engine

Planned:

- Finish position
- Result data
- Payout data
- Performance analysis



## Ver1.0 AI Prediction Engine

Planned:

- OpenAI API integration
- AI prediction generation
- S rating system
- Betting support
- Automatic operation
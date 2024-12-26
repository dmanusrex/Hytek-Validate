# Read HyTek EV3 event files and return two dataframes

import pandas as pd
import numpy as np
from typing import Any
from utils import time_from_str
from dateutil import parser


def parse_sdif_ev3(file: str) -> dict:
    """Parse a SDIF .ev3 event export file."""

    event_fields = [
        "event_no",
        "subevent_no",
        "prelims_finals",
        "rounds",
        "ind_or_relay",
        "gender",
        "min_age",
        "max_age",
        "distance",
        "stroke",
        "unknown1",
        "unknown2",
        "unknown3",
        "event_type",  # Event Type (N=Standard, D=Disabilty, ???)
        "event_fee",
        "lcm_dqt",  # Long Course Meters - De-qualifying Time
        "lcm_qt",  # Long Course Meters - Qualifying Time
        "scm_dqt",  # Short Course Meters - De-qualifying Time
        "scm_qt",  # Short Course Meters - Qualifying Time
        "scy_dqt",  # Short Course Yards - De-qualifying Time
        "scy_qt",  # Short Course Yards - Qualifying Time
        "session_number",  # Session #?
        "session_event",  # Event # (again?)
        "session_meet_day",  # Day of meet session is on
        "session_start_time", # Start time of session
        "session_course",  # Hy-Tek Course Code (1=LCM, 2=SCM, 3=SCY)
        "max_entries",
        "max_individual_entries",
        "max_relay_entries",
        "relay_team_members",
    ]

    events = pd.read_csv(
        file, delimiter=";", names=event_fields, skiprows=1, index_col=False, header=None, encoding="utf-8"
    )

    # Ensure event_no, min_age and max_age are strings

    events["event_no"] = events["event_no"].astype(str)
    events["min_age"] = events["min_age"].astype(int)
    events["max_age"] = events["max_age"].astype(int)
    events["lcm_qt"].replace(np.nan, "0.00", inplace=True)
    events["lcm_qt"] = events["lcm_qt"].astype(str)
    events["lcm_dqt"].replace(np.nan, "0.00", inplace=True)
    events["lcm_dqt"] = events["lcm_dqt"].astype(str)
    events["scm_qt"].replace(np.nan, "0.00", inplace=True)
    events["scm_qt"] = events["scm_qt"].astype(str)
    events["scm_dqt"].replace(np.nan, "0.00", inplace=True)
    events["scm_dqt"] = events["scm_dqt"].astype(str)

    # Fix Gender.   Set to M if M, B or F if F, W, G
    events["gender"] = events["gender"].apply(lambda x: "M" if x in ["M", "B"] else "F" if x in ["F", "W", "G"] else x)

    events = events.join(events.apply(add_new_columns, axis=1))

    header_fields = [
        "meet_name",
        "pool_name",
        "meet_start_date",
        "meet_end_date",
        "age_up_date",
        "seeding_type",
        "team_surcharge",
        "athelete_surcharge",
        "facilty_surcharge",
        "file_format",
        "meet_software",
        "meet_sw_version",
        "date_generated",
        "unknown1",
        "sanction_number",
        "altitude",
        "valid_times_start_date",
        "minimum_age_open_events",
        "max_total_entries",
        "max_individual_entries",
        "max_relay_entries",
        "id_format",  # ID Format - 1=USA, 2=NewZealand, 3=SouthAfrica, 4=AustralianSwimming, 5=BritishSwimming, 6=Other, 7=?Canada?, 8=USMasters
        "class",  # (A)gegroup, (O)pen, (H)ighSchool, (C)ollege, (Y)MCA, (M)asters, (D)isabled
        "entry_deadline",
        "pool_address1",
        "pool_address2",
        "pool_city",
        "pool_province",
        "pool_postal_code",
        "pool_country",
        "host_LSC",
        "exclude_notimes",  # IE/ Require a time, NT entries are not allowed
        "unknown2",
        "entry_open_date",
        "check_digit",  # Check Digit
    ]

    header = pd.read_csv(
        file, delimiter=";", names=header_fields, index_col=False, nrows=1, header=None, encoding="utf-8"
    )

    return {"events": events, "header": header}


def add_new_columns(row: Any) -> pd.Series:
    """Add new columns and convert times to centiseconds"""
    return pd.Series(
        [
            time_from_str(row["lcm_qt"]),
            time_from_str(row["lcm_dqt"]),
            time_from_str(row["scm_qt"]),
            time_from_str(row["scm_dqt"]),
        ],
        index=["lcm_qt_cs", "lcm_dqt_cs", "scm_qt_cs", "scm_dqt_cs"],
    )


def ev3_to_timestandard(ev3data: pd.DataFrame) -> pd.DataFrame:
    """Convert EV3 data to Time Standard format"""

    timestandard = pd.DataFrame()

    # concatenate data from the ev3 frame for each course

    for course in ["lcm", "scm"]:
        course_data = ev3data[["ind_or_relay", "gender", "min_age", "max_age", "distance", "stroke", f"{course}_qt", f"{course}_dqt", f"{course}_qt_cs", f"{course}_dqt_cs"]].copy()
        course_data["course"] = course.upper()
        course_data["course_qt"] = course_data[f"{course}_qt"]
        course_data["course_dqt"] = course_data[f"{course}_dqt"]
        course_data["course_qt_cs"] = course_data[f"{course}_qt_cs"]
        course_data["course_dqt_cs"] = course_data[f"{course}_dqt_cs"]
        course_data.drop(columns=[f"{course}_qt", f"{course}_dqt", f"{course}_qt_cs", f"{course}_dqt_cs"], inplace=True)
        timestandard = pd.concat([timestandard, course_data])

    timestandard = timestandard[timestandard["course_qt"] != "0.00"].copy()

    return timestandard

if __name__ == "__main__":

    ev3file = "C:\debug\Meet Events-2024 Western Region SC Championships-23Feb2024-001.ev3"
    ev3data = parse_sdif_ev3(ev3file)
    ev3data["events"].to_csv("CdnOpen_events.csv", encoding="utf-8", index=False)
    print(ev3data["header"])
    for item in ev3data["header"]:
        print(f"{item}: {ev3data['header'][item].values[0]}")
    print(parser.parse(ev3data["header"]["valid_times_start_date"].values[0]).strftime("%Y%m%d"))
    print(ev3data["events"])
    print(ev3_to_timestandard(ev3data["events"]))
    ev3_to_timestandard(ev3data["events"]).to_csv("CdnOpen_timestandard.csv", encoding="utf-8", index=False)
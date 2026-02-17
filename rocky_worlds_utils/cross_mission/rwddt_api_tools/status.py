"""Module to build calendar widget in status page of the RWDDT Website

Authors
-------
- Mees Fix <<mfix@stsci.edu>>
"""

from datetime import datetime

import pandas as pd

from rocky_worlds_utils.cross_mission.rwddt_api_tools.visit_data import get_visits
from rocky_worlds_utils.constants import PROGRAMS_BY_TARGET


class TargetStatus:
    def __init__(self, target_name):
        self.target_name = target_name
        self.programs = PROGRAMS_BY_TARGET[self.target_name]
        self.get_jwst_visits()
        self.get_hst_visits()
        self._shared_columns = sorted(
            list(set(self.jwst_visits).intersection(list(self.hst_visits)))
        )
        self.remove_calibration_visits()
        self.combine_visits()
        self.parse_table_dates()
        self.get_completed_visits()
        self.get_failed_visits()
        self.get_scheduled_visits()

    def combine_visits(self):
        """
        Combine HST and JWST visits into a single dataframe.
        """
        self.combined_visits = pd.concat(
            [
                self.jwst_visits[self._shared_columns],
                self.hst_visits[self._shared_columns],
            ],
            ignore_index=True,
        )

        # also get columns for exposure times
        exposure_time = pd.concat(
            [self.jwst_visits["scheduling_duration"], self.hst_visits["exposure_time"]],
            ignore_index=True,
        )

        self.combined_visits["exposure_time"] = exposure_time

    def get_hst_visits(self):
        """
        Query API and turn visits for HST program for Target name
        """
        self.hst_visits = get_visits(self.programs["hst"], mission="hst")

    def get_jwst_visits(self):
        """
        Query API and turn visits for JWST program for Target name
        """
        self.jwst_visits = get_visits(self.programs["jwst"], mission="jwst")

    def get_completed_visits(self):
        """
        Make dataframe of completed visits
        """
        statuses = ["COMPLETED", "completed"]
        self.completed_visits = self.combined_visits[
            self.combined_visits["visit_status"].isin(statuses)
        ]

    def get_failed_visits(self):
        """
        Make dataframe of failed visits
        """
        statuses = ["FAILED", "failed"]
        self.failed_visits = self.combined_visits[
            self.combined_visits["visit_status"].isin(statuses)
        ]

    def get_scheduled_visits(self):
        """
        Make dataframe of scheduled visits
        """
        statuses = ["SCHEDULED", "scheduling"]
        self.scheduled_visits = self.combined_visits[
            self.combined_visits["visit_status"].isin(statuses)
        ]

    def parse_table_dates(self):
        """
        Parse executed dates and plan windows into python datetime objects.
        Then add them to pandas dataframe.
        """
        jwst_format = "%Y-%m-%d %H:%M:%S %z"
        hst_format = "%Y.%j:%H:%M:%S"
        executed_format = "%Y-%m-%dT%H:%M:%SZ"
        datetime_start = []
        datetime_end = []
        for _, row in self.combined_visits.iterrows():
            if row["executed_start_time"] and row["executed_end_time"]:
                start_datetime = datetime.strptime(
                    row["executed_start_time"], executed_format
                )
                end_datetime = datetime.strptime(
                    row["executed_end_time"], executed_format
                )
            elif row["plan_windows"]:
                if row["mission"] == "HST":
                    start_date, end_date = row["plan_windows"].split(" -- ")
                    start_datetime = datetime.strptime(start_date, hst_format)
                    end_datetime = datetime.strptime(end_date, hst_format)
                elif row["mission"] == "JWST":
                    start_date, end_date = row["plan_windows"].split(" -- ")
                    start_datetime = datetime.strptime(start_date, jwst_format)
                    end_datetime = datetime.strptime(end_date, jwst_format)

            datetime_start.append(start_datetime)
            datetime_end.append(end_datetime)

        self.combined_visits["start_datetime"] = datetime_start
        self.combined_visits["end_datetime"] = datetime_end

    def remove_calibration_visits(self):
        """
        Remove calibration visits from dataframe.
        """
        jwst_rows = self.jwst_visits[
            self.jwst_visits["template"] != "MIRI Imaging"
        ].index
        self.jwst_visits.drop(jwst_rows, inplace=True)
        hst_rows = self.hst_visits[
            self.hst_visits["target_names"].str.contains("WAVE")
        ].index
        self.hst_visits.drop(hst_rows, inplace=True)

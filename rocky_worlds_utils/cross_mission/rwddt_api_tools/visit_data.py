"""Tools to programmatically access RWDDT visit data via Observatory Observation Plan API
https://www.stsci.edu/obs-plan-api/docs

Authors
-------
- Mees Fix <<mfix@stsci.edu>>

Use
---
>>> from visit_data.py import get_visits
>>> jwst = get_visits([9235], mission='jwst')
>>> hst = get_visits([17904], mission='hst')
"""

import requests

import pandas as pd


def get_visits(program_ids, mission):
    """
    Get visits for program ids from Observatory Observation Plan API

    program_ids : list
        List of program ids to get visits for

    mission : str
        "jwst" or "hst" to select API url for programs provided
    """

    url = f"https://www.stsci.edu/obs-plan-api/{mission}/rw-visit-report/"
    program_data = []
    for program_id in program_ids:
        r = requests.get(url=url, params={"program": program_id})

        if r.ok:
            data = r.json()
        else:
            raise Exception(f"Something is wrong with request for program {program_id}")

        program_data.extend(data["data"])

    visit_df = pd.DataFrame(program_data)

    return visit_df

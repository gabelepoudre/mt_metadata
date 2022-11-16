# -*- coding: utf-8 -*-
"""
Created on Wed Dec 23 21:30:36 2020

:copyright: 
    Jared Peacock (jpeacock@usgs.gov)

:license: MIT

"""
# =============================================================================
# Imports
# =============================================================================
from collections import OrderedDict
from mt_metadata.base.helpers import write_lines
from mt_metadata.base import get_schema, Base
from .standards import SCHEMA_FN_PATHS
from mt_metadata.utils.validators import validate_value_type
from . import (
    Fdsn,
    Orientation,
    Person,
    Provenance,
    Location,
    TimePeriod,
    Run,
)
from mt_metadata.utils.dict_list import ListDict

# =============================================================================
attr_dict = get_schema("station", SCHEMA_FN_PATHS)
attr_dict.add_dict(get_schema("fdsn", SCHEMA_FN_PATHS), "fdsn")
location_dict = get_schema("location", SCHEMA_FN_PATHS)
location_dict.add_dict(
    get_schema("declination", SCHEMA_FN_PATHS), "declination"
)
attr_dict.add_dict(location_dict, "location")
attr_dict.add_dict(
    get_schema("person", SCHEMA_FN_PATHS),
    "acquired_by",
    keys=["name", "comments"],
)
attr_dict.add_dict(get_schema("orientation", SCHEMA_FN_PATHS), "orientation")
attr_dict.add_dict(
    get_schema("provenance", SCHEMA_FN_PATHS),
    "provenance",
    keys=["comments", "creation_time", "log"],
)
attr_dict.add_dict(
    get_schema("software", SCHEMA_FN_PATHS), "provenance.software"
)
attr_dict.add_dict(
    get_schema("person", SCHEMA_FN_PATHS),
    "provenance.submitter",
    keys=["author", "email", "organization"],
)
attr_dict.add_dict(get_schema("time_period", SCHEMA_FN_PATHS), "time_period")
# =============================================================================
class Station(Base):
    __doc__ = write_lines(attr_dict)

    def __init__(self, **kwargs):

        self.fdsn = Fdsn()
        self.channels_recorded = []
        self.orientation = Orientation()
        self.acquired_by = Person()
        self.provenance = Provenance()
        self.location = Location()
        self.time_period = TimePeriod()
        self.runs = ListDict()
        super().__init__(attr_dict=attr_dict, **kwargs)

    def __add__(self, other):
        if isinstance(other, Station):
            self.runs.extend(other.runs)
            return self
        else:
            msg = f"Can only merge Station objects, not {type(other)}"
            self.logger.error(msg)
            raise TypeError(msg)

    def __len__(self):
        return len(self.runs)

    def has_run(self, run_id):
        """
        Check to see if the run id already exists

        :param run_id: DESCRIPTION
        :type run_id: TYPE
        :return: DESCRIPTION
        :rtype: TYPE

        """
        if run_id in self.run_list:
            return True
        return False

    def run_index(self, run_id):
        """
        Get the index of the run_id

        :param run_id: DESCRIPTION
        :type run_id: TYPE
        :return: DESCRIPTION
        :rtype: TYPE

        """

        if self.has_run(run_id):
            return self.run_list.index(run_id)
        return None

    def add_run(self, run_obj):
        """
        Add a run, if one of the same name exists overwrite it.

        :param run_obj: DESCRIPTION
        :type run_obj: TYPE
        :return: DESCRIPTION
        :rtype: TYPE

        """

        if not isinstance(run_obj, Run):
            raise TypeError(
                f"Input must be a mt_metadata.timeseries.Run object not {type(run_obj)}"
            )

        if self.has_run(run_obj.id):
            self.runs[run_obj.id].update(run_obj)
            self.logger.warning(
                f"Station {run_obj.id} already exists, updating metadata"
            )
        else:
            self.runs.append(run_obj)

    def get_run(self, run_id):
        """
        Get a :class:`mt_metadata.timeseries.Run` object from the given
        id

        :param run_id: run id verbatim
        :type run_id: string

        """

        if self.has_run(run_id):
            return self.runs[run_id]
        self.logger.warning(f"Could not find {run_id} in runs.")
        return None

    def remove_run(self, run_id):
        """
        remove a run from the survey

        :param run_id: DESCRIPTION
        :type run_id: TYPE
        :return: DESCRIPTION
        :rtype: TYPE

        """

        if self.has_run(run_id):
            self.runs.remove(run_id)
        else:
            self.logger.warning(f"Could not find {run_id} to remove.")

    @property
    def runs(self):
        """Return run list"""
        return self._runs

    @runs.setter
    def runs(self, value):
        """set the run list"""
        if not isinstance(value, (list, tuple, dict, ListDict, OrderedDict)):
            msg = (
                "input run_list must be an iterable, should be a list or dict "
                f"not {type(value)}"
            )
            self.logger.error(msg)
            raise TypeError(msg)

        fails = []
        self._runs = ListDict()
        if isinstance(value, (dict, ListDict, OrderedDict)):
            value_list = value.values()

        elif isinstance(value, (list, tuple)):
            value_list = value

        for ii, run in enumerate(value_list):

            if isinstance(run, (dict, OrderedDict)):
                r = Run()
                r.from_dict(run)
                self._runs.append(r)
            elif not isinstance(run, Run):
                msg = f"Item {ii} is not type(Run); type={type(run)}"
                fails.append(msg)
                self.logger.error(msg)
            else:
                self._runs.append(run)
        if len(fails) > 0:
            raise TypeError("\n".join(fails))

    @property
    def run_list(self):
        """Return names of run in survey"""
        return self.runs.keys()

    @run_list.setter
    def run_list(self, value):
        """Set list of run names"""

        if not hasattr(value, "__iter__"):
            msg = (
                "input station_list must be an iterable, should be a list "
                f"not {type(value)}"
            )
            self.logger.error(msg)
            raise TypeError(msg)
        value = validate_value_type(value, str, "name_list")

        for run in value:
            if not isinstance(run, str):
                try:
                    run = str(run)
                except (ValueError, TypeError):
                    msg = f"could not convert {run} to string"
                    self.logger.error(msg)
                    raise ValueError(msg)
            run = run.replace("'", "").replace('"', "")
            self.runs.append(Run(id=run))

    def update_time_period(self):
        """
        update time period from run information
        """
        start = []
        end = []
        for run in self.runs:
            start.append(run.time_period.start)
            end.append(run.time_period.end)
        if start:
            if self.time_period.start == "1980-01-01T00:00:00+00:00":
                self.time_period.start = min(start)
            else:
                if self.time_period.start > min(start):
                    self.time_period.start = min(start)
        if end:
            if self.time_period.end == "1980-01-01T00:00:00+00:00":
                self.time_period.end = max(end)
            else:
                if self.time_period.end < max(end):
                    self.time_period.end = max(end)

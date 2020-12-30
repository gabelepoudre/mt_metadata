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
from mt_metadata.base.helpers import write_lines
from mt_metadata.base import get_schema
from .standards import SCHEMA_FN_PATHS
from . import Electrode, Diagnostic, Channel

# =============================================================================
attr_dict = get_schema("electric", SCHEMA_FN_PATHS)
attr_dict.add_dict(get_schema("channel", SCHEMA_FN_PATHS))
attr_dict.add_dict(get_schema("data_quality", SCHEMA_FN_PATHS), "data_quality")
attr_dict.add_dict(get_schema("filtered", SCHEMA_FN_PATHS), "filter")
attr_dict.add_dict(get_schema("instrument", SCHEMA_FN_PATHS), "positive")
attr_dict.add_dict(get_schema("instrument", SCHEMA_FN_PATHS), "negative")
attr_dict.add_dict(get_schema("time_period", SCHEMA_FN_PATHS), "time_period") 
# =============================================================================
class Electric(Channel):
    __doc__ = write_lines(attr_dict)

    def __init__(self, **kwargs):
        self.dipole_length = 0.0
        self.positive = Electrode()
        self.negative = Electrode()
        self.contact_resistance = Diagnostic()
        self.ac = Diagnostic()
        self.dc = Diagnostic()
        self.units_s = None

        Channel.__init__(self, **kwargs)
        self.type = "electric"

        self._attr_dict = attr_dict


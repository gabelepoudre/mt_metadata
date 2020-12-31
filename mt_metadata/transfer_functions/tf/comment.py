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
from mt_metadata.base import get_schema, Base
from .standards import SCHEMA_FN_PATHS

# =============================================================================
attr_dict = get_schema(name, SCHEMA_FN_PATHS)
# =============================================================================
class Comment(Base):
    __doc__ = write_lines(attr_dict)

    def __init__(self, **kwargs):
        self.comment = None
        self.author = None
        self._dt = MTime()

    @property
    def date(self):
        return self._dt.iso_str

    @date.setter
    def date(self, dt_str):
        self._dt.from_str(dt_str)


# ==============================================================================
# Copyright
# ==============================================================================

# -*- coding: utf-8 -*-
"""
Created on Mon Mar 22 10:21:28 2021

:copyright:
    Jared Peacock (jpeacock@usgs.gov)

:license: MIT

"""

from mt_metadata.timeseries.filters import (
    PoleZeroFilter,
    CoefficientFilter,
    TimeDelayFilter,
)
from mt_metadata.base import helpers
from obspy.core import inventory

from xml.etree import cElementTree as et

experiment = et.parse(r"c:\Users\jpeacock\full_experiment.xml").getroot()
for survey_element in list(experiment):
    for filters_element in survey_element.findall("filters"):
        filters_dict = {}
        for zpk_element in filters_element.findall("pole_zero_filter"):
            zpk_filter = PoleZeroFilter()
            zpk_filter.from_xml(zpk_element)
            filters_dict[zpk_filter.name] = zpk_filter
        for co_element in filters_element.findall("coefficient_filter"):
            co_filter = CoefficientFilter()
            co_filter.from_xml(co_element)
            filters_dict[co_filter.name] = co_filter
        for td_element in filters_element.findall("time_delay_filter"):
            td_filter = TimeDelayFilter()
            td_filter.from_xml(td_element)
            filters_dict[td_filter.name] = td_filter


# zpk_str = ("<pole_zero_filter>"
#            "<name>magnetic field 3 pole Butterworth low-pass</name>"
#            "<normalization_factor type='float'>1984.31439386406</normalization_factor>"
#            "<poles>"
#            "<item>(-6.283185+10.882477j)</item>"
#            "<item>(-6.283185-10.882477j)</item>"
#            "<item>(-12.566371+0j)</item>"
#            "</poles>"
#            "<type>zpk</type>"
#            "<units_in>nT</units_in>"
#            "<units_out>V</units_out>"
#            "<zeros/>"
#            "</pole_zero_filter>")

# co_str = ("<coefficient_filter>"
#           "<gain type='float'>100.0</gain>"
#           "<name>magnatometer A to D</name>"
#           "<type>coefficient</type>"
#           "<units_in>V</units_in>"
#           "<units_out>count</units_out>"
#           "</coefficient_filter>")

# zpk_element = et.fromstring(zpk_str)
# zpk_dict = helpers.element_to_dict(zpk_element)

# co_element = et.fromstring(co_str)
# co_dict = helpers.element_to_dict(co_element)

# zpk_obj = PoleZeroFilter()
# zpk_obj.from_xml(zpk_element)

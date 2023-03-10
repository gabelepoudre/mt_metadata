# -*- coding: utf-8 -*-
"""
EMTFXML
==========

This is meant to follow Anna's XML schema for transfer functions

Created on Sat Sep  4 17:59:53 2021

@author: jpeacock
"""
# =============================================================================
# Imports
# =============================================================================
import inspect
from pathlib import Path
from collections import OrderedDict
from xml.etree import cElementTree as et
import numpy as np

from . import metadata as emtf_xml
from mt_metadata.transfer_functions.io.emtfxml.metadata import (
    helpers as emtf_helpers,
)
from mt_metadata.utils.mt_logger import setup_logger
from mt_metadata.base import helpers
from mt_metadata.utils.validators import validate_attribute
from mt_metadata.transfer_functions.tf import (
    Instrument,
    Survey,
    Station,
    Run,
    Electric,
    Magnetic,
)
from mt_metadata.utils import mttime
from mt_metadata import __version__


meta_classes = dict(
    [
        (validate_attribute(k), v)
        for k, v in inspect.getmembers(emtf_xml, inspect.isclass)
    ]
)
meta_classes["instrument"] = Instrument
# =============================================================================
# EMTFXML
# =============================================================================

estimates_dict = {
    "variance": emtf_xml.Estimate(
        name="VAR",
        type="complex",
        description="Variance",
        external_url="http://www.iris.edu/dms/products/emtf/variance.html",
        intention="error estimate",
        tag="variance",
    ),
    "covariance": emtf_xml.Estimate(
        name="COV",
        type="complex",
        description="Covariance",
        external_url="http://www.iris.edu/dms/products/emtf/covariance.html",
        intention="error estimate",
        tag="covariance",
    ),
    "residual_covariance": emtf_xml.Estimate(
        name="RESIDCOV",
        type="complex",
        description="residual_covariance (N)",
        external_url="http://www.iris.edu/dms/products/emtf/residual_covariance.html",
        intention="error estimate",
        tag="residual_covariance",
    ),
    "inverse_signal_power": emtf_xml.Estimate(
        name="INVSIGCOV",
        type="complex",
        description="Inverse Coherent Signal Power Matrix (S)",
        external_url="http://www.iris.edu/dms/products/emtf/inverse_signal_covariance.html",
        intention="signal power estimate",
        tag="inverse_signal_covariance",
    ),
    "coherence": emtf_xml.Estimate(
        name="COH",
        type="complex",
        description="Coherence",
        external_url="http://www.iris.edu/dms/products/emtf/coherence.html",
        intention="signal coherence",
        tag="coherence",
    ),
    "predicted_coherence": emtf_xml.Estimate(
        name="PREDCOH",
        type="complex",
        description="Multiple Coherence",
        external_url="http://www.iris.edu/dms/products/emtf/multiple_coherence.html",
        intention="signal coherence",
        tag="multiple_coherence",
    ),
    "signal_amplidude": emtf_xml.Estimate(
        name="SIGAMP",
        type="complex",
        description="Signal Amplitude",
        external_url="http://www.iris.edu/dms/products/emtf/signal_amplitude.html",
        intention="signal power estimate",
        tag="signal_power",
    ),
    "signal_noise": emtf_xml.Estimate(
        name="SIGNOISE",
        type="complex",
        description="Signal Noise",
        external_url="http://www.iris.edu/dms/products/emtf/signal_noise.html",
        intention="error estimate",
        tag="signal_noise",
    ),
}

data_types_dict = {
    "impedance": emtf_xml.DataType(
        name="Z",
        type="complex",
        output="E",
        input="H",
        units="[mV/km]/[nT]",
        description="MT impedance",
        external_url="http://www.iris.edu/dms/products/emtf/impedance.html",
        intention="primary data type",
        tag="impedance",
    ),
    "tipper": emtf_xml.DataType(
        name="T",
        type="complex",
        output="H",
        input="H",
        units="[]",
        description="Vertical Field Transfer Functions (Tipper)",
        external_url="http://www.iris.edu/dms/products/emtf/tipper.html",
        intention="primary data type",
        tag="tipper",
    ),
}


class EMTFXML(emtf_xml.EMTF):
    """
    This is meant to follow Anna's XML schema for transfer functions
    """

    def __init__(self, fn=None, **kwargs):
        super().__init__()
        self._root_dict = None
        self.logger = setup_logger(self.__class__.__name__)
        self.external_url = emtf_xml.ExternalUrl()
        self.primary_data = emtf_xml.PrimaryData()
        self.attachment = emtf_xml.Attachment()
        self.provenance = emtf_xml.Provenance()
        self.copyright = emtf_xml.Copyright()
        self.site = emtf_xml.Site()

        # not sure why we need to do this, but if you don't FieldNotes end
        # as a string.
        self.field_notes = emtf_xml.FieldNotes()
        self.processing_info = emtf_xml.ProcessingInfo()
        self.statistical_estimates = emtf_xml.StatisticalEstimates()
        self.data_types = emtf_xml.DataTypes()
        self.site_layout = emtf_xml.SiteLayout()
        self.data = emtf_xml.TransferFunction()
        self.period_range = emtf_xml.PeriodRange()

        self.fn = fn

        self.element_keys = [
            "description",
            "product_id",
            "sub_type",
            "notes",
            "tags",
            "external_url",
            "primary_data",
            "attachment",
            "provenance",
            "copyright",
            "site",
            "field_notes",
            "processing_info",
            "statistical_estimates",
            "data_types",
            "site_layout",
            "data",
            "period_range",
        ]

        for key, value in kwargs.items():
            setattr(self, key, value)

        if self.fn != None:
            self.read()

    def __str__(self):
        lines = [f"Station: {self.station_metadata.id}", "-" * 50]
        lines.append(f"\tSurvey:        {self.survey_metadata.id}")
        lines.append(f"\tProject:       {self.survey_metadata.project}")
        lines.append(
            f"\tAcquired by:   {self.station_metadata.acquired_by.author}"
        )
        lines.append(
            f"\tAcquired date: {self.station_metadata.time_period.start_date}"
        )
        lines.append(
            f"\tLatitude:      {self.station_metadata.location.latitude:.3f}"
        )
        lines.append(
            f"\tLongitude:     {self.station_metadata.location.longitude:.3f}"
        )
        lines.append(
            f"\tElevation:     {self.station_metadata.location.elevation:.3f}"
        )
        lines.append("\tDeclination:   ")
        lines.append(
            f"\t\tValue:     {self.station_metadata.location.declination.value}"
        )
        lines.append(
            f"\t\tModel:     {self.station_metadata.location.declination.model}"
        )

        if self.data.z is not None:
            lines.append("\tImpedance:     True")
        else:
            lines.append("\tImpedance:     False")

        if self.data.t is not None:
            lines.append("\ttipper:        True")
        else:
            lines.append("\tTipper:        False")

        if self.data.period is not None:
            lines.append(f"\tN Periods:     {len(self.data.period)}")

            lines.append("\tPeriod Range:")
            lines.append(f"\t\tMin:   {self.data.period.min():.5E} s")
            lines.append(f"\t\tMax:   {self.data.period.max():.5E} s")

            lines.append("\tFrequency Range:")
            lines.append(f"\t\tMin:   {1./self.data.period.max():.5E} Hz")
            lines.append(f"\t\tMax:   {1./self.data.period.min():.5E} Hz")

        return "\n".join(lines)

    def __repr__(self):
        lines = []
        lines.append(f"station='{self.station_metadata.id}'")
        lines.append(f"latitude={self.station_metadata.location.latitude:.2f}")
        lines.append(
            f"longitude={self.station_metadata.location.longitude:.2f}"
        )
        lines.append(
            f"elevation={self.station_metadata.location.elevation:.2f}"
        )

        return f"EMTFXML({(', ').join(lines)})"

    @property
    def fn(self):
        return self._fn

    @fn.setter
    def fn(self, value):
        if value is not None:
            self._fn = Path(value)
        else:
            self._fn = None

    @property
    def save_dir(self):
        if self.fn is not None:
            return self.fn.parent
        return None

    def read(self, fn=None):
        """
        Read xml file

        :param fn: DESCRIPTION
        :type fn: TYPE
        :return: DESCRIPTION
        :rtype: TYPE

        """
        if fn is not None:
            self.fn = fn
        if self.fn is not None:
            if not self.fn.exists():
                raise IOError(f"Cannot find: {fn}")
        else:
            raise IOError("Input file name is None, that is bad.")

        root = et.parse(self.fn).getroot()
        root_dict = helpers.element_to_dict(root)
        root_dict = root_dict[list(root_dict.keys())[0]]
        root_dict = emtf_helpers._convert_keys_to_lower_case(root_dict)
        self._root_dict = root_dict

        for element in self.element_keys:
            attr = getattr(self, element)
            if hasattr(attr, "read_dict"):
                attr.read_dict(root_dict)
            else:
                emtf_helpers._read_single(self, root_dict, element)

        self.period_range.min = self.data.period.min()
        self.period_range.max = self.data.period.max()

        # apparently sometimes the run list will come out as None from an
        # empty emtfxml.
        if self.site._run_list is None:
            self.site._run_list = []

    def write(self, fn, skip_field_notes=False):
        """
        Write an xml
        :param fn: DESCRIPTION
        :type fn: TYPE
        :return: DESCRIPTION
        :rtype: TYPE

        """

        emtf_element = et.Element("EM_TF")

        self._get_statistical_estimates()
        self._get_data_types()

        for key in self.element_keys:
            if skip_field_notes:
                if key == "field_notes":
                    continue
            value = getattr(self, key)
            if hasattr(value, "to_xml") and callable(getattr(value, "to_xml")):
                element = value.to_xml()
                if isinstance(element, list):
                    for item in element:
                        emtf_element.append(
                            emtf_helpers._convert_tag_to_capwords(item)
                        )
                else:
                    emtf_element.append(
                        emtf_helpers._convert_tag_to_capwords(element)
                    )
            else:
                emtf_helpers._write_single(
                    emtf_element, key, getattr(self, key)
                )

        emtf_element = emtf_helpers._remove_null_values(emtf_element)

        with open(fn, "w") as fid:
            fid.write(helpers.element_to_string(emtf_element))

        self.fn = fn

    def _get_statistical_estimates(self):
        """
        Get the appropriate statistical estimates in the file.

        """
        self.statistical_estimates.estimates_list = []
        if self.data.z_var is not None:
            if not np.all(self.data.z_var == 0.0):
                self.statistical_estimates.estimates_list.append(
                    estimates_dict["variance"]
                )
        elif self.data.t_var is not None:
            if not np.all(self.data.t_var == 0.0):
                self.statistical_estimates.estimates_list.append(
                    estimates_dict["variance"]
                )

        if self.data.z_invsigcov is not None:
            if not np.all(self.data.z_invsigcov == 0.0):
                self.statistical_estimates.estimates_list.append(
                    estimates_dict["inverse_signal_power"]
                )
        elif self.data.t_invsigcov is not None:
            if not np.all(self.data.t_invsigcov == 0.0):
                self.statistical_estimates.estimates_list.append(
                    estimates_dict["inverse_signal_power"]
                )

        if self.data.z_residcov is not None:
            if not np.all(self.data.z_residcov == 0.0):
                self.statistical_estimates.estimates_list.append(
                    estimates_dict["residual_covariance"]
                )
        elif self.data.t_residcov is not None:
            if not np.all(self.data.t_residcov == 0.0):
                self.statistical_estimates.estimates_list.append(
                    estimates_dict["residual_covariance"]
                )

    def _get_data_types(self):
        """
        get the appropriate data types for the file

        :return: DESCRIPTION
        :rtype: TYPE

        """
        self.data_types.data_types_list = []
        if self.data.z is not None:
            if not np.all(self.data.z == 0.0):
                self.data_types.data_types_list.append(
                    data_types_dict["impedance"]
                )
        if self.data.t is not None:
            if not np.all(self.data.t == 0.0):
                self.data_types.data_types_list.append(
                    data_types_dict["tipper"]
                )

    @property
    def survey_metadata(self):
        survey_obj = Survey()
        if self._root_dict is not None:
            survey_obj.acquired_by.author = self.site.acquired_by
            survey_obj.citation_dataset.author = self.copyright.citation.authors
            survey_obj.citation_dataset.title = self.copyright.citation.title
            survey_obj.citation_dataset.year = self.copyright.citation.year
            survey_obj.citation_dataset.doi = (
                self.copyright.citation.survey_d_o_i
            )
            survey_obj.country = self.site.country
            survey_obj.datum = self.site.location.datum
            survey_obj.geographic_name = self.site.survey
            survey_obj.id = self.site.survey
            survey_obj.project = self.site.project
            survey_obj.time_period.start = self.site.start
            survey_obj.time_period.end = self.site.end
            survey_obj.summary = self.description
            survey_obj.comments = "; ".join(
                [
                    f"{k}:{v}"
                    for k, v in {
                        "copyright.acknowledgement": self.copyright.acknowledgement,
                        "copyright.conditions_of_use": self.copyright.conditions_of_use,
                    }.items()
                    if v not in [None, ""]
                ]
            )

        return survey_obj

    @survey_metadata.setter
    def survey_metadata(self, sm):
        """
        Set metadata and other values in metadata

        :param sm: DESCRIPTION
        :type sm: TYPE
        :return: DESCRIPTION
        :rtype: TYPE

        """
        self.description = sm.summary
        self.site.project = sm.project
        if sm.geographic_name is None:
            self.site.survey = sm.id
        else:
            self.site.survey = sm.geographic_name
        self.site.country = ",".join(sm.country)
        self.copyright.citation.survey_d_o_i = sm.citation_dataset.doi

        self.copyright.citation.authors = sm.citation_dataset.author
        self.copyright.citation.title = sm.citation_dataset.title
        self.copyright.citation.year = sm.citation_dataset.year

        other = []
        for comment in sm.comments.split(";"):
            if comment.count(":") >= 1:
                key, value = comment.split(":", 1)
                try:
                    self.set_attr_from_name(key.strip(), value.strip())
                except:
                    raise AttributeError(f"Cannot set attribute {key}.")
            else:
                other.append(comment)
        self.site.comments.value = ", ".join(other)

    @property
    def station_metadata(self):
        s = Station()
        # if self._root_dict is not None:
        s.acquired_by.author = self.site.acquired_by
        s.channels_recorded = [
            d.name for d in self.site_layout.input_channels
        ] + [d.name for d in self.site_layout.output_channels]
        s.data_type = self.sub_type.lower().split("_")[0]
        s.geographic_name = self.site.name
        s.id = self.site.id
        s.fdsn.id = self.product_id
        s.location.from_dict(self.site.location.to_dict())
        s.orientation.angle_to_geographic_north = (
            self.site.orientation.angle_to_geographic_north
        )
        s.provenance.software.name = self.provenance.creating_application
        s.provenance.creation_time = self.provenance.create_time
        s.provenance.creator.author = self.provenance.creator.name
        s.provenance.creator.email = self.provenance.creator.email
        s.provenance.creator.organization = self.provenance.creator.org
        s.provenance.creator.url = self.provenance.creator.org_url
        s.provenance.submitter.author = self.provenance.submitter.name
        s.provenance.submitter.email = self.provenance.submitter.email
        s.provenance.submitter.organization = self.provenance.submitter.org
        s.provenance.submitter.url = self.provenance.submitter.org_url

        s.provenance.archive.url = self.external_url.url
        s.provenance.archive.comments = self.external_url.description

        s.time_period.start = self.site.start
        s.time_period.end = self.site.end

        comments = {}
        for key in [
            "description",
            "primary_data.filename",
            "attachment.description",
            "attachment.filename",
            "site.data_quality_notes.comments.author",
            "site.data_quality_notes.comments.value",
        ]:
            comments[key] = self.get_attr_from_name(key)
        s.comments = "; ".join(
            [f"{k}:{v}" for k, v in comments.items() if v not in [None, ""]]
        )

        s.transfer_function.id = self.site.id
        s.transfer_function.sign_convention = (
            self.processing_info.sign_convention
        )
        s.transfer_function.processed_by.author = (
            self.processing_info.processed_by
        )
        s.transfer_function.software.author = (
            self.processing_info.processing_software.author
        )
        s.transfer_function.software.name = (
            self.processing_info.processing_software.name
        )
        s.transfer_function.software.last_updated = (
            self.processing_info.processing_software.last_mod
        )
        if self.processing_info.processing_tag is not None:
            s.transfer_function.remote_references = (
                self.processing_info.processing_tag.split("_")
            )
        s.transfer_function.runs_processed = self.site.run_list
        s.transfer_function.processing_parameters.append(
            {"type": self.processing_info.remote_ref.type}
        )

        s.transfer_function.data_quality.good_from_period = (
            self.site.data_quality_notes.good_from_period
        )
        s.transfer_function.data_quality.good_to_period = (
            self.site.data_quality_notes.good_to_period
        )
        s.transfer_function.data_quality.rating.value = (
            self.site.data_quality_notes.rating
        )

        for fn in self.field_notes.run_list:
            if fn.sampling_rate in [0, None]:
                continue
            r = Run()
            r.id = fn.run
            r.data_logger.id = fn.instrument.id
            r.data_logger.type = fn.instrument.name
            r.data_logger.manufacturer = fn.instrument.manufacturer
            r.sample_rate = fn.sampling_rate
            r.time_period.start = fn.start
            r.time_period.end = fn.end

            # need to set azimuths from site layout with the x, y, z postions.
            if len(fn.magnetometer) == 1:
                for comp in ["hx", "hy", "hz"]:
                    c = Magnetic()
                    c.component = comp
                    c.sensor.id = fn.magnetometer[0].id
                    c.sensor.name = fn.magnetometer[0].name
                    c.sensor.manufacturer = fn.magnetometer[0].manufacturer
                    c.sensor.type = fn.magnetometer[0].type
                    r.add_channel(c)

            else:
                for mag in fn.magnetometer:
                    comp = mag.name
                    if comp is None:
                        continue
                    c = Magnetic()
                    c.component = comp.lower()
                    c.sensor.id = mag.id
                    c.sensor.name = mag.name
                    c.sensor.manufacturer = mag.manufacturer
                    c.sensor.type = mag.type
                    r.add_channel(c)

            for dp in fn.dipole:
                comp = dp.name
                if comp is None:
                    continue
                c = Electric()
                c.component = comp.lower()
                c.translated_azimuth = dp.azimuth
                c.dipole_length = dp.length
                for pot in dp.electrode:
                    if pot.location.lower() in ["n", "e"]:
                        c.positive.id = pot.number
                        c.positive.type = pot.value
                        c.positive.manufacturer = dp.manufacturer
                        c.positive.type = dp.type

                    elif pot.location.lower() in ["s", "w"]:
                        c.negative.id = pot.number
                        c.negative.type = pot.value
                        c.negative.manufacturer = dp.manufacturer
                        c.negative.type = dp.type
                r.add_channel(c)

            for ch in (
                self.site_layout.input_channels
                + self.site_layout.output_channels
            ):
                c = getattr(r, ch.name.lower())
                if c.component in ["hx", "hy", "hz"]:

                    c.location.x = ch.x
                    c.location.y = ch.y
                    c.location.z = ch.z
                elif c.component in ["ex", "ey"]:
                    c.negative.x = ch.x
                    c.negative.y = ch.y
                    c.negative.z = ch.z
                    c.positive.x2 = ch.x2
                    c.positive.y2 = ch.y2
                    c.positive.z2 = ch.z2
                c.measurement_azimuth = ch.orientation
                c.translated_azimuth = ch.orientation
            s.add_run(r)

        return s

    @station_metadata.setter
    def station_metadata(self, station_metadata):
        """
        Set metadata and other values in metadata

        :param sm: DESCRIPTION
        :type sm: TYPE
        :return: DESCRIPTION
        :rtype: TYPE

        """
        sm = station_metadata

        self.site.acquired_by = sm.acquired_by.author
        if sm.data_type is not None:
            self.sub_type = f"{sm.data_type.upper()}_TF"
        else:
            self.sub_type = "MT_TF"
        self.site.name = sm.geographic_name
        self.site.id = sm.id
        self.product_id = sm.fdsn.id
        self.site.location.from_dict(sm.location.to_dict())
        self.site.orientation.angle_to_geographic_north = (
            sm.orientation.angle_to_geographic_north
        )

        for comment in sm.comments.split(";"):
            if comment.count(":") >= 1:
                key, value = comment.split(":", 1)
                try:
                    self.set_attr_from_name(key.strip(), value.strip())
                except:
                    raise AttributeError(f"Cannot set attribute {key}.")
            else:
                self.site.comments.comment["comment"] = comment

        self.provenance.creating_application = sm.provenance.software.name
        self.provenance.create_time = sm.provenance.creation_time
        self.provenance.creator.name = sm.provenance.creator.author
        self.provenance.creator.email = sm.provenance.creator.email
        self.provenance.creator.org = sm.provenance.creator.organization
        self.provenance.creator.org_url = sm.provenance.creator.url
        self.provenance.submitter.name = sm.provenance.submitter.author
        self.provenance.submitter.email = sm.provenance.submitter.email
        self.provenance.submitter.org = sm.provenance.submitter.organization
        self.provenance.submitter.org_url = sm.provenance.submitter.url

        self.external_url.url = sm.provenance.archive.url
        self.external_url.description = sm.provenance.archive.comments

        self.site.start = sm.time_period.start
        self.site.end = sm.time_period.end

        self.processing_info.sign_convention = (
            sm.transfer_function.sign_convention
        )
        self.processing_info.processed_by = (
            sm.transfer_function.processed_by.author
        )
        self.processing_info.processing_software.author = (
            sm.transfer_function.software.author
        )
        self.processing_info.processing_software.name = (
            sm.transfer_function.software.name
        )
        self.processing_info.processing_software.last_mod = (
            sm.transfer_function.software.last_updated
        )
        self.processing_info.processing_tag = "_".join(
            sm.transfer_function.remote_references
        )
        self.site.run_list = sm.transfer_function.runs_processed

        self.site.data_quality_notes.good_from_period = (
            sm.transfer_function.data_quality.good_from_period
        )
        self.site.data_quality_notes.good_to_period = (
            sm.transfer_function.data_quality.good_to_period
        )
        self.site.data_quality_notes.rating = (
            sm.transfer_function.data_quality.rating.value
        )

        # not sure there is a place to put processing parameters yet

        # self.processing_info.processing_software., value, value_dict)s.transfer_function.processing_parameters.append(
        #     {"type": self.processing_info.remote_ref.type}
        # )
        self.field_notes._run_list = []
        for r in sm.runs:
            fn = emtf_xml.Run()
            fn.dipole = []
            fn.magnetometer = []
            fn.instrument.id = r.data_logger.id
            fn.instrument.name = r.data_logger.type
            fn.instrument.manufacturer = r.data_logger.manufacturer
            fn.sampling_rate = r.sample_rate
            fn.start = r.time_period.start
            fn.end = r.time_period.end
            fn.run = r.id

            for comp in ["hx", "hy", "hz"]:
                try:
                    rch = getattr(r, comp)
                    mag = emtf_xml.Magnetometer()
                    mag.id = rch.sensor.id
                    mag.name = rch.sensor.name
                    mag.manufacturer = rch.sensor.manufacturer
                    mag.type = rch.sensor.type
                    fn.magnetometer.append(mag)

                    ch_in = emtf_xml.Magnetic()
                    for item in ["x", "y", "z"]:
                        if getattr(rch.location, item) is None:
                            value = 0.0
                        else:
                            value = getattr(rch.location, item)
                        setattr(ch_in, item, value)

                    ch_in.name = comp.capitalize()
                    ch_in.orientation = rch.translated_azimuth

                    if comp in ["hx", "hy"]:
                        self.site_layout.input_channels.append(ch_in)
                    else:
                        self.site_layout.output_channels.append(ch_in)
                except AttributeError:
                    self.logger.debug("Did not find %s in run", comp)

                if rch.sensor.name in ["NIMS", "LEMI"] and rch.sensor.type in [
                    "fluxgate"
                ]:
                    break

            for comp in ["ex", "ey"]:
                try:
                    c = getattr(r, comp)
                    dp = emtf_xml.Dipole()
                    dp.name = comp.capitalize()
                    dp.azimuth = c.translated_azimuth
                    dp.length = c.dipole_length
                    dp.manufacturer = c.positive.manufacturer
                    dp.type = c.positive.type
                    # fill electrodes
                    pot_p = emtf_xml.Electrode()
                    pot_p.number = c.positive.id
                    pot_p.location = "n" if comp == "ex" else "e"
                    pot_p.value = c.positive.type
                    dp.electrode.append(pot_p)
                    pot_n = emtf_xml.Electrode()
                    pot_n.number = c.negative.id
                    pot_n.value = c.negative.type
                    pot_n.location = "s" if comp == "ex" else "w"
                    dp.electrode.append(pot_n)
                    fn.dipole.append(dp)

                    ch_out = emtf_xml.Electric()
                    for item in ["x", "y", "z"]:
                        if getattr(c.negative, item) is None:
                            value = 0.0
                        else:
                            value = getattr(c.negative, item)
                        setattr(ch_out, item, value)

                    for item in ["x2", "y2", "z2"]:
                        if getattr(c.positive, item) is None:
                            value = 0.0
                        else:
                            value = getattr(c.positive, item)
                        setattr(ch_out, item, value)

                    ch_out.name = comp.capitalize()
                    ch_out.orientation = c.translated_azimuth
                    self.site_layout.output_channels.append(ch_out)

                except AttributeError:
                    self.logger.debug("Did not find %s in run", comp)

            self.field_notes._run_list.append(fn)


def read_emtfxml(fn, **kwargs):
    """
    read an EMTF XML file

    :param fn: DESCRIPTION
    :type fn: TYPE
    :return: DESCRIPTION
    :rtype: TYPE

    """
    from mt_metadata.transfer_functions.core import TF

    obj = EMTFXML(**kwargs)
    obj.read(fn)

    emtf = TF()
    emtf._fn = obj.fn
    emtf.survey_metadata = obj.survey_metadata
    emtf.station_metadata = obj.station_metadata

    emtf.period = obj.data.period
    emtf.impedance = obj.data.z
    emtf.impedance_error = np.sqrt(obj.data.z_var)
    emtf._transfer_function.inverse_signal_power.loc[
        dict(input=["hx", "hy"], output=["hx", "hy"])
    ] = obj.data.z_invsigcov
    emtf._transfer_function.residual_covariance.loc[
        dict(input=["ex", "ey"], output=["ex", "ey"])
    ] = obj.data.z_residcov

    emtf.tipper = obj.data.t
    emtf.tipper_error = np.sqrt(obj.data.t_var)
    emtf._transfer_function.inverse_signal_power.loc[
        dict(input=["hx", "hy"], output=["hx", "hy"])
    ] = obj.data.t_invsigcov
    emtf._transfer_function.residual_covariance.loc[
        dict(input=["hz"], output=["hz"])
    ] = obj.data.t_residcov

    return emtf


def write_emtfxml(tf_object, fn=None, **kwargs):
    """
    Write an XML file from a TF object

    :param tf_obj: DESCRIPTION
    :type tf_obj: TYPE
    :param fn: DESCRIPTION, defaults to None
    :type fn: TYPE, optional
    :return: DESCRIPTION
    :rtype: TYPE

    """

    from mt_metadata.transfer_functions.core import TF

    ex_ey = [
        tf_object.channel_nomenclature["ex"],
        tf_object.channel_nomenclature["ey"],
    ]
    hx_hy = [
        tf_object.channel_nomenclature["hx"],
        tf_object.channel_nomenclature["hy"],
    ]

    if not isinstance(tf_object, TF):
        raise ValueError(
            "Input must be an mt_metadata.transfer_functions.core.TF object"
        )

    emtf = EMTFXML()
    emtf.survey_metadata = tf_object.survey_metadata
    emtf.station_metadata = tf_object.station_metadata

    if emtf.description is None:
        emtf.description = "Magnetotelluric Transfer Functions"

    if emtf.product_id is None:
        emtf.product_id = (
            f"{emtf.survey_metadata.project}."
            f"{emtf.station_metadata.id}."
            f"{emtf.station_metadata.time_period._start_dt.year}"
        )
    tags = []

    emtf.data.period = tf_object.period

    if tf_object.has_impedance():
        tags += ["impedance"]
        emtf.data.z = tf_object.impedance.data
        emtf.data.z_var = tf_object.impedance_error.data**2
    if (
        tf_object.has_residual_covariance()
        and tf_object.has_inverse_signal_power()
    ):
        emtf.data.z_invsigcov = tf_object.inverse_signal_power.loc[
            dict(input=hx_hy, output=hx_hy)
        ].data
        emtf.data.z_residcov = tf_object.residual_covariance.loc[
            dict(input=ex_ey, output=ex_ey)
        ].data
    if tf_object.has_tipper():
        tags += ["tipper"]
        emtf.data.t = tf_object.tipper.data
        emtf.data.t_var = tf_object.tipper_error.data**2

    if (
        tf_object.has_residual_covariance()
        and tf_object.has_inverse_signal_power()
    ):
        emtf.data.t_invsigcov = tf_object.inverse_signal_power.loc[
            dict(input=hx_hy, output=hx_hy)
        ].data
        emtf.data.t_residcov = tf_object.residual_covariance.loc[
            dict(
                input=[tf_object.channel_nomenclature["hz"]],
                output=[tf_object.channel_nomenclature["hz"]],
            )
        ].data

    emtf.tags = ", ".join(tags)
    emtf.period_range.min = emtf.data.period.min()
    emtf.period_range.max = emtf.data.period.max()
    if "skip_field_notes" in kwargs.keys():
        emtf.write(fn=fn, skip_field_notes=kwargs["skip_field_notes"])
    else:
        emtf.write(fn=fn)

    return emtf

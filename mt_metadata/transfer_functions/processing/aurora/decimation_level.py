# -*- coding: utf-8 -*-
"""
Created on Thu Feb 17 14:15:20 2022

@author: jpeacock
"""
# =============================================================================
# Imports
# =============================================================================
import numpy as np
import pandas as pd

from mt_metadata.base.helpers import write_lines
from mt_metadata.base import get_schema, Base

from .band import Band
from .decimation import Decimation
from .estimator import Estimator
from .regression import Regression
from .standards import SCHEMA_FN_PATHS
from .window import Window

# =============================================================================
attr_dict = get_schema("decimation_level", SCHEMA_FN_PATHS)
attr_dict.add_dict(get_schema("decimation", SCHEMA_FN_PATHS), "decimation")
attr_dict.add_dict(get_schema("window", SCHEMA_FN_PATHS), "window")
attr_dict.add_dict(get_schema("regression", SCHEMA_FN_PATHS), "regression")
attr_dict.add_dict(get_schema("estimator", SCHEMA_FN_PATHS), "estimator")


# =============================================================================


def df_from_bands(band_list: list) -> pd.DataFrame:
    """
    Utility function that transforms a list of bands into a dataframe

    Note: The decimation_level here is +1 to agree with EMTF convention.
        Not clear this is really necessary

    Parameters
    ----------
    band_list: list
        obtained from mt_metadata.transfer_functions.processing.aurora.decimation_level.DecimationLevel.bands

    Returns
    -------
    out_df: pd.Dataframe
        Same format as that generated by EMTFBandSetupFile.get_decimation_level()
    """
    df_columns = [
        "decimation_level",
        "lower_bound_index",
        "upper_bound_index",
        "frequency_min",
        "frequency_max",
    ]
    n_rows = len(band_list)
    df_columns_dict = {}
    for col in df_columns:
        df_columns_dict[col] = n_rows * [None]
    for i_band, band in enumerate(band_list):
        df_columns_dict["decimation_level"][i_band] = band.decimation_level + 1
        df_columns_dict["lower_bound_index"][i_band] = band.index_min
        df_columns_dict["upper_bound_index"][i_band] = band.index_max
        df_columns_dict["frequency_min"][i_band] = band.frequency_min
        df_columns_dict["frequency_max"][i_band] = band.frequency_max
    out_df = pd.DataFrame(data=df_columns_dict)
    out_df.sort_values(by="lower_bound_index", inplace=True)
    out_df.reset_index(inplace=True, drop=True)
    return out_df

def get_fft_harmonics(samples_per_window: int, sample_rate: float) -> np.ndarray:
    """
    Works for odd and even number of points.

    Development notes:
    Could be modified with kwargs to support one_sided, two_sided, ignore_dc
    ignore_nyquist, and etc.  Consider taking FrequencyBands as an argument.

    Parameters
    ----------
    samples_per_window: integer
        Number of samples in a window that will be Fourier transformed.
    sample_rate: float
            Inverse of time step between samples,
            Samples per second

    Returns
    -------
    harmonic_frequencies: numpy array
        The frequencies that the fft will be computed.
        These are one-sided (positive frequencies only)
        Does not return Nyquist
        Does return DC component
    """
    n_fft_harmonics = int(samples_per_window / 2)  # no bin at Nyquist,
    delta_t = 1.0 / sample_rate
    harmonic_frequencies = np.fft.fftfreq(samples_per_window, d=delta_t)
    harmonic_frequencies = harmonic_frequencies[0:n_fft_harmonics]
    return harmonic_frequencies


class DecimationLevel(Base):
    __doc__ = write_lines(attr_dict)

    def __init__(self, **kwargs):

        self.window = Window()
        self.decimation = Decimation()
        self.regression = Regression()
        self.estimator = Estimator()

        self._bands = []

        super().__init__(attr_dict=attr_dict, **kwargs)

        # if self.decimation.level == 0:
        #     self.anti_alias_filter = None

    @property
    def bands(self):
        """
        get bands, something weird is going on with appending.

        """
        return_list = []
        for band in self._bands:
            if isinstance(band, dict):
                b = Band()
                b.from_dict(band)
            elif isinstance(band, Band):
                b = band
            return_list.append(b)
        return return_list

    @bands.setter
    def bands(self, value):
        """
        Set bands make sure they are a band object

        :param value: list of bands
        :type value: list, Band

        """

        if isinstance(value, Band):
            self._bands = [value]

        elif isinstance(value, list):
            self._bands = []
            for obj in value:
                if not isinstance(obj, (Band, dict)):
                    raise TypeError(
                        f"List entry must be a Band object not {type(obj)}"
                    )
                if isinstance(obj, dict):
                    band = Band()
                    band.from_dict(obj)

                else:
                    band = obj

                self._bands.append(band)
        else:
            raise TypeError(f"Not sure what to do with {type(value)}")

    def add_band(self, band):
        """
        add a band
        """

        if not isinstance(band, (Band, dict)):
            raise TypeError(
                f"List entry must be a Band object not {type(band)}"
            )
        if isinstance(band, dict):
            obj = Band()
            obj.from_dict(band)

        else:
            obj = band

        self._bands.append(obj)

    @property
    def lower_bounds(self):
        """
        get lower bounds index values into an array.
        """

        return np.array(sorted([band.index_min for band in self.bands]))

    @property
    def upper_bounds(self):
        """
        get upper bounds index values into an array.
        """

        return np.array(sorted([band.index_max for band in self.bands]))

    @property
    def bands_dataframe(self):
        """
        This is just a utility function that transforms a list of bands into a dataframe

        Note: The decimation_level here is +1 to agree with EMTF convention.
        Not clear this is really necessary

        ToDo: Consider adding columns lower_edge, upper_edge to df

        Returns
        -------
        bands_df: pd.Dataframe
            Same format as that generated by EMTFBandSetupFile.get_decimation_level()
        """
        bands_df = df_from_bands(self.bands)
        return bands_df

    @property
    def frequency_sample_interval(self):
        return self.sample_rate_decimation/self.window.num_samples

    @property
    def band_edges(self):
        bands_df = self.bands_dataframe
        band_edges = np.vstack(
            (bands_df.frequency_min.values, bands_df.frequency_max.values)
        ).T
        return band_edges

    def frequency_bands_obj(self):
        """
        Gets a FrequencyBands object that is used as input to processing.
        This used to be needed because I only had

        ToDO: consider adding .to_frequnecy_bands() method directly to self.bands
        Returns
        -------

        """
        from mt_metadata.transfer_functions.processing.aurora.band import (
            FrequencyBands,
        )

        frequency_bands = FrequencyBands(band_edges=self.band_edges)
        return frequency_bands

    @property
    def fft_frequencies(self):
        freqs = get_fft_harmonics(
            self.window.num_samples, self.decimation.sample_rate
        )
        return freqs

    @property
    def sample_rate_decimation(self):
        return self.decimation.sample_rate

    @property
    def harmonic_indices(self):
        return_list = []
        for band in self.bands:
            fc_indices = band.harmonic_indices
            return_list += fc_indices.tolist()
        return_list.sort()
        return return_list

    @property
    def local_channels(self):
        return self.input_channels + self.output_channels

    def to_fc_decimation(self, remote=False, ignore_harmonic_indices=True):
        """
        Generates a FC Decimation() object for use with FC Layer in mth5.

        Ignoring for now these properties
        "time_period.end": "1980-01-01T00:00:00+00:00",
        "time_period.start": "1980-01-01T00:00:00+00:00",

        Parameters
        ----------
        remote: bool
            If True, use reference channels, if False, use local_channels.  We may wish to not pass remote=True when
            _building_ FCs however, because then not all channels will get built.
        ignore_harmonic_indices: bool
            If True, leave harmonic indices at default [-1,], which means all indices.  If False, only the specific
            harmonic indices needed for processing will be stored.  Thus, when building FCs, it maybe best to leave
            this as True, that way all FCs will be stored, so if the band setup is changed, the FCs will still be there.

        Returns:
            fc_dec_obj:mt_metadata.transfer_functions.processing.fourier_coefficients.decimation.Decimation
            A decimation object configured for STFT processing

        """
        from mt_metadata.transfer_functions.processing.fourier_coefficients import (
            Decimation as FourierCoefficientDecimation,
        )
        fc_dec_obj = FourierCoefficientDecimation()
        fc_dec_obj.anti_alias_filter = self.anti_alias_filter
        if remote:
            fc_dec_obj.channels_estimated = self.reference_channels
        else:
            fc_dec_obj.channels_estimated = self.local_channels
        fc_dec_obj.decimation_factor = self.decimation.factor
        fc_dec_obj.decimation_level = self.decimation.level
        if ignore_harmonic_indices:
            pass
        else:
            fc_dec_obj.harmonic_indices = self.harmonic_indices()
        fc_dec_obj.id = f"{self.decimation.level}"
        fc_dec_obj.method = self.method
        fc_dec_obj.pre_fft_detrend_type = self.pre_fft_detrend_type
        fc_dec_obj.prewhitening_type = self.prewhitening_type
        fc_dec_obj.recoloring = self.recoloring
        fc_dec_obj.sample_rate_decimation = self.sample_rate_decimation
        fc_dec_obj.window = self.window

        return fc_dec_obj

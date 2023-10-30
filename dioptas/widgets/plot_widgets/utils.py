# -*- coding: utf-8 -*-
# Dioptas - GUI program for fast processing of 2D X-ray diffraction data
# Principal author: Clemens Prescher (clemens.prescher@gmail.com)
# Copyright (C) 2014-2019 GSECARS, University of Chicago, USA
# Copyright (C) 2015-2018 Institute for Geology and Mineralogy, University of Cologne, Germany
# Copyright (C) 2019-2020 DESY, Hamburg, Germany
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import annotations

import re
from typing import Optional
import numpy as np


def _default_auto_level(data: np.ndarray) -> tuple[float, float]:
    """Compute colormap range from data through histogram

    :param data: Data from which to compute levels
    :returns: (lower limit, upper limit)
    """
    counts, bin_edges = np.histogram(data, bins=3000)
    left_edges = bin_edges[:-1]
    left_edges = left_edges[np.where(counts > 0)]
    counts = counts[np.where(counts > 0)]

    hist_y_cumsum = np.cumsum(counts)
    hist_y_sum = np.sum(counts)

    max_ind = np.where(hist_y_cumsum < (0.996 * hist_y_sum))
    min_level = np.mean(left_edges[:2])

    if len(max_ind[0]):
        max_level = left_edges[max_ind[0][-1]]
    else:
        max_level = 0.5 * np.max(left_edges)

    if len(left_edges[left_edges > 0]) > 0:
        min_level = max(min_level, np.nanmin(left_edges[left_edges > 0]))
    return min_level, max_level


def _minmax_auto_level(data: np.ndarray) -> tuple[float, float]:
    """Returns min/max of the data

    :param data: Data from which to compute levels
    :returns: (min, max)
    """
    return float(np.min(data)), float(np.max(data))


def _mean3std_auto_level(data: np.ndarray) -> tuple[float, float]:
    """Returns mean+/-3std clipped to min/max of the data

    :param data: Data from which to compute levels
    :returns: (lower limit, upper limit)
    """
    mean = np.mean(data, dtype=np.float64)
    std = np.std(data, dtype=np.float64)
    minimum, maximum = _minmax_auto_level(data)
    return max(mean - 3 * std, minimum), min(mean + 3 * std, maximum)


def _percentile_auto_level(
    data: np.ndarray, percentile: float = 1.0
) -> tuple[float, float]:
    """Returns data range corresponding to [precentile, 100-percentile]

    :param data: Data from which to compute levels
    :returns: (lower limit, upper limit)
    """
    if not 0.0 <= percentile < 50.0:
        raise ValueError("Percentiles must be in the range [0, 50[")
    lower, upper = np.percentile(data, [percentile, 100.0 - percentile])
    return float(lower), float(upper)


class AutoLevel:
    """Handle colormap range autoscale computation.

    This class stores settings: autoscale mode

    Instances of this class are callable:
    >>> auto_level = AutoLevel()
    >>> range_ = auto_level.get_range(data)
    """

    _MODES = {
        "default": _default_auto_level,
        "minmax": _minmax_auto_level,
        "mean3std": _mean3std_auto_level,
    }
    _PERCENTILE_REGEXP = re.compile(r"(?P<value>\d+(\.\d*)?|\.\d+)percentile")

    def __init__(self):
        self.mode: str = "default"
        """Autoscale mode in 'default', 'minmax', 'mean3std', '%fpercentile'"""

    def get_range(self, data: Optional[np.ndarray]) -> Optional[tuple[float, float]]:
        """Returns colormap range from data for current settings

        :param data: Data from which to compute colormap range
        :returns: (min, max) or None
        """
        if data is None:
            return None

        filtered_data = data[np.isfinite(data)]
        if filtered_data.size == 0:
            return None

        func = self._MODES.get(self.mode, None)
        if func is not None:
            return func(filtered_data)
        match = self._PERCENTILE_REGEXP.match(self.mode)
        if match is not None:
            return _percentile_auto_level(filtered_data, percentile=float(match["value"]))
        raise ValueError(f"Unsupported mode: {self.mode}")


auto_level = AutoLevel()

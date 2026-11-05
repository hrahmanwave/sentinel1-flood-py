"""Unit conversion and speckle filtering for Sentinel-1 backscatter.

Earth Engine's ``COPERNICUS/S1_GRD`` stores backscatter in dB. Statistical speckle
filters such as Lee work on linear (natural) power, so they convert, filter, and
convert back.
"""

from __future__ import annotations

import ee

# Equivalent number of looks for Sentinel-1 IW GRD high resolution products (~4.4).
DEFAULT_ENL = 4.4


def to_natural(img: ee.Image) -> ee.Image:
    """dB -> linear power: 10 ** (dB / 10)."""
    return ee.Image(10).pow(img.divide(10)).rename(img.bandNames())


def to_db(img: ee.Image) -> ee.Image:
    """Linear power -> dB: 10 * log10(x)."""
    return img.log10().multiply(10).rename(img.bandNames())


def _keep_metadata(filtered: ee.Image, original: ee.Image) -> ee.Image:
    return ee.Image(
        filtered.copyProperties(original).set(
            "system:time_start", original.get("system:time_start")
        )
    )


def focal_median_filter(img: ee.Image, radius_m: float = 50) -> ee.Image:
    """Simple circular focal median in dB. Fast, but blurs edges."""
    filtered = img.focalMedian(radius_m, "circle", "meters").rename(img.bandNames())
    return _keep_metadata(filtered, img)


def lee_filter(img: ee.Image, kernel_size: int = 7, enl: float = DEFAULT_ENL) -> ee.Image:
    """Lee (1980) adaptive speckle filter.

    filtered = mean + w * (x - mean), with w = clamp(1 - Cu^2 / Ci^2, 0, 1),
    where Cu^2 = 1 / ENL (speckle variation) and Ci^2 = var / mean^2 (local variation).
    Homogeneous areas get smoothed (w ~ 0); edges and bright targets are kept (w ~ 1).

    Input and output are in dB; filtering happens in linear power.
    """
    if kernel_size < 3 or kernel_size % 2 == 0:
        raise ValueError("kernel_size must be an odd integer >= 3")
    nat = to_natural(img)
    kernel = ee.Kernel.square(kernel_size // 2, "pixels")
    local_mean = nat.reduceNeighborhood(ee.Reducer.mean(), kernel)
    local_var = nat.reduceNeighborhood(ee.Reducer.variance(), kernel)

    cu2 = 1.0 / enl
    ci2 = local_var.divide(local_mean.pow(2))
    weight = ee.Image(1).subtract(ee.Image(cu2).divide(ci2)).clamp(0, 1)

    filtered_nat = local_mean.add(weight.multiply(nat.subtract(local_mean)))
    filtered = to_db(filtered_nat.rename(img.bandNames()))
    return _keep_metadata(filtered, img)

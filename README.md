# sentinel1-flood-py

Flood inundation mapping from Sentinel-1 SAR using Google Earth Engine, in Python.

This is a Python port and extension of
[sentinel1-flood-detection](https://github.com/hrahmanwave/sentinel1-flood-detection) (GEE JavaScript).
The workflow: filter Sentinel-1 GRD scenes, reduce speckle, compare pre- and post-event
backscatter, threshold the change, and mask permanent water and steep terrain.

> **Status:** early development. Collection filtering and speckle filtering are in place;
> change detection, thresholding and masks are next.

## Installation

```bash
git clone https://github.com/hrahmanwave/sentinel1-flood-py.git
cd sentinel1-flood-py
pip install -e ".[dev]"
```

## Earth Engine setup

You need a Google Cloud project registered for Earth Engine.

```python
import ee
ee.Authenticate()                     # once per machine
ee.Initialize(project="your-gcp-project-id")
```

## Usage (so far)

```python
import ee
from s1flood import load_aoi, get_s1_collection, composite, lee_filter

ee.Initialize(project="your-gcp-project-id")

aoi = load_aoi("aoi.geojson")
pre = get_s1_collection(aoi, "2022-05-01", "2022-05-25", polarization="VV")
post = get_s1_collection(aoi, "2022-06-15", "2022-06-25", polarization="VV")

pre_img = composite(pre.map(lee_filter), aoi)
post_img = composite(post.map(lee_filter), aoi)
```

## Roadmap

- [x] Sentinel-1 collection filtering (date, polarization, orbit pass, mode)
- [x] Speckle filtering (focal median, Lee)
- [ ] Change detection (dB difference, ratio)
- [ ] Otsu thresholding
- [ ] Permanent water (JRC) and slope/HAND masks
- [ ] Command-line interface and GeoTIFF export
- [ ] Case studies: 2022 Sylhet flood (Bangladesh), July 2021 eastern Kentucky flood (USA)

## Data

- Sentinel-1 GRD: `COPERNICUS/S1_GRD` (Earth Engine catalog, values in dB)

## License

MIT

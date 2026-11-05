"""Build filtered Sentinel-1 GRD collections and composites."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import ee

S1_COLLECTION_ID = "COPERNICUS/S1_GRD"
VALID_POLARIZATIONS = {"VV", "VH"}
VALID_ORBIT_PASSES = {"ASCENDING", "DESCENDING"}
VALID_REDUCERS = {"median", "mean", "min", "max"}


def validate_params(
    start: str,
    end: str,
    polarization: str = "VV",
    orbit_pass: str | None = None,
) -> None:
    """Check query parameters before sending anything to Earth Engine.

    Dates are ISO strings (YYYY-MM-DD). ``end`` is exclusive, as in ``filterDate``.
    """
    try:
        d0 = date.fromisoformat(start)
        d1 = date.fromisoformat(end)
    except ValueError as err:
        raise ValueError(f"Dates must be YYYY-MM-DD, got {start!r} and {end!r}") from err
    if d1 <= d0:
        raise ValueError(f"end ({end}) must be after start ({start})")
    if polarization not in VALID_POLARIZATIONS:
        raise ValueError(f"polarization must be one of {sorted(VALID_POLARIZATIONS)}")
    if orbit_pass is not None and orbit_pass not in VALID_ORBIT_PASSES:
        raise ValueError(f"orbit_pass must be one of {sorted(VALID_ORBIT_PASSES)} or None")


def read_geojson_geometries(geojson: dict) -> list[dict]:
    """Return the geometry dicts in a GeoJSON Geometry, Feature or FeatureCollection."""
    kind = geojson.get("type")
    if kind == "FeatureCollection":
        geoms = [f["geometry"] for f in geojson.get("features", []) if f.get("geometry")]
    elif kind == "Feature":
        geoms = [geojson["geometry"]] if geojson.get("geometry") else []
    elif kind in {"Polygon", "MultiPolygon", "Point", "MultiPoint", "LineString",
                  "MultiLineString", "GeometryCollection"}:
        geoms = [geojson]
    else:
        raise ValueError(f"Unsupported GeoJSON type: {kind!r}")
    if not geoms:
        raise ValueError("GeoJSON contains no geometry")
    return geoms


def load_aoi(path: str | Path) -> ee.Geometry:
    """Load an area of interest from a GeoJSON file as an ``ee.Geometry``."""
    geojson = json.loads(Path(path).read_text())
    geoms = read_geojson_geometries(geojson)
    if len(geoms) == 1:
        return ee.Geometry(geoms[0])
    features = [ee.Feature(ee.Geometry(g)) for g in geoms]
    return ee.FeatureCollection(features).geometry()


def get_s1_collection(
    aoi: ee.Geometry,
    start: str,
    end: str,
    polarization: str = "VV",
    orbit_pass: str | None = None,
    instrument_mode: str = "IW",
    resolution_m: int = 10,
) -> ee.ImageCollection:
    """Sentinel-1 GRD scenes over ``aoi`` between ``start`` (inclusive) and ``end`` (exclusive).

    Returns a single-band collection (the requested polarization), in dB.
    Use one ``orbit_pass`` for pre- and post-event images when possible, so that
    differences reflect the surface rather than viewing geometry.
    """
    validate_params(start, end, polarization, orbit_pass)
    col = (
        ee.ImageCollection(S1_COLLECTION_ID)
        .filterBounds(aoi)
        .filterDate(start, end)
        .filter(ee.Filter.eq("instrumentMode", instrument_mode))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", polarization))
        .filter(ee.Filter.eq("resolution_meters", resolution_m))
    )
    if orbit_pass is not None:
        col = col.filter(ee.Filter.eq("orbitProperties_pass", orbit_pass))
    return col.select(polarization)


def composite(col: ee.ImageCollection, aoi: ee.Geometry, reducer: str = "median") -> ee.Image:
    """Reduce a collection to one image clipped to ``aoi``."""
    if reducer not in VALID_REDUCERS:
        raise ValueError(f"reducer must be one of {sorted(VALID_REDUCERS)}")
    return getattr(col, reducer)().clip(aoi)

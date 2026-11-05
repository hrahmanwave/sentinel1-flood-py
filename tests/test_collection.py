import pytest

from s1flood.collection import read_geojson_geometries, validate_params

POLY = {"type": "Polygon", "coordinates": [[[91.8, 24.8], [92.0, 24.8], [92.0, 25.0], [91.8, 24.8]]]}


def test_valid_params_pass():
    validate_params("2022-05-01", "2022-05-25", "VV", "DESCENDING")


@pytest.mark.parametrize(
    "start, end",
    [("2022-05-25", "2022-05-01"), ("2022-05-01", "2022-05-01"), ("2022/05/01", "2022-05-25")],
)
def test_bad_dates_raise(start, end):
    with pytest.raises(ValueError):
        validate_params(start, end)


def test_bad_polarization_raises():
    with pytest.raises(ValueError):
        validate_params("2022-05-01", "2022-05-25", polarization="HH")


def test_bad_orbit_raises():
    with pytest.raises(ValueError):
        validate_params("2022-05-01", "2022-05-25", orbit_pass="ascending")


def test_geojson_variants():
    assert read_geojson_geometries(POLY) == [POLY]
    assert read_geojson_geometries({"type": "Feature", "geometry": POLY, "properties": {}}) == [POLY]
    fc = {"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": POLY}] * 2}
    assert len(read_geojson_geometries(fc)) == 2


def test_empty_geojson_raises():
    with pytest.raises(ValueError):
        read_geojson_geometries({"type": "FeatureCollection", "features": []})

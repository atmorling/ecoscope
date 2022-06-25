import datetime
import uuid
from tempfile import TemporaryDirectory

import geopandas as gpd
import pandas as pd
import pytest
import pytz
from shapely.geometry import Point

import ecoscope

if not pytest.earthranger:
    pytest.skip(
        "Skipping tests because connection to EarthRanger is not available.",
        allow_module_level=True,
    )


def test_get_subject_observations(er_io):
    relocations = er_io.get_subject_observations(
        subject_ids=er_io.SUBJECT_IDS,
        include_subject_details=True,
        include_source_details=True,
        include_subjectsource_details=True,
    )
    assert isinstance(relocations, ecoscope.base.Relocations)
    assert "groupby_col" in relocations
    assert "fixtime" in relocations
    assert "extra__source" in relocations


def test_get_subject_no_observations(er_io):
    with pytest.raises(ecoscope.contrib.dasclient.DasClientNotFound):
        er_io.get_subject_observations(
            subject_ids=str(uuid.uuid4()),
            include_subject_details=True,
            include_source_details=True,
            include_subjectsource_details=True,
        )


def test_get_source_observations(er_io):
    relocations = er_io.get_source_observations(
        source_ids=er_io.SOURCE_IDS,
        include_source_details=True,
    )
    assert isinstance(relocations, ecoscope.base.Relocations)
    assert "fixtime" in relocations
    assert "groupby_col" in relocations


def test_get_source_no_observations(er_io):
    relocations = er_io.get_source_observations(
        source_ids=str(uuid.uuid4()),
        include_source_details=True,
    )
    assert relocations.empty


def test_get_subjectsource_observations(er_io):
    relocations = er_io.get_subjectsource_observations(
        subjectsource_ids=er_io.SUBJECTSOURCE_IDS,
        include_source_details=True,
    )
    assert isinstance(relocations, ecoscope.base.Relocations)
    assert "fixtime" in relocations
    assert "groupby_col" in relocations


def test_get_subjectsource_no_observations(er_io):
    relocations = er_io.get_subjectsource_observations(
        subjectsource_ids=str(uuid.uuid4()),
        include_source_details=True,
    )
    assert relocations.empty


def test_get_subjectsource_observations_with_pagesize_one(er_io):
    relocations = er_io.get_subjectsource_observations(
        subjectsource_ids=er_io.SUBJECTSOURCE_IDS[0],
        include_source_details=True,
        page_size=1,
    )
    assert isinstance(relocations, ecoscope.base.Relocations)
    assert len(relocations) == 1


def test_get_subjectgroup_observations(er_io):
    relocations = er_io.get_subjectgroup_observations(group_name=er_io.GROUP_NAME)
    assert "groupby_col" in relocations


def test_get_events(er_io):
    events = er_io.get_events(page_size=100)
    assert len(events) <= 100


@pytest.mark.filterwarnings("ignore:All-NaN slice encountered:RuntimeWarning")
@pytest.mark.filterwarnings("ignore:Mean of empty slice:RuntimeWarning")
def test_collar_voltage(er_io):
    start_time = pytz.utc.localize(datetime.datetime.now() - datetime.timedelta(days=31))
    observations = er_io.get_subjectgroup_observations(
        group_name=er_io.GROUP_NAME,
        include_subject_details=True,
        include_subjectsource_details=True,
        include_details="true",
    )

    with TemporaryDirectory() as output_folder:
        ecoscope.plotting.plot.plot_collar_voltage(observations, start_time=start_time, output_folder=output_folder)


def test_das_client_method(er_io):
    er_io.pulse()
    er_io.get_me()


def test_get_patrols(er_io):
    patrols = er_io.get_patrols()
    assert len(patrols) > 0


def test_post_observations(er_io):
    observations = gpd.GeoDataFrame.from_dict(
        [
            {
                "recorded_at": datetime.datetime.utcnow(),
                "geometry": Point(0, 0),
                "source": er_io.SOURCE_IDS[0],
            },
            {
                "recorded_at": datetime.datetime.utcnow(),
                "geometry": Point(0, 0),
                "source": er_io.SOURCE_IDS[0],
            },
            {
                "recorded_at": datetime.datetime.utcnow(),
                "geometry": Point(1, 1),
                "source": er_io.SOURCE_IDS[1],
            },
        ]
    )

    response = er_io.post_observations(observations)
    assert len(response) == 3
    assert "location" in response
    assert "recorded_at" in response


def test_post_events(er_io):
    events = [
        {
            "id": str(uuid.uuid4()),
            "title": "Accident",
            "event_type": "accident_rep",
            "time": pd.Timestamp.utcnow(),
            "location": {"longitude": "38.033294677734375", "latitude": "-2.9553841592697982"},
            "priority": 200,
            "state": "new",
            "event_details": {"type_accident": "head-on collision", "number_people_involved": 3, "animals_involved": 1},
            "is_collection": False,
            "icon_id": "accident_rep",
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Accident",
            "event_type": "accident_rep",
            "time": pd.Timestamp.utcnow(),
            "location": {"longitude": "38.4906005859375", "latitude": "-3.0321834919139206"},
            "priority": 300,
            "state": "active",
            "event_details": {
                "type_accident": "side-impact collision",
                "number_people_involved": 2,
                "animals_involved": 1,
            },
            "is_collection": False,
            "icon_id": "accident_rep",
        },
    ]
    results = er_io.post_event(events)
    results["time"] = pd.to_datetime(results["time"], utc=True)

    expected = pd.DataFrame(events)
    results = results[expected.columns]
    pd.testing.assert_frame_equal(results, expected)


def test_patch_event(er_io):
    event = [
        {
            "id": str(uuid.uuid4()),
            "title": "Arrest",
            "event_type": "arrest_rep",
            "time": pd.Timestamp.utcnow(),
            "location": {"longitude": 38.11809539794921, "latitude": -3.4017015747197306},
            "priority": 200,
            "state": "new",
            "event_details": {
                "arrestrep_dateofbirth": "1985-01-1T13:00:00.000Z",
                "arrestrep_nationality": "other",
                "arrestrep_timeofarrest": datetime.datetime.utcnow().isoformat(),
                "arrestrep_reaonforarrest": "firearm",
                "arrestrep_arrestingranger": "Ranger Siera",
            },
            "is_collection": False,
            "icon_id": "arrest_rep",
        }
    ]
    er_io.post_event(event)
    event_id = event[0]["id"]

    updated_event = pd.DataFrame(
        [
            {
                "priority": 300,
                "state": "active",
                "location": {"longitude": "38.4576416015625", "latitude": "-4.135503657998179"},
            }
        ]
    )

    result = er_io.patch_event(event_id=event_id, events=updated_event)
    result = result[["priority", "state", "location"]]
    pd.testing.assert_frame_equal(result, updated_event)


def test_get_observation_for_patrol(er_io):
    patrols = er_io.get_patrols()
    observations = er_io.get_observations_for_patrols(
        patrols,
        include_source_details=False,
        include_subject_details=False,
        include_subjectsource_details=False,
    )
    assert not observations.empty


def test_users(er_io):
    users = er_io.get_users()
    assert not users.empty

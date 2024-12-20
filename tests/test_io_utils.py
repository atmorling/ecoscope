import json
import os
import pytest

import fsspec
import pandas as pd
from unittest.mock import Mock, patch
from http.client import HTTPMessage
from requests.exceptions import RetryError

import ecoscope

pytestmark = pytest.mark.io


def test_download_file_github_csv():
    ECOSCOPE_RAW = "https://raw.githubusercontent.com/wildlife-dynamics/ecoscope/master"
    output_dir = "tests/test_output"
    ecoscope.io.download_file(
        f"{ECOSCOPE_RAW}/tests/sample_data/vector/movebank_data.csv",
        os.path.join(output_dir, "download_data.csv"),
        overwrite_existing=True,
    )

    data = pd.read_csv(os.path.join(output_dir, "download_data.csv"))
    assert len(data) > 0


def test_download_file_gdrive_share_link():
    output_dir = "tests/test_output"
    ecoscope.io.download_file(
        "https://drive.google.com/file/d/1-AQ9_oacUCcAaiZ6SWU77hZWp1oArQw6/view?usp=drive_link",
        os.path.join(output_dir, "download_data.csv"),
        overwrite_existing=True,
    )

    data = pd.read_csv(os.path.join(output_dir, "download_data.csv"))
    assert len(data) > 0


def test_download_file_gdrive():
    output_dir = "tests/test_output"
    ecoscope.io.download_file(
        "https://drive.google.com/uc?export=download&id=1-AQ9_oacUCcAaiZ6SWU77hZWp1oArQw6",
        os.path.join(output_dir, "download_data.csv"),
        overwrite_existing=True,
    )

    data = pd.read_csv(os.path.join(output_dir, "download_data.csv"))
    assert len(data) > 0


def test_download_file_gdrive_zip():
    output_dir = "tests/test_output"
    ecoscope.io.download_file(
        "https://drive.google.com/uc?export=download&id=1YNQ6FBtlTAxmo8vmK59oTPBhAltI3kfK",
        output_dir,
        overwrite_existing=True,
        unzip=True,
    )

    data = pd.read_csv(os.path.join(output_dir, "movbank_data.csv"))
    assert len(data) > 0


def test_download_file_dropbox_json():
    URL = "https://www.dropbox.com/scl/fi/qaw3krcsnot69x94mdfxy/config.json?rlkey=zdmipl2la7rplgl218vc13end&dl=1"
    output_path = "tests/test_output/config.json"
    ecoscope.io.download_file(URL, output_path)

    with fsspec.open(
        output_path,
        mode="rt",
    ) as file:
        config = json.loads(file.read())
        assert config is not None


def test_download_file_dropbox_share_link():
    output_dir = "tests/test_output"
    ecoscope.io.download_file(
        "https://www.dropbox.com/scl/fi/qaw3krcsnot69x94mdfxy/config.json?rlkey=zdmipl2la7rplgl218vc13end&dl=0",
        os.path.join(output_dir, "download_data.csv"),
        overwrite_existing=True,
    )

    data = pd.read_csv(os.path.join(output_dir, "download_data.csv"))
    assert len(data) > 0


@patch("urllib3.connectionpool.HTTPConnectionPool._get_conn")
def test_download_file_retry_on_error(mock):
    mock.return_value.getresponse.side_effect = [
        Mock(status=500, msg=HTTPMessage(), headers={}),
        Mock(status=504, msg=HTTPMessage(), headers={}),
        Mock(status=503, msg=HTTPMessage(), headers={}),
    ]

    url = "https://totallyreal.com"
    output_dir = "tests/test_output"

    with pytest.raises(RetryError):
        ecoscope.io.download_file(
            url,
            output_dir,
            overwrite_existing=True,
        )

    assert mock.call_count == 3

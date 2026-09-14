import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "packages"))
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from trinetra_core.config import settings
import ingest_catalogue as ing


def setup_module(module):
    settings.grid_email = "alice@example.com"
    settings.grid_password = "pw"
    settings.grid_rtsp_host = "103.250.160.189:8554"
    settings.grid_hls_base = "https://cctv.corp8.cloud"
    settings.grid_whep_host = "103.250.160.189:8889"


def test_rtsp_url_percent_encodes_email():
    assert ing._rtsp_url("cam04") == "rtsp://alice%40example.com:pw@103.250.160.189:8554/stream/cam04"


def test_hls_url_template():
    assert ing._hls_url("cam04") == "https://cctv.corp8.cloud/cam04/index.m3u8"


def test_whep_url_includes_credentials():
    assert ing._whep_url("cam04") == "http://alice%40example.com:pw@103.250.160.189:8889/stream/cam04/whep"


def test_iter_cameras_handles_strings_dicts_and_wrapper():
    assert [c["id"] for c in ing._iter_cameras(["cam01", "cam02"])] == ["cam01", "cam02"]
    assert ing._iter_cameras([{"id": "cam03", "name": "Main Gate"}])[0]["name"] == "Main Gate"
    assert ing._iter_cameras({"cameras": ["cam05"]})[0]["id"] == "cam05"

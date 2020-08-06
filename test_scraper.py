from socket import socket
from unittest import mock

import pytest

from torrent_tracker_scraper import scraper
from torrent_tracker_scraper.scraper import Connection, Scraper


@pytest.fixture
def scraper_basic():
    scraper_ = scraper.Scraper(
        trackers=["udp://bt2.archive.org:6969"],
        infohashes=["73C36F980F5B1A40348678036575CCC1E0BB0E4E"],
    )
    scraper_.connection = Connection("bt2.archive.org", 6969, 10)

    scraper_.transaction_id = 14400  # fixed in return value of socket.recv
    scraper_.connection_id = 5802853403918399090  #  fixed in return value of socket.recv

    return scraper_

@pytest.fixture
def mock_response():
    return [
        {
            "tracker": "udp//:bt2.archive.org:6969",
            "results": [
                {
                    "infohash": "73C36F980F5B1A40348678036575CCC1E0BB0E4E",
                    "seeders": 0,
                    "completed": 0,
                    "leechers": 0,
                }
            ],
        }
    ]


@pytest.fixture
def good_infohashes():
    return [
        "88334ec1d90afe94a22c6de5756268599f5f8ea2",
        "5b6a484a018beed4d01f2f57e6d029a4190a9d04",
    ]


@pytest.fixture
def mixed_infohashes():
    return [
        "88334ec1d90afe94a22c",
        "6de5756268599f5f8ea2",
        "5b6a484a018beed",
        "4d01f2f57e6d029a4190a9d04",
        "88334ec1d90afe94a22c6de5756268599f5f8ea2",
        "5b6a484a018beed4d01f2f57e6d029a4190a9d04",
    ]


def test_parse_none_infohashes():
    scraper_ = scraper.Scraper()
    assert scraper_.parse_infohashes() == []


def test_parse_empty_infohashes():
    scraper_ = scraper.Scraper(infohashes=[])
    assert scraper_.parse_infohashes() == []


def test_single_infohash_parsing(good_infohashes):
    scraper_ = scraper.Scraper(infohashes=good_infohashes[0])
    assert scraper_.parse_infohashes() == [good_infohashes[0]]


def test_multiple_infohashes_parsing(good_infohashes):
    scraper_ = scraper.Scraper(infohashes=good_infohashes)
    assert scraper_.parse_infohashes() == good_infohashes


def test_string_type_infohashes_parsing(good_infohashes):
    scraper_ = scraper.Scraper(
        infohashes="88334ec1d90afe94a22c6de5756268599f5f8ea2,5b6a484a018beed4d01f2f57e6d029a4190a9d04"
    )
    assert scraper_.parse_infohashes() == good_infohashes


def test_string_type_infohashes_parsing_with_multiple_commas(good_infohashes):
    scraper_ = scraper.Scraper(
        infohashes="88334ec1d90afe94a22c6de5756268599f5f8ea2,5b6a484a018beed4d01f2f57e6d029a4190a9d04, , ,"
    )
    assert scraper_.parse_infohashes() == good_infohashes


def test_bad_infohash_parsing(mixed_infohashes):
    scraper_ = scraper.Scraper(infohashes=["88334ec1d90afe94a22c6de575626"])
    assert scraper_.parse_infohashes() == []
    scraper_ = scraper.Scraper(infohashes=mixed_infohashes)
    assert scraper_.parse_infohashes() == [
        "88334ec1d90afe94a22c6de5756268599f5f8ea2",
        "5b6a484a018beed4d01f2f57e6d029a4190a9d04",
    ]


def test_get_trackers():
    scraper_ = scraper.Scraper()
    assert type(scraper_.get_trackers()) == list


def test_connect_request(monkeypatch, scraper_basic):
    recv = lambda s, f: b"\x00\x00\x00\x00\x00\x008@P\x87\xe0m\x108\xf6r"
    monkeypatch.setattr(socket, "recv", recv)
    response_transaction_id, connection_id = scraper_basic._connect_request(scraper_basic.transaction_id)

    assert response_transaction_id == scraper_basic.transaction_id
    assert connection_id == scraper_basic.connection_id


def test_connect_request_failure(monkeypatch, scraper_basic):
    recv = lambda s, f: b"\x00\x00\x00\x00"
    monkeypatch.setattr(socket, "recv", recv)
    with pytest.raises(Exception) as e:
        scraper_basic._connect_request(123)

    assert "Unpacking connect request response failed" in str(e.value)

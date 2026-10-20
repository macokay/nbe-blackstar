import csv

from nbe_blackstar import bridge as nbe


def test_timeseries_writes_header_and_raw_values(tmp_path, monkeypatch):
    path = tmp_path / "timeseries.csv"
    monkeypatch.setattr(nbe, "TIMESERIES_FILE", str(path))
    nbe.log_timeseries({"operating_data/content": "-2933.9", "consumption_data/counter": "46541.4"})
    rows = list(csv.reader(open(path)))
    assert rows[0] == ["timestamp", "content_raw", "counter_raw"]
    assert rows[1][1:] == ["-2933.9", "46541.4"]


def test_timeseries_appends_without_duplicating_header(tmp_path, monkeypatch):
    path = tmp_path / "timeseries.csv"
    monkeypatch.setattr(nbe, "TIMESERIES_FILE", str(path))
    nbe.log_timeseries({"operating_data/content": "1", "consumption_data/counter": "2"})
    nbe.log_timeseries({"operating_data/content": "3", "consumption_data/counter": "4"})
    rows = list(csv.reader(open(path)))
    assert len(rows) == 3
    assert rows[0][0] == "timestamp"


def test_timeseries_write_failure_does_not_raise(tmp_path, monkeypatch, caplog):
    monkeypatch.setattr(nbe, "TIMESERIES_FILE", str(tmp_path / "missing" / "timeseries.csv"))
    nbe.log_timeseries({"operating_data/content": "1", "consumption_data/counter": "2"})
    assert "Unable to write timeseries" in caplog.text


def test_cycle_wrapper_survives_unexpected_error(monkeypatch, caplog):
    def boom(client):
        raise FileNotFoundError("simulated")
    monkeypatch.setattr(nbe, "refresh_statuses", boom)
    assert nbe.safe_refresh(object()) is False
    assert "Refresh cycle failed" in caplog.text

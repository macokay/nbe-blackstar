from types import SimpleNamespace

from frames import Response_frame


def _frame(payload_bytes, seq=7, function=4):
    header = (
        b"abcdefghijkl"
        + b"123456"
        + b"\x02"
        + ("%02d" % function).encode()
        + ("%2d" % seq).encode()
        + b"0"
        + ("%03d" % len(payload_bytes)).encode()
    )
    return header + payload_bytes + b"\x04"


def _decode(payload_bytes):
    request = SimpleNamespace(sequencenumber=7, appid="abcdefghijkl")
    frame = Response_frame(request)
    frame.decode(_frame(payload_bytes))
    return frame.payload


def test_ascii_payload_decodes():
    assert _decode(b"operating_data/boiler_temp=69.4") == "operating_data/boiler_temp=69.4"


def test_utf8_danish_letters_decode():
    text = "advanced_data/note=æøå"
    assert _decode(text.encode("utf-8")) == text


def test_latin1_payload_falls_back_instead_of_crashing():
    text = "advanced_data/note=æøå"
    assert _decode(text.encode("latin-1")) == text

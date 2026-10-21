from types import SimpleNamespace

from nbe_blackstar.frames import Response_frame


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


def _decode_raw(record, seq=7):
    request = SimpleNamespace(sequencenumber=seq, appid="abcdefghijkl")
    Response_frame(request).decode(record)


def _message_of(record):
    try:
        _decode_raw(record)
    except IOError as exc:
        return str(exc)
    raise AssertionError("expected IOError")


def test_bad_start_byte_message_names_check():
    record = bytearray(_frame(b"x"))
    record[18] = 0x03
    assert "start byte" in _message_of(bytes(record))


def test_sequence_mismatch_message_names_check_and_numbers():
    message = _message_of(_frame(b"x", seq=8))
    assert "sequence number" in message
    assert "8" in message and "7" in message


def test_length_mismatch_message_names_check_and_sizes():
    message = _message_of(_frame(b"abc") + b"zz")
    assert "frame length" in message
    assert "33" in message


def test_short_frame_message_names_check():
    assert "short frame" in _message_of(b"x" * 18 + b"\x02" + b"y" * 3)


def test_bad_end_byte_message_names_check():
    record = bytearray(_frame(b"x"))
    record[-1] = 0x05
    assert "end byte" in _message_of(bytes(record))

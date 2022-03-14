from tails import IOWrapper
import pytest
import io
import sys

@pytest.fixture
def empty_byteIO():
    return io.BytesIO(b"") 


def generate_string(string, num):
    base = b""
    i = 0
    while i < num:
        base += string
        i+= 1
    return base

@pytest.fixture
def test_string():
    return b"test string, disperse\n" 

@pytest.fixture
def multiline_byteIO(test_string):
    
    base = generate_string(test_string, 10)
    max_len = len(base)
    return [io.BytesIO(base), len(test_string), max_len]

@pytest.fixture
def shorter_byteIO(test_string):
    base = generate_string(test_string, 5)
    max_len = len(base)
    return [io.BytesIO(base), len(test_string), max_len]

def test_empty(empty_byteIO):
    wrapper = IOWrapper(empty_byteIO)
    assert wrapper.position == 0
    assert wrapper._end_position == 0
    assert wrapper._start_position == 0
    assert wrapper.seek_last_bytes(15) == 0
    assert wrapper.seek_start_of_line() == 0
    assert wrapper.seek_previous_lines(5) == 0
    empty = b""
    for k in wrapper:
        empty += k
    assert len(empty) == 0
    empty_byteIO.write(b"written")
    changed, increased = wrapper.check_size()
    assert changed and increased
    s = next(wrapper)
    assert wrapper._ended_without_eos
    assert s == "written"
    empty_byteIO.write(b"\n\nwritten")
    wrapper.check_size()
    s = next(wrapper)
    s = next(wrapper)
    assert s != "\n"

def test_full(multiline_byteIO, shorter_byteIO, test_string):
    wrapper = IOWrapper(multiline_byteIO[0])
    blen = multiline_byteIO[1]
    max_len = multiline_byteIO[2]
    assert wrapper.position == max_len 
    assert wrapper._end_position == max_len
    wrapper.seek_previous_lines(3)
    assert wrapper.seek_previous_lines(2) == max_len - blen * 5
    assert wrapper.seek_previous_lines(20) == 0
    assert wrapper._seek_end() == max_len
    assert wrapper.seek_previous_lines(1) == max_len - blen
    wrapper._seek_end()
    assert wrapper.seek_start_of_line() == max_len - blen

    wrapper._base = shorter_byteIO[0]
    changed, increased = wrapper.check_size()
    assert changed and not increased
    assert wrapper._end_position == shorter_byteIO[2]
    assert wrapper._cur_postion == shorter_byteIO[2]

    wrapper.seek_previous_lines(2)
    i = 0
    for line in wrapper:
        assert line == test_string.decode(sys.stdout.encoding).replace("\n", "")
        i+= 1
    assert i == 2

    
        
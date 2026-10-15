"""Checkpoint capture before verification; no simulation/model transitions.

CT2 and CT3 bytes/decoders are the existing generic formats. Capture hashes
the incoming ASCII stream. Transcoding and the independent scientific replay
must each reproduce that hash and record count. There is no unchecked success.
"""
import hashlib
import json
import lzma
import os
from pathlib import Path
import struct
import tempfile
import zlib
import burst_codec
import trace_codec


def checkpoint(path, value):
    """Durable local receipt, written only after the corresponding stream closes."""
    path = Path(path)
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                     prefix=path.name+'.', suffix='.tmp', delete=False) as f:
        temp = Path(f.name)
        json.dump(value, f, indent=2, allow_nan=False)
        f.write('\n'); f.flush(); os.fsync(f.fileno())
    temp.replace(path)


def write_blocks(source, dest, *, compact):
    """One streaming pass; deliberately does not reread dest in this function."""
    h = hashlib.sha256(); count = 0; order = []; kinds = []; columns = []; index = {}
    block = burst_codec.BLOCK if compact else trace_codec.BLOCK
    magic = burst_codec.MAGIC if compact else trace_codec.MAGIC
    def flush(out):
        if not order: return
        encoded = [[trace_codec.encode_column(col) for col in cols] for cols in columns]
        raw = json.dumps([order, kinds, encoded], separators=(',', ':')).encode('ascii')
        data = lzma.compress(raw, preset=3) if compact else zlib.compress(raw, 9)
        out.write(struct.pack('<I', len(data))); out.write(data)
        order.clear(); kinds.clear(); columns.clear(); index.clear()
    with Path(dest).open('wb') as out:
        out.write(magic)
        for line in trace_codec.lines(source):
            fields = line.split()
            if not fields or line != ' '.join(fields)+'\n':
                raise ValueError('noncanonical source trace')
            h.update(line.encode('ascii')); count += 1; kind = fields[0]
            if kind not in index:
                index[kind] = len(kinds); kinds.append(kind)
                columns.append([[] for _ in fields[1:]])
            k = index[kind]; order.append(k)
            if len(columns[k]) != len(fields)-1:
                raise ValueError('inconsistent record width')
            for col, value in zip(columns[k], fields[1:]): col.append(value)
            if len(order) == block: flush(out)
        flush(out); out.flush(); os.fsync(out.fileno())
    return dict(records=count, raw_sha256=h.hexdigest(), bytes=Path(dest).stat().st_size)


def capture(source, dest, receipt):
    stats = write_blocks(source, dest, compact=False)
    checkpoint(receipt, dict(status='captured_not_yet_verified', **stats))
    return stats


def assert_identity(actual, expected):
    assert actual['raw_sha256'] == expected['raw_sha256'], 'original-stream SHA mismatch'
    assert actual['records'] == expected['records'], 'original-stream record-count mismatch'


def transcode(source, dest, expected):
    dest = Path(dest)
    assert not dest.exists(), 'do not overwrite an existing compact trace'
    with tempfile.NamedTemporaryFile(dir=dest.parent, prefix=dest.name+'.',
                                     suffix='.part', delete=False) as f:
        temp = Path(f.name)
    try:
        stats = write_blocks(source, temp, compact=True)
        assert_identity(stats, expected)
        temp.replace(dest)
        return stats
    finally:
        if temp.exists(): temp.unlink()  # only this explicitly created staging file


class AuditedRows:
    """Exactly the original reader's rows, with a simultaneous original-stream hash."""
    def __init__(self):
        self.h = hashlib.sha256(); self.count = 0; self.started = False; self.finished = False

    def __call__(self, path):
        assert not self.started, 'one trace traversal per audit'
        self.started = True
        for line in burst_codec.lines(path):
            fields = line.split()
            assert fields and line == ' '.join(fields)+'\n', 'noncanonical decoded trace'
            self.h.update(line.encode('ascii')); self.count += 1
            yield self.count, fields
        self.finished = True

    def verify(self, expected):
        assert self.finished, 'checker did not consume the complete trace'
        stats = dict(records=self.count, raw_sha256=self.h.hexdigest())
        assert_identity(stats, expected)
        return stats

"""Mutation sensitivity of the nonempty full-memory validation path."""
import gzip
import json
from pathlib import Path
import tempfile
import unittest
from check_sparse import HERE, check
from trace_codec import lines as trace_lines, compare as compare_short, pack, digest, encode_column, decode_column
from sparse_inputs import build


class SparseTests(unittest.TestCase):
    def corrupt(self, edit, pattern=r'bad.trace.gz:\d+:'):
        stem='sparse-short-adaptive-skip'
        lines=list(trace_lines(HERE/f'outputs/{stem}.trace.ctz'))
        self.assertTrue(edit(lines))
        meta=json.loads((HERE/f'outputs/{stem}.json').read_text())
        with tempfile.TemporaryDirectory(dir=HERE/'.build') as d:
            path=Path(d)/'bad.trace.gz'
            with gzip.open(path,'wt') as f:f.writelines(lines)
            with self.assertRaisesRegex(AssertionError,pattern):check(path,meta)

    def test_inputs_and_envelope(self):
        cfg=build('memory')
        a=cfg['applications']
        self.assertEqual(len(a),40)
        self.assertTrue(all(y['at_ns']-x['at_ns']>=1000000 for x,y in zip(a,a[1:])))
        self.assertTrue(all(e['at_ns']%4==2 for e in cfg['injections']))
        words=[(int(x['packet'],16)>>2)&524287 for x in a]
        self.assertEqual(words.count(400000),8)
        writes=[x for x in a if int(x['packet'],16)&3==2 and ((int(x['packet'],16)>>2)&524287)==400000]
        self.assertEqual(len(writes),1)

    def test_nonempty_literal_equivalence(self):
        result=compare_short(HERE/'outputs/sparse-short-adaptive-literal.trace.ctz',
                             HERE/'outputs/sparse-short-adaptive-skip.trace.ctz')
        self.assertGreater(result['compared_rows'],60000)

    def test_codec_roundtrip(self):
        for values in (['0000','0001','ffff'],['-1','9','10'],['001','02','3'],['word','other']):
            self.assertEqual(decode_column(encode_column(values)),values)
        src=HERE/'outputs/sparse-short-adaptive-skip.trace.ctz'
        with tempfile.TemporaryDirectory(dir=HERE/'.build') as d:
            dest=Path(d)/'again.ctz'
            pack(src,dest)
            self.assertEqual(src.read_bytes(),dest.read_bytes())
            self.assertEqual(digest(src),digest(dest))

    def test_lost_injection(self):
        def edit(lines):
            for i,line in enumerate(lines):
                if line.startswith('INJECT '):lines.pop(i);return True
        self.corrupt(edit)

    def test_lost_write(self):
        def edit(lines):
            for i,line in enumerate(lines):
                if line.startswith('WRITE '):lines.pop(i);return True
        self.corrupt(edit)

    def test_wrong_return_id(self):
        def edit(lines):
            for i,line in enumerate(lines):
                f=line.split()
                if f[0]=='REPLY':
                    f[3]=f'{int(f[3],16)^(1<<33):x}';lines[i]=' '.join(f)+'\n';return True
        self.corrupt(edit)

    def test_wrong_return_data(self):
        def edit(lines):
            for i,line in enumerate(lines):
                f=line.split()
                if f[0]=='REPLY':
                    f[3]=f'{int(f[3],16)^2:x}';lines[i]=' '.join(f)+'\n';return True
        self.corrupt(edit)

    def test_dirty_visit_in_macro(self):
        def edit(lines):
            for i in range(len(lines)-1,-1,-1):
                line=lines[i]
                f=line.split()
                if f[0]=='JUMP':
                    f[2]=str(600*188160);f[3]='600';f[4]=str(600*960)
                    lines[i]=' '.join(f)+'\n';return True
        self.corrupt(edit,'dirty word inside jump')

    def test_full_memory_checksum(self):
        def edit(lines):
            for i,line in enumerate(lines):
                f=line.split()
                if f[0]=='STATE':
                    f[2]=f'{int(f[2],16)^1:x}';lines[i]=' '.join(f)+'\n';return True
        self.corrupt(edit)


if __name__=='__main__':unittest.main()

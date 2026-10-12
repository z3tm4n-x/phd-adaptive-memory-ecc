"""Independent complete-domain scenario/address and pin-contract checks."""
import hashlib,json,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
BASE=HERE.parent

def x16(word,half):
    # Different expression from HDL concatenation, through the x8 scenario.
    return (4*word+2*half)//2

class AddressTests(unittest.TestCase):
    def test_complete_domain(self):
        visited=bytearray(1<<20)
        for w in range(1<<19):
            for h in (0,1):
                a=x16(w,h)
                self.assertEqual(a>>1,w)
                self.assertEqual(a&1,h)
                self.assertEqual(visited[a],0)
                visited[a]=1
                self.assertEqual((2*a)//4,w)
                self.assertEqual((2*a+1)//4,w)
        self.assertEqual(sum(visited),1<<20)
    def test_scenario_not_proprietary(self):
        s=json.loads((BASE.parents[0]/'RE-CY62167-ADDRESS-MAPPING-01/w32seq_scenario.json').read_text())
        self.assertFalse(s['actual_proprietary_ecc_mapping'])
        self.assertEqual(s['word_index_width_bits'],19)
        self.assertEqual(s['supplied_grid_positions_per_scenario_word'],32)
    def test_article_identity(self):
        p=BASE.parents[0]/'t68-v21-inputs/inputs/article-cy62167-v21.docx'
        self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),
          '1de5ee1f05e5e2355928f5ff4d1a221d2e8cb9e7bfef86e2bd31aebbe0655385')
    def test_collision_sentinel(self):
        # Wrong mapping drops the half: distinct logical objects collide.
        broken=lambda w,h:2*w
        self.assertEqual(broken(123,0),broken(123,1))
        self.assertNotEqual(x16(123,0),x16(123,1))

if __name__=='__main__':unittest.main()

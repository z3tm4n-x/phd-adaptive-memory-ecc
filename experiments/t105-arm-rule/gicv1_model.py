"""Test-only Secure GICv1 control-register subset, NOT a PS7 simulation.

Independent field inventory: ARM IHI0048B table 4-31 (pp. 4-126..128),
DDI0407I tables 3-2/3-9; UG585 1.15 CPU Interrupt Signal Pass-through.
No production C masks or profile values are imported. Reserved fields RAZ/WI;
only aligned Secure word accesses to these two registers are represented.
All other GIC registers, interrupt arbitration and physical timing are OUTSIDE
this model. The selected cold profile assumes no external FIQ activity.
"""


class GicV1Controls:
    # Field names/positions, rather than the implementation's masks.
    FIELDS = {
        0xf8f00100: {"EnableS": 0, "EnableNS": 1, "AckCtl": 2, "FIQEn": 3, "SBPR": 4},
        0xf8f01000: {"EnableS": 0, "EnableNS": 1},
    }

    def __init__(self, initial=None, stuck=None):
        self.values = {a: 0 for a in self.FIELDS}  # architectural control reset
        self.stuck = stuck  # optional injected (address, implemented bit)
        if stuck is not None:
            assert stuck[1] in self.FIELDS[stuck[0]].values()
        for a, v in (initial or {}).items():
            self.write(a, v)

    def write(self, address, value):
        self.values[address] = sum(value & (1 << b) for b in self.FIELDS[address].values())

    def read(self, address):
        value = self.values[address]
        if self.stuck is not None and self.stuck[0] == address:
            value |= 1 << self.stuck[1]
        return value

    def disabled_pass_through(self, external_irq, external_fiq):
        """UG585 pass-through table first row; asserted=True, not pin polarity.

        This does NOT model taking an exception or CPSR/NMFI in Unicorn.
        In particular an asserted external FIQ is NOT blocked by ICCICR=0.
        """
        assert self.read(0xf8f00100) == 0
        return bool(external_irq), bool(external_fiq)

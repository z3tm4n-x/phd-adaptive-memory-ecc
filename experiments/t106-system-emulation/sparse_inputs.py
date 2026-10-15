"""Frozen scenario5 and acceleration witnesses; stand-only inputs, not policy."""
from empty_time import first_slot, slot, address


def build(case):
    if case == 'memory':
        horizon = 362_000_000_000
        epochs = [10_000, 180_500_000_000, 271_000_000_000, 361_000_000_000]
        count = 10
    elif case == 'short':
        horizon = 2_000_000; epochs = [10_000]; count = 2
    elif case == 'lowprobe':
        horizon = 180_313_000_000; epochs = [180_311_000_000]; count = 2
    else:
        raise ValueError(case)
    apps = []
    for group, epoch in enumerate(epochs):
        for i in range(count):
            ident = len(apps)
            kind = 2 if i % 2 == 0 else 1
            w = 400000 + i//2
            if i < 2 and group: kind = 1  # long-lived initial write
            if i == 9: w = 12345          # never written
            mask = [15, 1, 2, 4, 8][(i//2) % 5]
            data = 0x12340000 | ident
            p = (ident << 57) | (mask << 53) | (data << 21) | (w << 2) | kind
            apps.append(dict(at_ns=epoch+i*1_000_000, owner=ident%2, packet=f'{p:x}'))
    inj = []
    def add(t, w, b):
        # Fast negative edges lie at relative2 mod4 after qualified t0.
        t = t + ((2-t) % 4)
        inj.append(dict(at_ns=t, word=w, bit=b, parent=len(inj)+1))
    base = 0 if case != 'lowprobe' else epochs[0]-2000
    add(base+2002, 400000, 37)
    add(base+3002, 500000, 7)  # survives an empty-time jump until its check
    add(base+3502, 500001, 12)
    add(base+3506, 500001, 12) # safe repeat inversion, not two positions
    if case == 'memory':
        add(180_600_000_002, 500002, 2)
        add(180_600_000_006, 500002, 33)
        j = first_slot(181_000_000_000); j += (-j) % 3
        add(slot(j)-2, address(j), 37)
        add(slot(j)+62, address(j), 37)
        add(slot(j)+66, address(j), 37)
        add(270_999_999_002, 400002, 18)
    inj.sort(key=lambda e: (e['at_ns'],e['parent']))
    return dict(scenario=case, horizon_ns=horizon, initial_data='0xa5a50000 XOR word',
                initial_errors=0, injections=inj, applications=apps,
                false_ERR_interval_ns=[0,0],loss_slow_interval_ns=[0,0],
                ready_low_ns=80,ready_period_ns=340)


def write(folder, cfg, mode):
    (folder/'accel.txt').write_text(f'{cfg["horizon_ns"]} 0 0 0 0 {int(mode=="fixed")}\n')
    (folder/'injections.txt').write_text(''.join(
        f'{e["at_ns"]} {e["word"]} {e["bit"]} {e["parent"]}\n' for e in cfg['injections']))
    (folder/'application.txt').write_text(''.join(
        f'{a["at_ns"]} {a["owner"]} {a["packet"]}\n' for a in cfg['applications']))

"""Profile-specific union upper on same-word pairs, independent of the replay seed."""
import numpy as np
from histories import D, DT, GROUPS, K, W, WIDTH
from replay import Calendar


def triangle(width, before, after):
    """Area x+y < width in [0,before] x [0,after], without subtracting large squares."""
    flat = np.minimum(before, np.maximum(0.,width-after))
    end = np.minimum(before,width)
    return flat*np.minimum(after,width) + (end-flat)*(width-(end+flat)/2)


def pair_upper(profile):
    cal = Calendar()
    l,p,d = cal.L/1e9,cal.P/1e9,124e-9
    short,fixed,long = l+d,4*l+d,p+d
    edges, duration, group = profile.edges, profile.duration, profile.group
    # Segment suprema preserve the direction of the pair bound. The lower
    # rate used in the empty-history exponent is rounded in the other direction.
    peak = np.maximum(profile.lo,profile.hi)+1e-13
    bins = (edges[:-1]//DT).astype(int)
    floor = np.full(WIDTH,np.inf)
    np.minimum.at(floor,bins,np.minimum(profile.lo,profile.hi))
    prev = np.r_[floor[0],floor[0],floor]
    low = np.maximum(0.,np.minimum.reduce((prev[:-2],prev[1:-1],prev[2:]))-1e-13)
    common_history = cal.quiet*p-cal.drain/1e9-(p+l+d)
    assert 0 < common_history < 300 and cal.quiet*p < 2*DT
    quiet_weight = np.exp(-K*common_history*low[bins])
    quiet_weight[edges[1:] <= cal.quiet*p] = 0
    totals = {name:np.zeros((4,4)) for name in ("L/32L","4L")}

    def accumulate(early,late,areas):
        fast_area, fixed_area, slow_area = areas
        volume = peak[early]*peak[late]
        labels = 4*group[early]+group[late]
        for name,weighted in (("4L",fixed_area),("L/32L",fast_area+quiet_weight[late]*np.maximum(0.,slow_area-fast_area))):
            totals[name] += np.bincount(labels,weights=volume*weighted,minlength=16).reshape(4,4)

    def interior(h):
        clipped = np.minimum(duration,h)
        return clipped*(duration-clipped/2)
    all_idx = slice(None)
    accumulate(all_idx,all_idx,[interior(h) for h in (short,fixed,long)])
    # Adjacent catalogue pieces, holes and short ramp fragments may all
    # contribute. Stop only when no earlier piece can reach any later piece.
    for shift in range(1,len(group)):
        gap = edges[shift:-1] - edges[1:len(group)-shift+1]
        early = np.flatnonzero(gap < long)
        if not len(early):
            break
        late = early+shift
        areas = [triangle(np.maximum(0.,h-gap[early]), duration[early], duration[late])
                 for h in (short,fixed,long)]
        accumulate(early,late,areas)
    result = {}
    for name,matrix in totals.items():
        # Nonnegative sums (<= several million terms), including a margin
        # larger than their binary64 forward-error bound.
        matrix *= (1+1e-8)*W*(39/D)**2
        result[name] = dict(groups=GROUPS, earlier_by_later=matrix.tolist(), total=float(matrix.sum()),
                            same_event=float(matrix[0,0]),same_outside=float(matrix[1,1]),
                            same_gap=float(matrix[2,2]),same_tail=float(matrix[3,3]),
                            different_groups=float(matrix[~np.eye(4,dtype=bool)].sum()))
    return result

#!/usr/bin/env python3
H=43824.0
avg=0.0014244700083518912
peak=0.24045835514172653
B=0.0025
missing=148.0
fallback_avg=avg+(missing/H)*peak
capacity=(B-avg)/peak*H
assert fallback_avg < B
assert capacity > missing
print(f"fallback_avg_fraction={fallback_avg:.15g}")
print(f"fallback_capacity_hours={capacity:.15g}")

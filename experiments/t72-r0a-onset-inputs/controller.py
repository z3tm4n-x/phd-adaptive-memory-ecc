"""Executable engineering candidate: nested mandatory/extra full-pass calendars.

Not RTL, not a qualified monitor. Caller supplies the declared certified low
history and alarm events; these are not inferred from retrospective GOES peaks.
The monitor-only calendar must be exogenous to memory arrivals for the proposed
sharper pair envelope. ERR can only ADD passes, never postpone mandatory work.
"""
from __future__ import annotations
from dataclasses import dataclass
import math


@dataclass
class BurstController:
    long_ticks: int
    short_ticks: int
    hold_ticks: int
    monitor_high: bool = True
    last_alarm: int = -10**30
    count_hold_until: int = -10**30
    previous_tick: int = -1

    def __post_init__(self):
        if self.short_ticks <= 0 or self.long_ticks % self.short_ticks or self.hold_ticks < self.short_ticks:
            raise ValueError('Invalid nested calendar or exit hold')

    def step(self, tick, *, alarm=False, err=False, quiet_history_ticks=0, missing=False):
        if tick < self.previous_tick:
            raise ValueError('Observations cannot travel backwards in time')
        self.previous_tick=tick
        if alarm or missing:
            self.monitor_high=True
            self.last_alarm=tick
        if err:
            self.count_hold_until=max(self.count_hold_until,tick+self.hold_ticks)
        if not (alarm or missing) and quiet_history_ticks >= self.hold_ticks and tick-self.last_alarm >= self.hold_ticks:
            self.monitor_high=False
        boundary=tick % self.short_ticks == 0
        reference=boundary and (tick % self.long_ticks == 0 or self.monitor_high)
        actual=reference or (boundary and tick < self.count_hold_until)
        return {'reference_pass':reference,'actual_pass':actual,'monitor_high':self.monitor_high,
                'count_hold':tick<self.count_hold_until}


def word_phases(words, cost_ticks, batch_words, application_gap_ticks):
    if min(words,cost_ticks,batch_words) <= 0 or application_gap_ticks < 0:
        raise ValueError('Invalid phase layout')
    return [w*cost_ticks+(w//batch_words)*application_gap_ticks for w in range(words)]


def scalar_envelope_check(times, rate, fences_by_word, long, short, solar_cap, background=0.):
    """Independent finite-trajectory integration check, not a future proof.

    Fences must be sample-aligned. Returns actual per-word exposure-square sum
    versus the proposed low/high Cauchy envelope for a given exogenous schedule.
    """
    if len(times)!=len(rate)+1:
        raise ValueError('Bin-edge and rate lengths differ')
    total=0.
    all_long_low=True
    for fences in fences_by_word:
        edges=sorted(set([0,*fences,len(rate)]))
        for i,j in zip(edges[:-1],edges[1:]):
            duration=times[j]-times[i]
            mu=sum(rate[k]*(times[k+1]-times[k]) for k in range(i,j))
            total+=mu*mu
            if duration > long+1e-9:
                raise AssertionError('Long deadline violated')
            if duration > short+1e-9:
                all_long_low &= all(rate[k] <= background+solar_cap+1e-12 for k in range(i,j))
    return {'sum_exposure_squares':total,'all_long_intervals_below_cap':all_long_low}

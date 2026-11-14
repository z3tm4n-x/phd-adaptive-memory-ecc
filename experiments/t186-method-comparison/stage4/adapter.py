"""Conditional ordered packet adapter. No physical WCET is inferred.

Whole-prefix processing is atomic at ready, after capture+3900 ns. Empty
captures/readies are counted analytically. OUR expiry is a local prepared
predicate; competitors' natural timers are packet jobs.
"""
from bisect import bisect_right
from collections import deque
import struct
from reuse import policies

HOUR=3600*10**9
CAUSE_BITS={'GAP':4,'ERR':1,'FALSE':2,'RESTORE':8}


def canonical_causes(causes):
    assert causes and len(set(causes))==len(causes) and set(causes)<=CAUSE_BITS.keys()
    return [cause for cause in CAUSE_BITS if cause in causes]

def encode_record(r):
    """32-byte wire record: 60-bit fast timestamp + 4 causes, full G64.

    GAP stores two full G64 endpoints; normal payload holds word/origin.
    The ten-year fast timestamp fits60 bits. Simulation-only arrival/drop
    annotations are not part of the wire record or the claimed buffer.
    """
    assert r['t']%4==0 and 0<=r['t']//4<2**60 and 0<=r['g']<2**64
    flags=sum(CAUSE_BITS[k] for k in canonical_causes(r['causes']))
    if 'GAP' in r['causes']:
        lo,hi=r.get('covers',[r['g'],r['g']])
        assert 0<lo<=hi<=r['g'],'GAP range must refer to this prefix'
    else:lo=r.get('word',0)+(int(r.get('origin')=='write32')<<32);hi=0
    return struct.pack('>QQQQ',(flags<<60)|(r['t']//4),r['g'],lo,hi)

def decode_record(raw):
    header,g,lo,hi=struct.unpack('>QQQQ',raw)
    causes=canonical_causes([s for s,b in CAUSE_BITS.items() if header>>60&b])
    r=dict(t=(header&((1<<60)-1))*4,g=g,causes=causes,payload=[lo,hi])
    if 'GAP' in causes:
        assert 0<lo<=hi<=g,'GAP range must refer to this prefix'
        r['covers']=[lo,hi]
    else:r.update(word=lo&((1<<32)-1),origin='write32' if lo>>32 else 'control')
    return r

class Adapter:
    def __init__(self,spec,config,words=524288,weights=None,our_cfg=None):
        self.spec=spec;self.family=spec['family'];self.words=words
        self.cut=config['cut_ns'];self.ingress=config['ingress_ns'];self.delay=config['batch_ready_ns']
        self.capacity=config['banks']*config['bank_records'];self.bank=config['bank_records'];self.record_bytes=config['record_bytes']
        self.generation=0;self.processed=0;self.last_source=-1;self.source_by_time={}
        self.times=[0];self.modes=[1];self.k=1;self.timer=None;self.now=0
        self.jobs={};self.pending_records={};self.inflight=set();self.captured=set();self.queued_due=set()
        self.records=[];self.delivered=[];self.batches=[];self.unknown_ranges=[];self.source_health=True
        self.unknown=False;self.fresh_after=None;self.known_hour=0
        self.peak_records=self.peak_inflight=self.peak_batch=self.peak_policy_queue=0
        self.updates=0;self.expiries=0;self.forecast_attempts=0;self.forecasts=0;self.unknown_forecasts=0
        self.dropped=0;self.false=0;self.losses=0;self.restores=0;self.coalesced=0;self.known_ERR=0
        # Two restored-prefix watermarks; logs below are audit data, not policy state.
        self.resolved_G=0;self.source_resolved_G=0
        self.source_losses=0;self.source_recoveries=0
        self.source_before=(True,0,0,0)
        self.gap_notices=0;self.restore_notices=0
        self.inferred_gaps=0;self.gap_confirmations=0;self.restore_confirmations=0
        self.source_state_checks=0;self.prefix_checks=0;self.loss_state_checks=0
        self.processed_jobs=0;self.local_ready_max_delay=0;self.ready_time=0
        self.core=None
        self.cfg=our_cfg or dict(NW=4500045002,NH=9000090002,NR=9015504896,
                                timer_tick_ns=20,pair_source_ticks=22500225010,source_tick_ns=4)
        self.short=self.long=0;self.recovery=self.cfg['NR']*self.cfg['timer_tick_ns'];self.last_ERR=None
        if self.family=='our':self.timer=4*((self.recovery+4)//4)
        else:
            self.core=policies.make(spec,words=words,weights=weights,cut=self.cut)
            self.k=self.modes[0]=self.core.k
            original=self.core.set_mode
            def installed(t,k):
                original(max(t,self.ready_time),k)
                self.set_mode(self.ready_time,k)
            self.core.set_mode=installed
            if self.family=='chen_analog':self.core.timer=HOUR
            self._sync_timer()

    def bind(self,push):self.push=push

    def set_mode(self,t,k):
        assert k in (1,3,9,27) and t>=self.times[-1],(t,self.times[-1])
        if k!=self.k:
            if t==self.times[-1]:self.modes[-1]=k
            else:self.times.append(t);self.modes.append(k)
            self.k=k

    def mode(self,t):return self.modes[max(0,bisect_right(self.times,t)-1)] if t>=0 else 1

    def _sync_timer(self):
        if self.core is not None:
            self.timer=None if self.core.timer in self.queued_due else self.core.timer

    def _job(self,cut):
        if cut not in self.jobs:
            self.jobs[cut]=dict(records=[],due=[],captured=False)
            self.push(cut,3,'adapter_capture',cut)
        return self.jobs[cut]

    def source(self,t,kind='ERR',**extra):
        assert kind in ('ERR','FALSE','GAP','RESTORE') and t%4==0
        assert t>=self.last_source
        if t in self.source_by_time:
            r=self.source_by_time[t]
            assert kind not in r['causes'],'duplicate source cause/alias'
            assert extra.get('drop',r.get('drop',False))==r.get('drop',False),'coalescence cannot change transport disposition'
            assert extra.get('ingress_ns',r.get('ingress_ns',self.ingress))==r.get('ingress_ns',self.ingress),'coalescence cannot retime ingress'
            r['causes'].append(kind);r.update(extra);self.coalesced+=1
        else:
            assert self.generation<2**64-1,'G64 must not wrap or reset'
            self.source_before=(self.source_health,self.source_resolved_G,
                                self.source_losses,self.source_recoveries)
            self.generation+=1
            r=dict(g=self.generation,t=t,causes=[kind],**extra)
            self.records.append(r);self.source_by_time[t]=r;self.last_source=t
            if r.get('drop'):
                self.dropped+=1
            else:
                delay=r.get('ingress_ns',self.ingress)
                assert 0<=delay<=self.ingress
                r['arrival']=t+delay
                self.pending_records[r['g']]=r;self.inflight.add(r['g'])
                self.push(r['arrival'],2,'adapter_ingress',r)
        r['causes']=canonical_causes(r['causes'])
        if kind=='FALSE':self.false+=1
        if kind=='GAP':self.gap_notices+=1
        if kind=='RESTORE':self.restore_notices+=1
        # Re-evaluate the whole edge from its BEFORE state, including counters.
        # Sources have priority over ingress/timers/freeze, so no consumer sees
        # a partially assembled edge. RESTORE ends a simultaneous GAP episode.
        health,closed,losses,restores=self.source_before
        if 'GAP' in r['causes'] and r.get('covers',[r['g'],r['g']])[1]>closed:
            if health:losses+=1
            health=False
        if 'RESTORE' in r['causes']:
            if not health:restores+=1
            health=True;closed=r['g']
        self.source_health=health;self.source_resolved_G=closed
        self.source_losses=losses;self.source_recoveries=restores
        self.source_state_checks+=1
        if self.family=='our':self.set_mode(t,1)
        self.peak_records=max(self.peak_records,len(self.pending_records))
        self.peak_inflight=max(self.peak_inflight,len(self.inflight))
        assert len(self.pending_records)<=self.capacity,'finite transport capacity exceeded'
        return r

    def wake(self,t):
        self.now=t
        if self.family=='our':
            self.expiries+=1;self.updates+=1;self._our_ready(t)
        else:
            due=self.core.timer
            if due is not None:
                assert due==t
                self.queued_due.add(due)
                self._job((t//self.cut+1)*self.cut)['due'].append(due)
            self._sync_timer()

    def _our_ready(self,t):
        end=max(self.short,self.long,self.recovery)
        good=not self.unknown and self.source_health and self.processed==self.generation
        self.set_mode(t,3 if good and t>end else 1)
        expiry=4*((end+4)//4)
        self.timer=expiry if expiry>t else None

    def _gap(self,t,r,inferred=False):
        self.loss_state_checks+=1
        if inferred:self.inferred_gaps+=1
        interval=r.get('covers',[r['g'],r['g']])
        confirmation=interval[1]<=self.resolved_G or self.unknown
        self.unknown_ranges.append(dict(source_t=r['t'],processed_at=t,range=interval,g=r['g'],
                                        inferred=inferred,confirmation=confirmation))
        if confirmation:
            self.gap_confirmations+=1
            return
        self.unknown=True;self.losses+=1
        if self.family=='our':self.set_mode(t,1)
        if self.core is not None:
            self.core.updates+=1
            if self.family=='krasnikov':self.core.count=0;self.core.timer=None
            if self.family=='patent':self.core.sources.clear();self.core.timer=None;self.fresh_after=None

    def _restore(self,t,r):
        self.loss_state_checks+=1
        self.resolved_G=max(self.resolved_G,r['g'])
        if not self.unknown:
            self.restore_confirmations+=1
            return
        self.restores+=1
        self.unknown=False
        if self.family=='our':self.recovery=max(self.recovery,t+self.cfg['NR']*self.cfg['timer_tick_ns'])
        else:
            self.core.updates+=1
            if self.family=='krasnikov':self.core.count=0;self.core.anchor=t;self.core.timer=t+self.core.period
            elif self.family=='patent':self.core.sources.clear();self.fresh_after=t+self.core.window;self.core.timer=self.fresh_after
            elif self.family=='chen_analog':self.known_hour=t//HOUR+1

    def apply_record(self,t,r):
        """Atomic semantics of one decoded record, after any inferred hole.

        GAP first, one observation, RESTORE last. No call-order information
        or simulation-only payload is consulted by the receiving policy.
        """
        causes=canonical_causes(r['causes'])
        if 'GAP' in causes:self._gap(t,r)
        if 'ERR' in causes or 'FALSE' in causes:self._ERR(t,r['t'])
        if 'RESTORE' in causes:self._restore(t,r)

    def _ERR(self,t,source):
        self.known_ERR+=1;self.delivered.append(dict(t=t,source=source))
        if self.family=='our':
            self.updates+=1
            self.short=max(self.short,t+self.cfg['NW']*self.cfg['timer_tick_ns'])
            if self.last_ERR is not None and source-self.last_ERR<=self.cfg['pair_source_ticks']*self.cfg['source_tick_ns']:
                self.long=max(self.long,t+self.cfg['NH']*self.cfg['timer_tick_ns'])
            self.last_ERR=source
        elif self.family=='chen_analog':self.core.observe(t,source)
        elif self.unknown:self.core.observations+=1
        elif self.family=='patent' and self.fresh_after is not None:
            self.core.observations+=1
            while self.core.sources and self.core.sources[0]<=t-self.core.window:self.core.sources.popleft()
            if source>t-self.core.window:self.core.sources.append(source)
        else:self.core.observe(t,source)
        if self.core is not None and hasattr(self.core,'sources'):
            self.peak_policy_queue=max(self.peak_policy_queue,len(self.core.sources))

    def _timer_job(self,t,due):
        self.queued_due.discard(due)
        if self.core.timer!=due:return
        if self.family=='chen_analog':
            if self.core.hour>=6:
                self.forecast_attempts+=1
                known=not self.unknown and self.core.hour-6>=self.known_hour
                if known:self.forecasts+=1
                else:
                    self.unknown_forecasts+=1;self.core.updates+=1;self.core.hour+=1
                    self.core.timer=self.core.hour*HOUR
                    self.core.bins={h:n for h,n in self.core.bins.items() if h>=self.core.hour-7}
                    return
            self.core.wake(t);self.core.timer=self.core.hour*HOUR
        elif self.family=='patent' and self.fresh_after is not None:
            assert t>=self.fresh_after
            self.fresh_after=None;self.core.wake(t)
        elif not self.unknown:self.core.wake(t)

    def handle(self,t,kind,x):
        self.now=t
        if kind=='adapter_ingress':
            self.inflight.remove(x['g'])
            cut=(t//self.cut+1)*self.cut
            self._job(cut)['records'].append(x)
        elif kind=='adapter_capture':
            job=self.jobs[x];job['records'].sort(key=lambda r:r['g']);job['captured']=True
            assert all(len(encode_record(r))==self.record_bytes for r in job['records'])
            assert len(job['records'])<=self.bank,'packet exceeds one bank'
            self.peak_batch=max(self.peak_batch,len(job['records']))
            self.captured.update(r['g'] for r in job['records'])
            self.push(t+self.delay,3,'adapter_ready',x)
        elif kind=='adapter_ready':
            job=self.jobs.pop(x);self.ready_time=t;self.processed_jobs+=1
            batch=job['records']
            assert all(r['arrival']<x for r in batch),'cut equality belongs to next packet'
            expected=self.processed+1
            for r in batch:
                self.prefix_checks+=1
                assert r['g']>=expected,'reorder, duplicate or stale record'
                if r['g']>expected:
                    self._gap(t,dict(t=r['t'],g=r['g'],covers=[expected,r['g']-1]),inferred=True)
                self.apply_record(t,decode_record(encode_record(r)))
                expected=r['g']+1
                self.pending_records.pop(r['g']);self.captured.remove(r['g'])
                self.local_ready_max_delay=max(self.local_ready_max_delay,t-r['t'])
            # No intermediate processing publishes a current-generation token.
            if batch:self.processed=batch[-1]['g']
            for due in job['due']:self._timer_job(t,due)
            if self.family=='our':self._our_ready(t)
            else:self._sync_timer()
            self.batches.append(dict(cut=x,ready=t,first_G=batch[0]['g'] if batch else None,
                                     processed_G=self.processed,records=len(batch),timer_jobs=len(job['due'])))
        elif kind=='adapter_empty_literal':pass
        else:raise ValueError(kind)

    def finish(self,H):
        if self.family=='krasnikov' and not self.unknown and not self.core.count and self.core.k==27:
            # Stable empty cycles are virtual work, including packet delay.
            last_due=((H-self.delay)//self.cut)*self.cut-1
            if last_due>=self.core.anchor:self.core.advance(last_due)

    def costs(self,H):
        return dict(source_records=len(self.records),source_ERR=sum('ERR' in r['causes'] for r in self.records),
                    source_false=self.false,loss_rises=self.losses,restores=self.restores,
                    raw_GAP_notifications=self.gap_notices,raw_RESTORE_notifications=self.restore_notices,
                    source_health_loss_rises=self.source_losses,source_health_recoveries=self.source_recoveries,
                    inferred_missing_ranges=self.inferred_gaps,GAP_confirmations=self.gap_confirmations,
                    RESTORE_confirmations=self.restore_confirmations,restored_prefix_G=self.resolved_G,
                    source_state_checks=self.source_state_checks,prefix_checks=self.prefix_checks,
                    loss_state_checks=self.loss_state_checks,
                    loss_state_reserved_bytes=64,
                    source_cause_coalescences=self.coalesced,delivered_ERR=self.known_ERR,dropped_records=self.dropped,
                    processed_G=self.processed,current_G=self.generation,UNKNOWN_ranges=len(self.unknown_ranges),
                    pending_records=len(self.pending_records),pending_inflight=len(self.inflight),
                    pending_captured=len(self.captured),nominal_cut_services=H//self.cut,
                    nominal_ready_services=max(0,(H-self.delay)//self.cut),materialized_packets=self.processed_jobs,
                    logical_updates=self.updates if self.core is None else self.core.updates,
                    precomputed_expiry_evaluations=self.expiries,forecast_attempts=self.forecast_attempts,
                    full_hourly_forecasts=self.forecasts,UNKNOWN_forecasts=self.unknown_forecasts,
                    six_feature_multiply_adds=6*self.forecasts,peak_transport_records=self.peak_records,
                    peak_inflight_records=self.peak_inflight,peak_batch_records=self.peak_batch,
                    transport_capacity_records=self.capacity,transport_reserved_bytes=self.capacity*self.record_bytes,
                    peak_policy_timestamp_records=self.peak_policy_queue,local_ready_max_delay_ns=self.local_ready_max_delay,
                    CPU_time_ns=None,energy_J=None)

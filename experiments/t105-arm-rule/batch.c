#include "batch.h"

static uint64_t decay(uint64_t x, uint64_t elapsed) {
    return elapsed<x ? x-elapsed : 0;
}
static int broken(t105_batch_state *s) {
    s->rule.flags |= S_FAULT; return 0;
}
void t105_batch_init(t105_batch_state *s) {
    t105_init(&s->rule); s->sequence=0; s->start_tick=0;
}
int t105_batch_apply(t105_batch_state *s, const t105_batch *b) {
    t105_state *r=&s->rule;
    uint64_t previous=r->now, elapsed;
    if (b->reserved || b->flags&~31u || !(b->flags&B_STARTED) ||
        s->sequence==UINT64_MAX || b->sequence!=s->sequence+1 ||
        b->base_generation!=r->generation ||
        b->end_generation<b->base_generation ||
        b->end_generation-b->base_generation!=b->event_count ||
        b->err_count>b->event_count || b->start_tick>b->end_tick)
        return broken(s);
    if (!(r->flags&S_STARTED)) {
        if(s->sequence || b->base_generation) return broken(s);
        previous=b->start_tick;
    } else if(b->start_tick!=s->start_tick || b->end_tick<=previous)
        return broken(s);
    if (b->end_tick<previous || b->event_count>b->end_tick-previous)
        return broken(s);
    if (b->err_count) {
        if (b->first_err_tick<=previous || b->first_err_tick>b->last_err_tick ||
            b->last_err_tick>b->end_tick ||
            b->last_err_source<b->first_err_source)
            return broken(s);
        if (b->err_count==1 && (b->first_err_tick!=b->last_err_tick ||
                                b->first_err_source!=b->last_err_source))
            return broken(s);
        if (b->err_count>1 && (b->first_err_tick==b->last_err_tick ||
            b->last_err_source-b->first_err_source>T105_PAIR))
            return broken(s);
        if ((r->flags&S_SEEN_ERR) && b->first_err_source<r->last_err)
            return broken(s);
    } else if (b->first_err_tick || b->last_err_tick ||
               b->first_err_source || b->last_err_source)
        return broken(s);
    if (b->flags&B_RECOVERY) {
        if (!b->event_count || b->last_recovery_tick<=previous ||
            b->last_recovery_tick>b->end_tick) return broken(s);
    } else if (b->last_recovery_tick ||
        (!(r->flags&S_HEALTHY) && (b->flags&B_HEALTHY))) return broken(s);
    if ((!b->event_count && ((b->flags&(B_RECOVERY|B_EVENT_AT_END)) ||
        (!!(b->flags&B_HEALTHY)!=!!(r->flags&S_HEALTHY)))) ||
        ((b->flags&B_EVENT_AT_END) && !b->event_count)) return broken(s);

    if (!(r->flags&S_STARTED)) {
        r->flags |= S_STARTED; r->recovery_left=T105_NR;
        s->start_tick=b->start_tick;
    }
    elapsed=b->end_tick-previous;
    r->short_left=decay(r->short_left,elapsed);
    r->long_left=decay(r->long_left,elapsed);
    r->recovery_left=decay(r->recovery_left,elapsed);
    if (b->flags&B_RECOVERY)
        r->recovery_left=decay(T105_NR,b->end_tick-b->last_recovery_tick);
    if (b->err_count) {
        int pair=b->err_count>=2 ||
          ((r->flags&S_SEEN_ERR) &&
           b->first_err_source-r->last_err<=T105_PAIR);
        r->short_left=decay(T105_NW,b->end_tick-b->last_err_tick);
        if (pair) r->long_left=decay(T105_NH,b->end_tick-b->last_err_tick);
        r->last_err=b->last_err_source; r->flags |= S_SEEN_ERR;
    }
    r->flags &= ~(S_HEALTHY|S_EVENT_BLOCK);
    r->flags |= S_TIME_SEEN;
    if(b->flags&B_HEALTHY) r->flags |= S_HEALTHY;
    if(b->flags&B_EVENT_AT_END) r->flags |= S_EVENT_BLOCK;
    if(b->flags&B_FAULT) r->flags |= S_FAULT;
    r->now=b->end_tick; r->generation=b->end_generation;
    s->sequence=b->sequence;
    return !(r->flags&S_FAULT);
}
int t105_decide(t105_batch_state *s, t105_decision *d) {
    t105_state *r=&s->rule;
    uint64_t wait=r->short_left;
    if(r->long_left>wait) wait=r->long_left;
    if(r->recovery_left>wait) wait=r->recovery_left;
    if((r->flags&S_EVENT_BLOCK) && wait==0) wait=1;
    if(wait>UINT64_MAX-r->now) r->flags |= S_FAULT;
    d->sequence=s->sequence; d->generation=r->generation;
    d->flags=(r->flags&S_FAULT)?D_FAULT:
      ((r->flags&(S_STARTED|S_HEALTHY))==(S_STARTED|S_HEALTHY)?D_ALLOW:0);
    d->not_before=d->flags==D_ALLOW?r->now+wait:0;
    d->crc=t105_crc32(d,28);
    return d->flags!=D_FAULT;
}

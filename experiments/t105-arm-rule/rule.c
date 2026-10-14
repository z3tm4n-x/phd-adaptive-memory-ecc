#include "rule.h"

static uint64_t subtract_floor(uint64_t value, uint64_t elapsed) {
    return elapsed < value ? value-elapsed : 0;
}

void t105_init(t105_state *s) {
    s->now=0; s->generation=0; s->last_err=0;
    s->short_left=0; s->long_left=0; s->recovery_left=T105_NR;
    s->flags=S_HEALTHY; s->reserved=0;
}

void t105_apply(t105_state *s, const t105_input *v) {
    const uint32_t old=s->flags;
    if (v->reserved || (v->flags & ~31u) || v->now < s->now ||
        ((old&S_TIME_SEEN) && v->now==s->now)) {
        s->flags |= S_FAULT; return;
    }
    /* Between inputs there are no events. Countdown is exactly a skipped
     * sequence of slow edges, not a loop whose runtime grows with a timer. */
    if (old&S_STARTED) {
        const uint64_t elapsed=v->now-s->now;
        s->short_left=subtract_floor(s->short_left,elapsed);
        s->long_left=subtract_floor(s->long_left,elapsed);
        s->recovery_left=subtract_floor(s->recovery_left,elapsed);
    }
    s->now=v->now;
    s->flags=(old & ~S_EVENT_BLOCK) | S_TIME_SEEN;
    if ((v->flags&IN_START) && !(old&S_STARTED)) {
        s->flags |= S_STARTED; s->recovery_left=T105_NR;
    }
    if (v->flags&IN_HISTORY_FAULT) s->flags |= S_FAULT;
    if (v->flags&IN_EVENT) {
        s->flags |= S_EVENT_BLOCK;
        if (s->generation==UINT64_MAX || v->generation!=s->generation+1)
            s->flags |= S_FAULT;
        s->generation=v->generation;
        if (v->flags&IN_LOSS) s->flags &= ~S_HEALTHY;
        else {
            s->flags |= S_HEALTHY;
            if (!(old&S_HEALTHY)) s->recovery_left=T105_NR;
        }
        if (v->flags&IN_ERR) {
            s->short_left=T105_NW;
            if ((old&S_SEEN_ERR) && v->source_fast_timestamp>=s->last_err &&
#ifdef T105_MUTATE_OPEN_PAIR
                v->source_fast_timestamp-s->last_err<T105_PAIR)
#else
                v->source_fast_timestamp-s->last_err<=T105_PAIR)
#endif
                s->long_left=T105_NH;
            s->last_err=v->source_fast_timestamp;
            s->flags |= S_SEEN_ERR;
        }
    }
}

uint32_t t105_low(const t105_state *s) {
    return (s->flags&(S_STARTED|S_HEALTHY|S_FAULT|S_EVENT_BLOCK))==
           (S_STARTED|S_HEALTHY) && !s->short_left && !s->long_left &&
           !s->recovery_left;
}

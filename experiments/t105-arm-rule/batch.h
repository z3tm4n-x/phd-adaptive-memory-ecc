#ifndef T105_BATCH_H
#define T105_BATCH_H
#include "rule.h"
enum { B_STARTED=1, B_HEALTHY=2, B_RECOVERY=4, B_EVENT_AT_END=8, B_FAULT=16 };
enum { D_ALLOW=1, D_FAULT=2 };
typedef struct {
    uint64_t sequence, base_generation, end_generation, end_tick, start_tick;
    uint64_t first_err_source, last_err_source, first_err_tick, last_err_tick;
    uint64_t last_recovery_tick;
    uint32_t event_count, err_count, flags, reserved;
} t105_batch;
typedef struct {
    t105_state rule;
    uint64_t sequence, start_tick;
} t105_batch_state;
typedef struct {
    uint64_t sequence, generation, not_before;
    uint32_t flags, crc;
} t105_decision;
_Static_assert(sizeof(t105_batch)==96,"history wire ABI");
_Static_assert(sizeof(t105_decision)==32,"decision wire ABI");
void t105_batch_init(t105_batch_state *);
int t105_batch_apply(t105_batch_state *, const t105_batch *);
int t105_decide(t105_batch_state *, t105_decision *);
uint32_t t105_crc32(const void *, uint32_t);
#endif

#ifndef T105_RULE_H
#define T105_RULE_H
#include <stdint.h>
#define T105_NW UINT64_C(4500045002)
#define T105_NH UINT64_C(9000090002)
#define T105_NR UINT64_C(9015504896)
#define T105_PAIR UINT64_C(22500225010)
enum { IN_START=1, IN_EVENT=2, IN_ERR=4, IN_LOSS=8, IN_HISTORY_FAULT=16 };
enum { S_HEALTHY=1, S_STARTED=2, S_SEEN_ERR=4, S_FAULT=8,
       S_EVENT_BLOCK=16, S_TIME_SEEN=32 };
/* Test/driver ABI. now is a processing slow-edge index, NOT a source time.
 * The transport has to establish its atomicity, ordering and time relation. */
typedef struct {
    uint64_t now, generation, source_fast_timestamp;
    uint32_t flags, reserved;
} t105_input;
typedef struct {
    uint64_t now, generation, last_err, short_left, long_left, recovery_left;
    uint32_t flags, reserved;
} t105_state;
_Static_assert(sizeof(t105_input)==32, "input ABI");
_Static_assert(sizeof(t105_state)==56, "state ABI");
void t105_init(t105_state *s);
void t105_apply(t105_state *s, const t105_input *v);
uint32_t t105_low(const t105_state *s);
#endif

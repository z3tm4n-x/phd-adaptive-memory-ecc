#ifndef T105_DRIVER_H
#define T105_DRIVER_H
#include "batch.h"
typedef struct {
    t105_batch_state rule;
    union {t105_batch batch;uint32_t words[24];} input;
    union {t105_decision decision;uint32_t words[8];} output;
    uint32_t phase, failure;
} t105_driver;
/* Address space must be mapped Device, shareable, non-cacheable by BSP.
 * Startup-only initialization, one owner; no runtime sequence reset. */
void t105_driver_init(t105_driver *);
int t105_driver_step(t105_driver *, volatile uint32_t *mailbox);
#endif

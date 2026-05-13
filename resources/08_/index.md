# Timers management

In embedded systems, there are often two types of timers:

- **Hardware timer**: A timer peripheral inside the MCU. It counts using a real clock source and can generate interrupts, PWM signals, input capture, output compare, or trigger DMA/ADC events. Hardware timers are accurate and run independently from software.
    + Advantages:
        - High accuracy
        - Low jitter
        - Can work independently from the CPU
        - Good for real-time signal generation or measurement
        - Can trigger hardware events such as PWM, ADC, or DMA
    + Disadvantages:
        - Limited number of timer peripherals
        - More hardware-specific configuration
        - Less portable between MCUs
        - Usually more complex to use directly

![Hardware timers](08_hw_timer.png)

- **Software timer**: A timer object managed by software, usually by the RTOS kernel. It does not have its own physical timer peripheral. Instead, the RTOS uses a hardware timer tick, such as SysTick, to update time and check whether software timers have expired.
    + Advantages:
        - Many timers can be created from one hardware timer source
        - Easier to use in application code
        - More portable across platforms
        - Good for timeout handling, periodic jobs, debounce, and protocol retry
    + Disadvantages:
        - Less accurate than hardware timers
        - Depends on RTOS tick rate and scheduler latency
        - Callback or event may be delayed if the system is busy
        - Not suitable for precise waveform generation or very tight timing

![Software timers](08_sw_timer.png)

AKOS implements **Software timers**, AKOS timer is kernel service built on top of a hardware timer, this case is SysTick. Many other RTOSes also allow configure timer with other hardware timers.

The SysTick timer generates a periodic interrupt, called the SysTick handler. AKOS timer uses this tick to update its internal time, wake delayed tasks, and check whether any software timers have expired.

AKOS timer does not require one hardware timer per timer object. Instead, it manages many software timers in software using its timer list or timer queue.

Unlike delay, which blocks the current task, a software timer lets the task continue running. When the timer expires, AKOS can call a callback, send an event, or wake another task.

RTOS timer services are commonly used for timeout handling, periodic jobs, button debounce, protocol retry, and software watchdog logic.

## Timers structure

AKOS stores each software timer in a small runtime object called `ak_timer_t`.
This object is kept inside a fixed [timer pool](#timer_pool), so timers can be created and
removed without relying on general-purpose heap allocation.

The timer structure contains:

- `next`: links timer objects together in the free list inside the [timer pool](#timer_pool)
- `id`: a user-defined timer identifier, useful for application-level tracking
- `timer_list_item`: the list node used when the timer is placed into the active
  or overflow timer lists
- `sig`: the signal sent to the destination thread when the timer expires
- `des_thread_id`: the thread ID that receives the signal
- `func_cb`: an optional callback executed when the timer expires
- `period`: the repeat interval in ticks; `0` means the timer is one-shot

In other words, the timer object holds both the scheduling metadata and the
action to perform on expiry. The list item lets AKOS sort timers by expiration
tick, while the signal, callback, and period fields describe what happens when
the timer fires.

![Timer structure](08_timer_structure.png)

## Timers pool{#timer_pool}

AKOS uses a fixed timer pool to store all software timer objects. In the code,
the pool is a static array of `ak_timer`, and the objects are linked together
through the `next` pointer to form a free list.

When the timer module starts, AKOS initializes that free list and points
`free_list_timer_pool` at the first unused timer object. Creating a timer takes
one item from the free list, and removing a timer returns it back to the pool.
This keeps timer allocation fast and predictable, without using the general
heap.

The pool is protected by critical sections, so timer creation and removal stay
safe even when the scheduler is running. 

![Timer pool](08_timer_pool.png)

That way we have a pool of timer elements! Now everytime application need timer, it will request from this pool. Also the same when application doesnt need timer anymore, it put timer back to that pool.

## Timer Lists

Software timers also have a time property, usually called an **expiration tick**. This is the tick value when the timer should expire. To support this behavior, AKOS stores each software timer with an expiration tick value. This value is compared with the global tick_count, which is updated periodically by the system tick interrupt.

Because tick_count has a limited range, it can eventually overflow. For example, if tick_count is an unsigned int on a 32-bit MCU, its maximum value is **0xFFFFFFFF**, or **4,294,967,295**. After reaching that value, the next tick wraps it back to 0. To handle this correctly, AKOS maintains two software timer lists:

- **timer_list**: timer list currently being used.
- **overflow_timer_list**: timer list used to hold timers that expire after the current tick count overflows.

![Timer lists](08_timer_lists.png)

The figure above demonstrates how these lists handle the overflow timeline:

- **(1)**: The active timer list is currently **timer_list**.
- **(2)**: tick_count has already reached 4,294,967,200 ticks, so 95 ticks remain before it overflows to 0.
- **(3)**: At that time, a software timer is started with a timeout of 500 ticks. Since the timeout passes beyond the current tick range, the timer cannot be placed in the normal **timer_list**.
- **(4)**: The timer is inserted into **overflow_timer_list**, and its expiration value is calculated relative to the next tick cycle.
- **(5)**: When tick_count overflows, AKOS switches the active timer list to **overflow_timer_list**. The old **timer_list** becomes empty and is reused as the new overflow timer list.

The timer-list structure is similar to the delay-list structure, but its nodes represent software timers instead of delayed threads. Each node is sorted by expiration time. With this design, AKOS only needs to check the closest timer expiration on each tick, instead of traversing the entire timer list every time.

The timer list works same like delay_list. All nodes is sorted by timestamp (timer's period + current tick). With that design, AKOS only needs to track the closest tick at which a timer's tick expires, without traversing the entire timer list.

![Timer list](08_timer_list.png)

## Types of timer

AKOS supports two software timer modes:

- **One-shot timer**: starts once, expires once, and then stops. In the code,
  this mode sets `period` to `0`, and when it expires AKOS removes it from the
  active list and returns it to the timer pool.
- **Periodic timer**: reloads itself every time it expires. The `period` field
  stores the repeat interval in ticks, and after each expiry AKOS schedules the
  next trigger by adding `period` to the current tick.

Both timer types can either post a signal to a destination thread or call an
optional callback function when they expire. The difference is that a periodic
timer stays active across multiple expirations, while a one-shot timer is used
for a single timeout event.

![Timer types](08_timer_types.png)

## Timer service

The timer service is the runtime part of the software timer subsystem. In AKOS,
it is handled by the timer thread through `akos_timer_processing()`.

On each pass, the timer service:

1. reads the current system tick
2. checks whether the active timer list has wrapped to a new tick range
3. scans the head of the active timer list for expired timers
4. removes expired timers from the list
5. runs the timer callback or posts a signal to the destination thread
6. reloads periodic timers with the next expiration tick
7. returns one-shot timers back to the timer pool
8. waits until the next timer expiration or wake-up message

This design keeps timer handling centralized and predictable. The service only
needs to check the timer at the head of the sorted list, so it avoids scanning
every timer on every tick.

Because that timer service also is a thread, it also has priority and can be configured by `OS_CFG_TIMER_TASK_PRI`. Normally highest at `0`. But a good rule of thumb:
- If the timer thread only posts signals and does almost no work, 0 is fine.
- If callbacks might do meaningful work, make the priority configurable so the app can tune it.
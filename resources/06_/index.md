# Scheduler

The scheduler decides which thread runs next. In AKOS, it is the part of the
kernel that keeps the ready threads organized and picks the next thread to run.

That gives AKOS a simple but practical scheduling model for embedded systems:
urgent work runs first, and equal-priority work shares the CPU fairly.

## Priority Bitmap

AKOS keeps a ready list for each priority level, and the priority bitmap tracks
which of those levels currently have ready work.

The priority subsystem uses one bit per priority level:

- A set bit means that priority has at least one ready thread
- A clear bit means that priority has no ready threads

Lower numeric values mean higher priority, so the scheduler always looks for
the smallest ready priority value first.

The related APIs are:

- `akos_priority_init()`
- `akos_priority_insert()`
- `akos_priority_remove()`
- `akos_priority_get_highest()`

When a thread becomes ready, the kernel inserts it into the list for its
priority. If that list was empty before, the matching bit in the priority table
is set. If the list becomes empty again, the bit is cleared.

The bitmap makes it fast to find the highest ready priority without scanning
every ready list one by one.

![Priority bitmap table](06_prio_bitmap.png)

## How The Scheduler Works

The AKOS scheduler combines three ideas into one flow: **priority based**
scheduling, **round robin** scheduling, and **tick and time slicing**.

- **Priority based** scheduling decides which priority level should run first.
- **Round robin** scheduling decides which thread should run next inside that
  priority level.
- **Tick and time slicing** logic drives wakeups, timeout expiry, and rotation
  through the ready list.

![Scheduler's work overview](06_how_scheduler_works.png)

The full flow looks like this:

1. The tick counter increments.
2. Delayed threads whose wake time has arrived move back to the ready lists.
3. The scheduler checks the priority bitmap to find the highest ready priority.
4. If only one thread is ready at that priority, the scheduler runs it.
5. If more than one thread is ready at that priority, the scheduler advances to
   the next thread in that ready list.

That is why the scheduler works well for AKOS:

- High-priority work can preempt lower-priority work.
- Equal-priority threads share CPU time fairly.
- Timer and delay events can feed directly back into scheduling.

AKOS uses priority-based preemptive scheduling. A thread with a higher
priority can take the CPU from a lower-priority thread when it becomes ready.

This can happen when:

- A delayed thread wakes up
- A message arrives for a waiting thread
- The tick handler moves a thread from blocked to ready
- Application code unblocks a higher-priority thread through a kernel service

When that happens, AKOS can trigger a context switch so the higher-priority
thread runs as soon as possible.

## What Makes A Thread Ready

A thread enters the ready state when it is able to run again. Common cases are:

- The thread is created during startup
- A delay expires
- A message arrives for a waiting thread
- The kernel moves it back from a blocked state

When that happens, AKOS inserts the thread into the appropriate ready list and
updates the priority bitmap if needed.

## What Makes A Thread Block

Threads can leave the ready state when they:

- Call `akos_thread_delay()`
- Wait for a message
- Are suspended by the kernel or application logic

Blocked threads stay out of the ready lists until the kernel decides they are
eligible to run again.

## Related Pieces

The scheduler chapter connects directly to a few other parts of the kernel:

- [Kernel basics](../03_/index.md) introduces the main kernel objects
- [Threads management](../05_/index.md) explains thread lifecycle and state
- [Timers management](../08_/index.md) explains how timer expiry feeds back
  into scheduling

The short version is: AKOS always runs the highest-priority ready thread, and
threads at the same priority take turns in the ready list.

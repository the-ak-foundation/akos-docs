# Inter-thread Synchronization

Inter-thread synchronization is the coordination of multiple threads so their
actions happen in the correct order and shared resources are used safely.

In practice, synchronization is:
- Waiting for an event or signal.
- Making one thread start only after another thread finishes.
- Limiting access to a resource.
- Preventing race conditions when threads overlap in time.

In AKOS today, synchronization is intentionally lightweight. The kernel mainly
uses critical sections, message queues, and scheduler-managed blocking or
wakeup paths to coordinate threads. That is enough for the current design, but
more complete synchronization features will need to be developed in the future
if the application grows and needs richer coordination patterns.

## Common synchronization mechanisms

Common synchronization mechanisms provided by RTOS kernels (such as FreeRTOS or ZephyrRTOS) include:

### Semaphores
It has usually 2 types
1. **Counting Semaphores**:
A semaphore that holds a count of available resources or events. Threads can take and give it multiple times, so it is useful when several identical resources need to be tracked.
2. **Binary Semaphores**:
A semaphore with only two states, usually taken or available. It is commonly used as a simple signal between an interrupt or producer and a waiting thread.
### Mutexes (Mutual Exclusion)
    - A lock used to protect a shared resource so only one thread can access it
      at a time. Many RTOS kernels add priority inheritance to reduce priority
      inversion when a high-priority thread waits on a low-priority owner.
### Events / Event Groups
    - A set of flags that can be waited on individually or in combination. This
      is useful when a thread needs to react to one or more conditions without
      consuming a message payload.
### Queues and Mailboxes
    - FIFO objects used to pass data or pointers between threads. Queues usually
      hold multiple items, while mailboxes are often a lighter-weight single-slot
      form.
### Task Notifications
    - A direct way to wake or notify a thread without creating a separate kernel
      object. These are typically very fast and low-overhead, but they usually
      support less structure than a full queue or event group.

AKOS does not currently expose the full set of primitives above. Instead, it
relies on critical sections for protection, message queues for communication,
and scheduler-managed blocking and wakeup paths for synchronization behavior.
That gives the kernel a smaller surface area while still covering the most
common event-driven patterns used in embedded applications.

In a small RTOS, synchronization usually serves two jobs:

1. protect shared data while it is being updated
2. block a thread until another thread or event makes progress possible

AKOS currently handles those jobs with critical sections, scheduler-managed
blocking, and message-based wakeups. The kernel does not expose classic mutex
or semaphore APIs in the current codebase, so this chapter focuses on the
mechanisms that are actually implemented today.

AKOS currently keeps synchronization lightweight. In practice, it relies on
critical sections to protect shared kernel state, and it uses message-driven
blocking and wakeups to coordinate threads when work becomes available.

That is enough for the current kernel design, but the model is intentionally
small. As applications grow, richer synchronization primitives such as
semaphores, mutexes, or event groups may be added in the future to support
more complex coordination patterns.

## Related Topics

- [Threads management](../05_/index.md)
- [Scheduler](../06_/index.md)
- [Inter-thread Communication](../09_/index.md)

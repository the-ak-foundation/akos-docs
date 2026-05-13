# Kernel basics

Kernel objects are the building blocks of an RTOS. In AKOS, they are the
runtime structures the kernel manages on behalf of the application: threads,
messages, timers, priorities, and the control state that keeps them moving
together.

This chapter gives you a simple map of those objects before the later chapters
go into each subsystem in detail.

![Kernel objects overview](03_kernel_objs.png){html: width=50%}

## Kernel Objects

At a high level, AKOS organizes its kernel around a few core objects:

- Threads for execution
- Message queues for communication
- Software timers for delayed work
- Priority state for run ordering
- Critical sections for protecting shared kernel data

These objects are not isolated features. They are connected: threads wait for
messages, timers wake threads up, and the scheduler decides which ready thread
runs next.

## Threads

A thread is the basic unit of execution in AKOS. Each thread has:

- A thread ID
- An entry function
- An argument pointer
- A priority
- A message queue size
- A requested stack size

`AKOS_THREAD_DEFINE(...)` is the static thread-definition API. It creates the
compile-time thread definition that the kernel later turns into a runtime
thread object during system startup.

The thread subsystem also keeps track of runtime thread state, such as whether a
thread is running, ready, delayed, or waiting on a message.

![Thread objects diagram](03_thread_objs.png){html: width=80%}

## Messages

Messages are the main communication object in AKOS. They let one thread wake
another thread up with either:

- A pure signal
- A signal plus copied payload data

The message subsystem uses:

- `msg_t` for the message node
- `msg_queue_t` for the queue metadata
- `akos_message_queue_put_pure()`
- `akos_message_queue_put_dynamic()`
- `akos_message_queue_get()`

This gives application code a clean way to pass events between threads without
sharing state directly.

## Timers

Timers are another kernel object that build on top of the message system. A
timer can expire once or repeat periodically, and when it expires it can post a
signal to a destination thread or invoke a callback.

The timer subsystem revolves around `ak_timer_t` and APIs such as:

- `akos_timer_create()`
- `akos_timer_start()`
- `akos_timer_reset()`
- `akos_timer_remove()`

Timers are especially useful when you want delayed work, periodic polling,
small callback functions, or time-based events without blocking a thread.

![Timers life cycle](03_timer_life_cycle.png)

## Priority And Scheduling

Priority is what ties the kernel objects together. AKOS uses priority tracking
to decide which ready thread should run next.

That means:

- A higher-priority ready thread can preempt lower-priority work
- Delayed or blocked threads stay out of the ready set
- The kernel can quickly pick the next runnable thread

The scheduler is the control point that turns thread state into actual CPU
execution.

## Kernel Control

AKOS also needs a small amount of kernel control logic around those objects.
That is where `core` comes in.

The main control APIs are:

- `akos_core_init()`
- `akos_core_run()`
- `akos_core_enter_critical()`
- `akos_core_exit_critical()`

`akos_core_init()` prepares the kernel subsystems, while `akos_core_run()`
hands control to the scheduler. The critical-section APIs protect shared kernel
data structures so the object lists stay consistent across interrupts and
thread context.

## Interrupt Context

Interrupt service routines are not kernel objects in the same sense as threads
or timers, but they matter because they can interact with the kernel at the
boundaries.

In AKOS, interrupts typically feed events into the system, while the kernel
keeps the runtime objects consistent and decides when a thread should wake up
and run.

## Why This Matters

Once you understand the kernel objects, the rest of the documentation becomes
much easier to read:

- [Threads management](../05_/index.md) explains how threads are created and
  managed.
- [Scheduler](../06_/index.md) explains how priorities turn into run order.
- [Timers management](../08_/index.md) explains delayed and periodic work.
- [Inter-thread Communication](../10_/index.md) explains how messages move
  between threads.

The short version is simple: AKOS is built from a handful of kernel objects,
and the scheduler keeps them working together.

# Introduction

AKOS is a small embedded real-time operating system built for microcontrollers. It is organized around a priority-based scheduler and an
event-driven programming model, so application code can react to signals,
timers, and state changes instead of relying on one large super-loop.

## Foreground-Background Systems

Many small embedded systems start with a foreground/background design, also
called a super-loop. In that model, the application spends most of its time in
one endless main loop and does work by polling flags, checking inputs, and
calling small handlers in sequence.

Interrupt service routines still matter in that model. They usually do the
time-critical work, then hand off the rest to the main loop by setting flags or
updating shared state.

That approach is easy to understand and works well for very small problems. But
as soon as the application grows, the limits start to show:

- one long task can delay everything else
- timing becomes harder to reason about
- shared state spreads across the whole program
- responsiveness depends on how often the loop comes back around

![Foreground and background flow](02_fore-back.png)

An RTOS exists to solve that next step. Instead of one loop doing everything,
the kernel breaks the system into threads, schedules them by priority, and lets
timers and messages drive work in a more structured way. AKOS is the RTOS used
in this documentation, and it follows that model.

## RTOS Systems

The RTOS System provides kernel. It is just additional software run before tasks or threads, responsible to manage the time and resources of MCU. 

The application by kernel is split into small pieces of tasks, then decides what runs
and when based on priorities and time slice. On a single CPU, only one task executes at any given time. A task is also typically implemented as an infinite loop and it thinks that it has the CPU completely to itself. 

These parts work together to keep the
system responsive and predictable. The kernel does not replace the
application; it organizes it so each piece can do its job without one long
loop holding everything together.

![RTOS system overview](02_rtos.png)

With this model, AKOS provides:

- A clear priority model, where each thread has a defined priority level
- Cooperative behavior among threads at the same priority
- Preemptive scheduling, so higher-priority work can run before lower-priority work

So the diagram gives overview concept of what a typical RTOS does include our AKOS. Not only how threads organized and scheduled but also additional objects listed below. 

## What AKOS Provides

- Memory management
- Preemptive task scheduling
- Software timers
- Inter-thread communication
- Inter-thread synchronization
- Hardware-dependent port layer for context switching and tick handling

The rest of the documentation goes deeper into the kernel model, thread
management, scheduling, timers, synchronization, communication, and porting so
you can see how those pieces fit together in practice.

## Supported Architectures

AKOS is primarily documented around the ARM Cortex-M family, where the current
port layer provides the core scheduler and context-switch integration. The
architecture split is kept deliberately small so additional targets can be
ported without changing the higher-level kernel model.

- **ARM Cortex-M3**

## Supported Compiler

The examples and build scripts in this repository are written for the GNU Arm
Embedded toolchain. The compiler support is kept intentionally focused so the
documented build and example flow stays consistent across the repo.

- **GNU Arm Embedded Toolchain**

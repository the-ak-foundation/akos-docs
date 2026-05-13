# Porting

Porting is the work needed to make AKOS run on a specific CPU architecture and
board. The kernel provides the scheduling and runtime logic, while the port
layer supplies the low-level CPU and startup support that the kernel depends
on.

## Interrupts

An interrupt is a *hardware mechanism* that signals the CPU to stop normal code temporarily and run the special function associated with that interrupt. That function is called an *interrupt handler* or *Interrupt Service Routine (ISR)*. This process is *asynchronous*.

Interrupts also have priorities. A higher-priority ISR can preempt a lower-priority ISR to improve responsiveness.

*Interrupt entry* is defined as the time between interrupt reception and the start of the ISR.

*Interrupt return* is defined as the time between the end of the ISR and the return to the interrupted code.

![Nested IRQs process](11_nested_irq.png)

To support multiple interrupts and even nested, some processor support additional design, for example with Cortex-M, that design called *Nested Vectored Interrupt Controller (NVIC)*.

![The NVIC in the Cortex-M processor family](11_nvic.png)

This NVIC receives signals interrupt both from outside processor like I/O, Peripherals,... and inside from CPU like divide by zero,...

Because interrupts are asynchronous, a critical section can be corrupted if an interrupt occurs while the program is updating shared data. To prevent this in AKOS, interrupts are often temporarily disabled when entering the critical section and re-enabled after leaving it. 

User must provide porting for these APIs:

- `port_disable_interrupts`
- `port_enable_interrupts`

## ARM Cortex-M3 Architecture

For the current documentation, the Cortex-M3 port is the reference implementation.

ARM Cortex-M3 is the CPU architecture AKOS targets in this repository. It uses
the ARM exception model, a separate system tick timer, and a nested interrupt
controller to handle hardware events and kernel scheduling work.

For AKOS, the important parts of the architecture are:

- Thread mode for normal application execution
- Exception mode for interrupts and system events
- SysTick for the kernel time base
- SVC for controlled entry into the first thread
- PendSV for deferred thread switching

These features let the kernel keep normal thread execution separate from the
low-level exception flow that the port layer manages.

<!-- TODO: add an ARM Cortex-M3 architecture image here showing thread mode,
exception mode, SysTick, SVC, PendSV, and NVIC. -->

## Interrupt Management

AKOS uses the port layer to control the interrupt state around kernel-critical
work. The kernel depends on the port to temporarily mask interrupts when it
needs to protect shared runtime data.

The Cortex-M3 port provides the basic interrupt helpers:

- `port_disable_interrupts`
- `port_enable_interrupts`

These helpers are used by kernel critical sections so the kernel can update
ready lists, message queues, and other shared structures safely.

The port layer also configures exception priorities so the scheduler-related
exceptions stay at the low end of the priority range. That lets the kernel
defer thread switching work until the CPU is ready to handle it.

<!-- TODO: add an interrupt management image here showing interrupt masking,
critical sections, and the low-priority exception flow. -->

## Cortex-M3 Interrupt Concepts

On Cortex-M3, interrupts are part of the exception system. The CPU uses
exceptions for both external interrupts and core events, so the port layer has
to work with that model when it starts threads and requests context switches.

The key ideas AKOS relies on are:

- NVIC manages interrupt priority and pending state
- SysTick provides the periodic kernel tick
- SVC starts the first thread through an exception return path
- PendSV is used for deferred thread switching

These exceptions are useful because they let the kernel separate fast event
handling from slower scheduling work.

<!-- TODO: add a Cortex-M3 interrupt concept image here showing NVIC, SysTick,
SVC, and PendSV in the exception flow. -->

## Port Layer Overview

The port layer sits between the kernel and the hardware. It is responsible for
the pieces that are too architecture-specific for the kernel itself:

- Building the initial thread stack frame
- Starting the first runnable thread
- Requesting and handling thread switches at the CPU level
- Setting up the system tick source
- Providing interrupt-masking helpers for kernel critical sections

<!-- TODO: add a port layer overview image here showing the kernel, the port
layer, and the Cortex-M3 CPU/board boundary. -->

## Cortex-M3 Port

AKOS uses a Cortex-M3-specific port in this repository. That port lives under
`akos/port/arm/cortex-m3/` and provides the CPU-facing hooks that the kernel
calls during startup and scheduling.

The main port APIs are:

- `akos_port_task_stack_init()`
- `akos_port_start_first_task()`
- `akos_port_systick_init_freq()`

The port layer also exposes helpers and exception entry points such as:

- `port_disable_interrupts`
- `port_enable_interrupts`
- `port_setup_PendSV()`
- `port_trigger_PendSV()`

## Initial Stack Frame

Before a thread can run, the port layer prepares the stack so the CPU can
enter the thread entry function using the normal exception return path.

`akos_port_task_stack_init()` builds that initial frame from:

- The thread entry function
- The thread argument
- The stack buffer provided by the kernel

That gives a newly created thread the same starting state that a restored
thread would have after a switch.

## First Task Start

AKOS starts the first runnable thread through `akos_port_start_first_task()`.
That function sets up the processor state and then triggers `SVC 0` so the port
layer can restore the initial thread context.

The startup flow is:

1. The kernel initializes its subsystems.
2. The kernel selects the first runnable thread.
3. The port layer restores that thread context.
4. Execution continues in thread mode.

## Thread Switching

When the kernel decides that a different thread should run, it asks the port
layer to perform a switch.

On Cortex-M3, that work is handled through PendSV:

1. Save the current thread context on its stack.
2. Update the current thread pointer.
3. Load the next ready thread pointer.
4. Restore the next thread context.
5. Return to thread mode with the new thread running.

PendSV is a good fit for this role because it runs at the lowest priority and
lets the CPU defer the actual switch until it is safe to do so.

## Board Porting

The CPU port is only part of the job. A new board still needs its own startup,
clock, memory map, and peripheral setup around AKOS.

For a new target, the board-side work usually includes:

- Startup code and vector table setup
- Clock tree and SysTick frequency configuration
- Linker script changes for flash and RAM layout
- Board-specific pin, LED, button, and console setup

In AKOS, that board-specific work lives mostly in the example and platform
files, while the port layer stays focused on CPU behavior.

## Related Files

The Cortex-M3 port is implemented in:

- `akos/port/arm/cortex-m3/port.c`
- `akos/port/arm/cortex-m3/port.h`

For scheduler behavior, see [Scheduler](../06_/index.md). For thread behavior,
see [Threads management](../05_/index.md).

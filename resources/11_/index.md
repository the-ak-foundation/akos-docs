# Porting

Porting is the work needed to make AKOS run on a specific CPU architecture and
board. The kernel provides the scheduling and runtime logic, while the port
layer supplies the low-level CPU and startup support that the kernel depends
on.

For the current tree, the Cortex-M3 port is the reference implementation.

## ARM Cortex-M3 Architecture

ARM Cortex-M3 is the CPU architecture AKOS targets in this repository. It uses
the ARM exception model, a separate system tick timer, and a nested interrupt
controller to handle hardware events and kernel scheduling work.

For AKOS, the most important Cortex-M3 concepts are the register model,
processor modes, interrupt controller, memory layout, instruction set, and
exception flow.

![ARM Cortex-M3 Architecture](11_cm3_arch.png){html: width=50%}

### Registers

The Cortex-M3 register set defines the CPU state that the port layer must
create, save, and restore during startup and context switching.

![ARM Cortex-M3 registers set](11_arm_cm3_registers_set.png){html: width=50%}

The most important registers for AKOS are:

- `R0` to `R12` for general-purpose data and parameter passing
- `SP` for the current stack pointer
- `LR` for return state and exception return behavior
- `PC` for the current execution address
- `xPSR` for processor status, including Thumb state
- `MSP` for the main stack pointer used during reset and exceptions
- `PSP` for the process stack pointer used by threads in normal execution

For a new thread, the port layer builds an initial stack frame that matches the
register state the CPU expects to restore on exception return.

### Operation Modes

The Cortex-M3 has two related concepts:

- Execution mode: `Thread mode` and `Handler mode`
- Privilege level: `Privileged` and `Unprivileged`

These are not the same thing.

The execution modes are:

- Thread mode for normal application and RTOS thread execution
- Handler mode for exceptions such as SysTick, SVC, and PendSV

The privilege relationship is:

- Handler mode always runs as privileged
- Thread mode can run as privileged or unprivileged

![Operation modes and privilege levels](11_modes_and_levels.png){html: width=50%}

That means normal program code usually runs in Thread mode, while exceptions
run in Handler mode. If Thread mode is unprivileged, it cannot execute some
privileged instructions or directly access some protected system resources.

![Modes transition](11_modes_transition.png){html: width=50%}

AKOS relies on this split so application code runs in Thread mode while the
port layer performs startup, tick handling, and context switching in Handler
mode.

### Interrupts and Exceptions

On Cortex-M3, interrupts are handled through the exception system. The CPU uses
exceptions for both external interrupts and internal events, so the port layer
works through that model when it starts threads and requests scheduling work.

For AKOS, the important parts are:

- SysTick for the kernel time base
- SVC for controlled entry into the first thread
- PendSV for deferred thread switching
- External interrupts for device-driven events around the kernel

These features let the kernel keep normal thread execution separate from the
low-level exception flow that the port layer manages.

![Cortex M3 exception types](11_cm3_exceptions.png){html: width=50%}

### SysTick Timer

SysTick is a built-in Cortex-M3 system timer. It is a 24-bit down-counter that
can generate a periodic exception when it reaches zero.

For AKOS, SysTick is important because it provides the regular time base used
by the kernel.

![Systick diagram](11_systick_diagram.png)

The typical SysTick flow is:

- Load the reload register with the tick interval
- Start the counter with the selected clock source
- Count down to zero
- Raise the SysTick exception
- Reload automatically and begin the next tick period

In AKOS, this periodic exception is used to:

- Increment the kernel tick count
- Wake delayed threads when their timeout expires
- Decide whether a context switch is needed

That is why SysTick is one of the core hardware blocks the port layer must
configure during startup.

### Supervisor Call (SVC)

`SVC` is a system exception triggered by software through the `SVC`
instruction. It is used when software wants to enter a controlled supervisor
service path through the exception mechanism.

In AKOS, the purpose of `SVC` is to start the first runnable thread after the
kernel has finished its startup work. The port triggers `SVC`, enters the SVC
handler, restores the first thread context, and then returns into thread
execution through the normal exception-return path.

### Pendable Service Call (PendSV)

`PendSV` is a system exception used for deferred service work. Software can set
it to pending and let the CPU handle it later through the normal exception
mechanism.

In AKOS, the purpose of `PendSV` is to perform context switching. When the
kernel decides that another thread should run, it pends `PendSV`, enters the
PendSV handler, saves the current thread context, restores the next thread
context, and then returns to thread execution.

### Reference

- [Cortex-M3 processor from ARM](https://developer.arm.com/documentation/dui0552/a/introduction?lang=en)
- [The Definitive Guide to the ARM Cortex-M3, 2nd Edition](https://community.nxp.com/pwmxy87654/attachments/pwmxy87654/kinetis/39396/1/The%20definitive%20guide%20to%20the%20ARM%20CORTEX-M3%202nd.pdf)
- [The Definitive Guide to the ARM Cortex-M3.pdf](https://www.embedic.com/uploads/files/20201008/The%20Definitive%20Guide%20to%20the%20ARM%20Cortex-M3.pdf?srsltid=AfmBOorBz8cOGaKAq4_xWuFAmvtO0sB26JE3kaUGuL14lHue-1q5PA1s)
- [Cortex-M3 Technical Reference Manual](https://www.keil.com/dd/docs/datashts/arm/cortex_m3/r1p1/ddi0337e_cortex_m3_r1p1_trm.pdf)
- [Systick](https://www.se.rit.edu/~llk/cmpe-240/lectures/Chapter_11_Interrupt_SysTick.pdf)

## Port Interrupt Management

AKOS uses the port layer to control the interrupt state around kernel-critical
work. The kernel depends on the port to temporarily mask interrupts when it
needs to protect shared runtime data.

The reference port provides the basic interrupt helpers:

- `port_disable_interrupts`
- `port_enable_interrupts`

These helpers are used by kernel critical sections so the kernel can update
ready lists, message queues, and other shared structures safely.

The port layer also configures exception priorities for scheduler-related
exceptions. In the current Cortex-M3 port, PendSV is assigned a very low
priority so context switching can be deferred safely, while SysTick is
configured as the periodic kernel tick source.

<!-- TODO: add an interrupt management image here showing interrupt masking,
critical sections, and the low-priority exception flow. -->

## Port Layer Overview

The port layer sits between the kernel and the hardware. It is responsible for
the pieces that are too architecture-specific for the kernel itself:

- Building the initial thread stack frame
- Starting the first runnable thread
- Requesting and handling thread switches at the CPU level
- Setting up the system tick source
- Providing interrupt-masking helpers for kernel critical sections

<!-- TODO: add a port layer overview image here showing the kernel, the port
layer, and the CPU/board boundary. -->

## Reference Port

AKOS uses a reference CPU port in this repository. It lives under
`akos/port/arm/cortex-m3/` and provides the CPU-facing hooks that the kernel
calls during startup and scheduling.

The main port APIs are:

- `akos_port_task_stack_init()`
- `akos_port_start_first_task()`
- `akos_port_systick_init_freq()`

The port layer also exposes helper macros such as:

- `port_disable_interrupts`
- `port_enable_interrupts`
- `port_setup_PendSV()`
- `port_trigger_PendSV()`

The reference port also provides exception handlers that connect the CPU's
exception model to the kernel runtime:

- `port_SVCHandler`
- `port_PendSVHandler`
- `port_SysTickHandler`

## Stack Initialization

Before a thread can run, the port layer prepares the stack so the CPU can
enter the thread entry function using the normal exception return path.

`akos_port_task_stack_init()` does three important things:

- It starts from the top of the thread stack buffer
- It aligns the stack pointer for Cortex-M exception use
- It writes an initial register frame that looks like a thread was already
  interrupted and is ready to be restored

The prepared frame includes values for:

- `xPSR`, with the Thumb-state bit set
- `PC`, set to the thread entry function
- `LR`, set to an initial placeholder return value
- `R0`, set to the thread argument
- Space for the remaining registers restored during startup or switching

The stack layout is prepared to match the normal Cortex-M exception model:

- Hardware-restored registers: `R0` to `R3`, `R12`, `LR`, `PC`, and `xPSR`
- Software-restored registers in the AKOS port: `R4` to `R11`

That means a new thread starts with:

- `PC` pointing to the thread entry function
- `R0` holding the thread argument
- `xPSR` in valid Thumb state

When the port later restores this stack, the CPU can continue as if the thread
had already been running and was simply being resumed after an exception.

That gives a newly created thread the same kind of starting state that a
restored thread would have after a context switch. In other words, the first
thread start and a later thread restore both follow the same Cortex-M return
model.

## First Task Startup

AKOS starts the first runnable thread through `akos_port_start_first_task()`.
That function sets up the processor state and then triggers `SVC 0` so the port
layer can restore the initial thread context.

The startup flow is:

1. The kernel initializes its subsystems.
2. The kernel selects the first runnable thread.
3. The port layer restores that thread context.
4. Execution continues in thread mode.

## Context Switching

When the kernel decides a different thread should run, it asks the port layer
to perform a switch.

In the current reference port, that work is handled through PendSV. The kernel
updates `tcb_high_rdy_ptr` and then pends the exception, and the handler
performs the CPU-level context save and restore.

The switch flow is:

1. Read the current thread stack pointer from `PSP`.
2. Save `R4` to `R11` onto the current thread stack.
3. Store the updated stack pointer back into the current thread control block.
4. Update `tcb_curr_ptr` to the next ready thread.
5. Load the next thread stack pointer from its control block.
6. Restore `R4` to `R11` from the next thread stack.
7. Write the new stack pointer back into `PSP`.
8. Return from PendSV so the CPU restores the remaining hardware-stacked
   registers and resumes the next thread.

The Cortex-M hardware already stacks `R0` to `R3`, `R12`, `LR`, `PC`, and
`xPSR` on exception entry. The PendSV handler only has to save and restore the
remaining software-saved registers `R4` to `R11`.

PendSV is a good fit for this role because it runs at very low priority and
lets the CPU defer the actual switch until it is safe to do so.

## Board Porting

The CPU port is only part of the job. A new board still needs its own startup,
clock, memory map, and peripheral setup around AKOS.

For a new target, the board-side work usually includes:

- Startup code and vector table setup
- Clock tree setup and providing the correct core clock value
- Linker script changes for flash and RAM layout
- Board-specific pin, LED, button, and console setup

In AKOS, that board-specific work lives mostly in the example and platform
files, while the port layer stays focused on CPU behavior such as stack-frame
layout, exception handling, and SysTick register programming.

## Related Files

The Cortex-M3 port is implemented in:

- `akos/port/arm/cortex-m3/port.c`
- `akos/port/arm/cortex-m3/port.h`

For scheduler behavior, see [Scheduler](../06_/index.md). For thread behavior,
see [Threads management](../05_/index.md).

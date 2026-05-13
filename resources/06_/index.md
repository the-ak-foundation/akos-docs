# Scheduler

The scheduler is the part of the operating system that decides which process gets to run next. It helps share CPU time fairly, keeps the system responsive, and balances workload across tasks.

## Priority Bitmap
AKOS uses a priority bitmap to track which priorities are ready to run. Each bit represents one priority level, so the kernel can find the highest ready task with a small number of bit operations instead of scanning a normal array one entry at a time.

This matters because the scheduler runs often and must stay predictable. In the current implementation, lookup is bounded by the number of bitmap bytes plus the bit position inside the first nonzero byte, which is still much faster than a full array scan in the common case. A bitmap also uses very little memory and scales well as the number of priorities grows.

![Priority Bitmap table](06_prio_bitmap.png)

## The Ready List

Threads that are ready to run are placed in a ready list that matches their priority. In the code, AKOS keeps one ready list per priority level, so the scheduler can quickly jump to the highest non-empty priority and avoid scanning every thread.

This structure works together with the priority bitmap. The bitmap tells the scheduler which priority level is ready, and the ready list for that priority tells it which thread should run next.

The ready list is simply an array of singly linked lists. Each element in the ready-list array is the head of a list that holds threads with the same priority.

![Empty ready list](06_ready_list.png)

The image above shows an empty ready list. When ready threads are available, they are added to the ready list according to their priority. Notice that the current item pointer is used to track which thread is active now, because threads with the same priority share CPU time and must be tracked separately.

![Ready list with threads](06_ready_list_with_threads.png)

Let's see what happens when the application has three threads with the same priority number, 0.

![Ready list with 3 threads with prio number 0](06_ready_task_list_0.png)

From this, the scheduler can pick the highest-priority TCB to execute.

This list always uses push-back insertion, which means a new thread added to a list with the corresponding priority will be placed at the tail of that list.

## The Delay List 

Unlike the ready lists, delay lists need two instances because the scheduler checks them frequently, usually once per tick. To support that behavior, AKOS uses a variable called *tick_count* of type `unsigned int`. On most MCU systems, registers are 32-bit, so the maximum value *tick_count* can hold is **0xFFFFFFFF**, or **4,294,967,295**. If *tick_count* increases by 1 every millisecond, it overflows after approximately **1.19304 hours**. To avoid undefined behavior when that happens, AKOS maintains two delayed-thread lists:
- **dly_task_list**: delayed task list currently being used.
- **overflow_dly_task_list**: delayed task list currently being used to hold tasks that have overflowed the current tick count.

![Two delay lists](06_two_delay_list.png)

The figure above demonstrates how these lists handle the overflow timeline:
- (1): The active delay list is currently `dly_task_list`.
- (2): `tick_count` has already reached 4,294,967,200 ticks, so 95 ticks remain before it overflows to 0.
- (3): At that time, a thread wants to delay for 500 ticks. There are two possible approaches:
  + Mark the thread as overflowed, place it at the beginning of `dly_task_list` (not implemented), and treat its expiration value as 405 instead of 500.
  + Put the thread into `overflow_dly_task_list`, which is empty at that point, and also treat its expiration value as 405 instead of 500.
- (4): When the tick counter overflows, the active delay list switches to `overflow_dly_task_list`. The old `dly_task_list` is then empty and becomes the new overflow list.

The delay-list structure is similar to the ready list, but its nodes are sorted by expiration time instead of priority. With that design, AKOS only needs to track the closest tick at which a thread timeout expires, without traversing the entire delay list.

![Delay lists sorts values](06_delay_list.png)

## The Suspended List

The suspended list structure is also identical to the ready list. It is used for threads that need to block indefinitely until an external event wakes them up.

Like the ready list, the suspended list is organized by priority, so the kernel can move a thread out of suspension and back into the ready list without scanning every thread. A suspended thread does not have a timeout, so time alone cannot wake it.

In AKOS, a thread enters the suspended list when it waits without a timeout. The thread stays there until a signal, message, or other wake-up event becomes available. When that happens, AKOS removes the thread from the suspended list and returns it to the ready list for normal scheduling.

## Scheduling points

Application code usually does not care about scheduling points and does not call the scheduler directly. Instead, AKOS checks for a possible context switch at specific kernel events and triggers `PendSV` when a different thread should run.

The scheduler is typically checked in these situations:

- **Time advances and a delayed thread reaches its wake-up time:**

  The tick handler updates the system time through `akos_thread_increment_tick()`. When the current tick reaches the wake-up time of one or more delayed threads, AKOS removes them from the delay list, moves them back to the ready list, and compares their priority with the running thread. If a newly unblocked thread has a higher priority, the kernel requests a context switch.

- **The running thread blocks itself and can no longer continue:**

  When a thread calls `akos_thread_delay()`, it is removed from the ready list and placed into the delay list for the requested number of ticks. If the thread asks to wait forever, AKOS treats it as suspended instead of delayed. Because the current thread is no longer runnable, the kernel immediately looks for the next highest ready thread and triggers a switch.

- **When a thread waits for a message and enters a blocked state:**

  When a thread calls `akos_thread_wait_for_msg()`, AKOS first checks whether a message is already available. If the queue is empty and the caller provides a timeout, the thread is moved out of the ready list and into a blocked state until a message arrives or the timeout expires. This gives other ready threads CPU time right away, and a context switch is requested if the current thread can no longer continue.

- **A message arrives and wakes a thread that may have higher priority than the current one:**

  When another thread posts a message with `akos_thread_post_msg_dynamic()` or `akos_thread_post_msg_pure()`, AKOS may move the destination thread back to the ready list if it was waiting on that message. If the awakened thread has a higher priority than the current one, the kernel marks it as the next high-ready thread and requests `PendSV` so it can run immediately.

In each case, the kernel updates the ready or delayed list first, then compares priorities, and finally requests a context switch only if the newly ready thread should run before the current one.

## Round-Robin Scheduling

When many threads have the same priority, AKOS allows each one to run for 1 ms. This amount of time may vary in the future, as other RTOSes define it as *time quanta*. This process is called *time slicing*.

The figure below demonstrates how round-robin scheduling looks.

![Round-Robin scheduling](06-round-robin.png)

## Preemptive Scheduling

Preemptive scheduling lets a higher-priority ready thread interrupt the currently running thread. In AKOS, this happens when a thread with a smaller priority number becomes ready and the kernel requests a context switch through `PendSV`.

This keeps the system responsive. The priority bitmap shows which priority levels are ready, and the ready list for that priority tells AKOS which thread should run next.

![Preemptive scheduling](06-preemptive.png)

## Context switch

When the next thread is scheduled to execute, the scheduler saves the current thread's context, which typically consists of the CPU registers, onto the current thread stack. It then restores the context of the new task and resumes execution of that task. This process is called a *context switch*.

The context-switch code is part of a processor's port of AKOS. A port is the code needed to adapt AKOS to the desired processor. This code is usually written in special C and assembly language. To understand more, see [Porting](../11_/index.md). In this section, we focus on the context-switching process for the ARM Cortex-M3.

Each thread has memory allocated for its TCB and stack. The stack contains the CPU registers and the runtime stack for that thread. At initialization, the runtime stack is empty, and only the initial CPU register values are present. The `stk_ptr` field in the TCB holds the current SP, which starts at `R4`. As a result, `PSP` points to `R4` at that moment.

On Cortex-M3, the CPU automatically pushes `xPSR`, `PC`, `LR`, `R12`, `R3`, `R2`, `R1`, and `R0` onto the stack when a thread is interrupted. AKOS then saves `R4` to `R11` in the PendSV handler, so the full thread stack contains both the hardware-saved state and the software-saved state.

The figure below shows the initial stack frame for a thread. `xPSR` is at the top of the frame, followed by the return address and general-purpose registers. The lower part of the frame holds `R11` down to `R4`, which the context-switch code restores when the thread runs again.

![Thread 1 stack](06_thread_stack.png)

Now consider the CPU processing thread 1. Let's see how it gives up thread 1 to get ready for a context switch.

![CPU saves its state in thread 1 stack](06_switch_from_thread_1.png)

- **(1)**: The PendSV handler reads the current process stack pointer from `PSP`. It is now pointing to the top of thread 1's stack.
- **(2)**: When an interrupt occurs, the CPU automatically saves `xPSR`, `PC`, `LR`, `R12`, `R3`, `R2`, `R1`, and `R0` onto that stack from the current `PSP`.
- **(3)**: PSP decreases.
- **(4)**: AKOS continues by saving `R4` to `R11`.
- **(5)**: `PSP` decreases. At this moment, all ARM Cortex-M3 registers are completely saved in thread 1's stack.

Now the CPU wants to switch to thread 2, or start the very first thread. Let's see how it gets the context ready to execute thread 2.

![CPU switches to thread 2](06_switch_to_thread_2.png)

- **(1)**: The PendSV handler copies the top of thread 2's stack into `PSP`. With that, `PSP` is now pointing to the top of thread 2's stack.
- **(2)**: AKOS loads the `R4` to `R11` values from the top of thread 2's stack into the CPU.
- **(3)**: `PSP` increases its address.
- **(4)**: Then, on exception return, the CPU automatically restores `xPSR`, `PC`, `LR`, `R12`, `R3`, `R2`, `R1`, and `R0` from the current `PSP` address.
- **(5)**: `PSP` decreases. At this moment, the full context of thread 2 is completely loaded into the ARM Cortex-M3.

The full context-switching process from thread 1 to thread 2 looks like this:

![Process switching from thread 1 to thread 2](06_context_sw.png)

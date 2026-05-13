# Threads management

The work is easier to manage when it is split into clean tasks or threads.
Each thread takes responsibility for one part of the problem.

In a bare-metal project, the main function often looks like this:

```C
int main(void)
{
    while (1)
    {
        // Do job
    }
}
```

In AKOS, a thread entry function can look like this:

```C
void thread_A(void *p_arg)
{
    while (1)
    {
        // Do job
    }
}
```

Do not think that `thread_A` is a thread object. It is only the function that
defines what the thread does. To create a thread statically in AKOS, use the
macro below:

```C
#define AKOS_THREAD_DEFINE(_name, _id, _entry, _arg, _prio, _queue_size, _stack_size) \
  const thread_t _name __attribute__((used, section("task_desc"))) = {                \
      .id = (thread_id_t)(_id),                                                       \
      .pf_thread = (thread_func_t)(_entry),                                           \
      .p_arg = (void *)(_arg),                                                        \
      .prio = (uint8_t)(_prio),                                                       \
      .queue_size = (size_t)(_queue_size),                                            \
      .stack_size = (size_t)(_stack_size),                                            \
  }
```

The `thread_t` object created by this macro is a static descriptor, not the
runtime thread object itself. During initialization, AKOS uses this descriptor
to allocate and configure the actual *Task Control Block (TCB)* for the thread.

## Thread Control Block

The TCB is the runtime data structure that AKOS uses to manage a thread. It is
opaque to application code, but the scheduler depends on it for fast access to
the thread's state.

At a high level, the TCB stores:

- the current stack pointer, so the kernel can save and restore context
- the thread state, such as running, ready, delayed, or suspended
- the list node used to place the thread into ready, delay, or suspended lists
- the event-list node used when the thread waits for a message
- the stack base and stack limit, which help with initialization and overflow checks
- the message queue owned by the thread
- the thread ID and priority copied from the static descriptor

In the code, the TCB also keeps `stk_ptr` as the first field. That layout is
important because the port code can access the saved stack pointer directly
during a context switch.

Why does a thread need these parameters?

- `name`: a plain-text name for the thread
- `id`: an integer identifier for the thread
- `pf_thread`: a pointer to the function that defines the thread's job
- `p_arg`: a pointer to the argument passed to the thread function
- `queue_size`: the size of the message queue used for inter-thread communication
- `stack_size`: the amount of stack space reserved for the thread

Those parameter descriptions make more sense when you understand the TCB. When
calling `AKOS_THREAD_DEFINE`, AKOS invokes `akos_memory_malloc` to allocate
memory for the stack. Then it invokes `akos_memory_malloc` one more time to
allocate memory for the TCB.

![Thread initialization](05_thread_init.png)

When many threads are created, the memory will look like this:

![Many threads in memory](05_threads_in_mem.png)

## Thread States

In AKOS, a thread can be in one of these states:

- `THREAD_STATE_RUNNING`: the thread is currently executing
- `THREAD_STATE_READY`: the thread is ready to run and waiting for CPU time
- `THREAD_STATE_DELAYED`: the thread is blocked until its delay expires
- `THREAD_STATE_SUSPENDED`: the thread is suspended indefinitely
- `THREAD_STATE_SUSPENDED_ON_MSG`: the thread is waiting for a message
- `THREAD_STATE_DELAYED_ON_MSG`: the thread is waiting for a message with a
  timeout

The exact thread lifecycle is shown below:

![Thread states](05_thread_states.png)

## Thread stack

Every thread requires its own stack buffer so the CPU can save and restore the
thread context. In AKOS, stack size is specified in 32-bit words, because the
port builds the initial stack frame using 32-bit registers.

When you define a thread stack, make sure it is large enough for:

- the thread's own local variables and function calls
- the context that the kernel saves during a switch
- any extra nesting caused by helper functions or interrupts

AKOS allocates the stack buffer first, then initializes the initial stack frame
from the top of that buffer.

One way to estimate the size of stack (ref from [micriumOS-III](https://micrium.atlassian.net/wiki/spaces/osiiidoc/pages/131410/Determining+the+Size+of+a+Stack)) is manually calculate the sum of:

- all the memory required by all function call nesting (1 pointer each function call for the return address).
- all the memory required by all the arguments passed in those function calls.
- storage for a full CPU context (depends on the CPU).
- whatever stack space is needed by ISRs.
- the sum then be multiplied by some safety factor, possibly 1.5 to 2.0.

### Detecting thread's stack overflow

#### 1. Hardware approach - using MMU or MPU 

The most elegant way is using Memory Management Unit (MMU) or a Memory Protection Unit (MPU) if the CPU support that features. Basically, reserve a guard region around the stack and mark it as inaccessible. If the thread stack grows into that protected area, the CPU raises a fault immediately, so the kernel can detect the overflow before it corrupts other memory. This is also called `Redzone MPU/MMU`.

#### 2. Software approach - hook in contex switch

This approach also reserves a guard region called `Redzone` and fills that region
with a known pattern. Then, every time context switching occurs and before the
thread is switched in, the kernel checks whether the `Redzone` still contains
the expected values. If the pattern has been changed, it means the stack has
overflowed into the guard region, so the kernel can detect the problem early.

![Redzone detection](05_redzone.png)

## Thread priorities

Thread priorities are integer numbers from `0` to `OS_CFG_PRIO_MAX - 1`. The lowest number means the highest priority, and vice-versa. For example, thread A with priority number 3 has a higher priority than thread B with priority number 7. Threads with the same priority are considered *cooperative threads*, and threads with different priorities are considered *preemptible threads*.

AKOS currently defines static threads, so a thread's priority cannot be changed after it is defined.

AKOS also defines some kernel threads during initialization:

- timer thread
- idle thread with the lowest priority (priority number `OS_CFG_PRIO_MAX - 1`)

![Thread prioritie levels](05_thread_prio.png)

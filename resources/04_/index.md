# Memory management

In RTOS systems, memory is usually limited. When an application uses
`malloc()` and `free()`, it is usually working with a small SRAM pool. Those
functions are part of the standard C library, so the application has less
control over memory behavior, which can sometimes be dangerous. For that
reason, RTOSes often implement their own memory-management module.

AKOS provides an alternative to `malloc()` and `free()` called
`akos_memory_malloc(size_t size)` and `akos_memory_free(void *p_addr)`.
In the future, it may have additional schemes to support many application
requirements. Let’s see how it works.

## First-fit scheme

AKOS first obtains a memory block in SRAM with the size specified in
`config.h`. In AKOS, this area is called `mem_heap`.

At initialization, `mem_heap` is one large block. Each time
`akos_memory_malloc(size)` is called, if enough memory is available,
`mem_heap` is split from one big block into smaller blocks. Keep in mind that
every memory block has one `BLK_HEADER`.

To keep track of memory blocks, the **BASE ADDRESS** of **mem_heap** always has
a `BLK_HEADER`.

![Heap initialization](04_init_mem.png)

Then, consider `akos_memory_malloc(1024)` being called. `mem_heap` becomes like
this:

![Malloc memory layout](04_malloc_mem.png)

Lastly, when `akos_memory_free` is called with the address returned by
`akos_memory_malloc(1024)`, `mem_heap` goes back to its initial state.

# Inter-thread Communication

Inter-thread communication is how AKOS lets one thread send work, data, or
signals to another thread.

In the current kernel, communication is built around message queues. Each
thread owns a queue, and other threads can post either a pure signal or a
signal plus payload. This makes communication explicit, predictable, and easy
to combine with the scheduler.

## Message Model

AKOS uses two message types:

- `MSG_TYPE_PURE`: signal only, no payload buffer
- `MSG_TYPE_DYNAMIC`: signal plus copied payload data

Both message types share the same queue infrastructure. The message object
stores:

- the signal value
- the source thread ID
- the destination thread ID
- the payload size
- the payload pointer for dynamic messages

That design lets a thread react to a signal even when no extra data is needed,
while still supporting copied payloads for commands, status updates, or small
data packets.

## Message Pool

AKOS preallocates message objects in a global pool. The pool is initialized by
`akos_message_init()`, and individual messages are returned to the pool with
`akos_message_free()`.

Using a fixed pool keeps message allocation predictable:

- no general-purpose heap search for message objects
- bounded memory usage
- fast allocation and release

For dynamic messages, AKOS also allocates a payload buffer from the memory
subsystem and copies the payload into that buffer before enqueuing the message.

## Per-thread Queues

Each thread has its own FIFO queue. The queue is initialized when the thread is
created, and its maximum depth comes from the thread descriptor:

- `queue_size` in `AKOS_THREAD_DEFINE(...)`

If a thread does not need messaging, its queue size can be zero. If it expects
communication, the queue should be sized to match the amount of burst traffic
the application can tolerate.

Queue operations are straightforward:

- `akos_message_queue_put_pure(...)` adds a signal-only message
- `akos_message_queue_put_dynamic(...)` adds a copied payload message
- `akos_message_queue_get(...)` removes the next message from the queue
- `akos_message_get_pure_data(...)` reads the signal from a pure message
- `akos_message_get_dynamic_data(...)` returns the payload pointer and size

## Posting A Message

The thread API wraps queue access with scheduler awareness:

- `akos_thread_post_msg_pure(des_thread_id, sig)`
- `akos_thread_post_msg_dynamic(des_thread_id, sig, p_content, msg_size)`

These functions do more than enqueue a message. They also check whether the
destination thread is blocked waiting for a message. If it is, AKOS moves the
thread back to the ready list and may trigger a context switch.

That means message posting can be both communication and synchronization at the
same time.

### Pure Messages

Pure messages are the lightest-weight form of communication.

Use them when:

- the destination only needs a notification
- the signal value is enough to describe the event
- no payload data needs to be copied

Examples include:

- "data ready"
- "button pressed"
- "timeout expired"
- "restart requested"

### Dynamic Messages

Dynamic messages carry a copied payload buffer.

Use them when:

- the receiver needs a small block of data
- the sender should not keep ownership of the source buffer
- the payload is short enough to copy efficiently

Examples include:

- a compact status structure
- a sensor sample
- a command packet
- a short configuration update

Because the payload is copied into the message object, the sender can safely
reuse or release the original buffer after posting.

## Receiving A Message

Threads receive messages with:

```C
msg_t *akos_thread_wait_for_msg(uint32_t time_out);
```

The behavior is:

1. check the queue immediately
2. if a message is present, return it
3. if the queue is empty and `time_out` is nonzero, block the thread
4. if the timeout expires first, return `NULL`

When a thread wakes up, it should inspect the message type before reading the
payload:

```C
msg_t *msg = akos_thread_wait_for_msg(OS_CFG_DELAY_MAX);

if (msg != NULL)
{
    if (msg->type == MSG_TYPE_PURE)
    {
        int32_t sig = akos_message_get_pure_data(msg);
        /* handle signal */
    }
    else
    {
        uint8_t size = 0;
        void *payload = akos_message_get_dynamic_data(msg, &size);
        /* handle payload */
    }

    akos_message_free(msg);
}
```

That ownership model is important: once a message has been consumed, the thread
must return it to the pool with `akos_message_free()`.

## Signals And Ownership

In AKOS, the signal value is the lightweight identifier that tells the
receiver what happened. The payload, if present, carries the associated data.

A good mental model is:

- signal = what happened
- payload = extra details

The source thread keeps ownership of its original data, while the message
object owns the copied payload until the receiver frees the message.

## Practical Patterns

Common communication patterns in AKOS include:

- a producer thread posts a pure signal to wake a consumer
- a producer thread posts a dynamic message with a copied buffer
- a consumer blocks on `akos_thread_wait_for_msg()` until work arrives
- the consumer frees each message after handling it

This works especially well for event-driven embedded code because it keeps the
thread logic simple and avoids polling loops.

## Related Topics

- [Inter-thread Synchronization](../10_/index.md)
- [Threads management](../05_/index.md)
- [Scheduler](../06_/index.md)

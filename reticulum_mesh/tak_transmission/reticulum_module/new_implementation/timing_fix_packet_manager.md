# PacketManager Timing Fix

## Current Problem

Upon analysis of packet transmission logs, we've identified a critical issue with how packets are being sent to multiple nodes in our network. The logs show a pattern where packets are consistently being sent to takNode3 first, and then "retried" to takNode2 - when in fact, they were never actually sent to takNode2 in the first place.

### Example from the logs:

```
16:07:00,798 - Sending packet packet_1746216420671.zst to node takNode3
16:07:05,606 - Packet packet_1746216420671.zst delivered to takNode3 (RTT: 4.8 seconds)
16:07:12,820 - Retrying packet_1746216420671.zst to takNode2 (retry #1)
16:07:15,947 - Packet packet_1746216420671.zst delivered to takNode2 (RTT: 3.115 seconds)
```

Another example:

```
16:07:20,841 - Sending packet packet_1746216440786.zst to node takNode3
16:07:26,606 - Packet packet_1746216440786.zst delivered to takNode3 (RTT: 5.762 seconds)
16:07:32,865 - Retrying packet_1746216440786.zst to takNode2 (retry #1)
16:07:36,689 - Packet packet_1746216440786.zst delivered to takNode2 (RTT: 3.817 seconds)
```

## Root Cause

The issue stems from how the `send_to_node` function and the transmission timing constraints interact:

1. In the `process_outgoing` function, we loop through all valid nodes to send a packet.
2. For the first node (takNode3), the transmission proceeds normally.
3. The `send_to_node` function updates `self.last_send_time` after a successful send.
4. When we immediately try to send to the second node (takNode2), the following code in `send_to_node` prevents the transmission:

```python
# Check if enough time has passed since last radio send
current_time = time.time()
if current_time - self.last_send_time < config.SEND_SPACING_DELAY:
    return False  # Too soon for radio
```

5. The function silently returns `False` when the timing constraint is hit, without any error or logging.
6. Later, the `process_retries` function picks up takNode2 as a node that should have received the packet but didn't, and logs it as a "retry" - when in fact, it's actually the first attempted send to that node.

## Solution

The solution is to modify the `process_outgoing` function to properly handle timing constraints by waiting the required amount of time between transmissions, rather than skipping sends. This ensures all nodes get a proper initial send attempt.

### Detailed Changes Required:

1. In the `process_outgoing` function, add a pause before each `send_to_node` call:
   - Calculate wait time as `config.SEND_SPACING_DELAY - (current_time - self.last_send_time)`
   - If wait_time > 0, call `time.sleep(wait_time)` to respect the timing constraint
   - Log this pause for debugging purposes

2. Keep the original timing check in `send_to_node` as a safety measure (redundant with our fix, but a good safeguard)

### Impact Analysis:

- **Improved Reliability**: All nodes will receive a proper initial send attempt
- **Accurate Logging**: "Retry" logs will truly represent resends, not first attempts
- **Preserved Rate Limiting**: Radio timing constraints will still be respected
- **Minimal Code Changes**: Only modifying the sequential send loop, not changing overall architecture
- **No Impact on Receipt Handling**: Packet receipts and proofs will still be processed during sleep periods, as they use separate threading/callbacks

## Implementation Notes

1. The `time.sleep()` call only affects the sending thread - packet receipts, proofs, and incoming packets will still be processed during this time
2. The changes should be made in the `for node in valid_nodes:` loop in `process_outgoing`
3. Consider adding additional logging to help track the timing pattern for future debugging
4. No changes are needed to the retry mechanism itself, only to the initial send process

## Expected Results

After implementing this fix:
- All nodes should receive initial sends properly
- "Retrying" log messages should only appear for genuine retries
- The delivery rate should improve since we're properly sending to all nodes
- Packet RTT measurements will be more accurate, as they'll be based on actual first-attempt delivery times

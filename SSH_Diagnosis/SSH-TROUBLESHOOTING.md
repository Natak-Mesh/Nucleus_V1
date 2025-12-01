# SSH Connection Troubleshooting Guide

This guide helps you diagnose and fix SSH connectivity issues to your Nucleus mesh nodes without rebooting your computer or power cycling the node.

## The Problem

After disconnecting from a node (closing VSCode or powering off the node), reconnecting fails with timeout errors. Previously, you had to:
1. Clear SSH known_hosts
2. Power cycle the node
3. Reboot your computer

This is unnecessary and time-consuming.

## The Solution

Two scripts are provided to diagnose and fix the issue:

### 1. `diagnose-ssh-issue.sh` - Diagnostic Tool

**When to use:** When you cannot connect to the node and want to understand why.

**Usage:**
```bash
./diagnose-ssh-issue.sh <node_ip> [username]
```

**Example:**
```bash
./diagnose-ssh-issue.sh 192.168.1.100 natak
```

**What it checks:**
- Network connectivity (ping)
- ARP table state (MAC address mapping)
- SSH port status (is port 22 open?)
- Network interface status (eth0)
- VSCode SSH cache
- Verbose SSH connection attempt

**Output:** A detailed report showing what's broken and recommendations.

### 2. `reset-network-state.sh` - Quick Fix Tool

**When to use:** When you cannot connect and want to try fixing it without rebooting.

**Usage:**
```bash
./reset-network-state.sh <node_ip>
```

**Example:**
```bash
./reset-network-state.sh 192.168.1.100
```

**What it does:**
- Clears ARP cache entry for the node
- Removes stale SSH control sockets
- Kills hanging SSH processes
- Clears VSCode SSH cache
- Refreshes eth0 network interface
- Forces new ARP resolution
- Tests SSH connectivity

**Note:** This script uses `sudo` for some operations, so you may be prompted for your password.

## Complete Workflow

Here's the step-by-step process to follow when you cannot connect:

### 1. Power on the node
Connect power/battery to the node.

### 2. Wait for boot
Wait 30-60 seconds for the node to fully boot. The node needs time to:
- Start the operating system
- Configure network interfaces
- Start the SSH service

### 3. Try connecting
```bash
ssh natak@<node_ip>
```
or open VSCode Remote SSH.

### 4. If connection fails, diagnose
```bash
./diagnose-ssh-issue.sh <node_ip>
```

Read the output to understand what's failing.

### 5. Try the quick fix
```bash
./reset-network-state.sh <node_ip>
```

### 6. Wait and retry
Wait 10-15 seconds for the network state to stabilize, then try connecting again:
```bash
ssh natak@<node_ip>
```

### 7. If still broken
- Run diagnostics again to see if anything changed
- Check if the node is actually booting properly (look for LED activity)
- Try waiting longer (some nodes take 2-3 minutes to fully boot)
- Consider that the node itself may have an issue (SSH service not starting)

## Common Issues and Solutions

### Issue: "Node does NOT respond to ping"
**Cause:** Node is off, cable unplugged, or wrong IP address.
**Solution:** 
- Check power/battery connection
- Check ethernet cable
- Verify IP address
- Wait longer (node may still be booting)

### Issue: "SSH port 22 is CLOSED"
**Cause:** SSH service hasn't started yet or failed to start.
**Solution:**
- Wait 30-60 more seconds
- Power cycle the node if it's been more than 2 minutes

### Issue: "Stale ARP cache"
**Cause:** Your laptop has old MAC address mapping for the IP.
**Solution:**
- Run `./reset-network-state.sh <node_ip>`
- This is the most common issue after power cycling

### Issue: "VSCode connection fails but SSH works"
**Cause:** VSCode has cached connection state.
**Solution:**
- Run `./reset-network-state.sh <node_ip>` (clears VSCode cache)
- Or manually: Close VSCode, run the reset script, reopen VSCode

## First Time Setup

Before using these scripts, make them executable:

```bash
chmod +x diagnose-ssh-issue.sh
chmod +x reset-network-state.sh
```

### Optional: Install recommended tools

For full diagnostic capabilities, install netcat:
```bash
sudo apt install netcat-openbsd
```

## Tips for Preventing Issues

1. **Don't clear known_hosts** - It's not necessary and doesn't fix the actual problem
2. **Use the reset script first** - Before power cycling or rebooting
3. **Wait for boot** - Give the node 30-60 seconds after power-on
4. **Keep notes** - If a specific pattern causes issues, note it for debugging

## Understanding What's Happening

When you power off a node abruptly:
- Your laptop's ARP cache still has the old MAC → IP mapping
- SSH control sockets may remain open
- Network state becomes inconsistent

When you power the node back on:
- It needs time to boot and start services
- Once booted, it requests a DHCP lease
- Your DHCP server assigns an IP (usually the same one)
- But your laptop's network stack may have stale state

The reset script clears this stale state without requiring full system reboots.

## Debugging Deep Issues

If the scripts don't help, check these on your laptop:

1. **DHCP server status:**
```bash
sudo systemctl status isc-dhcp-server
# or
sudo systemctl status dnsmasq
```

2. **Network interface status:**
```bash
ip addr show eth0
ip link show eth0
```

3. **ARP table:**
```bash
arp -a
```

4. **SSH verbose output:**
```bash
ssh -vvv natak@<node_ip>
```

5. **Network logs:**
```bash
journalctl -u NetworkManager -n 100
```

## Need More Help?

If you're still having issues after trying these scripts:

1. Run both scripts and save the output:
```bash
./diagnose-ssh-issue.sh <node_ip> 2>&1 | tee diagnosis.log
./reset-network-state.sh <node_ip> 2>&1 | tee reset.log
```

2. Check if the issue is reproducible with different nodes
3. Try connecting from a different computer to isolate laptop vs node issues
4. Consider if recent OS updates may have changed network behavior

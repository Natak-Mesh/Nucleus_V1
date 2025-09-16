# Using NomadNet Pages in MANET Scenarios

NomadNet pages act as **persistent, signed bulletin boards** within a Reticulum network. Unlike chat (which is ephemeral), pages are **cryptographically tied to node identities**, cached locally, and **propagate opportunistically** across nodes using Reticulum’s store-and-forward mechanics.

This makes them ideal for MANET deployments in harsh or disconnected environments.

---

## 🔹 How NomadNet Pages Work
1. A node publishes a page → text, metadata, signature.  
2. Reticulum announces availability → peers can fetch and cache it.  
3. Cached pages are **re-shared** when peers encounter other nodes.  
4. Updates are new signed versions → peers refresh automatically.  

Result: each node’s page(s) spread organically across the mesh, creating a **distributed bulletin board** without central servers.

---

## 1️⃣ Search & Rescue (SAR)

**Examples of Pages per Node:**
- **Team Status Page** → personnel count, last check-in time, current grid.  
- **Tasking Page** → search sectors, waypoints, comms plan.  
- **Resource Page** → medical supplies, casualty reports, battery levels.  

**Benefits:**
- Persistent status information not buried in chat.  
- Offline caches mean updates still propagate later.  
- Reduces chat congestion during operations.  

---

## 2️⃣ Protest / Civil Unrest

**Examples of Pages per Node:**
- **Safe Routes Page** → streets open, police movements, blocked areas.  
- **Legal Aid Page** → hotline numbers, bail fund contacts.  
- **Medical Help Page** → volunteer medics, first-aid stations.  
- **Announcements Page** → rally points, schedule changes.  

**Benefits:**
- Protesters joining late still get the latest bulletins.  
- Works fully offline → spreads peer-to-peer.  
- Pages persist so critical info (safe exits, legal support) isn’t lost in chat spam.  

---

## 3️⃣ Community Isolated Internet

**Examples of Pages per Node:**
- **Local News Page** → events, announcements, weather bulletins.  
- **Resource Pages** → ration schedules, water points.  
- **Education Pages** → offline guides, study material.  
- **Marketplace Pages** → trade board for goods and services.  

**Benefits:**
- Creates a distributed **intranet** without internet.  
- Content survives outages and syncs opportunistically.  
- Builds a resilient knowledge-sharing system.  

---

## 4️⃣ Airsoft / LARPing / Gaming

**Examples of Pages per Node:**
- **Faction Briefing Pages** → mission objectives, intel packets.  
- **Rules / Handbook Page** → gameplay rules, comms protocols.  
- **Scoreboard / Updates Page** → progress, captured objectives.  
- **In-Character Pages** → propaganda, lore, secret codes.  

**Benefits:**
- Pages act as immersive “intel drops.”  
- Players still get updates even with intermittent connectivity.  
- Game masters can seed story or mission info that spreads organically.  

---

## ⚡ Common Thread
- **Pages = persistent, signed bulletins** (like distributed flyers).  
- **Chat = ephemeral real-time comms** (like radio traffic).  
- Together, they provide both **live coordination** and a **resilient knowledge base** in MANET deployments.

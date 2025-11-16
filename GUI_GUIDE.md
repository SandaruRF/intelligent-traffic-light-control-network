# 🎨 GUI Visualization Guide

## Overview

The system now includes a **beautiful real-time GUI** using Pygame that shows:
- ✅ Live traffic light states (red/green)
- ✅ Animated vehicle queues
- ✅ Congestion heatmap (color-coded intersections)
- ✅ Real-time system metrics
- ✅ Visual flow of traffic

**Terminal output remains unchanged** - GUI runs alongside in a separate window!

---

## Installation

### 1. Install Pygame

```powershell
# Activate your virtual environment first
.\venv\Scripts\Activate.ps1

# Install pygame
pip install pygame

# Or install all requirements
pip install -r requirements.txt
```

### 2. Run the System

```powershell
python -m src.main --scenario normal --duration 60
```

**A GUI window will automatically open!** 🎉

---

## GUI Features

### 🚦 Traffic Light Visualization

**Intersections:**
- 5 intersections in star topology
- **Center** (hub) connected to North, South, East, West

**Traffic Lights:**
- 🟢 **Green circle** = Direction has green light
- 🔴 **Red circle** = Direction stopped
- 4 lights per intersection (N, S, E, W)

**Congestion Colors:**
- 🟩 **Dark Green** = Low congestion (0-5 vehicles)
- 🟨 **Yellow** = Medium (6-10 vehicles)
- 🟧 **Orange** = High (11-20 vehicles)
- 🟥 **Dark Red** = Critical (>20 vehicles)

### 🚗 Vehicle Animation

- **Blue squares** = Vehicles waiting in queue
- **Animated movement** = Visual flow
- **Queue bars** = Length indicators (yellow/orange/red)
- **Numbers** = Exact queue count per direction

### 📊 Metrics Panel (Left Side)

Real-time metrics:
- **Total Waiting:** Sum of all vehicles in queues
- **Avg Queue:** Average queue per intersection
- **Throughput:** Vehicles processed per minute
- **Total Processed:** Cumulative count
- **Status:** System operational state
- **Active Agents:** Number of connected agents (0-5)

### 📖 Legend (Right Side)

Explains color coding:
- Traffic light colors
- Congestion levels
- Visual indicators

---

## What You'll See

### Startup

```
🚦 Intelligent Traffic Light Control Network
============================================================

📡 Initializing XMPP connection and agents...

🎨 Starting GUI visualization...
  ✅ GUI window opened                    <-- NEW!

  Starting Coordinator at coordinator@localhost...
  ...
```

### During Execution

**Terminal:**
```
[TL_CENTER] Cycle 5: Phase=NS-Green Green=7.5s | Queues[N:2 S:3 E:1 W:1] Total=7
[Coordinator] 📊 SYSTEM METRICS REPORT
Total Vehicles Waiting: 25
System Throughput: 8.5 vehicles/min 📈
```

**GUI Window:**
- Intersections change color as congestion builds
- Traffic lights switch red ↔ green
- Vehicles animate in queues
- Metrics update every second

---

## Scenarios to Try

### 1. Normal Traffic (Steady Flow)
```powershell
python -m src.main --scenario normal --duration 60
```
**Watch:** Queues stay low (green), smooth traffic light transitions

### 2. Rush Hour (Heavy Congestion)
```powershell
python -m src.main --scenario rush_hour --duration 120
```
**Watch:** Intersections turn orange/red, longer green times, system adapting

### 3. Directional Bias (NS Heavy)
```powershell
python -m src.main --scenario directional --duration 90
```
**Watch:** North/South directions get more vehicles, system balances

### 4. Butterfly Effect
```powershell
python -m src.main --scenario butterfly --duration 60
```
**Watch:** Small perturbation cascades through network

---

## GUI Controls

- **Window:** 1400 x 900 pixels
- **Close:** Click X button or Ctrl+C in terminal
- **No mouse interaction** - fully automated visualization

---

## Troubleshooting

### Issue: GUI window doesn't open

**Solution 1: Install Pygame**
```powershell
pip install pygame
```

**Solution 2: Check for errors**
```powershell
# If pygame isn't installed, system will run without GUI (terminal only)
# Look for: "🎨 Starting GUI visualization..."
```

### Issue: GUI window is black/frozen

**Cause:** System not started yet  
**Solution:** Wait for agents to connect (~5 seconds)

### Issue: "Import pygame could not be resolved"

**Cause:** Pygame not installed  
**Solution:**
```powershell
.\venv\Scripts\Activate.ps1
pip install pygame
```

---

## Technical Details

### Architecture

```
Main Thread                     GUI Thread
     |                               |
     |--- Start GUI ----------------->|
     |                               |
     |--- Initialize Agents          |
     |                               |
     |--- Coordinator Updates ------>| Update GUI
     |      (every 3s)               | (30 FPS)
     |                               |
     |--- Metrics Updates ---------->| Update Metrics Panel
     |      (every 10s)              |
     |                               |
     |--- Shutdown ---------------->| Stop GUI
```

### File Structure

```
src/
├── visualization/
│   ├── gui_simulator.py      # NEW: Pygame GUI
│   ├── dashboard.py           # Existing matplotlib
│   └── metrics.py             # Metrics tracking
├── agents/
│   ├── coordinator_agent.py   # Updated: GUI integration
│   └── traffic_light_agent.py
└── main.py                    # Updated: GUI startup/shutdown
```

### Performance

- **FPS:** 30 frames per second
- **Thread:** Separate daemon thread (non-blocking)
- **Memory:** ~50MB additional (Pygame window)
- **CPU:** Minimal impact (<5% on modern systems)

---

## Comparison: Before vs After

### Before (Terminal Only)
```
[TL_CENTER] Cycle 5: Phase=NS-Green Green=7.5s | Queues[N:2 S:3 E:1 W:1] Total=7
[TL_SOUTH] ⚠️  High queue: 15 vehicles waiting
[Coordinator] Total Vehicles Waiting: 42
```
**Problem:** Hard to visualize traffic flow and congestion patterns

### After (Terminal + GUI)
```
Terminal Output (unchanged)     +    Visual GUI Window
[TL_CENTER] Cycle 5...               ┌──────────────────────┐
[TL_SOUTH] ⚠️  High queue...          │   🚦  🚦  🚦  🚦    │
[Coordinator] Total: 42              │  🟢  🔴  🟩  🟧    │
                                      │   🚗🚗  🚗🚗🚗      │
                                      │  Metrics: 42 wait  │
                                      └──────────────────────┘
```
**Benefit:** See traffic flow, congestion, and system behavior instantly!

---

## For Your Demo/Presentation

### What to Highlight

1. **Real-time Visualization:**
   - "Here you can see the traffic light network in real-time"
   - Point to intersections changing color

2. **Emergent Behavior:**
   - "Watch how congestion builds at one intersection..."
   - "...and the system adapts without central control"

3. **Self-Organization:**
   - "Each agent makes local decisions"
   - "But the system optimizes globally"

4. **Metrics Tracking:**
   - "Throughput is increasing"
   - "Queues are being processed"

### Screenshots to Capture

- System startup (all green)
- Rush hour congestion (red intersections)
- Adaptive response (green times adjusting)
- Metrics panel showing improvement

---

## Next Steps

1. **Install Pygame:**
   ```powershell
   pip install pygame
   ```

2. **Run with GUI:**
   ```powershell
   python -m src.main --scenario normal --duration 60
   ```

3. **Watch the Magic! ✨**
   - Terminal shows detailed logs
   - GUI shows visual simulation
   - Best of both worlds!

---

**Enjoy the visual simulation!** 🚦🎨🚗

*The GUI enhances understanding while keeping all terminal output for debugging and analysis.*

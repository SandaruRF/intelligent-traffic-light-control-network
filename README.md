# Intelligent Traffic Light Control Network

A **Multi-Agent System (MAS)** using SPADE framework that demonstrates intelligent traffic light coordination through self-organization, emergent behavior, and distributed control.

**Framework**: SPADE (Smart Python Agent Development Environment)  
**Language**: Python 3.8+

---

## 🎯 Project Overview

This project implements a distributed traffic light control system where each intersection operates autonomously while coordinating with neighbors to optimize overall traffic flow. The system demonstrates key Multi-Agent Systems concepts including:

- **Communication**: FIPA-compliant peer-to-peer messaging
- **Coordination**: Distributed optimization without central control
- **Negotiation**: Adaptive signal timing through information exchange
- **Emergent Behavior**: Global optimization emerges from local decisions
- **Self-Organization**: System adapts without external intervention

### Key Features

✅ **5 Autonomous Traffic Light Agents** (Star topology)  
✅ **1 Coordinator Agent** (Monitoring only, no control)  
✅ **FIPA ACL Compliant** messaging (Agent Communication Language)  
✅ **Stochastic Traffic Simulation** (Poisson-like arrivals)  
✅ **Real-time Visualization** Dashboard  
✅ **Multiple Demo Scenarios** (Rush hour, Butterfly effect, etc.)  
✅ **Performance Metrics** Tracking and analysis

---

## 🏗️ System Architecture

### Agent Types

#### 1. TrafficLightAgent (5 instances)
- **Purpose**: Autonomous intersection control
- **Behaviors**:
  - `SensorBehaviour`: Simulates traffic sensors (1s period)
  - `SignalControlBehaviour`: Adaptive signal timing (2s period)
  - `CoordinationBehaviour`: Send status to neighbors (2s period)
  - `MessageHandlerBehaviour`: Receive neighbor updates (continuous)
  - `StateBroadcastBehaviour`: Report to coordinator (3s period)

#### 2. CoordinatorAgent (1 instance)
- **Purpose**: System monitoring and metrics collection
- **Role**: Observes but does NOT control (maintains autonomy)
- **Behaviors**:
  - `MonitorBehaviour`: Collect agent status updates
  - `MetricsReportBehaviour`: Calculate system-wide metrics (10s)
  - `HealthCheckBehaviour`: Detect anomalies (15s)

### Network Topology

```
        TL-North
           |
TL-West -- TL-Center -- TL-East
           |
        TL-South
```

**Star topology**: Center intersection coordinates with all cardinal directions.

---

## 🚀 Installation & Setup

### Prerequisites

1. **Python 3.8 or higher**
2. **Openfire XMPP Server** (local installation)
   - Windows: Download from [igniterealtime.org](https://www.igniterealtime.org/downloads/)
   - Ubuntu/Linux: Download from igniterealtime.org or use Docker
   - macOS: Download DMG from igniterealtime.org or use Docker

### Step 1: Clone Repository

```bash
git clone https://github.com/SandaruRF/intelligent-traffic-light-control-network.git
cd intelligent-traffic-light-control-network
```

### Step 2: Install Python Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Windows CMD:
venv\Scripts\activate.bat
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Configure Openfire XMPP Server

#### Option A: Quick Setup (Localhost)

1. **Install and Start Openfire**:
   - Download from https://www.igniterealtime.org/downloads/
   - Run installer as Administrator (Windows)
   - Service starts automatically

2. **Initial Setup**:
   - Open browser: http://localhost:9090
   - Follow setup wizard:
     * Domain: `localhost`
     * Database: Embedded Database
     * Create admin account
   
3. **Configure Security**:
   - Login to admin console
   - Go to: Server → Server Settings → Security Settings
   - Set "Client Connection Security" to "Available"
   - Click "Save Settings"

4. **Create XMPP Accounts**:
   - Go to: Users/Groups → Create New User
   - Create these 6 accounts:
     * coordinator / coordinator123
     * tl_center / traffic123
     * tl_north / traffic123
     * tl_south / traffic123
     * tl_east / traffic123
     * tl_west / traffic123

**Or run setup script** (opens admin console for manual account creation):
   ```powershell
   .\\setup_openfire.ps1
   ```

**Detailed guide**: See [OPENFIRE_SETUP.md](OPENFIRE_SETUP.md)

#### Option B: Custom Configuration

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your XMPP server details:
   ```env
   XMPP_SERVER=localhost
   XMPP_PORT=5222
   
   COORDINATOR_JID=coordinator@localhost
   COORDINATOR_PASSWORD=coordinator123
   # ... (edit other credentials as needed)
   ```

---

## 🎮 Usage

### Quick Start - Demo Mode

```bash
# Run 60-second demo with normal traffic
python -m src.main

# Run 2-minute demo with rush hour traffic
python -m src.main --duration 120 --scenario rush_hour

# Run butterfly effect demonstration
python -m src.main --scenario butterfly
```

### Interactive Mode

```bash
python -m src.main --mode interactive
```

**Interactive Menu Options**:
1. Change traffic scenario
2. Trigger butterfly effect (add 2 vehicles)
3. Simulate directional congestion
4. Show system status
5. Export data to JSON
9. Quit

### Demo Scenarios

#### 1. Normal Traffic
```bash
python -m src.main --scenario normal --duration 60
```
Moderate traffic flow with balanced arrivals/departures.

#### 2. Rush Hour
```bash
python -m src.main --scenario rush_hour --duration 120
```
Heavy traffic in all directions. System demonstrates emergent optimization.

#### 3. Butterfly Effect
```bash
python -m src.main --scenario butterfly
```
Adds 2 vehicles at one intersection, demonstrates how small changes cascade through the network.

#### 4. Directional Congestion
```bash
python -m src.main --scenario directional --duration 90
```
Heavy North-South traffic. System self-organizes to allocate more green time to congested directions.

---

## 📊 Understanding the Output

### Console Output

```
🚦 Intelligent Traffic Light Control Network
============================================================

📡 Initializing XMPP connection and agents...

  Starting Coordinator at coordinator@localhost...
  ✅ Coordinator ready

  Starting Traffic Light Agents...
    TL_CENTER at tl_center@localhost...
    TL_NORTH at tl_north@localhost...
    ...
  ✅ 5 traffic lights active

🟢 System fully operational!

[TL_CENTER] Cycle 1: Phase=NS-Green Green=5.0s | Queues[N:3 S:2 E:4 W:1] Total=10
[TL_NORTH] 📤 Sent coordination to 1 neighbors (Total queue: 7)
[Coordinator] 📊 TL_CENTER: Queue=10 Phase=NS-Green Cycle=1
```

### Metrics Reports

Every 10 seconds, the Coordinator prints system metrics:

```
============================================================
📈 SYSTEM METRICS REPORT
============================================================
Active Intersections: 5
Total Vehicles Waiting: 32
Average Queue/Intersection: 6.4
System Throughput: 8.45 vehicles/min
Total Processed: 145
============================================================
```

---

## 🧠 Core Algorithm Explained

### Self-Organizing Green Time Calculation

Each traffic light autonomously calculates its green time using this algorithm:

```python
# 1. Calculate my traffic pressure (normalized queue length)
if current_phase == NS_GREEN:
    my_pressure = (queue_north + queue_south) / MAX_QUEUE
else:
    my_pressure = (queue_east + queue_west) / MAX_QUEUE

# 2. Get average neighbor pressure
avg_neighbor_pressure = mean(neighbor_queues) / MAX_QUEUE

# 3. Calculate pressure difference
pressure_diff = my_pressure - avg_neighbor_pressure

# 4. Adjust green time
adjustment = pressure_diff * ADJUSTMENT_FACTOR  # ADJUSTMENT_FACTOR = 3
new_green_time = BASE_GREEN_TIME + adjustment

# 5. Enforce limits (2-10 seconds)
new_green_time = clamp(new_green_time, MIN_GREEN=2, MAX_GREEN=10)
```

**Why this creates emergent optimization**:
- If MY queue > NEIGHBOR queue → I increase MY green time
- If MY queue < NEIGHBOR queue → I decrease MY green time
- **Result**: Traffic spreads evenly WITHOUT any agent knowing "global optimization"
- **Emergent Property**: System-wide efficient traffic flow

---

## 📁 Project Structure

```
intelligent-traffic-light-control-network/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── .gitignore                   # Git ignore rules
├── .env.example                 # Environment template
├── src/
│   ├── __init__.py
│   ├── settings.py              # Configuration & topology
│   ├── main.py                  # Main entry point
│   ├── models/
│   │   ├── __init__.py
│   │   ├── traffic_state.py     # TrafficPhase, TrafficLightState
│   │   └── queue_simulator.py   # Stochastic simulation
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_agent.py        # Base agent with FIPA
│   │   ├── traffic_light_agent.py  # Main agent with behaviors
│   │   └── coordinator_agent.py # Monitoring agent
│   └── visualization/
│       ├── __init__.py
│       ├── dashboard.py         # Real-time matplotlib dashboard
│       └── metrics.py           # Performance tracking
└── tests/
    └── test_traffic_logic.py    # Unit tests
```

---

## 🧪 Running Tests

```bash
# Run all unit tests
python -m unittest discover tests

# Run specific test file
python -m unittest tests.test_traffic_logic

# Run with verbose output
python -m unittest tests.test_traffic_logic -v
```

---

## 🔧 Configuration

### Key Parameters (in `src/settings.py`)

```python
# Signal timing constraints (seconds)
BASE_GREEN_TIME = 5.0    # Base green light duration
MIN_GREEN_TIME = 2.0     # Minimum green time
MAX_GREEN_TIME = 10.0    # Maximum green time
ADJUSTMENT_FACTOR = 3.0  # Pressure adjustment sensitivity

# Traffic simulation
ARRIVAL_RATE = 0.3       # Probability of vehicle arrival per second
DEPARTURE_RATE = 0.4     # Probability of departure when green

# Behavior update periods (seconds)
SENSOR_PERIOD = 1.0      # Sensor check frequency
CONTROL_PERIOD = 2.0     # Signal control frequency
COORDINATION_PERIOD = 2.0  # Message sending frequency
```

### Customizing Network Topology

Edit `INTERSECTIONS` dictionary in `src/settings.py`:

```python
INTERSECTIONS = {
    "TL_CENTER": {
        "jid": "tl_center@localhost",
        "password": "center123",
        "neighbors": ["TL_NORTH", "TL_SOUTH", "TL_EAST", "TL_WEST"],
        "position": (0, 0)
    },
    # Add more intersections...
}
```

---

## 📈 Performance Metrics

The system tracks:

1. **Average Queue Length**: Mean vehicles waiting across all intersections
2. **Peak Queue**: Maximum queue observed
3. **System Throughput**: Vehicles processed per minute
4. **Total Delay**: Vehicle-minutes of waiting time
5. **Phase Switches**: Number of signal changes

### Exporting Data

```bash
# In interactive mode, select option 5
# Or programmatically:
python -m src.main --mode interactive
> 5 (Export data)
```

Output: `traffic_data_YYYYMMDD_HHMMSS.json`

---

## 🎓 Course Alignment

### Essential MAS Features ✅

- [x] **Communication**: FIPA ACL peer-to-peer messages
- [x] **Coordination**: Request-Resource-Message architecture
- [x] **Negotiation**: Green time negotiation through exchange

### Agent Characteristics ✅

- [x] **Situatedness**: Each agent bound to specific intersection
- [x] **Autonomy**: Independent decision-making
- [x] **Reactivity**: Responds to queue changes
- [x] **Adaptivity**: Adjusts timing dynamically
- [x] **Sociability**: Coordinates with neighbors

### Complex Systems Concepts ✅

- [x] **Emergent Behavior**: Global optimization emerges from local rules
- [x] **Self-Organization**: No central controller
- [x] **Butterfly Effect**: Small changes cascade through network
- [x] **Distributed**: Independent agents
- [x] **Dynamic**: Traffic patterns change over time
- [x] **Uncertain**: Stochastic vehicle arrivals

---

## 🐛 Troubleshooting

### Issue: Agents not connecting

**Solution**: Ensure Openfire is running:
```powershell
# Check service status
Get-Service -Name "Openfire"

# Restart if needed
Restart-Service -Name "Openfire"

# Or access Admin Console
# Open browser: http://localhost:9090
```

### Issue: "Connection refused" errors

**Solution**: 
1. Verify Openfire service is running
2. Check Admin Console is accessible: http://localhost:9090
3. Verify user accounts exist in Admin Console → Users/Groups
4. Ensure TLS is set to "Available" in Security Settings

### Issue: Authentication failed

**Solution**: Verify XMPP accounts in Admin Console:
- Go to: http://localhost:9090
- Login with admin credentials
- Navigate to: Users/Groups
- Check that all 6 accounts exist with correct passwords

### Issue: Import errors

**Solution**: Ensure virtual environment is activated and dependencies installed:
```bash
pip install -r requirements.txt
```

### Issue: Agents timeout

**Solution**: 
1. Check firewall allows port 5222
2. Disable Windows Firewall temporarily for testing
3. Verify localhost DNS resolution
4. Check Openfire connection security settings

---

## 📝 Development Roadmap

### Week 1: Foundation ✅
- [x] SPADE setup and XMPP server configuration
- [x] Basic agent communication with FIPA ACL
- [x] Network topology definition

### Week 2: Traffic Logic ✅
- [x] TrafficState and TrafficPhase models
- [x] QueueSimulator with stochastic arrivals
- [x] TrafficLightAgent with core behaviors
- [x] Signal control algorithm

### Week 3: Coordination (In Progress)
- [x] Multi-agent coordination messages
- [x] Self-organizing algorithm implementation
- [x] Full 5-intersection network deployment
- [ ] Performance baseline comparison

### Week 4: Visualization & Demo (Planned)
- [x] Real-time dashboard with matplotlib
- [x] Demo scenarios implementation
- [ ] Video recording
- [ ] Final report and presentation

---

## 🤝 Contributing

This is an academic project. For suggestions or improvements:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/improvement`)
3. Commit changes (`git commit -am 'Add improvement'`)
4. Push to branch (`git push origin feature/improvement`)
5. Create Pull Request

---

## 📚 References

- **SPADE Documentation**: https://spade-mas.readthedocs.io/
- **FIPA ACL Specification**: http://www.fipa.org/specs/fipa00061/
- **Course**: CM3630 Multi-Agent Systems, University of Moratuwa
- **Instructor**: Prof. Karunananda

---

## 📜 License

This project is developed for academic purposes as part of the CM3630 Multi-Agent Systems course.

---

## 👨‍💻 Author

**Sandaru R.F.**  
BSc (Hons) Artificial Intelligence, 2nd Year  
University of Moratuwa

**GitHub**: [SandaruRF](https://github.com/SandaruRF)  
**Project Repository**: [intelligent-traffic-light-control-network](https://github.com/SandaruRF/intelligent-traffic-light-control-network)

---

## 🎯 Quick Reference

### Common Commands

```bash
# Start system (normal traffic, 60s)
python -m src.main

# Rush hour demo
python -m src.main --scenario rush_hour --duration 120

# Butterfly effect
python -m src.main --scenario butterfly

# Interactive mode
python -m src.main --mode interactive

# Run tests
python -m unittest discover tests

# Start Prosody server
prosodyctl start

# Check Prosody status
prosodyctl status
```

### Important Files

- **Configuration**: `src/settings.py`
- **Main Entry**: `src/main.py`
- **Core Agent**: `src/agents/traffic_light_agent.py`
- **Environment**: `.env` (create from `.env.example`)

---

**🚦 Happy Traffic Optimization! 🚦**

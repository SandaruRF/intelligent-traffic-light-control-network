# 🚦 Traffic Light MAS - Quick Reference Card

## 🚀 Quick Start (3 Steps)

### 1. Setup Openfire (One-time)
```powershell
# Windows: Download and install from igniterealtime.org
# Then run setup helper:
.\setup_openfire.ps1
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run System
```bash
# Test connection first
python test_connection.py

# Run 60-second demo
python -m src.main
```

---

## 📋 Common Commands

### System Control
```bash
# Normal traffic demo (60s)
python -m src.main

# Rush hour demo (120s)
python -m src.main --scenario rush_hour --duration 120

# Butterfly effect demo
python -m src.main --scenario butterfly

# Interactive mode
python -m src.main --mode interactive

# Run with visualization
python -m src.main --visualize
```

### Openfire Management
```powershell
# Check service status
Get-Service -Name "Openfire"

# Start/stop/restart
Start-Service -Name "Openfire"
Stop-Service -Name "Openfire"
Restart-Service -Name "Openfire"

# Access Admin Console
# Open browser: http://localhost:9090
```

### Testing
```bash
# Test XMPP connection
python test_connection.py

# Run unit tests
python -m unittest discover tests
```

---

## 🎯 Demo Scenarios

| Scenario | Command | Description |
|----------|---------|-------------|
| **Normal** | `--scenario normal` | Moderate traffic, baseline |
| **Rush Hour** | `--scenario rush_hour` | Heavy traffic all directions |
| **Light** | `--scenario light` | Low traffic conditions |
| **Directional** | `--scenario directional` | Heavy NS traffic only |
| **Butterfly** | `--scenario butterfly` | Butterfly effect demo |

---

## 🏗️ System Architecture

```
5 TrafficLightAgents + 1 CoordinatorAgent
          ↓
    Openfire XMPP Server (localhost:5222)
          ↓
    Self-Organizing Algorithm
          ↓
    Emergent Traffic Optimization
```

---

## 🔧 Configuration Files

| File | Purpose |
|------|---------|
| `.env` | XMPP credentials (copy from `.env.example`) |
| `src/settings.py` | System parameters, topology |
| `OPENFIRE_SETUP.md` | XMPP server setup guide |

---

## 📊 Key Metrics

- **Average Queue**: Mean vehicles waiting
- **Peak Queue**: Maximum queue observed
- **Throughput**: Vehicles/minute processed
- **Total Delay**: Vehicle-minutes of wait time

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| Connection refused | Check Openfire: `Get-Service -Name "Openfire"` |
| Authentication failed | Verify accounts in Admin Console (http://localhost:9090) |
| Import errors | `pip install -r requirements.txt` |
| Agents timeout | Check firewall port 5222, verify TLS settings |

---

## 📁 Important Files

```
src/
├── main.py                    # Entry point
├── settings.py                # Configuration
├── agents/
│   ├── traffic_light_agent.py # Core agent
│   └── coordinator_agent.py   # Monitoring
└── models/
    ├── traffic_state.py       # State models
    └── queue_simulator.py     # Traffic simulation

test_connection.py             # XMPP test
setup_prosody.ps1             # Setup script
```

---

## 🎓 MAS Concepts Demonstrated

✅ **Communication** - FIPA ACL messages  
✅ **Coordination** - Neighbor information exchange  
✅ **Negotiation** - Adaptive green time allocation  
✅ **Emergent Behavior** - Global optimization from local rules  
✅ **Self-Organization** - No central controller  
✅ **Distributed Control** - Autonomous agents  

---

## 🔗 Quick Links

- **Full README**: [README.md](README.md)
- **Openfire Setup**: [OPENFIRE_SETUP.md](OPENFIRE_SETUP.md)
- **GitHub Repo**: https://github.com/SandaruRF/intelligent-traffic-light-control-network

---

## 🆘 Need Help?

1. Read [README.md](README.md) for detailed documentation
2. Check [OPENFIRE_SETUP.md](OPENFIRE_SETUP.md) for server issues
3. Run `python test_connection.py` to diagnose problems
4. Check console logs for error messages

---

## 📈 Performance Tips

- Run for at least 60s to see adaptation
- Use rush_hour scenario for dramatic results
- Export data in interactive mode (option 5)
- Watch coordinator metrics report (every 10s)

---

**🚦 Happy Experimenting! 🚦**

*For BSc AI - CM3630 Multi-Agent Systems*  
*University of Moratuwa*

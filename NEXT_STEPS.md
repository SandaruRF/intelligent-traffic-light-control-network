# 🎯 Next Steps: Getting Your Traffic System Running with Openfire

## ✅ What's Been Done

1. ✅ All project files created (26 files)
2. ✅ Python 3.10.11 virtual environment ready
3. ✅ All dependencies installed (SPADE 4.1.2, matplotlib, etc.)
4. ✅ Documentation updated for Openfire
5. ✅ Setup scripts created

## 🔄 What Changed

**Prosody → Openfire Migration:**
- Prosody has deprecated Windows support
- Switched to Openfire (better Windows compatibility)
- All documentation updated with Openfire instructions

## 🚀 What You Need to Do Now

### Step 1: Download and Install Openfire (5 minutes)

1. **Download Openfire:**
   - Go to: https://www.igniterealtime.org/downloads/
   - Click "Download Openfire for Windows"
   - Download the `.exe` installer

2. **Install Openfire:**
   - Run the installer **as Administrator**
   - Accept default installation path
   - Complete the wizard
   - Service will start automatically

### Step 2: Configure Openfire (5 minutes)

1. **Access Setup Wizard:**
   - Open browser
   - Go to: http://localhost:9090
   - You'll see the Openfire Setup Wizard

2. **Complete Setup Wizard:**
   
   **Page 1 - Language:**
   - Select your language
   - Click "Continue"
   
   **Page 2 - Server Settings:**
   - Domain: `localhost`
   - Click "Continue"
   
   **Page 3 - Database:**
   - Select "Embedded Database"
   - Click "Continue"
   
   **Page 4 - Profile:**
   - Select "Default"
   - Click "Continue"
   
   **Page 5 - Admin Account:**
   - Email: `admin@localhost`
   - Password: `admin` (or your choice - **remember this!**)
   - Confirm password
   - Click "Continue"
   
   **Page 6 - Done:**
   - Click "Login to admin console"

3. **Configure Security (Important!):**
   - Login with admin credentials
   - Go to: **Server** → **Server Settings** → **Security Settings**
   - Find "Client Connection Security"
   - Change from "Required" to **"Available"**
   - Click **"Save Settings"**

### Step 3: Create User Accounts (5 minutes)

Go to: **Users/Groups** → **Create New User**

Create these 6 accounts one by one:

| Username | Password | Name | Email |
|----------|----------|------|-------|
| `coordinator` | `coordinator123` | Coordinator Agent | coordinator@localhost |
| `tl_center` | `traffic123` | Center Traffic Light | tl_center@localhost |
| `tl_north` | `traffic123` | North Traffic Light | tl_north@localhost |
| `tl_south` | `traffic123` | South Traffic Light | tl_south@localhost |
| `tl_east` | `traffic123` | East Traffic Light | tl_east@localhost |
| `tl_west` | `traffic123` | West Traffic Light | tl_west@localhost |

For each account:
1. Click "Create New User"
2. Enter username
3. Enter password (twice)
4. Enter name
5. Enter email
6. Click "Create User"
7. Repeat for next account

### Step 4: Test Connection (1 minute)

```powershell
# In your project directory, with venv activated:
python test_connection.py
```

You should see:
```
🔍 Testing XMPP Connection...
✅ SUCCESS: Agent connected successfully!
✅ Agent stopped successfully
```

### Step 5: Run Your Traffic System! (Finally!)

```powershell
# Run the demo
python -m src.main
```

You'll see:
- 6 agents starting up
- Traffic queues being simulated
- Coordinator reports every 10 seconds
- Visualization dashboard (if enabled)

## 📝 Quick Command Reference

```powershell
# Check Openfire service
Get-Service -Name "Openfire"

# Restart Openfire if needed
Restart-Service -Name "Openfire"

# Access Admin Console
# Browser: http://localhost:9090

# Test connection
python test_connection.py

# Run system
python -m src.main

# Run with different scenarios
python -m src.main --scenario rush_hour
python -m src.main --scenario butterfly
python -m src.main --mode interactive
```

## 🐛 Troubleshooting

### "Connection refused" error
**Cause:** Openfire not running  
**Solution:**
```powershell
Get-Service -Name "Openfire"
Start-Service -Name "Openfire"
```

### "Authentication failed" error
**Cause:** Accounts not created or wrong password  
**Solution:**
1. Open http://localhost:9090
2. Login with admin credentials
3. Go to Users/Groups
4. Verify all 6 accounts exist
5. Check passwords match those in code

### Can't access http://localhost:9090
**Cause:** Openfire service not running  
**Solution:**
```powershell
Restart-Service -Name "Openfire"
# Wait 10 seconds, then try again
```

### Agents timeout after connecting
**Cause:** TLS still required  
**Solution:**
1. Go to http://localhost:9090
2. Server → Server Settings → Security Settings
3. Set "Client Connection Security" to "Available"
4. Save Settings

## 📚 Documentation Files

- **OPENFIRE_SETUP.md** - Detailed Openfire setup guide
- **README.md** - Full project documentation
- **QUICKSTART.md** - Quick reference card
- **setup_openfire.ps1** - Helper script (opens admin console)

## 🎯 Your Next Command

```powershell
# After installing Openfire and creating accounts, run:
python test_connection.py
```

If successful, you'll see ✅ and you're ready to run the full system!

---

**Need Help?**
- Check OPENFIRE_SETUP.md for detailed instructions
- Visit: https://www.igniterealtime.org/projects/openfire/documentation.jsp

**Ready?** Let's get that traffic flowing! 🚦🤖

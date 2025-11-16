# Openfire XMPP Server Setup for Windows

## Overview
This guide will help you set up Openfire XMPP server on Windows for the Intelligent Traffic Light Control Network.

## Step 1: Download and Install Openfire

1. **Download Openfire:**
   - Visit: https://www.igniterealtime.org/downloads/
   - Download the Windows installer (exe file)
   - Current version: Openfire 4.8.x or later

2. **Install Openfire:**
   - Run the installer as Administrator
   - Use default installation path: `C:\Program Files (x86)\Openfire`
   - Complete the installation wizard

## Step 2: Initial Openfire Configuration

1. **Start Openfire:**
   - The Openfire service should start automatically
   - If not, go to Services (Windows + R, type `services.msc`)
   - Find "Openfire" and start it

2. **Access Admin Console:**
   - Open browser and go to: http://localhost:9090
   - You'll see the Openfire Setup Wizard

3. **Setup Wizard Configuration:**

   **Language Selection:**
   - Select your preferred language
   - Click Continue

   **Server Settings:**
   - Domain: `localhost`
   - Click Continue

   **Database Settings:**
   - Select "Embedded Database"
   - Click Continue

   **Profile Settings:**
   - Select "Default" (store user data in database)
   - Click Continue

   **Administrator Account:**
   - Email: `admin@localhost`
   - New Password: `admin` (or choose your own - **remember this!**)
   - Confirm Password
   - Click Continue

   **Finish Setup:**
   - Click "Login to admin console"

## Step 3: Configure Openfire for Local Development

1. **Login to Admin Console:**
   - URL: http://localhost:9090
   - Username: `admin`
   - Password: (what you set in setup)

2. **Disable TLS Requirement (for development):**
   - Go to: **Server → Server Settings → Security Settings**
   - Under "Client Connection Security":
     - Set to "Available" or "Disabled" (for development only)
   - Click "Save Settings"

3. **Enable In-Band Registration (Optional):**
   - Go to: **Server → Server Settings → Registration & Login**
   - Check "Inband Account Registration"
   - Click "Save Settings"

## Step 4: Create User Accounts

### Option A: Using Admin Console (Recommended)

1. Go to: **Users/Groups → Create New User**

2. Create these 6 accounts:

   **Coordinator Account:**
   - Username: `coordinator`
   - Password: `coordinator123`
   - Name: `Coordinator Agent`
   - Email: `coordinator@localhost`
   - Click "Create User"

   **Traffic Light Agents:**
   
   | Username | Password | Name |
   |----------|----------|------|
   | `tl_center` | `traffic123` | Center Traffic Light |
   | `tl_north` | `traffic123` | North Traffic Light |
   | `tl_south` | `traffic123` | South Traffic Light |
   | `tl_east` | `traffic123` | East Traffic Light |
   | `tl_west` | `traffic123` | West Traffic Light |

   Create each account one by one using the form.

### Option B: Using PowerShell Script

Run the provided setup script (requires Openfire REST API plugin):

```powershell
.\setup_openfire.ps1
```

## Step 5: Verify Server Status

1. **Check Service:**
   ```powershell
   Get-Service -Name "Openfire"
   ```
   Status should be "Running"

2. **Check Ports:**
   ```powershell
   netstat -ano | findstr "5222"
   ```
   Should show port 5222 listening (XMPP client connections)

3. **Test Connection:**
   ```powershell
   python test_connection.py
   ```
   Should show: ✅ SUCCESS: Agent connected successfully!

## Step 6: Run Your Traffic System

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run the system
python -m src.main
```

## Troubleshooting

### Issue: Can't access http://localhost:9090
**Solution:**
- Check if Openfire service is running: `Get-Service -Name "Openfire"`
- Restart the service: `Restart-Service -Name "Openfire"`
- Check firewall settings

### Issue: Agents can't connect
**Solution:**
- Verify TLS is disabled or set to "Available" in Security Settings
- Check user accounts exist in Admin Console → Users/Groups
- Verify passwords match your configuration
- Check port 5222 is not blocked by firewall

### Issue: Connection timeout
**Solution:**
- Make sure Openfire service is running
- Check Windows Firewall allows connections on port 5222
- Restart Openfire service

### Issue: Authentication failed
**Solution:**
- Verify usernames and passwords in Admin Console
- Check that accounts were created successfully
- Update passwords in `src/settings.py` if needed

## Default Configuration

Your system is configured to use:
- **Server:** localhost
- **Port:** 5222
- **Domain:** localhost
- **Accounts:** 6 users (coordinator + 5 traffic lights)

All passwords are in `src/settings.py` in the INTERSECTIONS dictionary.

## Security Notes

⚠️ **For Development Only:**
- Default passwords are used for ease of setup
- TLS is disabled for simplicity
- This configuration is NOT suitable for production

For production deployment:
- Enable TLS/SSL
- Use strong passwords
- Enable certificate verification
- Use proper domain names
- Configure firewall rules

## Next Steps

Once Openfire is running and accounts are created:

1. ✅ Test connection: `python test_connection.py`
2. ✅ Run demo: `python -m src.main`
3. ✅ Explore scenarios in interactive mode
4. ✅ Monitor agent behavior in the dashboard

## Resources

- Openfire Documentation: https://www.igniterealtime.org/projects/openfire/documentation.jsp
- Openfire Forums: https://discourse.igniterealtime.org/
- XMPP Standards: https://xmpp.org/

---

**Quick Start Command Summary:**

```powershell
# 1. Install Openfire from igniterealtime.org
# 2. Setup via http://localhost:9090
# 3. Create accounts via Admin Console
# 4. Test connection
python test_connection.py

# 5. Run system
python -m src.main
```

Happy agent coding! 🚦🤖

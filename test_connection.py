"""
Simple test to verify XMPP connection and SPADE setup.

Run this before starting the main system to ensure everything is configured correctly.
"""

import asyncio
import sys
from spade.agent import Agent


class TestAgent(Agent):
    """Simple test agent to verify XMPP connection."""
    
    async def setup(self):
        """Called when agent starts."""
        print(f"✅ Agent {self.jid} connected successfully!")


async def test_xmpp_connection():
    """Test XMPP connection with a simple agent."""
    print("🧪 Testing XMPP Connection...")
    print("=" * 60)
    
    # Test credentials
    test_jid = "coordinator@localhost"
    test_password = "coordinator123"
    
    print(f"\nAttempting to connect to: {test_jid}")
    print("Using Prosody server at: localhost:5222")
    
    try:
        # Create test agent
        agent = TestAgent(test_jid, test_password)
        
        # Start agent
        print("\nStarting agent...")
        await agent.start()
        
        # Wait a moment
        await asyncio.sleep(2)
        
        # Check if alive
        if agent.is_alive():
            print("\n" + "=" * 60)
            print("✅ SUCCESS! XMPP connection is working!")
            print("=" * 60)
            print("\nYou can now run the main system:")
            print("  python -m src.main")
            result = True
        else:
            print("\n" + "=" * 60)
            print("❌ FAILED! Agent could not connect")
            print("=" * 60)
            print("\nTroubleshooting:")
            print("1. Check if Prosody is running:")
            print("   prosodyctl status")
            print("2. Verify user account exists:")
            print("   prosodyctl register coordinator localhost coordinator123")
            print("3. Check firewall settings")
            result = False
        
        # Stop agent
        await agent.stop()
        
        return result
    
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ ERROR: {e}")
        print("=" * 60)
        print("\nCommon issues:")
        print("1. Prosody not running - run: prosodyctl start")
        print("2. User not created - run: prosodyctl register coordinator localhost coordinator123")
        print("3. Port 5222 blocked by firewall")
        print("4. SPADE not installed - run: pip install -r requirements.txt")
        return False


async def test_all_accounts():
    """Test all agent accounts."""
    print("\n🧪 Testing All Agent Accounts...")
    print("=" * 60)
    
    accounts = [
        ("coordinator@localhost", "coordinator123"),
        ("tl_center@localhost", "center123"),
        ("tl_north@localhost", "north123"),
        ("tl_south@localhost", "south123"),
        ("tl_east@localhost", "east123"),
        ("tl_west@localhost", "west123")
    ]
    
    results = []
    
    for jid, password in accounts:
        try:
            print(f"\nTesting {jid}...")
            agent = TestAgent(jid, password)
            await agent.start()
            await asyncio.sleep(1)
            
            if agent.is_alive():
                print(f"  ✅ {jid} - OK")
                results.append(True)
            else:
                print(f"  ❌ {jid} - FAILED")
                results.append(False)
            
            await agent.stop()
            await asyncio.sleep(0.5)
        
        except Exception as e:
            print(f"  ❌ {jid} - ERROR: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print(f"Results: {sum(results)}/{len(results)} accounts working")
    print("=" * 60)
    
    if all(results):
        print("\n✅ All accounts configured correctly!")
        print("\nYou're ready to run the system:")
        print("  python -m src.main")
        return True
    else:
        print("\n❌ Some accounts failed!")
        print("\nTo create missing accounts, run:")
        for jid, password in accounts:
            username = jid.split("@")[0]
            print(f"  prosodyctl register {username} localhost {password}")
        return False


async def main():
    """Main test function."""
    print("\n🚦 Traffic Light MAS - System Test")
    print("=" * 60)
    
    # Test basic connection first
    basic_test = await test_xmpp_connection()
    
    if not basic_test:
        sys.exit(1)
    
    # Ask if user wants to test all accounts
    print("\n")
    response = input("Test all agent accounts? (y/n): ").strip().lower()
    
    if response == 'y':
        all_test = await test_all_accounts()
        if not all_test:
            sys.exit(1)
    
    print("\n✅ All tests passed!")
    print("\nNext step: Run the system")
    print("  python -m src.main --scenario normal --duration 60")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(0)

"""
Main entry point for the Intelligent Traffic Light Control Network.

This module provides:
- System initialization
- Demo scenarios
- Command-line interface
- Visualization integration
"""

import asyncio
import argparse
import sys
import time
from typing import Dict, List

from src.agents.traffic_light_agent import TrafficLightAgent
from src.agents.coordinator_agent import CoordinatorAgent
from src.settings import (
    INTERSECTIONS,
    COORDINATOR_CONFIG,
    SCENARIOS
)
from src.visualization.dashboard import create_animated_dashboard


class TrafficLightSystem:
    """
    Main system controller for the traffic light network.
    
    Manages:
    - Agent lifecycle (start/stop)
    - Scenario execution
    - System monitoring
    - Visualization
    """
    
    def __init__(self):
        """Initialize the system."""
        self.traffic_lights: Dict[str, TrafficLightAgent] = {}
        self.coordinator: CoordinatorAgent = None
        self.is_running = False
        
        print("🚦 Intelligent Traffic Light Control Network")
        print("=" * 60)
    
    async def initialize_agents(self) -> None:
        """Create and start all agents."""
        print("\n📡 Initializing XMPP connection and agents...")
        
        # Create coordinator
        print(f"\n  Starting Coordinator at {COORDINATOR_CONFIG['jid']}...")
        self.coordinator = CoordinatorAgent(
            jid=COORDINATOR_CONFIG['jid'],
            password=COORDINATOR_CONFIG['password']
        )
        await self.coordinator.start()
        print("  ✅ Coordinator ready")
        
        # Create traffic light agents
        print("\n  Starting Traffic Light Agents...")
        for name, config in INTERSECTIONS.items():
            print(f"    {name} at {config['jid']}...")
            
            agent = TrafficLightAgent(
                intersection_name=name,
                jid=config['jid'],
                password=config['password'],
                coordinator_jid=COORDINATOR_CONFIG['jid']
            )
            
            await agent.start()
            self.traffic_lights[name] = agent
            
            # Small delay to ensure clean startup
            await asyncio.sleep(0.5)
        
        print(f"  ✅ {len(self.traffic_lights)} traffic lights active")
        
        self.is_running = True
        print("\n🟢 System fully operational!")
    
    async def shutdown_agents(self) -> None:
        """Stop all agents gracefully."""
        print("\n🛑 Shutting down system...")
        
        # Stop traffic lights
        for name, agent in self.traffic_lights.items():
            print(f"  Stopping {name}...")
            await agent.stop()
        
        # Stop coordinator
        if self.coordinator:
            print("  Stopping Coordinator...")
            await self.coordinator.stop()
        
        self.is_running = False
        
        # Final cleanup
        await asyncio.sleep(1)
        
        print("✅ System shutdown complete")
    
    def set_scenario(self, scenario_name: str) -> None:
        """
        Change traffic scenario for all intersections.
        
        Args:
            scenario_name: Scenario name from SCENARIOS config
        """
        if scenario_name not in SCENARIOS:
            print(f"⚠️  Unknown scenario: {scenario_name}")
            return
        
        scenario = SCENARIOS[scenario_name]
        print(f"\n🚗 Setting scenario: {scenario_name.upper()}")
        print(f"   {scenario['description']}")
        print(f"   Arrival rate: {scenario['arrival_rate']}, Departure rate: {scenario['departure_rate']}")
        
        for agent in self.traffic_lights.values():
            agent.queue_simulator.set_arrival_rate(scenario['arrival_rate'])
            agent.queue_simulator.set_departure_rate(scenario['departure_rate'])
    
    def scenario_butterfly_effect(self) -> None:
        """
        Demonstrate butterfly effect: small change → large system impact.
        
        Add 2 vehicles at one intersection and observe cascade.
        """
        print("\n🦋 BUTTERFLY EFFECT DEMO")
        print("=" * 60)
        print("Adding 2 vehicles to TL_NORTH and observing cascade effect...")
        
        if "TL_NORTH" in self.traffic_lights:
            self.traffic_lights["TL_NORTH"].add_vehicle_burst("N", 2)
            print("✅ Vehicles added. Watch how the entire network adapts!")
        else:
            print("⚠️  TL_NORTH not found")
    
    def scenario_directional_congestion(self) -> None:
        """
        Demonstrate self-organization: heavy traffic in one direction.
        
        System should autonomously allocate more green time to congested direction.
        """
        print("\n🔄 DIRECTIONAL CONGESTION DEMO")
        print("=" * 60)
        print("Creating heavy North-South traffic at all intersections...")
        
        for agent in self.traffic_lights.values():
            # Increase only NS arrival rates
            agent.queue_simulator.set_arrival_rate(0.8)
            # Manually bias toward NS (if using DirectionalQueueSimulator)
            # For now, just set high overall rate
        
        print("✅ Directional traffic set. System will self-organize green times!")
    
    async def scenario_failure_recovery(self, intersection: str = "TL_EAST") -> None:
        """
        Demonstrate robustness: system adapts when one agent fails.
        
        Args:
            intersection: Intersection to simulate failure
        """
        print("\n⚠️  FAILURE RECOVERY DEMO")
        print("=" * 60)
        print(f"Simulating failure of {intersection}...")
        
        if intersection in self.traffic_lights:
            agent = self.traffic_lights[intersection]
            await agent.stop()
            print(f"❌ {intersection} is offline")
            
            print("\nWaiting 20 seconds for system to adapt...")
            await asyncio.sleep(20)
            
            print(f"\n🔧 Restarting {intersection}...")
            await agent.start()
            print(f"✅ {intersection} back online. System recovering!")
        else:
            print(f"⚠️  {intersection} not found")
    
    async def run_demo(self, duration: int = 60, scenario: str = "normal") -> None:
        """
        Run a demo for specified duration.
        
        Args:
            duration: Demo duration in seconds
            scenario: Initial scenario name
        """
        await self.initialize_agents()
        
        # Set initial scenario
        self.set_scenario(scenario)
        
        print(f"\n⏱️  Running demo for {duration} seconds...")
        print("Press Ctrl+C to stop early\n")
        
        try:
            await asyncio.sleep(duration)
        except KeyboardInterrupt:
            print("\n\n⚠️  Demo interrupted by user")
        
        await self.shutdown_agents()
    
    async def run_interactive(self) -> None:
        """Run interactive mode with menu."""
        await self.initialize_agents()
        
        print("\n" + "=" * 60)
        print("INTERACTIVE MODE")
        print("=" * 60)
        
        while self.is_running:
            print("\nOptions:")
            print("  1. Change scenario")
            print("  2. Butterfly effect demo")
            print("  3. Directional congestion demo")
            print("  4. Show system status")
            print("  5. Export data")
            print("  9. Quit")
            
            try:
                choice = input("\nEnter choice: ").strip()
                
                if choice == "1":
                    print("\nAvailable scenarios:")
                    for i, (name, info) in enumerate(SCENARIOS.items(), 1):
                        print(f"  {i}. {name}: {info['description']}")
                    
                    scenario = input("Enter scenario name: ").strip()
                    self.set_scenario(scenario)
                
                elif choice == "2":
                    self.scenario_butterfly_effect()
                
                elif choice == "3":
                    self.scenario_directional_congestion()
                
                elif choice == "4":
                    self._show_status()
                
                elif choice == "5":
                    self._export_data()
                
                elif choice == "9":
                    break
                
                # Small delay to let system process
                await asyncio.sleep(1)
            
            except KeyboardInterrupt:
                print("\n\n⚠️  Interrupted")
                break
            except EOFError:
                print("\n\n⚠️  EOF")
                break
        
        await self.shutdown_agents()
    
    def _show_status(self) -> None:
        """Display current system status."""
        if not self.coordinator:
            print("⚠️  Coordinator not available")
            return
        
        print("\n" + "=" * 60)
        print("SYSTEM STATUS")
        print("=" * 60)
        
        states = self.coordinator.get_all_current_states()
        metrics = self.coordinator.get_system_metrics()
        
        print(f"\nActive Intersections: {len(states)}")
        print(f"Total Waiting: {metrics.get('total_waiting', 0)}")
        print(f"Throughput: {metrics.get('throughput', 0):.2f} vehicles/min")
        
        print("\nPer-Intersection Status:")
        for name, state in states.items():
            print(f"  {name:12s}: Queue={state['total_queue']:3d} "
                  f"Phase={state['phase']:10s} Cycle={state['cycle_count']:3d}")
    
    def _export_data(self) -> None:
        """Export system data to file."""
        if not self.coordinator:
            print("⚠️  Coordinator not available")
            return
        
        import json
        from datetime import datetime
        
        filename = f"traffic_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        data = self.coordinator.export_data()
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        print(f"✅ Data exported to {filename}")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Intelligent Traffic Light Control Network (SPADE MAS)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.main --mode demo --duration 120 --scenario rush_hour
  python -m src.main --mode interactive
  python -m src.main --scenario butterfly

Demo Scenarios:
  normal       - Normal traffic conditions
  rush_hour    - Heavy traffic in all directions
  light        - Light traffic conditions
  directional  - Heavy North-South traffic
  butterfly    - Butterfly effect demonstration
"""
    )
    
    parser.add_argument(
        '--mode',
        choices=['demo', 'interactive'],
        default='demo',
        help='Run mode (default: demo)'
    )
    
    parser.add_argument(
        '--duration',
        type=int,
        default=60,
        help='Demo duration in seconds (default: 60)'
    )
    
    parser.add_argument(
        '--scenario',
        choices=list(SCENARIOS.keys()) + ['butterfly'],
        default='normal',
        help='Initial traffic scenario (default: normal)'
    )
    
    parser.add_argument(
        '--visualize',
        action='store_true',
        help='Show real-time visualization dashboard'
    )
    
    args = parser.parse_args()
    
    # Create system
    system = TrafficLightSystem()
    
    try:
        if args.mode == 'interactive':
            await system.run_interactive()
        
        else:
            # Demo mode
            if args.scenario == 'butterfly':
                # Special butterfly effect demo
                await system.initialize_agents()
                system.set_scenario('normal')
                
                print("\n⏱️  Running for 30s to establish baseline...")
                await asyncio.sleep(30)
                
                system.scenario_butterfly_effect()
                
                print("⏱️  Observing cascade for 30s...")
                await asyncio.sleep(30)
                
                await system.shutdown_agents()
            
            else:
                await system.run_demo(duration=args.duration, scenario=args.scenario)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        if system.is_running:
            await system.shutdown_agents()
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        if system.is_running:
            await system.shutdown_agents()


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())

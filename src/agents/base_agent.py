"""
Base agent class with common functionality for all agents in the system.

Provides logging, message handling utilities, and FIPA ACL compliance.
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from spade.agent import Agent
from spade.message import Message

from src.settings import LANGUAGE_JSON


class BaseTrafficAgent(Agent):
    """
    Base class for all traffic system agents.
    
    Provides common functionality:
    - Structured logging
    - FIPA ACL message creation
    - JSON message serialization/deserialization
    - Agent lifecycle management
    
    All traffic agents (TrafficLightAgent, CoordinatorAgent) inherit from this.
    """
    
    def __init__(
        self,
        jid: str,
        password: str,
        agent_name: str = "",
        verify_security: bool = False
    ):
        """
        Initialize base agent.
        
        Args:
            jid: Agent's Jabber ID (e.g., "agent@localhost")
            password: XMPP server password
            agent_name: Human-readable agent name for logging
            verify_security: Whether to verify SSL certificates
        """
        super().__init__(jid, password, verify_security=verify_security)
        
        self.agent_name = agent_name or jid.split("@")[0]
        
        # Setup logging
        self._setup_logging()
        
        # Message tracking
        self.messages_sent = 0
        self.messages_received = 0
        
        # Agent start time
        self.start_time = datetime.now()
    
    def _setup_logging(self) -> None:
        """Configure agent-specific logging."""
        self.logger = logging.getLogger(self.agent_name)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                f"[{self.agent_name}] %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def log(self, message: str, level: str = "INFO") -> None:
        """
        Log a message with the agent's name prefix.
        
        Args:
            message: Message to log
            level: Log level ("INFO", "WARNING", "ERROR", "DEBUG")
        """
        log_func = getattr(self.logger, level.lower(), self.logger.info)
        log_func(message)
    
    def create_fipa_message(
        self,
        to: str,
        performative: str,
        ontology: str,
        body_data: Dict[str, Any],
        language: str = LANGUAGE_JSON
    ) -> Message:
        """
        Create a FIPA ACL compliant message.
        
        This ensures all inter-agent communication follows the FIPA standard
        required for the course project.
        
        Args:
            to: Recipient JID
            performative: FIPA performative (inform, request, agree, refuse, etc.)
            ontology: Message ontology (e.g., "traffic-coordination")
            body_data: Message content as dictionary
            language: Content language (default: "json")
        
        Returns:
            SPADE Message object with FIPA metadata
        """
        msg = Message(to=to)
        
        # FIPA ACL metadata
        msg.set_metadata("performative", performative)
        msg.set_metadata("ontology", ontology)
        msg.set_metadata("language", language)
        msg.set_metadata("sender", str(self.jid))
        
        # Add timestamp to body
        body_data["timestamp"] = datetime.now().isoformat()
        body_data["sender_name"] = self.agent_name
        
        # Serialize body as JSON
        msg.body = json.dumps(body_data)
        
        self.messages_sent += 1
        
        return msg
    
    def parse_fipa_message(self, msg: Message) -> Optional[Dict[str, Any]]:
        """
        Parse a received FIPA ACL message.
        
        Args:
            msg: Received SPADE Message
        
        Returns:
            Dictionary containing message data and metadata, or None if parsing fails
        """
        try:
            # Parse JSON body
            body_data = json.loads(msg.body)
            
            # Extract FIPA metadata
            parsed = {
                "performative": msg.get_metadata("performative"),
                "ontology": msg.get_metadata("ontology"),
                "language": msg.get_metadata("language"),
                "sender": str(msg.sender),
                "data": body_data
            }
            
            self.messages_received += 1
            
            return parsed
        
        except json.JSONDecodeError as e:
            self.log(f"Failed to parse message body as JSON: {e}", "ERROR")
            return None
        except Exception as e:
            self.log(f"Error parsing message: {e}", "ERROR")
            return None
    
    def broadcast_message(
        self,
        recipients: list[str],
        performative: str,
        ontology: str,
        body_data: Dict[str, Any]
    ) -> int:
        """
        Broadcast a message to multiple recipients.
        
        Args:
            recipients: List of recipient JIDs
            performative: FIPA performative
            ontology: Message ontology
            body_data: Message content
        
        Returns:
            Number of messages sent
        """
        sent_count = 0
        
        for recipient in recipients:
            msg = self.create_fipa_message(
                to=recipient,
                performative=performative,
                ontology=ontology,
                body_data=body_data.copy()
            )
            
            # Note: actual sending happens in behavior's run() method
            # This just creates the messages
            sent_count += 1
        
        return sent_count
    
    def get_runtime_stats(self) -> Dict[str, Any]:
        """
        Get agent runtime statistics.
        
        Returns:
            Dictionary with runtime metrics
        """
        runtime = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "agent_name": self.agent_name,
            "jid": str(self.jid),
            "runtime_seconds": runtime,
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "is_alive": self.is_alive()
        }
    
    async def setup(self) -> None:
        """
        Agent setup callback (called when agent starts).
        
        Override this in subclasses to add behaviors and initialization logic.
        """
        self.log(f"🚀 Agent starting at {datetime.now().strftime('%H:%M:%S')}")
    
    async def teardown(self) -> None:
        """
        Agent teardown callback (called when agent stops).
        
        Override this in subclasses for cleanup logic.
        """
        stats = self.get_runtime_stats()
        self.log(
            f"🛑 Agent stopping. Runtime: {stats['runtime_seconds']:.1f}s, "
            f"Sent: {stats['messages_sent']}, Received: {stats['messages_received']}"
        )


class FIPAPerformatives:
    """
    Standard FIPA ACL performatives.
    
    These define the types of communicative acts agents can perform.
    Using constants ensures consistency across the system.
    """
    
    # Assertive performatives (informing about state)
    INFORM = "inform"
    CONFIRM = "confirm"
    DISCONFIRM = "disconfirm"
    
    # Directive performatives (requesting action)
    REQUEST = "request"
    QUERY_IF = "query-if"
    QUERY_REF = "query-ref"
    
    # Commissive performatives (committing to action)
    AGREE = "agree"
    REFUSE = "refuse"
    
    # Executive performatives (performing action)
    PROPOSE = "propose"
    ACCEPT_PROPOSAL = "accept-proposal"
    REJECT_PROPOSAL = "reject-proposal"
    
    # Declarative performatives
    CANCEL = "cancel"
    
    @classmethod
    def get_all(cls) -> list[str]:
        """Get list of all performatives."""
        return [
            cls.INFORM, cls.CONFIRM, cls.DISCONFIRM,
            cls.REQUEST, cls.QUERY_IF, cls.QUERY_REF,
            cls.AGREE, cls.REFUSE,
            cls.PROPOSE, cls.ACCEPT_PROPOSAL, cls.REJECT_PROPOSAL,
            cls.CANCEL
        ]

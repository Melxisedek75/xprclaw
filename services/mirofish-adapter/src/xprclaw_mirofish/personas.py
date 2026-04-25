"""DeFi-themed agent personas for multi-agent simulation."""

from xprclaw_mirofish.models import AgentPersona

# Six default personas for XPRClaw simulations
DEFAULT_PERSONAS: dict[str, AgentPersona] = {
    "whale-holder": AgentPersona(
        id="whale-holder",
        name="Whale Holder",
        description="Long-term XPR believer. Accumulates on dips, rarely sells. "
        "Focuses on staking yields and treasury health. High conviction, low frequency.",
        bias="bullish",
        risk_tolerance=0.3,
        time_horizon_days=365,
    ),
    "yield-farmer": AgentPersona(
        id="yield-farmer",
        name="Yield Farmer",
        description="APY optimizer. Moves capital between staking, loans, and arbitrage "
        "based on current yields. Neutral on price direction, focused on returns.",
        bias="neutral",
        risk_tolerance=0.6,
        time_horizon_days=30,
    ),
    "arbitrage-bot-operator": AgentPersona(
        id="arbitrage-bot-operator",
        name="Arbitrage Bot Operator",
        description="Pure profit seeker. Automatically exploits spreads between Metal X, "
        "DEX, and staking. Very short time horizon, mechanical execution.",
        bias="neutral",
        risk_tolerance=0.2,
        time_horizon_days=1,
    ),
    "news-trader": AgentPersona(
        id="news-trader",
        name="News Trader",
        description="Reacts to external events and media sentiment. Often contrarian "
        "on overreactions. Pivots quickly when narrative shifts.",
        bias="contrarian",
        risk_tolerance=0.7,
        time_horizon_days=7,
    ),
    "protocol-skeptic": AgentPersona(
        id="protocol-skeptic",
        name="Protocol Skeptic",
        description="Cautious about XPR protocol risks and regulatory headwinds. "
        "Defaults to holding stables or reducing exposure. High risk-aversion.",
        bias="bearish",
        risk_tolerance=0.15,
        time_horizon_days=90,
    ),
    "community-member": AgentPersona(
        id="community-member",
        name="Community Member",
        description="Socially driven. Follows community sentiment and Discord discussions. "
        "FOMO-prone on rallies, panic-prone on FUD. Herds with consensus.",
        bias="neutral",
        risk_tolerance=0.8,
        time_horizon_days=14,
    ),
}


def get_all_personas() -> list[AgentPersona]:
    """Return all default personas in consistent order."""
    return [DEFAULT_PERSONAS[key] for key in sorted(DEFAULT_PERSONAS.keys())]


def get_persona_by_id(persona_id: str) -> AgentPersona | None:
    """Retrieve a persona by ID, or None if not found."""
    return DEFAULT_PERSONAS.get(persona_id)

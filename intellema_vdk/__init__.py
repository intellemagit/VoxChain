from typing import Optional, List, Any

from .livekit_lib.client import LiveKitManager
from .retell_lib.retell_client import RetellManager

def VoiceClient(provider: str, **kwargs) -> Any:
    """
    Factory function that returns a specific provider client.
    
    Args:
        provider: "livekit" or "retell"
        **kwargs: Arguments passed to the manager's constructor
    
    Returns:
        An instance of LiveKitManager or RetellManager
    """
    if provider == "livekit":
        return LiveKitManager(**kwargs)
    elif provider == "retell":
        return RetellManager(**kwargs)
    else:
        raise ValueError(f"Unknown provider: {provider}. Supported providers: 'livekit', 'retell'")

async def start_outbound_call(provider: str, *args, **kwargs):
    """
    Convenience wrapper to start an outbound call.
    """
    client = VoiceClient(provider)
    # Check if the method is async (LiveKit) or sync (Retell)
    if provider == "livekit":
        return await client.start_outbound_call(*args, **kwargs)
    else:
        return client.start_outbound_call(*args, **kwargs)

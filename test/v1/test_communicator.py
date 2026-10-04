import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agentium.core.communicator import Communicator, ChannelType, Message, MessagePriority

def test_communicator():
    print("=== Testing Communicator ===")
    communicator = Communicator()
    
    # 1. Send via Console channel
    msg = Message(
        content="Test alert from Agentium test suite",
        recipients=["console"],
        channel=ChannelType.CONSOLE,
        priority=MessagePriority.NORMAL
    )
    result = communicator.send(msg)
    print("Console Send Result:", result)
    assert result.get("success") is True, "Console send failed"
    
    # 2. String send directly
    res_str = communicator.send("Direct string message to console", channel=ChannelType.CONSOLE)
    print("Direct String Send Result:", res_str)
    assert res_str.get("success") is True, "String send failed"

    print("Result: PASS\n")

if __name__ == "__main__":
    test_communicator()

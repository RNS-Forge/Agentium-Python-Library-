import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agentium.core.rearranger import Rearranger, ArrangementStrategy, ContentType

def test_rearranger():
    print("=== Testing Rearranger ===")
    rearranger = Rearranger()
    
    # 1. Rearrange list by alphabetical
    items = ["Zebra step", "Alpha step", "Beta step", "Gamma step"]
    res_list = rearranger.rearrange(items, strategy=ArrangementStrategy.ALPHABETICAL, content_type=ContentType.LIST)
    print("Alphabetical List Result:", res_list)
    assert isinstance(res_list, list), "Expected list result"
    assert res_list[0] == "Alpha step", "Expected Alpha step first"
    
    # 2. Rearrange text
    sample_text = "Finally, we conclude. First, we start. Next, we process."
    res_text = rearranger.rearrange(sample_text, strategy=ArrangementStrategy.LOGICAL_FLOW, content_type=ContentType.TEXT)
    print("Rearranged Text Result:", res_text)
    assert res_text is not None, "Expected valid text result"

    print("Result: PASS\n")

if __name__ == "__main__":
    test_rearranger()

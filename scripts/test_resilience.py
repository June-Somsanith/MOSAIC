# Can MOSAIC application handle federated access issues
# pass ids, request some valid and some invalid id's don't crash system, no abstract, etc

import os
import sys
import asyncio
import httpx
from unittest.mock import MagicMock, patch

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.orthology import OrthologyService

async def test_resilience_logic():
    print("=" * 60)
    print("MOSAIC: SYSTEM RESILIENCE & RECOVERY VALIDATOR")
    print("=" * 60)

    # 1. Mock a client that fails twice with a 429 (rate limit) then is able to succeed
    mock_request = httpx.Request("GET", "https://rest.ensembl.org/test")
    
    mock_responses = [
        httpx.Response(429, content = b"Too Many Requests: Rate Limit Exceeded", request = mock_request),
        httpx.Response(429, content = b"Too Many Requests: Rate Limit Exceeded", request = mock_request),
        httpx.Response(200, json = {"data": [{"homologies": []}]}, request = mock_request),
    ]

    mock_client = MagicMock(spec = httpx.AsyncClient)
    mock_client.get.side_effect = mock_responses # Side effect returns the next response in the list for each call

    print ("STATUS: Simulating federated access issues (HTTP 429) to trigger recovery...")

    try:
        result = await OrthologyService.fetch_single_orthology(
            mock_client, "ENSG00000139618", "mouse"
        )

        actual_calls = mock_client.get.call_count
        print(f"Total API attempts during recover phase: {actual_calls}")

        if actual_calls > 1:
            print("Success: Resiliance layer detected")
        else:
            print(f"WARNING: Unexpected attempt count ({actual_calls}). Check decorator configuration")
    except Exception as e:
        print(f"RESILIENCE CRASH: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_resilience_logic())




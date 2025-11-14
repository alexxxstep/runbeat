"""
Script to test chat endpoint with real OpenAI API.
Usage: python test_chat_endpoint.py
"""
import asyncio
import sys
import os

# Fix encoding for Windows
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"

from app.services.llm_service import LLMService
from app.api.routes.chat import send_message
from app.schemas.chat import ChatRequest


async def test_llm_service():
    """Test LLMService directly."""
    print("[TEST] Testing LLMService...")

    try:
        llm = LLMService()

        prompt = """
You are RunBeat AI assistant. Parse the user's workout request into structured JSON.

User message: "Легке відновлення 30 хвилин"

Extract:
{
  "type": "steady|progressive|intervals|fartlek",
  "duration_minutes": <number>,
  "intensity": "low|moderate|high",
  "hr_zones": [<min>, <max>],
  "confidence": <0-1>,
  "needs_clarification": <bool>,
  "clarification_question": "<string if needed>"
}

Return ONLY valid JSON.
"""

        result = await llm.parse_workout(prompt=prompt)
        print("[OK] LLMService test passed!")
        print(f"Result type: {type(result).__name__}")
        print(f"Result: {result.model_dump() if hasattr(result, 'model_dump') else result}")
        return True

    except Exception as e:
        print(f"[ERROR] LLMService test failed: {e}")
        return False


async def test_chat_endpoint():
    """Test chat endpoint."""
    print("\n[TEST] Testing chat endpoint...")

    try:
        llm = LLMService()

        # Test case 1: Simple workout
        print("\nTest 1: Simple workout")
        request1 = ChatRequest(message="Легке відновлення 30 хвилин")
        response1 = await send_message(request1, llm)

        print(f"[OK] Test 1 passed!")
        print(f"Message: {response1.message}")
        print(f"Needs clarification: {response1.needs_clarification}")
        if response1.workout:
            print(f"Workout type: {response1.workout.type}")
            print(f"Duration: {response1.workout.duration_minutes} min")
            print(f"Intensity: {response1.workout.intensity}")

        # Test case 2: Workout requiring clarification
        print("\nTest 2: Workout requiring clarification")
        request2 = ChatRequest(message="Хочу пробігти 40 хв з інтервалами")
        response2 = await send_message(request2, llm)

        print(f"[OK] Test 2 passed!")
        print(f"Message: {response2.message}")
        print(f"Needs clarification: {response2.needs_clarification}")

        return True

    except Exception as e:
        print(f"[ERROR] Chat endpoint test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("=" * 50)
    print("Testing Chat Endpoints")
    print("=" * 50)

    # Test LLMService
    llm_result = await test_llm_service()

    if not llm_result:
        print("\n[ERROR] LLMService test failed. Check OpenAI API key.")
        sys.exit(1)

    # Test chat endpoint
    endpoint_result = await test_chat_endpoint()

    if not endpoint_result:
        print("\n[ERROR] Chat endpoint test failed.")
        sys.exit(1)

    print("\n" + "=" * 50)
    print("[SUCCESS] All tests passed!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())


"""
Manual test script for conversation flow with real OpenAI API.
Tests the problematic scenario that was reported by the user.
"""
import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000"
TEST_USER_ID = "test_manual_user_123"


async def test_problematic_scenario():
    """
    Test the problematic scenario:
    1. "інтервальна"
    2. "44 хвилин"
    3. "класика джаз"
    4. "так"
    5. "середня"

    Expected: Agent should NOT repeat questions.
    """
    print("=" * 80)
    print("🧪 TESTING PROBLEMATIC SCENARIO")
    print("=" * 80)

    messages = [
        "інтервальна",
        "44 хвилин",
        "класика джаз",
        "так",
        "середня"
    ]

    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, message in enumerate(messages, 1):
            print(f"\n📤 Message {i}: \"{message}\"")
            print("-" * 80)

            try:
                response = await client.post(
                    f"{BASE_URL}/chat/message",
                    json={
                        "user_id": TEST_USER_ID,
                        "message": message
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    ai_response = data.get("response", "No response")

                    print(f"📥 AI Response: {ai_response}")

                    # Check for problematic patterns
                    if i > 1 and "Яка планується тривалість та інтенсивність?" in ai_response:
                        print("⚠️  WARNING: Agent repeated the same question!")
                    else:
                        print("✅ Response looks good - no repetition detected")

                else:
                    print(f"❌ Error: Status {response.status_code}")
                    print(f"   Response: {response.text}")

            except Exception as e:
                print(f"❌ Exception: {e}")

            # Small delay between messages
            await asyncio.sleep(1)

    print("\n" + "=" * 80)
    print("🏁 TEST COMPLETED")
    print("=" * 80)


async def test_all_info_at_once():
    """
    Test when user provides all information at once.
    """
    print("\n" + "=" * 80)
    print("🧪 TESTING ALL INFO AT ONCE")
    print("=" * 80)

    message = "легка пробіжка 30 хвилин під рок"

    async with httpx.AsyncClient(timeout=30.0) as client:
        print(f"\n📤 Message: \"{message}\"")
        print("-" * 80)

        try:
            response = await client.post(
                f"{BASE_URL}/chat/message",
                json={
                    "user_id": f"{TEST_USER_ID}_2",
                    "message": message
                }
            )

            if response.status_code == 200:
                data = response.json()
                ai_response = data.get("response", "No response")

                print(f"📥 AI Response: {ai_response}")

                # Check if agent recognized all parameters
                if "30" in ai_response and any(word in ai_response.lower() for word in ["легка", "low"]):
                    print("✅ Agent recognized duration and intensity")
                else:
                    print("⚠️  Agent might have missed some parameters")

                if any(word in ai_response.lower() for word in ["створ", "create"]):
                    print("✅ Agent is ready to create workout")
                else:
                    print("⚠️  Agent didn't ask for confirmation")

            else:
                print(f"❌ Error: Status {response.status_code}")

        except Exception as e:
            print(f"❌ Exception: {e}")

    print("\n" + "=" * 80)
    print("🏁 TEST COMPLETED")
    print("=" * 80)


async def main():
    """Run all manual tests."""
    print("\n🚀 Starting manual conversation tests...")
    print("⏳ Make sure backend is running on http://localhost:8000\n")

    # Wait a bit for user to see the message
    await asyncio.sleep(2)

    # Test 1: Problematic scenario
    await test_problematic_scenario()

    # Wait between tests
    await asyncio.sleep(2)

    # Test 2: All info at once
    await test_all_info_at_once()

    print("\n✅ All manual tests completed!")
    print("\n📊 Summary:")
    print("   - Check if agent repeated questions (should NOT repeat)")
    print("   - Check if agent acknowledged each response")
    print("   - Check if agent created workout successfully")


if __name__ == "__main__":
    asyncio.run(main())


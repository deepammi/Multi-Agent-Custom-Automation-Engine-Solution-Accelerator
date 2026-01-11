#!/usr/bin/env python3
"""
Final Verification Test - Complete end-to-end test
"""
import asyncio
import aiohttp

async def test_final_verification():
    print("🎯 FINAL VERIFICATION TEST")
    print("=" * 80)
    
    query = "analyze all bills and communications with keyword TBI-001 or TBI Corp"
    
    async with aiohttp.ClientSession() as session:
        # 1. Submit query
        print("1️⃣ Submitting TBI analysis query...")
        async with session.post(
            "http://localhost:8000/api/v3/process_request",
            json={"description": query, "session_id": "final-test"}
        ) as response:
            data = await response.json()
            plan_id = data["plan_id"]
            print(f"   ✅ Plan created: {plan_id}")
        
        # 2. Wait for processing
        print("2️⃣ Waiting for agent processing...")
        await asyncio.sleep(20)
        
        # 3. Get results
        print("3️⃣ Retrieving results...")
        async with session.get(f"http://localhost:8000/api/v3/plan?plan_id={plan_id}") as response:
            if response.status == 200:
                plan_data = await response.json()
                
                plan = plan_data.get("plan", {})
                messages = plan_data.get("messages", [])
                
                print(f"   📋 Plan Status: {plan.get('status', 'unknown')}")
                print(f"   📨 Messages Retrieved: {len(messages)}")
                
                # 4. Check for TBI content
                tbi_messages = []
                total_content_length = 0
                
                for msg in messages:
                    content = msg.get("content", "")
                    total_content_length += len(content)
                    
                    if "TBI" in content.upper() or "TBC" in content.upper():
                        tbi_messages.append({
                            "agent": msg.get("agent_name", "Unknown"),
                            "length": len(content),
                            "preview": content[:100] + "..." if len(content) > 100 else content
                        })
                
                print(f"   📊 Total Content Length: {total_content_length} characters")
                print(f"   🔍 TBI-Related Messages: {len(tbi_messages)}")
                
                if tbi_messages:
                    print("\n4️⃣ TBI-Related Content Found:")
                    for i, msg in enumerate(tbi_messages, 1):
                        print(f"   {i}. {msg['agent']} Agent ({msg['length']} chars)")
                        print(f"      Preview: {msg['preview']}")
                
                # 5. Final assessment
                print("\n" + "="*80)
                print("🎯 FINAL ASSESSMENT")
                print("="*80)
                
                if len(messages) > 0:
                    print("✅ Messages are being saved to database")
                else:
                    print("❌ No messages found in database")
                
                if tbi_messages:
                    print("✅ TBI-related content is being captured and analyzed")
                else:
                    print("❌ No TBI-related content found")
                
                if total_content_length > 1000:
                    print("✅ Detailed agent responses are being saved")
                else:
                    print("❌ Agent responses appear to be truncated")
                
                if len(messages) > 0 and tbi_messages and total_content_length > 1000:
                    print("\n🎉 SUCCESS: System is working correctly!")
                    print("   - Agents are processing queries")
                    print("   - Messages are being saved to database")
                    print("   - TBI analysis is being performed")
                    print("   - Frontend can retrieve complete results")
                else:
                    print("\n⚠️  ISSUES DETECTED: System needs further investigation")
                
            else:
                print(f"   ❌ Failed to retrieve results: {response.status}")

if __name__ == "__main__":
    asyncio.run(test_final_verification())
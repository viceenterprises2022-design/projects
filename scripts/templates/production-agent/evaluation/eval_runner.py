import json
import asyncio
from security.adrian_init import AdrianSecurityHarness
from agent.graph import run_agent_graph
from evaluation.judges.accuracy_judge import AccuracyJudge

async def run_evaluation():
    print("====================================================")
    print("🚀 Starting Production AI Agent Safety & Intent Eval")
    print("====================================================")
    
    # Load dataset dynamically based on file location
    import os
    dataset_path = os.path.join(os.path.dirname(__file__), "golden_dataset.json")
    with open(dataset_path, "r") as f:
        dataset = json.load(f)
        
    harness = AdrianSecurityHarness(api_key="eval_key", mode="block")
    harness.initialize()
    judge = AccuracyJudge()
    
    passed_tests = 0
    total_tests = len(dataset)
    
    for i, test in enumerate(dataset):
        query = test["query"]
        expected_intent = test["expected_intent"]
        safety = test["safety"]
        
        print(f"\n[Test #{i+1}] Query: '{query}'")
        
        # Layer 4 pre-eval check
        security_verdict = harness.analyze_intent(query)
        
        predicted_intent = "general"
        is_blocked = security_verdict.get("action") == "BLOCK"
        
        if is_blocked:
            predicted_intent = "blocked"
            print(f" 🔒 Security Red-Line Caught: {security_verdict['reason']}")
        else:
            # Safe to run graph
            res = await run_agent_graph("eval_session", query, {})
            # Sample intent classification matching
            if "crm" in query.lower() or "customer" in query.lower():
                predicted_intent = "crm_lookup"
            elif "search" in query.lower() or "find" in query.lower():
                predicted_intent = "search"
            print(f" ✅ Execution completed successfully. Output snippet: {res['output'][:50]}...")
            
        score = judge.evaluate(expected_intent, predicted_intent)
        if score == 1.0:
            passed_tests += 1
            print(f" Result: PASSED (Intent matched expected: {expected_intent})")
        else:
            print(f" Result: FAILED (Expected: {expected_intent}, Predicted: {predicted_intent})")
            
    accuracy = (passed_tests / total_tests) * 100
    print("\n====================================================")
    print(f"📊 Evaluation Complete: {passed_tests}/{total_tests} Passed")
    print(f"📈 Total Accuracy: {accuracy:.2f}%")
    print("====================================================")

if __name__ == "__main__":
    asyncio.run(run_evaluation())

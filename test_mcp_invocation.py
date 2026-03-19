import requests
import json
import asyncio

async def test_mcp_tool_invocation():
    base_url = "http://127.0.0.1:8000"

    # Test fetch_patient_context_bundle
    tool_name = "fetch_patient_context_bundle"
    input_data = {"patient_id": "patient_001"}
    print(f"\nInvoking {tool_name} with input: {input_data}")
    response = requests.post(f"{base_url}/mcp/invoke-tool?tool_name={tool_name}", json=input_data)
    print(f"Response Status Code: {response.status_code}")
    print(f"Response Body: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    # Test build_digital_twin
    tool_name = "build_digital_twin"
    input_data = {"patient_id": "patient_001"}
    print(f"\nInvoking {tool_name} with input: {input_data}")
    response = requests.post(f"{base_url}/mcp/invoke-tool?tool_name={tool_name}", json=input_data)
    print(f"Response Status Code: {response.status_code}")
    print(f"Response Body: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    # Test run_scenario_projection
    tool_name = "run_scenario_projection"
    input_data = {"scenario_id": "scenario_xyz"}
    print(f"\nInvoking {tool_name} with input: {input_data}")
    response = requests.post(f"{base_url}/mcp/invoke-tool?tool_name={tool_name}", json=input_data)
    print(f"Response Status Code: {response.status_code}")
    print(f"Response Body: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    # Test compare_scenario_outcomes
    tool_name = "compare_scenario_outcomes"
    input_data = {"scenario_ids": ["scenario_a", "scenario_b"]}
    print(f"\nInvoking {tool_name} with input: {input_data}")
    response = requests.post(f"{base_url}/mcp/invoke-tool?tool_name={tool_name}", json=input_data)
    print(f"Response Status Code: {response.status_code}")
    print(f"Response Body: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    # Test explain_projection
    tool_name = "explain_projection"
    input_data = {"projection_id": "projection_123"}
    print(f"\nInvoking {tool_name} with input: {input_data}")
    response = requests.post(f"{base_url}/mcp/invoke-tool?tool_name={tool_name}", json=input_data)
    print(f"Response Status Code: {response.status_code}")
    print(f"Response Body: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    # Test non-existent tool
    tool_name = "non_existent_tool"
    input_data = {"some_key": "some_value"}
    print(f"\nInvoking {tool_name} with input: {input_data}")
    response = requests.post(f"{base_url}/mcp/invoke-tool?tool_name={tool_name}", json=input_data)
    print(f"Response Status Code: {response.status_code}")
    print(f"Response Body: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]

if __name__ == "__main__":
    asyncio.run(test_mcp_tool_invocation())

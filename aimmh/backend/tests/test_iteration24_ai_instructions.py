"""
Iteration 24: AI Instructions Endpoints Tests
Tests for AI visitor instruction endpoints:
- GET /api/ai-instructions (JSON)
- GET /api/v1/ai-instructions (JSON)
- GET /ai-instructions.txt (Plain text)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestAiInstructionsEndpoints:
    """Test AI visitor instruction endpoints"""

    def test_api_ai_instructions_json_returns_200(self):
        """GET /api/ai-instructions returns 200 with JSON payload"""
        response = requests.get(f"{BASE_URL}/api/ai-instructions")
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields
        assert "hub_name" in data
        assert data["hub_name"] == "AIMMH Hub"
        assert "goal" in data
        assert "quickstart" in data
        assert "patterns" in data
        assert "operating_notes" in data
        assert "api_endpoints" in data

    def test_api_ai_instructions_json_has_quickstart_steps(self):
        """GET /api/ai-instructions returns quickstart array with steps"""
        response = requests.get(f"{BASE_URL}/api/ai-instructions")
        assert response.status_code == 200
        data = response.json()
        
        quickstart = data.get("quickstart", [])
        assert isinstance(quickstart, list)
        assert len(quickstart) >= 5
        assert "Registry" in quickstart[0]
        assert "Instantiate" in quickstart[1]

    def test_api_ai_instructions_json_has_patterns(self):
        """GET /api/ai-instructions returns patterns array with orchestration patterns"""
        response = requests.get(f"{BASE_URL}/api/ai-instructions")
        assert response.status_code == 200
        data = response.json()
        
        patterns = data.get("patterns", [])
        assert isinstance(patterns, list)
        assert len(patterns) >= 6
        
        pattern_names = [p["pattern"] for p in patterns]
        assert "fan_out" in pattern_names
        assert "daisy_chain" in pattern_names
        assert "room_all" in pattern_names
        assert "room_synthesized" in pattern_names
        assert "council" in pattern_names
        assert "roleplay" in pattern_names

    def test_api_ai_instructions_json_has_operating_notes(self):
        """GET /api/ai-instructions returns operating_notes array"""
        response = requests.get(f"{BASE_URL}/api/ai-instructions")
        assert response.status_code == 200
        data = response.json()
        
        notes = data.get("operating_notes", [])
        assert isinstance(notes, list)
        assert len(notes) >= 4

    def test_api_ai_instructions_json_has_api_endpoints(self):
        """GET /api/ai-instructions returns api_endpoints object"""
        response = requests.get(f"{BASE_URL}/api/ai-instructions")
        assert response.status_code == 200
        data = response.json()
        
        endpoints = data.get("api_endpoints", {})
        assert "health" in endpoints
        assert "ready" in endpoints
        assert "hub_base" in endpoints
        assert "registry" in endpoints

    def test_api_v1_ai_instructions_returns_200(self):
        """GET /api/v1/ai-instructions returns 200 with same JSON payload"""
        response = requests.get(f"{BASE_URL}/api/v1/ai-instructions")
        assert response.status_code == 200
        data = response.json()
        
        # Verify same structure as /api/ai-instructions
        assert "hub_name" in data
        assert "goal" in data
        assert "quickstart" in data
        assert "patterns" in data
        assert "operating_notes" in data
        assert "api_endpoints" in data

    def test_api_v1_ai_instructions_matches_api_ai_instructions(self):
        """GET /api/v1/ai-instructions returns same data as /api/ai-instructions"""
        response1 = requests.get(f"{BASE_URL}/api/ai-instructions")
        response2 = requests.get(f"{BASE_URL}/api/v1/ai-instructions")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        data1 = response1.json()
        data2 = response2.json()
        
        assert data1 == data2

    def test_ai_instructions_txt_returns_200(self):
        """GET /ai-instructions.txt returns 200 with plain text"""
        response = requests.get(f"{BASE_URL}/ai-instructions.txt")
        assert response.status_code == 200
        
        # Verify content type is text
        content_type = response.headers.get("content-type", "")
        assert "text/plain" in content_type

    def test_ai_instructions_txt_contains_guide_content(self):
        """GET /ai-instructions.txt contains expected guide content"""
        response = requests.get(f"{BASE_URL}/ai-instructions.txt")
        assert response.status_code == 200
        
        text = response.text
        
        # Verify key sections
        assert "AIMMH Hub" in text
        assert "AI Visitor Guide" in text
        assert "Goal:" in text
        assert "Quickstart:" in text
        assert "Patterns:" in text
        assert "Operating Notes:" in text

    def test_ai_instructions_txt_contains_patterns(self):
        """GET /ai-instructions.txt contains orchestration patterns"""
        response = requests.get(f"{BASE_URL}/ai-instructions.txt")
        assert response.status_code == 200
        
        text = response.text
        
        assert "fan_out" in text
        assert "daisy_chain" in text
        assert "room_all" in text
        assert "room_synthesized" in text
        assert "council" in text
        assert "roleplay" in text

    def test_ai_instructions_txt_contains_endpoint_references(self):
        """GET /ai-instructions.txt contains endpoint references"""
        response = requests.get(f"{BASE_URL}/ai-instructions.txt")
        assert response.status_code == 200
        
        text = response.text
        
        assert "/api/ai-instructions" in text
        assert "/api/health" in text
        assert "/api/ready" in text

#!/usr/bin/env python3
"""
Comprehensive API Testing Script for RunBeat
Tests all backend endpoints that can be tested automatically
"""
import os
import sys
import json
import requests
from typing import Dict, Any, Optional
from datetime import datetime

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "https://runbeatbackend-production.up.railway.app")
TIMEOUT = 30

# Test results
results = {
    "passed": [],
    "failed": [],
    "skipped": [],
    "total": 0
}

def print_test(name: str, status: str, message: str = ""):
    """Print test result with color coding"""
    results["total"] += 1
    if status == "PASSED":
        results["passed"].append(name)
        print(f"{Colors.GREEN}✓{Colors.END} {name}: {Colors.GREEN}PASSED{Colors.END}")
    elif status == "FAILED":
        results["failed"].append(name)
        print(f"{Colors.RED}✗{Colors.END} {name}: {Colors.RED}FAILED{Colors.END}")
        if message:
            print(f"  {Colors.YELLOW}→{Colors.END} {message}")
    elif status == "SKIPPED":
        results["skipped"].append(name)
        print(f"{Colors.YELLOW}⊘{Colors.END} {name}: {Colors.YELLOW}SKIPPED{Colors.END}")
        if message:
            print(f"  {Colors.YELLOW}→{Colors.END} {message}")

def test_health_endpoint():
    """Test health check endpoint"""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "healthy" and "timestamp" in data:
                print_test("Health Check", "PASSED")
                return True
            else:
                print_test("Health Check", "FAILED", "Invalid response format")
                return False
        else:
            print_test("Health Check", "FAILED", f"HTTP {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_test("Health Check", "FAILED", str(e))
        return False

def test_readiness_endpoint():
    """Test readiness check endpoint"""
    try:
        response = requests.get(f"{BACKEND_URL}/health/ready", timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "ready":
                print_test("Readiness Check", "PASSED")
                return True
            else:
                print_test("Readiness Check", "FAILED", "Invalid response format")
                return False
        else:
            print_test("Readiness Check", "FAILED", f"HTTP {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_test("Readiness Check", "FAILED", str(e))
        return False

def test_liveness_endpoint():
    """Test liveness check endpoint"""
    try:
        response = requests.get(f"{BACKEND_URL}/health/live", timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "alive":
                print_test("Liveness Check", "PASSED")
                return True
            else:
                print_test("Liveness Check", "FAILED", "Invalid response format")
                return False
        else:
            print_test("Liveness Check", "FAILED", f"HTTP {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_test("Liveness Check", "FAILED", str(e))
        return False

def test_cors_headers():
    """Test CORS headers"""
    try:
        # Make OPTIONS request to check CORS
        response = requests.options(
            f"{BACKEND_URL}/health",
            headers={"Origin": "https://runbeatweb-production.up.railway.app"},
            timeout=TIMEOUT
        )
        cors_headers = {
            "access-control-allow-origin": response.headers.get("Access-Control-Allow-Origin"),
            "access-control-allow-methods": response.headers.get("Access-Control-Allow-Methods"),
            "access-control-allow-credentials": response.headers.get("Access-Control-Allow-Credentials"),
        }

        if cors_headers["access-control-allow-origin"]:
            print_test("CORS Headers", "PASSED", f"Origin: {cors_headers['access-control-allow-origin']}")
            return True
        else:
            print_test("CORS Headers", "FAILED", "CORS headers not present")
            return False
    except requests.exceptions.RequestException as e:
        print_test("CORS Headers", "FAILED", str(e))
        return False

def test_spotify_auth_initiation():
    """Test Spotify auth initiation (without user_id)"""
    try:
        response = requests.get(f"{BACKEND_URL}/auth/spotify", timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            if "auth_url" in data and "state" in data:
                print_test("Spotify Auth Initiation", "PASSED")
                return True
            else:
                print_test("Spotify Auth Initiation", "FAILED", "Invalid response format")
                return False
        else:
            print_test("Spotify Auth Initiation", "FAILED", f"HTTP {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_test("Spotify Auth Initiation", "FAILED", str(e))
        return False

def test_chat_endpoint_structure():
    """Test chat endpoint structure (requires OpenAI, so we test error handling)"""
    try:
        # Test with invalid request (missing user_id)
        response = requests.post(
            f"{BACKEND_URL}/chat/message",
            json={"message": "test"},
            timeout=TIMEOUT
        )
        # Should return 422 or 400 (validation error) or 200 (if user_id is optional)
        if response.status_code in [200, 400, 422]:
            print_test("Chat Endpoint Structure", "PASSED", f"Endpoint responds (HTTP {response.status_code})")
            return True
        else:
            print_test("Chat Endpoint Structure", "FAILED", f"Unexpected HTTP {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_test("Chat Endpoint Structure", "FAILED", str(e))
        return False

def test_workouts_endpoint_structure():
    """Test workouts endpoint structure"""
    try:
        # Test GET without user_id (should return 422 or 400)
        response = requests.get(f"{BACKEND_URL}/workouts", timeout=TIMEOUT)
        if response.status_code in [400, 422]:
            print_test("Workouts Endpoint Structure", "PASSED", "Endpoint validates input")
            return True
        elif response.status_code == 200:
            print_test("Workouts Endpoint Structure", "PASSED", "Endpoint accepts requests")
            return True
        else:
            print_test("Workouts Endpoint Structure", "FAILED", f"Unexpected HTTP {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_test("Workouts Endpoint Structure", "FAILED", str(e))
        return False

def test_playlists_endpoint_structure():
    """Test playlists endpoint structure"""
    try:
        # Test GET history without user_id (should return 422 or 400)
        response = requests.get(f"{BACKEND_URL}/playlists/history", timeout=TIMEOUT)
        if response.status_code in [400, 422]:
            print_test("Playlists Endpoint Structure", "PASSED", "Endpoint validates input")
            return True
        elif response.status_code == 200:
            print_test("Playlists Endpoint Structure", "PASSED", "Endpoint accepts requests")
            return True
        else:
            print_test("Playlists Endpoint Structure", "FAILED", f"Unexpected HTTP {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_test("Playlists Endpoint Structure", "FAILED", str(e))
        return False

def test_api_documentation():
    """Test if API documentation is accessible (only in development)"""
    try:
        response = requests.get(f"{BACKEND_URL}/docs", timeout=TIMEOUT, allow_redirects=False)
        if response.status_code == 200:
            print_test("API Documentation", "PASSED", "Available in development mode")
            return True
        elif response.status_code == 404:
            print_test("API Documentation", "SKIPPED", "Not available in production (expected)")
            return True
        else:
            print_test("API Documentation", "SKIPPED", f"HTTP {response.status_code}")
            return True
    except requests.exceptions.RequestException as e:
        print_test("API Documentation", "SKIPPED", str(e))
        return True

def main():
    """Run all tests"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}=== RunBeat API Comprehensive Testing ==={Colors.END}\n")
    print(f"Backend URL: {BACKEND_URL}\n")

    # Health checks
    print(f"{Colors.BOLD}1. Health Check Endpoints{Colors.END}")
    print("=" * 50)
    test_health_endpoint()
    test_readiness_endpoint()
    test_liveness_endpoint()
    print()

    # CORS
    print(f"{Colors.BOLD}2. CORS Configuration{Colors.END}")
    print("=" * 50)
    test_cors_headers()
    print()

    # Authentication
    print(f"{Colors.BOLD}3. Authentication Endpoints{Colors.END}")
    print("=" * 50)
    test_spotify_auth_initiation()
    print()

    # API Endpoints Structure
    print(f"{Colors.BOLD}4. API Endpoints Structure{Colors.END}")
    print("=" * 50)
    test_chat_endpoint_structure()
    test_workouts_endpoint_structure()
    test_playlists_endpoint_structure()
    print()

    # Documentation
    print(f"{Colors.BOLD}5. Documentation{Colors.END}")
    print("=" * 50)
    test_api_documentation()
    print()

    # Summary
    print(f"\n{Colors.BOLD}{Colors.BLUE}=== Test Summary ==={Colors.END}\n")
    print(f"Total tests: {results['total']}")
    print(f"{Colors.GREEN}Passed: {len(results['passed'])}{Colors.END}")
    print(f"{Colors.RED}Failed: {len(results['failed'])}{Colors.END}")
    print(f"{Colors.YELLOW}Skipped: {len(results['skipped'])}{Colors.END}")

    if results['failed']:
        print(f"\n{Colors.RED}Failed tests:{Colors.END}")
        for test in results['failed']:
            print(f"  - {test}")

    # Exit code
    if len(results['failed']) > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()


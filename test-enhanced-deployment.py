#!/usr/bin/env python3
"""
Enhanced Strands Deployment Test Script
Tests all endpoints and functionality after deployment
"""

import json
import requests
import time
import sys
import boto3
from typing import Dict, Any, Optional

# Colors for output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color

def print_status(message: str):
    print(f"{Colors.BLUE}[INFO]{Colors.NC} {message}")

def print_success(message: str):
    print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {message}")

def print_warning(message: str):
    print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {message}")

def print_error(message: str):
    print(f"{Colors.RED}[ERROR]{Colors.NC} {message}")

def print_test(message: str):
    print(f"{Colors.PURPLE}[TEST]{Colors.NC} {message}")

class EnhancedStrandsTestSuite:
    def __init__(self, stack_name: str = "one-piece-tcg-strands-enhanced"):
        self.stack_name = stack_name
        self.region = "us-east-1"
        self.endpoints = {}
        self.session = requests.Session()
        self.session.timeout = 30
        
    def get_stack_outputs(self) -> bool:
        """Retrieve stack outputs from CloudFormation"""
        try:
            print_status("Retrieving stack outputs...")
            
            cf_client = boto3.client('cloudformation', region_name=self.region)
            response = cf_client.describe_stacks(StackName=self.stack_name)
            
            if not response['Stacks']:
                print_error(f"Stack {self.stack_name} not found")
                return False
                
            outputs = response['Stacks'][0].get('Outputs', [])
            
            for output in outputs:
                key = output['OutputKey']
                value = output['OutputValue']
                self.endpoints[key] = value
                print_success(f"{key}: {value}")
            
            return True
            
        except Exception as e:
            print_error(f"Failed to get stack outputs: {str(e)}")
            return False
    
    def test_health_endpoint(self) -> bool:
        """Test the health check endpoint"""
        print_test("Testing health endpoint...")
        
        try:
            health_url = self.endpoints.get('HealthEndpoint')
            if not health_url:
                print_error("Health endpoint not found in stack outputs")
                return False
            
            response = self.session.get(health_url)
            
            if response.status_code == 200:
                data = response.json()
                print_success(f"Health check passed: {data.get('status', 'unknown')}")
                
                # Check features
                features = data.get('features', [])
                print_status(f"Available features: {len(features)}")
                for feature in features:
                    print(f"  ✅ {feature}")
                
                return True
            else:
                print_error(f"Health check failed with status {response.status_code}")
                return False
                
        except Exception as e:
            print_error(f"Health check error: {str(e)}")
            return False
    
    def test_chat_endpoint_basic(self) -> bool:
        """Test basic chat functionality"""
        print_test("Testing basic chat endpoint...")
        
        try:
            chat_url = self.endpoints.get('ChatEndpoint')
            if not chat_url:
                print_error("Chat endpoint not found in stack outputs")
                return False
            
            test_message = "Hello! I'm testing the enhanced Strands agent."
            
            payload = {
                "message": test_message,
                "sessionId": f"test-session-{int(time.time())}"
            }
            
            response = self.session.post(
                chat_url,
                json=payload,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                agent_response = data.get('response', '')
                
                print_success("Chat endpoint working!")
                print_status(f"Agent response preview: {agent_response[:100]}...")
                
                # Check for pirate theme
                pirate_indicators = ['🏴‍☠️', 'Ahoy', 'matey', 'treasure', 'pirate']
                has_pirate_theme = any(indicator in agent_response for indicator in pirate_indicators)
                
                if has_pirate_theme:
                    print_success("✅ Pirate theme detected in response")
                else:
                    print_warning("⚠️ Pirate theme not clearly detected")
                
                # Check tools availability
                tools = data.get('tools_available', [])
                if tools:
                    print_success(f"✅ {len(tools)} tools available: {', '.join(tools)}")
                else:
                    print_warning("⚠️ No tools reported as available")
                
                return True
            else:
                print_error(f"Chat request failed with status {response.status_code}")
                print_error(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print_error(f"Chat test error: {str(e)}")
            return False
    
    def test_deck_recommendation(self) -> bool:
        """Test competitive deck recommendation functionality"""
        print_test("Testing deck recommendation tool...")
        
        try:
            chat_url = self.endpoints.get('ChatEndpoint')
            if not chat_url:
                return False
            
            test_message = "Show me a Red Shanks deck for OP09 West region"
            
            payload = {
                "message": test_message,
                "sessionId": f"deck-test-{int(time.time())}"
            }
            
            response = self.session.post(
                chat_url,
                json=payload,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                agent_response = data.get('response', '')
                
                # Check for deck-related content
                deck_indicators = ['deck', 'leader', 'decklist', 'tournament', 'gumgum.gg']
                has_deck_content = any(indicator.lower() in agent_response.lower() for indicator in deck_indicators)
                
                if has_deck_content:
                    print_success("✅ Deck recommendation functionality working")
                    print_status("Response contains deck-related content")
                else:
                    print_warning("⚠️ Deck recommendation may not be working properly")
                
                # Check for gumgum.gg attribution
                if 'gumgum.gg' in agent_response:
                    print_success("✅ Proper gumgum.gg attribution found")
                else:
                    print_warning("⚠️ gumgum.gg attribution not found")
                
                return True
            else:
                print_error(f"Deck recommendation test failed with status {response.status_code}")
                return False
                
        except Exception as e:
            print_error(f"Deck recommendation test error: {str(e)}")
            return False
    
    def test_shopify_integration(self) -> bool:
        """Test Shopify integration functionality"""
        print_test("Testing Shopify integration...")
        
        try:
            chat_url = self.endpoints.get('ChatEndpoint')
            if not chat_url:
                return False
            
            test_message = "Do you have any One Piece booster packs in stock?"
            
            payload = {
                "message": test_message,
                "sessionId": f"shopify-test-{int(time.time())}"
            }
            
            response = self.session.post(
                chat_url,
                json=payload,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                agent_response = data.get('response', '')
                
                # Check for inventory-related content
                inventory_indicators = ['stock', 'inventory', 'available', 'price', 'cart']
                has_inventory_content = any(indicator.lower() in agent_response.lower() for indicator in inventory_indicators)
                
                if has_inventory_content:
                    print_success("✅ Shopify integration responding")
                else:
                    print_warning("⚠️ Shopify integration may not be fully functional")
                
                return True
            else:
                print_error(f"Shopify integration test failed with status {response.status_code}")
                return False
                
        except Exception as e:
            print_error(f"Shopify integration test error: {str(e)}")
            return False
    
    def test_websocket_connectivity(self) -> bool:
        """Test WebSocket endpoint connectivity (basic check)"""
        print_test("Testing WebSocket endpoint...")
        
        try:
            websocket_url = self.endpoints.get('WebSocketApiUrl')
            if not websocket_url:
                print_error("WebSocket endpoint not found in stack outputs")
                return False
            
            print_success(f"WebSocket endpoint available: {websocket_url}")
            print_status("Note: Full WebSocket testing requires a WebSocket client")
            print_status("Use a tool like wscat to test: wscat -c {websocket_url}")
            
            return True
            
        except Exception as e:
            print_error(f"WebSocket test error: {str(e)}")
            return False
    
    def run_all_tests(self) -> bool:
        """Run the complete test suite"""
        print(f"{Colors.CYAN}🏴‍☠️ Enhanced Strands Deployment Test Suite{Colors.NC}")
        print("=" * 50)
        
        # Get stack outputs
        if not self.get_stack_outputs():
            return False
        
        print("\n" + "=" * 50)
        
        tests = [
            ("Health Check", self.test_health_endpoint),
            ("Basic Chat", self.test_chat_endpoint_basic),
            ("Deck Recommendation", self.test_deck_recommendation),
            ("Shopify Integration", self.test_shopify_integration),
            ("WebSocket Connectivity", self.test_websocket_connectivity)
        ]
        
        results = []
        
        for test_name, test_func in tests:
            print(f"\n{Colors.CYAN}--- {test_name} ---{Colors.NC}")
            try:
                result = test_func()
                results.append((test_name, result))
                if result:
                    print_success(f"{test_name} PASSED ✅")
                else:
                    print_error(f"{test_name} FAILED ❌")
            except Exception as e:
                print_error(f"{test_name} ERROR: {str(e)}")
                results.append((test_name, False))
        
        # Summary
        print(f"\n{Colors.CYAN}🏴‍☠️ Test Results Summary{Colors.NC}")
        print("=" * 50)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name}: {status}")
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print_success("🎉 All tests passed! The enhanced deployment is working correctly!")
            return True
        else:
            print_warning(f"⚠️ {total - passed} test(s) failed. Check the logs above for details.")
            return False

def main():
    """Main test execution"""
    if len(sys.argv) > 1:
        stack_name = sys.argv[1]
    else:
        stack_name = "one-piece-tcg-strands-enhanced"
    
    print(f"Testing stack: {stack_name}")
    
    test_suite = EnhancedStrandsTestSuite(stack_name)
    success = test_suite.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

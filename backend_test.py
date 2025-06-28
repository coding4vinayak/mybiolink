import requests
import unittest
import random
import string
import time
import sys
from datetime import datetime

# Backend URL from frontend .env
BACKEND_URL = "https://68881b55-dbc4-4481-ba19-63fdeafac5ea.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

def random_string(length=8):
    """Generate a random string for testing"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

class LinkBioAPITest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test data once for all tests"""
        cls.timestamp = int(time.time())
        cls.test_email = f"test_{cls.timestamp}@example.com"
        cls.test_username = f"test_user_{cls.timestamp}"
        cls.test_password = "TestPassword123!"
        cls.token = None
        cls.user_id = None
        cls.linkpage_id = None
        cls.link_id = None
        
        print(f"\n🔍 TESTING WITH USER: {cls.test_username} / {cls.test_email}")
        print(f"🔍 BACKEND URL: {API_URL}")
    
    def test_01_signup(self):
        """Test user signup"""
        print(f"\n🔍 Testing signup with {self.test_email} / {self.test_username}")
        
        response = requests.post(f"{API_URL}/signup", json={
            "email": self.test_email,
            "username": self.test_username,
            "password": self.test_password
        })
        
        self.assertEqual(response.status_code, 200, f"Signup failed: {response.text}")
        data = response.json()
        
        # Verify response structure
        self.assertIn("access_token", data, "No access token in response")
        self.assertIn("user", data, "No user data in response")
        self.assertEqual(data["user"]["email"], self.test_email)
        self.assertEqual(data["user"]["username"], self.test_username)
        
        # Save token for subsequent tests
        self.token = data["access_token"]
        self.user_id = data["user"]["id"]
        
        print(f"✅ Signup successful - User ID: {self.user_id}")
    
    def test_02_login(self):
        """Test user login"""
        print(f"\n🔍 Testing login with {self.test_email}")
        
        response = requests.post(f"{API_URL}/login", json={
            "email": self.test_email,
            "password": self.test_password
        })
        
        self.assertEqual(response.status_code, 200, f"Login failed: {response.text}")
        data = response.json()
        
        # Verify response
        self.assertIn("access_token", data)
        self.assertIn("user", data)
        self.assertEqual(data["user"]["email"], self.test_email)
        
        # Update token
        self.token = data["access_token"]
        print("✅ Login successful")
    
    def test_03_get_current_user(self):
        """Test getting current user info"""
        print("\n🔍 Testing get current user")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{API_URL}/me", headers=headers)
        
        self.assertEqual(response.status_code, 200, f"Get user failed: {response.text}")
        data = response.json()
        
        # Verify user data
        self.assertEqual(data["email"], self.test_email)
        self.assertEqual(data["username"], self.test_username)
        self.assertEqual(data["id"], self.user_id)
        
        print("✅ Get current user successful")
    
    def test_04_create_linkpage(self):
        """Test creating a link page"""
        print("\n🔍 Testing create link page")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.post(f"{API_URL}/linkpage", json={
            "title": f"{self.test_username}'s Links",
            "description": "My awesome links",
            "theme_color": "#3B82F6"
        }, headers=headers)
        
        self.assertEqual(response.status_code, 200, f"Create link page failed: {response.text}")
        data = response.json()
        
        # Verify link page data
        self.assertIn("id", data)
        self.assertEqual(data["user_id"], self.user_id)
        self.assertEqual(data["username"], self.test_username)
        self.assertEqual(data["title"], f"{self.test_username}'s Links")
        
        self.linkpage_id = data["id"]
        print(f"✅ Link page created - ID: {self.linkpage_id}")
    
    def test_05_get_my_linkpage(self):
        """Test getting user's link page"""
        print("\n🔍 Testing get my link page")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{API_URL}/linkpage/my", headers=headers)
        
        self.assertEqual(response.status_code, 200, f"Get link page failed: {response.text}")
        data = response.json()
        
        # Verify link page data
        self.assertEqual(data["id"], self.linkpage_id)
        self.assertEqual(data["user_id"], self.user_id)
        self.assertEqual(data["username"], self.test_username)
        
        print("✅ Get link page successful")
    
    def test_06_update_linkpage(self):
        """Test updating link page"""
        print("\n🔍 Testing update link page")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        new_title = f"Updated {self.test_username}'s Links"
        response = requests.put(f"{API_URL}/linkpage", json={
            "title": new_title,
            "theme_color": "#EF4444"  # Red theme
        }, headers=headers)
        
        self.assertEqual(response.status_code, 200, f"Update link page failed: {response.text}")
        data = response.json()
        
        # Verify updated data
        self.assertEqual(data["title"], new_title)
        self.assertEqual(data["theme_color"], "#EF4444")
        
        print("✅ Link page updated successfully")
    
    def test_07_add_link(self):
        """Test adding a link"""
        print("\n🔍 Testing add link")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.post(f"{API_URL}/linkpage/links", json={
            "title": "My GitHub",
            "url": "https://github.com",
            "icon": "💻"
        }, headers=headers)
        
        self.assertEqual(response.status_code, 200, f"Add link failed: {response.text}")
        data = response.json()
        
        # Verify link data
        self.assertIn("id", data)
        self.assertEqual(data["title"], "My GitHub")
        self.assertEqual(data["url"], "https://github.com")
        self.assertEqual(data["icon"], "💻")
        
        self.link_id = data["id"]
        print(f"✅ Link added - ID: {self.link_id}")
    
    def test_08_update_link(self):
        """Test updating a link"""
        print(f"\n🔍 Testing update link {self.link_id}")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.put(f"{API_URL}/linkpage/links/{self.link_id}", json={
            "title": "Updated GitHub",
            "url": "https://github.com",
            "icon": "🌟"
        }, headers=headers)
        
        self.assertEqual(response.status_code, 200, f"Update link failed: {response.text}")
        data = response.json()
        
        # Verify response
        self.assertEqual(data["message"], "Link updated successfully")
        
        print("✅ Link updated successfully")
    
    def test_09_get_public_linkpage(self):
        """Test getting public link page"""
        print(f"\n🔍 Testing get public link page for {self.test_username}")
        
        response = requests.get(f"{API_URL}/linkpage/{self.test_username}")
        
        self.assertEqual(response.status_code, 200, f"Get public link page failed: {response.text}")
        data = response.json()
        
        # Verify public link page
        self.assertEqual(data["username"], self.test_username)
        self.assertIn("links", data)
        
        # Verify our link is in the page
        link_found = False
        for link in data["links"]:
            if link["id"] == self.link_id:
                link_found = True
                self.assertEqual(link["title"], "Updated GitHub")
                self.assertEqual(link["icon"], "🌟")
        
        self.assertTrue(link_found, "Added link not found in public page")
        print("✅ Public link page retrieved successfully")
    
    def test_10_track_link_click(self):
        """Test tracking link click"""
        print(f"\n🔍 Testing track link click for {self.link_id}")
        
        response = requests.post(f"{API_URL}/linkpage/links/{self.link_id}/click")
        
        self.assertEqual(response.status_code, 200, f"Track click failed: {response.text}")
        data = response.json()
        
        # Verify response
        self.assertEqual(data["message"], "Click tracked")
        
        # Verify click count increased
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{API_URL}/linkpage/my", headers=headers)
        data = response.json()
        
        link_found = False
        for link in data["links"]:
            if link["id"] == self.link_id:
                link_found = True
                self.assertGreaterEqual(link["clicks"], 1, "Click count not increased")
        
        self.assertTrue(link_found, "Link not found after click tracking")
        print("✅ Link click tracked successfully")
    
    def test_11_delete_link(self):
        """Test deleting a link"""
        print(f"\n🔍 Testing delete link {self.link_id}")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.delete(f"{API_URL}/linkpage/links/{self.link_id}", headers=headers)
        
        self.assertEqual(response.status_code, 200, f"Delete link failed: {response.text}")
        data = response.json()
        
        # Verify response
        self.assertEqual(data["message"], "Link deleted successfully")
        
        # Verify link is deleted
        response = requests.get(f"{API_URL}/linkpage/my", headers=headers)
        data = response.json()
        
        for link in data["links"]:
            self.assertNotEqual(link["id"], self.link_id, "Link not deleted")
        
        print("✅ Link deleted successfully")

if __name__ == "__main__":
    # Create a test suite with tests in order
    test_suite = unittest.TestSuite()
    test_suite.addTest(LinkBioAPITest('test_01_signup'))
    test_suite.addTest(LinkBioAPITest('test_02_login'))
    test_suite.addTest(LinkBioAPITest('test_03_get_current_user'))
    test_suite.addTest(LinkBioAPITest('test_04_create_linkpage'))
    test_suite.addTest(LinkBioAPITest('test_05_get_my_linkpage'))
    test_suite.addTest(LinkBioAPITest('test_06_update_linkpage'))
    test_suite.addTest(LinkBioAPITest('test_07_add_link'))
    test_suite.addTest(LinkBioAPITest('test_08_update_link'))
    test_suite.addTest(LinkBioAPITest('test_09_get_public_linkpage'))
    test_suite.addTest(LinkBioAPITest('test_10_track_link_click'))
    test_suite.addTest(LinkBioAPITest('test_11_delete_link'))
    
    # Run the tests
    result = unittest.TextTestRunner().run(test_suite)
    
    # Return non-zero exit code if tests failed
    sys.exit(not result.wasSuccessful())
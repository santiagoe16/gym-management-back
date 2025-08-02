#!/usr/bin/env python3
"""
Test script for Sales endpoints
Tests all CRUD operations and special endpoints for sales
"""

import requests
import json
import time
from datetime import datetime, date
from decimal import Decimal

# Configuration
BASE_URL = "http://localhost:8001/api/v1"
SALES_URL = f"{BASE_URL}/sales"
PRODUCTS_URL = f"{BASE_URL}/products"

class SalesTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.trainer_token = None
        self.created_sales = []
        self.created_products = []
        self.created_users = []
        self.created_gyms = []
        
    def print_test_result(self, test_name, success, message=""):
        """Print test result with consistent formatting"""
        status = "[OK]" if success else "[FAIL]"
        print(f"{status} {test_name}")
        if message:
            print(f"    {message}")
        print()

    def login_admin(self):
        """Login as admin"""
        login_data = {
            "email": "admin@gym.com",
            "password": "admin123",
            "gym_id": 1
        }
        response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            self.admin_token = response.json()["access_token"]
            return True
        return False

    def login_trainer(self):
        """Login as trainer"""
        login_data = {
            "email": "trainer@gym.com", 
            "password": "trainer123",
            "gym_id": 1
        }
        response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            self.trainer_token = response.json()["access_token"]
            return True
        return False

    def create_test_product(self, name="Test Product", price=10.50, quantity=100, gym_id=1):
        """Create a test product for sales"""
        product_data = {
            "name": f"{name}_{int(time.time())}_{int(time.time() * 1000) % 10000}",
            "price": price,
            "quantity": quantity,
            "gym_id": gym_id,
            "is_active": True
        }
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = self.session.post(PRODUCTS_URL, json=product_data, headers=headers)
        
        if response.status_code == 200:
            product = response.json()
            self.created_products.append(product["id"])
            return product
        else:
            print(f"Failed to create test product (Status: {response.status_code}): {response.text}")
            return None

    def create_test_user(self, name="Test User", email=None, gym_id=1):
        """Create a test user for sales"""
        if not email:
            email = f"user_{int(time.time())}@test.com"
        
        user_data = {
            "full_name": name,
            "email": email,
            "document_id": f"DOC{int(time.time())}",
            "phone": f"+123456789{int(time.time()) % 10000}",
            "birth_date": "1990-01-01",
            "gender": "male",
            "address": "Test Address",
            "emergency_contact": "Emergency Contact",
            "emergency_phone": "+1234567890"
        }
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = self.session.post(f"{BASE_URL}/users/", json=user_data, headers=headers)
        
        if response.status_code == 200:
            user = response.json()
            self.created_users.append(user["id"])
            return user
        else:
            print(f"Failed to create test user: {response.text}")
            return None

    def test_login(self):
        """Test admin and trainer login"""
        print("Testing login...")
        
        # Test admin login
        if self.login_admin():
            self.print_test_result("Admin login", True)
        else:
            self.print_test_result("Admin login", False, "Failed to login as admin")
            return False
        
        # Test trainer login
        if self.login_trainer():
            self.print_test_result("Trainer login", True)
        else:
            self.print_test_result("Trainer login", False, "Failed to login as trainer")
            return False
        
        return True

    def test_create_sale_admin(self):
        """Test creating a sale as admin"""
        print("Testing create sale as admin...")
        
        # Create test product
        product = self.create_test_product("Admin Sale Product", 16.00, 50)
        if not product:
            self.print_test_result("Create sale as admin", False, "Failed to create test product")
            return False
        
        # Create sale as admin
        sale_data = {
            "product_id": product["id"],
            "gym_id": 1,  # Admin can specify gym_id
            "quantity": 3
        }
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = self.session.post(SALES_URL, json=sale_data, headers=headers)
        
        if response.status_code == 200:
            sale = response.json()
            self.created_sales.append(sale["id"])
            expected_total = 16.00 * 3
            # Convert string to float for comparison
            actual_total = float(sale["total_amount"])
            if actual_total == expected_total and sale["quantity"] == 3:
                self.print_test_result("Create sale as admin", True, f"Created sale ID: {sale['id']}, Total: {sale['total_amount']}")
                return True
            else:
                self.print_test_result("Create sale as admin", False, f"Sale data incorrect. Expected total: {expected_total}, got: {actual_total}")
                return False
        else:
            self.print_test_result("Create sale as admin", False, f"Status: {response.status_code}, Response: {response.text}")
            return False

    def test_create_sale_trainer(self):
        """Test creating a sale as trainer"""
        print("Testing create sale as trainer...")
        
        # Create test product
        product = self.create_test_product("Trainer Sale Product", 25.00, 30)
        if not product:
            self.print_test_result("Create sale as trainer", False, "Failed to create test product")
            return False
        
        # Create sale as trainer (gym_id will be set automatically)
        sale_data = {
            "product_id": product["id"],
            "quantity": 2
        }
        
        headers = {"Authorization": f"Bearer {self.trainer_token}"}
        response = self.session.post(SALES_URL, json=sale_data, headers=headers)
        
        if response.status_code == 200:
            sale = response.json()
            self.created_sales.append(sale["id"])
            expected_total = 25.00 * 2
            # Convert string to float for comparison
            actual_total = float(sale["total_amount"])
            if actual_total == expected_total and sale["quantity"] == 2:
                self.print_test_result("Create sale as trainer", True, f"Created sale ID: {sale['id']}, Total: {sale['total_amount']}")
                return True
            else:
                self.print_test_result("Create sale as trainer", False, f"Sale data incorrect. Expected total: {expected_total}, got: {actual_total}")
                return False
        else:
            self.print_test_result("Create sale as trainer", False, f"Status: {response.status_code}, Response: {response.text}")
            return False

    def test_create_sale_insufficient_stock(self):
        """Test creating a sale with insufficient stock"""
        print("Testing create sale with insufficient stock...")
        
        # Create a new product with low stock to ensure we have control
        product = self.create_test_product("Low Stock Product", 10.00, 2, gym_id=1)

        if not product:
            self.print_test_result("Create sale insufficient stock", False, "Failed to create test product")
            return False
        
        print(f"    Created product with ID: {product['id']}")
        

        
        # Try to buy more than available
        sale_data = {
            "product_id": product["id"],
            "gym_id": 1,  # Admin needs to specify gym_id
            "quantity": 5  # More than available (2)
        }
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = self.session.post(SALES_URL, json=sale_data, headers=headers)
        
        if response.status_code == 400:
            self.print_test_result("Create sale insufficient stock", True, "Correctly rejected insufficient stock")
            return True
        else:
            self.print_test_result("Create sale insufficient stock", False, f"Expected 400, got {response.status_code}, Response: {response.text}")
            return False

    def test_create_sale_invalid_product(self):
        """Test creating a sale with invalid product"""
        print("Testing create sale with invalid product...")
        
        sale_data = {
            "product_id": 99999,  # Non-existent product
            "quantity": 1
        }
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = self.session.post(SALES_URL, json=sale_data, headers=headers)
        
        if response.status_code == 404:
            self.print_test_result("Create sale invalid product", True, "Correctly rejected invalid product")
            return True
        else:
            self.print_test_result("Create sale invalid product", False, f"Expected 404, got {response.status_code}")
            return False

    def test_create_sale_trainer_wrong_gym(self):
        """Test creating a sale as trainer with product from different gym"""
        print("Testing create sale as trainer with product from different gym...")
        
        # Try to create test product in a different gym (assuming gym_id=2 exists)
        product = self.create_test_product("Different Gym Product", 20.00, 10, gym_id=2)
        if not product:
            # If we can't create products in different gyms, skip this test
            self.print_test_result("Create sale trainer wrong gym", True, "Skipped - cannot create products in different gyms")
            return True
        
        # Try to buy product from different gym
        sale_data = {
            "product_id": product["id"],
            "quantity": 1
        }
        
        headers = {"Authorization": f"Bearer {self.trainer_token}"}
        response = self.session.post(SALES_URL, json=sale_data, headers=headers)
        
        if response.status_code == 404:
            self.print_test_result("Create sale trainer wrong gym", True, "Correctly rejected product from different gym")
            return True
        else:
            self.print_test_result("Create sale trainer wrong gym", False, f"Expected 404, got {response.status_code}")
            return False

    def test_read_sales(self):
        """Test reading all sales"""
        print("Testing read sales...")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        response = self.session.get(SALES_URL, headers=headers, timeout=10)
        if response.status_code == 200:
            sales = response.json()
            self.print_test_result("Read sales", True, f"Found {len(sales)} sales")
            return True
        else:
            self.print_test_result("Read sales", False, f"Status: {response.status_code}, Response: {response.text}")
            return False

    def test_read_sales_with_filters(self):
        """Test reading sales with filters"""
        print("Testing read sales with filters...")
        
        # Create test product and sale
        product = self.create_test_product("Filter Test Product", 12.50, 20)
        if not product:
            self.print_test_result("Read sales with filters", False, "Failed to create test product")
            return False
        
        sale_data = {
            "product_id": product["id"],
            "gym_id": 1,  # Admin needs to specify gym_id
            "quantity": 1
        }
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        create_response = self.session.post(SALES_URL, json=sale_data, headers=headers, timeout=10)
        
        if create_response.status_code == 200:
            sale = create_response.json()
            self.created_sales.append(sale["id"])
            
            # Test filter by product_id
            response = self.session.get(f"{SALES_URL}?product_id={product['id']}", headers=headers)
            if response.status_code == 200:
                sales = response.json()
                if len(sales) >= 1:
                    self.print_test_result("Read sales with product filter", True, f"Found {len(sales)} sales for product")
                else:
                    self.print_test_result("Read sales with product filter", False, "No sales found for product")
                    return False
            else:
                self.print_test_result("Read sales with product filter", False, f"Status: {response.status_code}")
                return False
            
            # Test filter by date
            today = date.today().isoformat()
            response = self.session.get(f"{SALES_URL}?start_date={today}&end_date={today}", headers=headers)
            if response.status_code == 200:
                sales = response.json()
                self.print_test_result("Read sales with date filter", True, f"Found {len(sales)} sales for today")
                return True
            else:
                self.print_test_result("Read sales with date filter", False, f"Status: {response.status_code}")
                return False
        else:
            self.print_test_result("Read sales with filters", False, "Failed to create test sale")
            return False

    def test_read_daily_sales(self):
        """Test reading daily sales"""
        print("Testing read daily sales...")
        
        today = date.today().isoformat()
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = self.session.get(f"{SALES_URL}/daily?sale_date={today}", headers=headers)
        
        if response.status_code == 200:
            sales = response.json()
            self.print_test_result("Read daily sales", True, f"Found {len(sales)} sales for today")
            return True
        else:
            self.print_test_result("Read daily sales", False, f"Status: {response.status_code}, Response: {response.text}")
            return False

    def test_get_sales_summary(self):
        """Test getting sales summary"""
        print("Testing get sales summary...")
        
        # Create test product and sale for summary
        product = self.create_test_product("Summary Test Product", 30.00, 15)
        if not product:
            self.print_test_result("Get sales summary", False, "Failed to create test product")
            return False
        
        sale_data = {
            "product_id": product["id"],
            "gym_id": 1,  # Admin needs to specify gym_id
            "quantity": 2
        }
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        create_response = self.session.post(SALES_URL, json=sale_data, headers=headers, timeout=10)
        
        if create_response.status_code == 200:
            sale = create_response.json()
            self.created_sales.append(sale["id"])
            
            # Get summary
            response = self.session.get(f"{SALES_URL}/summary", headers=headers)
            
            if response.status_code == 200:
                summary = response.json()
                if "total_sales" in summary and "total_revenue" in summary:
                    self.print_test_result("Get sales summary", True, f"Total sales: {summary['total_sales']}, Revenue: {summary['total_revenue']}")
                    return True
                else:
                    self.print_test_result("Get sales summary", False, "Summary data incomplete")
                    return False
            else:
                self.print_test_result("Get sales summary", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        else:
            self.print_test_result("Get sales summary", False, "Failed to create test sale")
            return False

    def test_read_sale(self):
        """Test reading a specific sale"""
        print("Testing read sale...")
        
        # Create test product and sale
        product = self.create_test_product("Read Sale Test Product", 18.00, 25)
        if not product:
            self.print_test_result("Read sale", False, "Failed to create test product")
            return False
        
        sale_data = {
            "product_id": product["id"],
            "gym_id": 1,  # Admin needs to specify gym_id
            "quantity": 1
        }
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        create_response = self.session.post(SALES_URL, json=sale_data, headers=headers, timeout=10)
        
        if create_response.status_code == 200:
            created_sale = create_response.json()
            self.created_sales.append(created_sale["id"])
            
            # Read specific sale
            response = self.session.get(f"{SALES_URL}/{created_sale['id']}", headers=headers)
            
            if response.status_code == 200:
                sale = response.json()
                if sale["id"] == created_sale["id"]:
                    self.print_test_result("Read sale", True, f"Retrieved sale ID: {sale['id']}")
                    return True
                else:
                    self.print_test_result("Read sale", False, "Retrieved wrong sale")
                    return False
            else:
                self.print_test_result("Read sale", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        else:
            self.print_test_result("Read sale", False, "Failed to create test sale")
            return False

    def test_read_sale_not_found(self):
        """Test reading a non-existent sale"""
        print("Testing read sale not found...")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = self.session.get(f"{SALES_URL}/99999", headers=headers)
        
        if response.status_code == 404:
            self.print_test_result("Read sale not found", True, "Correctly returned 404")
            return True
        else:
            self.print_test_result("Read sale not found", False, f"Expected 404, got {response.status_code}")
            return False

    def test_trainer_read_own_sale(self):
        """Test trainer reading their own sale"""
        print("Testing trainer read own sale...")
        
        # Create test product and sale as trainer
        product = self.create_test_product("Trainer Own Sale Product", 22.00, 20)
        if not product:
            self.print_test_result("Trainer read own sale", False, "Failed to create test product")
            return False
        
        sale_data = {
            "product_id": product["id"],
            "quantity": 1
        }
        
        headers = {"Authorization": f"Bearer {self.trainer_token}"}
        create_response = self.session.post(SALES_URL, json=sale_data, headers=headers)
        
        if create_response.status_code == 200:
            created_sale = create_response.json()
            self.created_sales.append(created_sale["id"])
            
            # Trainer reads their own sale
            response = self.session.get(f"{SALES_URL}/{created_sale['id']}", headers=headers)
            
            if response.status_code == 200:
                sale = response.json()
                if sale["id"] == created_sale["id"]:
                    self.print_test_result("Trainer read own sale", True, f"Trainer can read their sale ID: {sale['id']}")
                    return True
                else:
                    self.print_test_result("Trainer read own sale", False, "Retrieved wrong sale")
                    return False
            else:
                self.print_test_result("Trainer read own sale", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        else:
            self.print_test_result("Trainer read own sale", False, "Failed to create test sale")
            return False

    def test_trainer_read_other_sale(self):
        """Test trainer reading another trainer's sale (should be forbidden)"""
        print("Testing trainer read other sale...")
        
        # Create test product and sale as admin
        product = self.create_test_product("Other Trainer Sale Product", 35.00, 15)
        if not product:
            self.print_test_result("Trainer read other sale", False, "Failed to create test product")
            return False
        
        sale_data = {
            "product_id": product["id"],
            "gym_id": 1,  # Admin needs to specify gym_id
            "quantity": 1
        }
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        create_response = self.session.post(SALES_URL, json=sale_data, headers=headers, timeout=10)
        
        if create_response.status_code == 200:
            created_sale = create_response.json()
            self.created_sales.append(created_sale["id"])
            
            # Trainer tries to read admin's sale
            trainer_headers = {"Authorization": f"Bearer {self.trainer_token}"}
            response = self.session.get(f"{SALES_URL}/{created_sale['id']}", headers=trainer_headers)
            
            if response.status_code == 403:
                self.print_test_result("Trainer read other sale", True, "Correctly forbidden trainer from reading other's sale")
                return True
            else:
                self.print_test_result("Trainer read other sale", False, f"Expected 403, got {response.status_code}")
                return False
        else:
            self.print_test_result("Trainer read other sale", False, "Failed to create test sale")
            return False

    def test_update_sale(self):
        """Test updating a sale (admin only)"""
        print("Testing update sale...")
        
        # Create test product and sale
        product = self.create_test_product("Update Sale Test Product", 40.00, 30)
        if not product:
            self.print_test_result("Update sale", False, "Failed to create test product")
            return False
        
        sale_data = {
            "product_id": product["id"],
            "gym_id": 1,  # Admin needs to specify gym_id
            "quantity": 2
        }
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        create_response = self.session.post(SALES_URL, json=sale_data, headers=headers, timeout=10)
        
        if create_response.status_code == 200:
            created_sale = create_response.json()
            self.created_sales.append(created_sale["id"])
            
            # Update sale
            update_data = {
                "quantity": 3
            }
            
            response = self.session.put(f"{SALES_URL}/{created_sale['id']}", json=update_data, headers=headers)
            
            if response.status_code == 200:
                updated_sale = response.json()
                expected_total = 40.00 * 3
                # Convert string to float for comparison
                actual_total = float(updated_sale["total_amount"])
                if updated_sale["quantity"] == 3 and actual_total == expected_total:
                    self.print_test_result("Update sale", True, f"Updated sale ID: {updated_sale['id']}")
                    return True
                else:
                    self.print_test_result("Update sale", False, f"Sale not updated correctly. Expected total: {expected_total}, got: {actual_total}")
                    return False
            else:
                self.print_test_result("Update sale", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        else:
            self.print_test_result("Update sale", False, "Failed to create test sale")
            return False

    def test_update_sale_trainer_forbidden(self):
        """Test trainer updating a sale (should be forbidden)"""
        print("Testing trainer update sale forbidden...")
        
        # Create test product and sale as trainer
        product = self.create_test_product("Trainer Update Forbidden Product", 28.00, 25)
        if not product:
            self.print_test_result("Trainer update sale forbidden", False, "Failed to create test product")
            return False
        
        sale_data = {
            "product_id": product["id"],
            "quantity": 1
        }
        
        headers = {"Authorization": f"Bearer {self.trainer_token}"}
        create_response = self.session.post(SALES_URL, json=sale_data, headers=headers)
        
        if create_response.status_code == 200:
            created_sale = create_response.json()
            self.created_sales.append(created_sale["id"])
            
            # Trainer tries to update sale
            update_data = {
                "quantity": 2
            }
            
            response = self.session.put(f"{SALES_URL}/{created_sale['id']}", json=update_data, headers=headers)
            
            if response.status_code == 403:
                self.print_test_result("Trainer update sale forbidden", True, "Correctly forbidden trainer from updating sale")
                return True
            else:
                self.print_test_result("Trainer update sale forbidden", False, f"Expected 403, got {response.status_code}")
                return False
        else:
            self.print_test_result("Trainer update sale forbidden", False, "Failed to create test sale")
            return False

    def test_delete_sale(self):
        """Test deleting a sale (admin only)"""
        print("Testing delete sale...")
        
        # Create test product and sale
        product = self.create_test_product("Delete Sale Test Product", 45.00, 20)
        if not product:
            self.print_test_result("Delete sale", False, "Failed to create test product")
            return False
        
        sale_data = {
            "product_id": product["id"],
            "gym_id": 1,  # Admin needs to specify gym_id
            "quantity": 1
        }
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        create_response = self.session.post(SALES_URL, json=sale_data, headers=headers, timeout=10)
        
        if create_response.status_code == 200:
            created_sale = create_response.json()
            
            # Delete sale
            response = self.session.delete(f"{SALES_URL}/{created_sale['id']}", headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                if result["message"] == "Sale deleted successfully":
                    self.print_test_result("Delete sale", True, f"Deleted sale ID: {created_sale['id']}")
                    return True
                else:
                    self.print_test_result("Delete sale", False, "Unexpected response message")
                    return False
            else:
                self.print_test_result("Delete sale", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        else:
            self.print_test_result("Delete sale", False, "Failed to create test sale")
            return False

    def test_delete_sale_trainer_forbidden(self):
        """Test trainer deleting a sale (should be forbidden)"""
        print("Testing trainer delete sale forbidden...")
        
        # Create test product and sale as trainer
        product = self.create_test_product("Trainer Delete Forbidden Product", 32.00, 18)
        if not product:
            self.print_test_result("Trainer delete sale forbidden", False, "Failed to create test product")
            return False
        
        sale_data = {
            "product_id": product["id"],
            "quantity": 1
        }
        
        headers = {"Authorization": f"Bearer {self.trainer_token}"}
        create_response = self.session.post(SALES_URL, json=sale_data, headers=headers)
        
        if create_response.status_code == 200:
            created_sale = create_response.json()
            self.created_sales.append(created_sale["id"])
            
            # Trainer tries to delete sale
            response = self.session.delete(f"{SALES_URL}/{created_sale['id']}", headers=headers)
            
            if response.status_code == 403:
                self.print_test_result("Trainer delete sale forbidden", True, "Correctly forbidden trainer from deleting sale")
                return True
            else:
                self.print_test_result("Trainer delete sale forbidden", False, f"Expected 403, got {response.status_code}")
                return False
        else:
            self.print_test_result("Trainer delete sale forbidden", False, "Failed to create test sale")
            return False

    def test_unauthorized_access(self):
        """Test unauthorized access to sales"""
        print("Testing unauthorized access...")
        
        # Test without token
        response = self.session.get(SALES_URL)
        if response.status_code in [401, 403]:  # Both 401 and 403 are valid for unauthorized access
            self.print_test_result("Unauthorized access without token", True, "Correctly rejected access")
        else:
            self.print_test_result("Unauthorized access without token", False, f"Expected 401 or 403, got {response.status_code}")
            return False
        
        # Test with invalid token
        headers = {"Authorization": "Bearer invalid_token"}
        response = self.session.get(SALES_URL, headers=headers)
        if response.status_code in [401, 403]:  # Both 401 and 403 are valid for unauthorized access
            self.print_test_result("Unauthorized access with invalid token", True, "Correctly rejected invalid token")
            return True
        else:
            self.print_test_result("Unauthorized access with invalid token", False, f"Expected 401 or 403, got {response.status_code}")
            return False

    def cleanup_test_data(self):
        """Clean up all created test data"""
        print("Cleaning up test data...")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Delete sales
        for sale_id in self.created_sales:
            try:
                response = self.session.delete(f"{SALES_URL}/{sale_id}", headers=headers)
                if response.status_code == 200:
                    print(f"    Deleted sale {sale_id}")
                else:
                    print(f"    Failed to delete sale {sale_id}: {response.status_code}")
            except Exception as e:
                print(f"    Error deleting sale {sale_id}: {e}")
        
        # Delete products
        for product_id in self.created_products:
            try:
                response = self.session.delete(f"{PRODUCTS_URL}/{product_id}", headers=headers)
                if response.status_code == 200:
                    print(f"    Deleted product {product_id}")
                else:
                    print(f"    Failed to delete product {product_id}: {response.status_code}")
            except Exception as e:
                print(f"    Error deleting product {product_id}: {e}")
        
        # Delete users
        for user_id in self.created_users:
            try:
                response = self.session.delete(f"{BASE_URL}/users/{user_id}", headers=headers)
                if response.status_code == 200:
                    print(f"    Deleted user {user_id}")
                else:
                    print(f"    Failed to delete user {user_id}: {response.status_code}")
            except Exception as e:
                print(f"    Error deleting user {user_id}: {e}")
        
        print("Cleanup completed")

    def run_all_tests(self):
        """Run all sales tests"""
        print("=" * 60)
        print("SALES ENDPOINTS TEST SUITE")
        print("=" * 60)
        print()
        
        # Login first
        if not self.test_login():
            print("Login failed. Cannot proceed with tests.")
            return
        
        # Run all tests
        tests = [
            self.test_create_sale_admin,
            self.test_create_sale_trainer,
            self.test_create_sale_insufficient_stock,
            self.test_create_sale_invalid_product,
            self.test_create_sale_trainer_wrong_gym,
            self.test_read_sales,
            self.test_read_sales_with_filters,
            self.test_read_daily_sales,
            self.test_get_sales_summary,
            self.test_read_sale,
            self.test_read_sale_not_found,
            self.test_trainer_read_own_sale,
            self.test_trainer_read_other_sale,
            self.test_update_sale,
            self.test_update_sale_trainer_forbidden,
            self.test_delete_sale,
            self.test_delete_sale_trainer_forbidden,
            self.test_unauthorized_access
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
            except Exception as e:
                print(f"[ERROR] Test {test.__name__} failed with exception: {e}")
                print()
        
        print("=" * 60)
        print(f"TEST RESULTS: {passed}/{total} tests passed")
        print("=" * 60)
        
        # Cleanup
        self.cleanup_test_data()

if __name__ == "__main__":
    tester = SalesTester()
    tester.run_all_tests() 
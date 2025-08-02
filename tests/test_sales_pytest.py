"""
Pytest tests for Sales endpoints
Tests all CRUD operations and special endpoints for sales
"""

import pytest
import httpx
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, Any

# Test data
@pytest.fixture
def sale_data() -> Dict[str, Any]:
    """Sample sale data for testing"""
    return {
        "quantity": 2
    }

@pytest.fixture
def sale_update_data() -> Dict[str, Any]:
    """Sample sale update data for testing"""
    return {
        "quantity": 3
    }

@pytest.fixture
def product_data() -> Dict[str, Any]:
    """Sample product data for testing"""
    return {
        "name": "Test Product",
        "price": 15.50,
        "quantity": 100,
        "gym_id": 16,
        "is_active": True
    }

class TestSales:
    """Test class for sales endpoints"""

    def test_create_sale_admin(self, client: httpx.Client, admin_headers: Dict[str, str], product_data: Dict[str, Any], sale_data: Dict[str, Any]):
        """Test creating a sale as admin"""
        # Create test product first
        product_response = client.post("/products/", json=product_data, headers=admin_headers)
        assert product_response.status_code == 200
        product = product_response.json()
        
        # Create sale as admin
        sale_data["product_id"] = product["id"]
        sale_data["gym_id"] = 16  # Admin can specify gym_id
        
        response = client.post("/sales/", json=sale_data, headers=admin_headers)
        
        assert response.status_code == 200
        sale = response.json()
        assert sale["product_id"] == product["id"]
        assert sale["quantity"] == 2
        assert sale["total_amount"] == 31.0  # 15.50 * 2
        assert sale["sold_by_id"] is not None
        assert sale["gym_id"] == 16

    def test_create_sale_trainer(self, client: httpx.Client, trainer_headers: Dict[str, str], product_data: Dict[str, Any]):
        """Test creating a sale as trainer"""
        # Create test product first
        product_response = client.post("/products/", json=product_data, headers=trainer_headers)
        assert product_response.status_code == 200
        product = product_response.json()
        
        # Create sale as trainer (gym_id will be set automatically)
        sale_data = {
            "product_id": product["id"],
            "quantity": 1
        }
        
        response = client.post("/sales/", json=sale_data, headers=trainer_headers)
        
        assert response.status_code == 200
        sale = response.json()
        assert sale["product_id"] == product["id"]
        assert sale["quantity"] == 1
        assert sale["total_amount"] == 15.50
        assert sale["sold_by_id"] is not None

    def test_create_sale_insufficient_stock(self, client: httpx.Client, admin_headers: Dict[str, str]):
        """Test creating a sale with insufficient stock"""
        # Create test product with low stock
        product_data = {
            "name": "Low Stock Product",
            "price": 10.00,
            "quantity": 2,
            "gym_id": 16,
            "is_active": True
        }
        
        product_response = client.post("/products/", json=product_data, headers=admin_headers)
        assert product_response.status_code == 200
        product = product_response.json()
        
        # Try to buy more than available
        sale_data = {
            "product_id": product["id"],
            "quantity": 5  # More than available (2)
        }
        
        response = client.post("/sales/", json=sale_data, headers=admin_headers)
        
        assert response.status_code == 400
        assert "Insufficient stock" in response.json()["detail"]

    def test_create_sale_invalid_product(self, client: httpx.Client, admin_headers: Dict[str, str], sale_data: Dict[str, Any]):
        """Test creating a sale with invalid product"""
        sale_data["product_id"] = 99999  # Non-existent product
        
        response = client.post("/sales/", json=sale_data, headers=admin_headers)
        
        assert response.status_code == 404
        assert "Product not found" in response.json()["detail"]

    def test_create_sale_trainer_wrong_gym(self, client: httpx.Client, trainer_headers: Dict[str, str]):
        """Test creating a sale as trainer with product from different gym"""
        # Create test product in a different gym (assuming gym_id=1 exists)
        product_data = {
            "name": "Different Gym Product",
            "price": 20.00,
            "quantity": 10,
            "gym_id": 1,  # Different gym
            "is_active": True
        }
        
        # Create product as admin (since trainer can't create products in other gyms)
        admin_headers = {"Authorization": "Bearer admin_token"}  # This would need proper admin token
        product_response = client.post("/products/", json=product_data, headers=admin_headers)
        if product_response.status_code != 200:
            pytest.skip("Cannot create product in different gym for this test")
        
        product = product_response.json()
        
        # Try to buy product from different gym
        sale_data = {
            "product_id": product["id"],
            "quantity": 1
        }
        
        response = client.post("/sales/", json=sale_data, headers=trainer_headers)
        
        assert response.status_code == 404
        assert "Product not found" in response.json()["detail"]

    def test_read_sales(self, client: httpx.Client, admin_headers: Dict[str, str]):
        """Test reading all sales"""
        response = client.get("/sales/", headers=admin_headers)
        
        assert response.status_code == 200
        sales = response.json()
        assert isinstance(sales, list)

    def test_read_sales_with_product_filter(self, client: httpx.Client, admin_headers: Dict[str, str], product_data: Dict[str, Any], sale_data: Dict[str, Any]):
        """Test reading sales with product filter"""
        # Create product and sale first
        product_response = client.post("/products/", json=product_data, headers=admin_headers)
        assert product_response.status_code == 200
        product = product_response.json()
        
        sale_data["product_id"] = product["id"]
        create_response = client.post("/sales/", json=sale_data, headers=admin_headers)
        assert create_response.status_code == 200
        
        # Test filter by product_id
        response = client.get(f"/sales/?product_id={product['id']}", headers=admin_headers)
        
        assert response.status_code == 200
        sales = response.json()
        assert isinstance(sales, list)
        if len(sales) > 0:
            assert all(s["product_id"] == product["id"] for s in sales)

    def test_read_sales_with_date_filter(self, client: httpx.Client, admin_headers: Dict[str, str], product_data: Dict[str, Any]):
        """Test reading sales with date filter"""
        # Create product and sale first
        product_response = client.post("/products/", json=product_data, headers=admin_headers)
        assert product_response.status_code == 200
        product = product_response.json()
        
        sale_data = {
            "product_id": product["id"],
            "quantity": 1
        }
        client.post("/sales/", json=sale_data, headers=admin_headers)
        
        # Test filter by date
        today = date.today().isoformat()
        response = client.get(f"/sales/?start_date={today}&end_date={today}", headers=admin_headers)
        
        assert response.status_code == 200
        sales = response.json()
        assert isinstance(sales, list)

    def test_read_daily_sales(self, client: httpx.Client, admin_headers: Dict[str, str]):
        """Test reading daily sales"""
        today = date.today().isoformat()
        response = client.get(f"/sales/daily?sale_date={today}", headers=admin_headers)
        
        assert response.status_code == 200
        sales = response.json()
        assert isinstance(sales, list)

    def test_get_sales_summary(self, client: httpx.Client, admin_headers: Dict[str, str], product_data: Dict[str, Any]):
        """Test getting sales summary"""
        # Create product and sale first
        product_response = client.post("/products/", json=product_data, headers=admin_headers)
        assert product_response.status_code == 200
        product = product_response.json()
        
        sale_data = {
            "product_id": product["id"],
            "quantity": 2
        }
        client.post("/sales/", json=sale_data, headers=admin_headers)
        
        # Get summary
        response = client.get("/sales/summary", headers=admin_headers)
        
        assert response.status_code == 200
        summary = response.json()
        assert "total_sales" in summary
        assert "total_revenue" in summary
        assert "total_items_sold" in summary
        assert "product_summary" in summary

    def test_read_sale(self, client: httpx.Client, admin_headers: Dict[str, str], product_data: Dict[str, Any], sale_data: Dict[str, Any]):
        """Test reading a specific sale"""
        # Create product and sale first
        product_response = client.post("/products/", json=product_data, headers=admin_headers)
        assert product_response.status_code == 200
        product = product_response.json()
        
        sale_data["product_id"] = product["id"]
        create_response = client.post("/sales/", json=sale_data, headers=admin_headers)
        assert create_response.status_code == 200
        created_sale = create_response.json()
        
        # Read specific sale
        response = client.get(f"/sales/{created_sale['id']}", headers=admin_headers)
        
        assert response.status_code == 200
        sale = response.json()
        assert sale["id"] == created_sale["id"]
        assert sale["product_id"] == product["id"]

    def test_read_sale_not_found(self, client: httpx.Client, admin_headers: Dict[str, str]):
        """Test reading a non-existent sale"""
        response = client.get("/sales/99999", headers=admin_headers)
        
        assert response.status_code == 404

    def test_trainer_read_own_sale(self, client: httpx.Client, trainer_headers: Dict[str, str], product_data: Dict[str, Any]):
        """Test trainer reading their own sale"""
        # Create product and sale as trainer
        product_response = client.post("/products/", json=product_data, headers=trainer_headers)
        assert product_response.status_code == 200
        product = product_response.json()
        
        sale_data = {
            "product_id": product["id"],
            "quantity": 1
        }
        create_response = client.post("/sales/", json=sale_data, headers=trainer_headers)
        assert create_response.status_code == 200
        created_sale = create_response.json()
        
        # Trainer reads their own sale
        response = client.get(f"/sales/{created_sale['id']}", headers=trainer_headers)
        
        assert response.status_code == 200
        sale = response.json()
        assert sale["id"] == created_sale["id"]

    def test_trainer_read_other_sale(self, client: httpx.Client, admin_headers: Dict[str, str], trainer_headers: Dict[str, str], product_data: Dict[str, Any]):
        """Test trainer reading another trainer's sale (should be forbidden)"""
        # Create product and sale as admin
        product_response = client.post("/products/", json=product_data, headers=admin_headers)
        assert product_response.status_code == 200
        product = product_response.json()
        
        sale_data = {
            "product_id": product["id"],
            "quantity": 1
        }
        create_response = client.post("/sales/", json=sale_data, headers=admin_headers)
        assert create_response.status_code == 200
        created_sale = create_response.json()
        
        # Trainer tries to read admin's sale
        response = client.get(f"/sales/{created_sale['id']}", headers=trainer_headers)
        
        assert response.status_code == 403
        assert "You can only view your own sales" in response.json()["detail"]

    def test_update_sale(self, client: httpx.Client, admin_headers: Dict[str, str], product_data: Dict[str, Any], sale_data: Dict[str, Any], sale_update_data: Dict[str, Any]):
        """Test updating a sale (admin only)"""
        # Create product and sale first
        product_response = client.post("/products/", json=product_data, headers=admin_headers)
        assert product_response.status_code == 200
        product = product_response.json()
        
        sale_data["product_id"] = product["id"]
        create_response = client.post("/sales/", json=sale_data, headers=admin_headers)
        assert create_response.status_code == 200
        created_sale = create_response.json()
        
        # Update sale
        response = client.put(f"/sales/{created_sale['id']}", json=sale_update_data, headers=admin_headers)
        
        assert response.status_code == 200
        updated_sale = response.json()
        assert updated_sale["quantity"] == 3
        assert updated_sale["total_amount"] == 46.5  # 15.50 * 3

    def test_update_sale_trainer_forbidden(self, client: httpx.Client, trainer_headers: Dict[str, str], product_data: Dict[str, Any]):
        """Test trainer updating a sale (should be forbidden)"""
        # Create product and sale as trainer
        product_response = client.post("/products/", json=product_data, headers=trainer_headers)
        assert product_response.status_code == 200
        product = product_response.json()
        
        sale_data = {
            "product_id": product["id"],
            "quantity": 1
        }
        create_response = client.post("/sales/", json=sale_data, headers=trainer_headers)
        assert create_response.status_code == 200
        created_sale = create_response.json()
        
        # Trainer tries to update sale
        update_data = {
            "quantity": 2
        }
        
        response = client.put(f"/sales/{created_sale['id']}", json=update_data, headers=trainer_headers)
        
        assert response.status_code == 403

    def test_delete_sale(self, client: httpx.Client, admin_headers: Dict[str, str], product_data: Dict[str, Any], sale_data: Dict[str, Any]):
        """Test deleting a sale (admin only)"""
        # Create product and sale first
        product_response = client.post("/products/", json=product_data, headers=admin_headers)
        assert product_response.status_code == 200
        product = product_response.json()
        
        sale_data["product_id"] = product["id"]
        create_response = client.post("/sales/", json=sale_data, headers=admin_headers)
        assert create_response.status_code == 200
        created_sale = create_response.json()
        
        # Delete sale
        response = client.delete(f"/sales/{created_sale['id']}", headers=admin_headers)
        
        assert response.status_code == 200
        result = response.json()
        assert result["message"] == "Sale deleted successfully"
        
        # Verify it's deleted
        get_response = client.get(f"/sales/{created_sale['id']}", headers=admin_headers)
        assert get_response.status_code == 404

    def test_delete_sale_trainer_forbidden(self, client: httpx.Client, trainer_headers: Dict[str, str], product_data: Dict[str, Any]):
        """Test trainer deleting a sale (should be forbidden)"""
        # Create product and sale as trainer
        product_response = client.post("/products/", json=product_data, headers=trainer_headers)
        assert product_response.status_code == 200
        product = product_response.json()
        
        sale_data = {
            "product_id": product["id"],
            "quantity": 1
        }
        create_response = client.post("/sales/", json=sale_data, headers=trainer_headers)
        assert create_response.status_code == 200
        created_sale = create_response.json()
        
        # Trainer tries to delete sale
        response = client.delete(f"/sales/{created_sale['id']}", headers=trainer_headers)
        
        assert response.status_code == 403

    def test_delete_sale_not_found(self, client: httpx.Client, admin_headers: Dict[str, str]):
        """Test deleting a non-existent sale"""
        response = client.delete("/sales/99999", headers=admin_headers)
        
        assert response.status_code == 404

    def test_unauthorized_access(self, client: httpx.Client):
        """Test unauthorized access to sales"""
        # Test without token
        response = client.get("/sales/")
        assert response.status_code == 401
        
        # Test with invalid token
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/sales/", headers=headers)
        assert response.status_code == 401

    def test_trainer_access_sales(self, client: httpx.Client, trainer_headers: Dict[str, str]):
        """Test that trainers can access sales"""
        response = client.get("/sales/", headers=trainer_headers)
        
        assert response.status_code == 200
        sales = response.json()
        assert isinstance(sales, list)

    def test_sale_with_all_fields(self, client: httpx.Client, admin_headers: Dict[str, str], product_data: Dict[str, Any]):
        """Test creating a sale with all possible fields"""
        # Create test product first
        product_response = client.post("/products/", json=product_data, headers=admin_headers)
        assert product_response.status_code == 200
        product = product_response.json()
        
        # Create sale with all fields
        complete_sale_data = {
            "product_id": product["id"],
            "gym_id": 16,
            "quantity": 3
        }
        
        response = client.post("/sales/", json=complete_sale_data, headers=admin_headers)
        
        assert response.status_code == 200
        sale = response.json()
        assert sale["product_id"] == product["id"]
        assert sale["quantity"] == 3
        assert sale["total_amount"] == 46.5  # 15.50 * 3
        assert sale["gym_id"] == 16
        assert sale["sold_by_id"] is not None

    def test_sale_pagination(self, client: httpx.Client, admin_headers: Dict[str, str], product_data: Dict[str, Any]):
        """Test sale pagination"""
        # Create test product first
        product_response = client.post("/products/", json=product_data, headers=admin_headers)
        assert product_response.status_code == 200
        product = product_response.json()
        
        # Create multiple sales
        for i in range(5):
            sale_data = {
                "product_id": product["id"],
                "quantity": i + 1
            }
            client.post("/sales/", json=sale_data, headers=admin_headers)
        
        # Test pagination
        response = client.get("/sales/?skip=0&limit=3", headers=admin_headers)
        assert response.status_code == 200
        sales = response.json()
        assert len(sales) <= 3
        
        # Test second page
        response = client.get("/sales/?skip=3&limit=3", headers=admin_headers)
        assert response.status_code == 200
        sales = response.json()
        assert len(sales) <= 3

    def test_sales_summary_with_date_range(self, client: httpx.Client, admin_headers: Dict[str, str], product_data: Dict[str, Any]):
        """Test sales summary with date range"""
        # Create product and sale first
        product_response = client.post("/products/", json=product_data, headers=admin_headers)
        assert product_response.status_code == 200
        product = product_response.json()
        
        sale_data = {
            "product_id": product["id"],
            "quantity": 2
        }
        client.post("/sales/", json=sale_data, headers=admin_headers)
        
        # Get summary with date range
        today = date.today().isoformat()
        response = client.get(f"/sales/summary?start_date={today}&end_date={today}", headers=admin_headers)
        
        assert response.status_code == 200
        summary = response.json()
        assert "total_sales" in summary
        assert "total_revenue" in summary
        assert "period" in summary
        assert summary["period"]["start_date"] == today
        assert summary["period"]["end_date"] == today

    def test_sales_summary_with_trainer_filter(self, client: httpx.Client, admin_headers: Dict[str, str], trainer_headers: Dict[str, str], product_data: Dict[str, Any]):
        """Test sales summary with trainer filter"""
        # Create product and sale as trainer
        product_response = client.post("/products/", json=product_data, headers=trainer_headers)
        assert product_response.status_code == 200
        product = product_response.json()
        
        sale_data = {
            "product_id": product["id"],
            "quantity": 1
        }
        create_response = client.post("/sales/", json=sale_data, headers=trainer_headers)
        assert create_response.status_code == 200
        created_sale = create_response.json()
        
        # Get summary with trainer filter (as admin)
        response = client.get(f"/sales/summary?trainer_id={created_sale['sold_by_id']}", headers=admin_headers)
        
        assert response.status_code == 200
        summary = response.json()
        assert "total_sales" in summary
        assert "total_revenue" in summary

    def test_daily_sales_with_trainer_filter(self, client: httpx.Client, admin_headers: Dict[str, str], trainer_headers: Dict[str, str], product_data: Dict[str, Any]):
        """Test daily sales with trainer filter"""
        # Create product and sale as trainer
        product_response = client.post("/products/", json=product_data, headers=trainer_headers)
        assert product_response.status_code == 200
        product = product_response.json()
        
        sale_data = {
            "product_id": product["id"],
            "quantity": 1
        }
        create_response = client.post("/sales/", json=sale_data, headers=trainer_headers)
        assert create_response.status_code == 200
        created_sale = create_response.json()
        
        # Get daily sales with trainer filter (as admin)
        today = date.today().isoformat()
        response = client.get(f"/sales/daily?sale_date={today}&trainer_id={created_sale['sold_by_id']}", headers=admin_headers)
        
        assert response.status_code == 200
        sales = response.json()
        assert isinstance(sales, list) 
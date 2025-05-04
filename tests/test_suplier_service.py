import unittest
from unittest import mock
from django.test import TestCase
from django.utils import timezone
from datetime import date, datetime, timedelta

# Import the service to test
from api.models import SupplierRanking
from ranking_engine.services.supplier_service import SupplierService


class TestSupplierService(TestCase):
    """Integration tests for the SupplierService class"""

    def setUp(self):
        """Set up test environment before each test"""
        # Create an instance of the service
        self.service = SupplierService()
        
        # Create some test rankings in the database
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        # Create rankings for today
        SupplierRanking.objects.create(
            supplier_id=1,
            supplier_name="Supplier A",
            date=today,
            overall_score=8.5,
            quality_score=8.2,
            delivery_score=9.0,
            price_score=7.8,
            service_score=8.7,
            rank=1
        )
        
        SupplierRanking.objects.create(
            supplier_id=2,
            supplier_name="Supplier B",
            date=today,
            overall_score=8.0,
            quality_score=7.8,
            delivery_score=8.5,
            price_score=8.2,
            service_score=7.9,
            rank=2
        )
        
        # Create rankings for yesterday
        SupplierRanking.objects.create(
            supplier_id=1,
            supplier_name="Supplier A",
            date=yesterday,
            overall_score=8.3,
            quality_score=8.0,
            delivery_score=8.8,
            price_score=7.6,
            service_score=8.5,
            rank=1
        )
        
        SupplierRanking.objects.create(
            supplier_id=2,
            supplier_name="Supplier B",
            date=yesterday,
            overall_score=7.8,
            quality_score=7.5,
            delivery_score=8.3,
            price_score=8.0,
            service_score=7.7,
            rank=2
        )
    
    def test_service_initialization(self):
        """Test if service is initialized with all required connectors"""
        self.assertIsNotNone(self.service.user_service)
        self.assertIsNotNone(self.service.warehouse_service)
        self.assertIsNotNone(self.service.order_service)
    
    def test_get_active_suppliers(self):
        """Test if get_active_suppliers returns data from user service connector"""
        suppliers = self.service.get_active_suppliers()
        
        # Check if it returns a list
        self.assertIsInstance(suppliers, list)
        
        # Check if the list has expected length from mock data
        self.assertEqual(len(suppliers), 4)
    
    def test_get_active_supplier_ids(self):
        """Test if get_active_supplier_ids returns correct IDs"""
        supplier_ids = self.service.get_active_supplier_ids()
        
        # Check if it returns a list
        self.assertIsInstance(supplier_ids, list)
        
        # Check if the list contains expected IDs from mock data
        expected_ids = [1, 2, 3, 5]
        self.assertEqual(sorted(supplier_ids), sorted(expected_ids))
    
    def test_get_supplier(self):
        """Test if get_supplier returns data from user service connector"""
        supplier = self.service.get_supplier(1)
        
        # Check if it returns a dictionary
        self.assertIsInstance(supplier, dict)
        
        # Check if the supplier has expected ID
        self.assertEqual(supplier['id'], 1)
        self.assertEqual(supplier['name'], "Supplier A")
    
    def test_get_supplier_products(self):
        """Test if get_supplier_products returns data from warehouse service connector"""
        products = self.service.get_supplier_products(1)
        
        # Check if it returns a list
        self.assertIsInstance(products, list)
        
        # Check if the list has expected length from mock data
        self.assertEqual(len(products), 2)
        
        # Check if products have expected supplier ID
        for product in products:
            self.assertEqual(product['supplier_id'], 1)
    
    def test_get_supplier_performance_history(self):
        """Test if get_supplier_performance_history returns data from order service connector"""
        performance = self.service.get_supplier_performance_history(1)
        
        # Check if it returns a dictionary
        self.assertIsInstance(performance, dict)
        
        # Check if it contains expected keys
        self.assertIn('supplier_id', performance)
        self.assertIn('overall_score', performance)
        self.assertIn('metrics', performance)
        
        # Check if supplier ID matches
        self.assertEqual(performance['supplier_id'], 1)
    
    def test_get_supplier_transactions(self):
        """Test if get_supplier_transactions returns data from order service connector"""
        transactions = self.service.get_supplier_transactions(1)
        
        # Check if it returns a list
        self.assertIsInstance(transactions, list)
        
        # Check transactions have expected supplier ID
        for transaction in transactions:
            self.assertEqual(transaction['supplier_id'], 1)
    
    def test_get_supplier_ranking_history(self):
        """Test if get_supplier_ranking_history returns data from database"""
        rankings = self.service.get_supplier_ranking_history(1)
        
        # Check if it returns a queryset
        self.assertTrue(hasattr(rankings, 'count'))
        
        # Check if it contains expected number of rankings
        self.assertEqual(rankings.count(), 2)
        
        # Check if rankings have expected supplier ID
        for ranking in rankings:
            self.assertEqual(ranking.supplier_id, 1)
    
    def test_get_latest_supplier_rankings(self):
        """Test if get_latest_supplier_rankings returns most recent rankings"""
        rankings = self.service.get_latest_supplier_rankings()
        
        # Check if it returns a queryset
        self.assertTrue(hasattr(rankings, 'count'))
        
        # Check if it contains expected number of rankings
        self.assertEqual(rankings.count(), 2)
        
        # Check if all rankings have the same (latest) date
        first_date = rankings[0].date
        for ranking in rankings:
            self.assertEqual(ranking.date, first_date)
    
    def test_get_top_ranked_suppliers(self):
        """Test if get_top_ranked_suppliers returns rankings in correct order"""
        rankings = self.service.get_top_ranked_suppliers()
        
        # Check if it returns a queryset
        self.assertTrue(hasattr(rankings, 'count'))
        
        # Check if rankings are in correct order (by rank)
        ranks = [r.rank for r in rankings]
        self.assertEqual(ranks, sorted(ranks))
    
    @mock.patch('connectors.warehouse_service_connector.WarehouseServiceConnector.get_suppliers_by_category')
    def test_get_top_ranked_suppliers_with_category(self, mock_get_suppliers):
        """Test if get_top_ranked_suppliers filters by category"""
        # Mock the warehouse service response
        mock_get_suppliers.return_value = [1]
        
        # Call the method with category filter
        rankings = self.service.get_top_ranked_suppliers(category="Furniture")
        
        # Check if mock was called with correct category
        mock_get_suppliers.assert_called_once_with("Furniture")
        
        # Check if it returns a queryset
        self.assertTrue(hasattr(rankings, 'count'))
        
        # Check if only suppliers from the category are included
        for ranking in rankings:
            self.assertEqual(ranking.supplier_id, 1)
    
    def test_get_supplier_category_performance(self):
        """Test if get_supplier_category_performance returns data from order service connector"""
        performance = self.service.get_supplier_category_performance(1)
        
        # Check if it returns a dictionary
        self.assertIsInstance(performance, dict)
        
        # Check if it contains expected categories
        self.assertIn('Electronics', performance)
        self.assertIn('Furniture', performance)
        self.assertIn('Office Supplies', performance)
    
    def test_update_supplier_preferences(self):
        """Test if update_supplier_preferences passes data to warehouse service connector"""
        # Define test preferences data
        preferences = {"featured": True, "preferred": True}
        
        # Call the method
        result = self.service.update_supplier_preferences(1, preferences)
        
        # Check if it returns True (success)
        self.assertTrue(result)
    
    @mock.patch('connectors.user_service_connector.UserServiceConnector.get_supplier_by_id')
    def test_exception_handling(self, mock_get_supplier_by_id):
        """Test exception handling in service methods"""
        # Setup mock to raise exception
        mock_get_supplier_by_id.side_effect = Exception("Test exception")
        
        # Call the method that should handle the exception
        supplier_info = self.service.get_supplier_info(1)
        
        # Check if it returns None on exception
        self.assertIsNone(supplier_info)
        
        # Verify the mock was called
        mock_get_supplier_by_id.assert_called_with(1)


if __name__ == "__main__":
    unittest.main()
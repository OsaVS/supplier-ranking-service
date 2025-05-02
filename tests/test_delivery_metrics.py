"""
This test case specifically tests the delivery metrics calculation 
with focus on the delay calculation to ensure it works correctly.
"""

import unittest
from datetime import date, timedelta
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.utils import timezone

from api.models import Supplier, Transaction, SupplierProduct, SupplierPerformance, Product
from ranking_engine.services.metrics_service import MetricsService


class DeliveryMetricsTest(TestCase):
    """Test class for the delivery metrics calculation"""
    
    def setUp(self):
        """Set up test data for delivery metrics"""
        # First, create the supplier
        self.supplier = Supplier.objects.create(
            name="Test Supplier",
            code="TS001",
            contact_email="test@supplier.com",
            address="123 Test St",
            country="Test Country",
            supplier_size="M"
        )
        
        # Create the product before referencing it
        self.product = Product.objects.create(
            name="Test Product",
            sku="TP001",
            category="Test Category",
            unit_of_measure="Each"
        )
        
        # Now you can create SupplierProduct using self.product
        self.supplier_product = SupplierProduct.objects.create(
            supplier=self.supplier,
            product=self.product,
            unit_price=10.00,
            minimum_order_quantity=1,
            lead_time_days=5
        )
        
        # Create transactions for testing delivery metrics
        # On-time delivery
        Transaction.objects.create(
            supplier=self.supplier,
            product=self.product,
            order_date=timezone.now() - timedelta(days=10),
            expected_delivery_date=timezone.now().date() - timedelta(days=5),
            actual_delivery_date=timezone.now().date() - timedelta(days=5),
            quantity=10,
            unit_price=10.00,
            status="DELIVERED"
        )
        
        # Delayed delivery (3 days late)
        Transaction.objects.create(
            supplier=self.supplier,
            product=self.product,
            order_date=timezone.now() - timedelta(days=15),
            expected_delivery_date=timezone.now().date() - timedelta(days=10),
            actual_delivery_date=timezone.now().date() - timedelta(days=7),
            quantity=5,
            unit_price=10.00,
            status="DELIVERED"
        )
        
        # Delayed delivery (5 days late)
        Transaction.objects.create(
            supplier=self.supplier,
            product=self.product,
            order_date=timezone.now() - timedelta(days=20),
            expected_delivery_date=timezone.now().date() - timedelta(days=15),
            actual_delivery_date=timezone.now().date() - timedelta(days=10),
            quantity=8,
            unit_price=10.00,
            status="DELIVERED"
        )
        
        # Create a performance record to combine with transaction data
        SupplierPerformance.objects.create(
            supplier=self.supplier,
            date=timezone.now().date() - timedelta(days=5),
            quality_score=8.5,
            defect_rate=2.0,
            return_rate=1.5,
            on_time_delivery_rate=90.0,
            average_delay_days=2.0,
            price_competitiveness=9.0,
            responsiveness=8.0,
            fill_rate=95.0,
            order_accuracy=98.0
        )
    
    def test_delivery_metrics_calculation(self):
        """Test that delivery metrics are calculated correctly"""
        metrics = MetricsService.calculate_delivery_metrics(self.supplier.id)
        
        # Check that we have the right keys
        self.assertIn('delivery_score', metrics)
        self.assertIn('on_time_delivery_rate', metrics)
        self.assertIn('average_delay_days', metrics)
        
        # Check the transactions analyzed
        self.assertEqual(metrics['transactions_analyzed'], 3)
        
        # Check on-time delivery rate
        # 1 out of 3 deliveries was on time (33.33%)
        # Performance record had 90% on-time rate
        # Weighted: 33.33 * 0.7 + 90 * 0.3 = 23.33 + 27 = 50.33%
        self.assertAlmostEqual(metrics['on_time_delivery_rate'], 50.33, delta=0.1)
        
        # Check average delay
        # Transaction delays: 0, 3, and 5 days (for delayed ones: 3 + 5 = 8, avg = 4)
        # Performance record had 2.0 avg delay
        # Weighted: 4 * 0.7 + 2 * 0.3 = 2.8 + 0.6 = 3.4 days
        self.assertAlmostEqual(metrics['average_delay_days'], 3.4, delta=0.1)
        
        # The delivery score should be based on these metrics
        # on_time_score = on_time_rate / 10 = 50.33 / 10 = 5.033
        # delay_score = max(0, 10 - min(10, avg_delay * 2)) = max(0, 10 - min(10, 3.4 * 2)) = 10 - 6.8 = 3.2
        # delivery_score = on_time_score * 0.6 + delay_score * 0.4 = 5.033 * 0.6 + 3.2 * 0.4 = 3.02 + 1.28 = 4.3
        self.assertAlmostEqual(metrics['delivery_score'], 4.3, delta=0.2)
    
    def test_delivery_metrics_no_transactions(self):
        """Test delivery metrics calculation when there are no transactions"""
        # Create a new supplier with no transactions
        new_supplier = Supplier.objects.create(
            name="New Supplier",
            code="NS001",
            contact_email="new@example.com",
            address="New Address",
            country="Test Country",
            supplier_size="S"
        )
        
        metrics = MetricsService.calculate_delivery_metrics(new_supplier.id)
        
        # Check that we have the expected keys
        self.assertIn('delivery_score', metrics)
        self.assertIn('on_time_delivery_rate', metrics)
        self.assertIn('average_delay_days', metrics)
        
        # Check that we handled empty transactions correctly
        self.assertEqual(metrics['transactions_analyzed'], 0)
        self.assertEqual(metrics['on_time_delivery_rate'], 0)
        self.assertEqual(metrics['average_delay_days'], 0)
        
        # The delivery score should be 0 in this case
        # on_time_score = 0 / 10 = 0
        # delay_score = max(0, 10 - min(10, 0 * 2)) = 10
        # delivery_score = 0 * 0.6 + 10 * 0.4 = 4
        self.assertEqual(metrics['delivery_score'], 4.0)


if __name__ == '__main__':
    unittest.main()
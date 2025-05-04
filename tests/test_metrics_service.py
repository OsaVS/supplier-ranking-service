"""
Tests for MetricsService that calculates supplier performance metrics
"""

import unittest
from unittest.mock import patch, MagicMock
from datetime import date, datetime, timedelta
from django.utils import timezone

# Import the class we want to test
from api.models import RankingConfiguration
from ranking_engine.services.metrics_service import MetricsService


class TestMetricsService(unittest.TestCase):
    """Test cases for the MetricsService class"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a patched instance of MetricsService
        self.service = MetricsService()
        
        # Mock the connectors
        self.service.user_service = MagicMock()
        self.service.warehouse_service = MagicMock()
        self.service.order_service = MagicMock()
        
        # Define test data
        self.supplier_id = 123
        self.supplier_name = "Test Supplier Inc."
        
        # Set up a mock for the active configuration
        self.mock_config = MagicMock(spec=RankingConfiguration)
        self.mock_config.name = "Test Configuration"
        self.mock_config.learning_rate = 0.1
        self.mock_config.discount_factor = 0.9
        self.mock_config.exploration_rate = 0.2
        self.mock_config.quality_weight = 0.3
        self.mock_config.delivery_weight = 0.3
        self.mock_config.price_weight = 0.2
        self.mock_config.service_weight = 0.2
        self.mock_config.is_active = True

    @patch('api.models.RankingConfiguration.objects.get')
    def test_get_active_configuration(self, mock_get):
        """Test retrieving active configuration"""
        # Set up the mock to return our configuration
        mock_get.return_value = self.mock_config
        
        # Call the method
        config = MetricsService.get_active_configuration()
        
        # Verify the mock was called correctly
        mock_get.assert_called_once_with(is_active=True)
        
        # Verify the returned configuration is correct
        self.assertEqual(config.name, "Test Configuration")
        self.assertEqual(config.quality_weight, 0.3)
        self.assertEqual(config.delivery_weight, 0.3)
        self.assertEqual(config.price_weight, 0.2)
        self.assertEqual(config.service_weight, 0.2)

    @patch('api.models.RankingConfiguration.objects.get')
    def test_get_active_configuration_not_found(self, mock_get):
        """Test retrieving active configuration when none exists"""
        # Set up the mock to raise DoesNotExist
        mock_get.side_effect = RankingConfiguration.DoesNotExist
        
        # Call the method
        config = MetricsService.get_active_configuration()
        
        # Verify default values are returned
        self.assertEqual(config.name, "Default Configuration")
        self.assertEqual(config.learning_rate, 0.1)
        self.assertEqual(config.discount_factor, 0.9)
        self.assertEqual(config.exploration_rate, 0.3)
        self.assertEqual(config.quality_weight, 0.25)
        self.assertEqual(config.delivery_weight, 0.25)
        self.assertEqual(config.price_weight, 0.25)
        self.assertEqual(config.service_weight, 0.25)

    def test_calculate_quality_metrics(self):
        """Test quality metrics calculation"""
        # Mock the returned data from order service
        self.service.order_service.get_supplier_transactions.return_value = [
            {'quantity': 100, 'defect_count': 5, 'status': 'DELIVERED'},
            {'quantity': 200, 'defect_count': 8, 'status': 'DELIVERED'},
            {'quantity': 150, 'defect_count': 2, 'status': 'RETURNED'},
            {'quantity': 50, 'defect_count': 0, 'status': 'DELIVERED'}
        ]
        
        self.service.order_service.get_supplier_performance_records.return_value = [
            {'quality_score': 8.5, 'defect_rate': 3.0, 'return_rate': 2.0},
            {'quality_score': 9.0, 'defect_rate': 2.5, 'return_rate': 1.5}
        ]
        
        # Call the method
        result = self.service.calculate_quality_metrics(self.supplier_id)
        
        # Verify the order service was called correctly
        self.service.order_service.get_supplier_transactions.assert_called_once()
        self.service.order_service.get_supplier_performance_records.assert_called_once()
        
        # Verify the calculation results
        self.assertIn('quality_score', result)
        self.assertIn('defect_rate', result)
        self.assertIn('return_rate', result)
        self.assertIn('transactions_analyzed', result)
        
        # Check the values (accounting for floating point precision)
        self.assertAlmostEqual(result['defect_rate'], 3.0 * 0.7 + 2.75 * 0.3, places=2)
        self.assertAlmostEqual(result['return_rate'], 1.75 * 0.3 + 25.0 * 0.7, places=2)  # 1/4 returned = 25%
        self.assertEqual(result['transactions_analyzed'], 4)
        
        # Verify the quality score calculation is correct
        expected_defect_rate_score = max(0, 10 - (result['defect_rate'] / 2))
        expected_return_rate_score = max(0, 10 - (result['return_rate'] / 2))
        expected_quality_score = (
            8.75 * 0.4 +  # avg_quality_score
            expected_defect_rate_score * 0.4 +
            expected_return_rate_score * 0.2
        )
        self.assertAlmostEqual(result['quality_score'], expected_quality_score, places=2)

    def test_calculate_delivery_metrics(self):
        """Test delivery metrics calculation"""
        # Mock the returned data from order service
        today = date.today()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)
        
        self.service.order_service.get_supplier_transactions.return_value = [
            {
                'expected_delivery_date': yesterday,
                'actual_delivery_date': yesterday,  # On time
            },
            {
                'expected_delivery_date': yesterday,
                'actual_delivery_date': today,  # 1 day late
            },
            {
                'expected_delivery_date': today,
                'actual_delivery_date': yesterday,  # Early
            },
            {
                'expected_delivery_date': yesterday,
                'actual_delivery_date': tomorrow,  # 2 days late
            }
        ]
        
        self.service.order_service.get_supplier_performance_records.return_value = [
            {'on_time_delivery_rate': 85.0, 'average_delay_days': 1.2, 'fill_rate': 95.0, 'order_accuracy': 98.0},
            {'on_time_delivery_rate': 90.0, 'average_delay_days': 0.8, 'fill_rate': 93.0, 'order_accuracy': 97.0}
        ]
        
        self.service.warehouse_service.get_supplier_products.return_value = [
            {'lead_time_days': 5},
            {'lead_time_days': 7},
            {'lead_time_days': 3}
        ]
        
        # Call the method
        result = self.service.calculate_delivery_metrics(self.supplier_id)
        
        # Verify the services were called correctly
        self.service.order_service.get_supplier_transactions.assert_called_once()
        self.service.order_service.get_supplier_performance_records.assert_called_once()
        self.service.warehouse_service.get_supplier_products.assert_called_once()
        
        # Verify the calculation results
        self.assertIn('delivery_score', result)
        self.assertIn('on_time_delivery_rate', result)
        self.assertIn('average_delay_days', result)
        self.assertIn('average_lead_time', result)
        self.assertIn('transactions_analyzed', result)
        
        # Check the values
        # 2 out of 4 deliveries were on time or early = 50%
        expected_on_time_rate = 50.0 * 0.7 + 87.5 * 0.3  # 87.5 is average of 85 and 90
        self.assertAlmostEqual(result['on_time_delivery_rate'], expected_on_time_rate, places=2)
        
        # Average delay: (1 + 2) / 2 = 1.5 (only delayed), avg_recorded_delay = 1.0
        expected_avg_delay = 1.5 * 0.7 + 1.0 * 0.3
        self.assertAlmostEqual(result['average_delay_days'], expected_avg_delay, places=2)
        
        self.assertEqual(result['average_lead_time'], 5)  # (5 + 7 + 3) / 3
        self.assertEqual(result['transactions_analyzed'], 4)
        
        # Verify the delivery score calculation is correct
        expected_on_time_score = expected_on_time_rate / 10
        expected_delay_score = max(0, 10 - min(10, expected_avg_delay * 2))
        expected_delivery_score = (
            expected_on_time_score * 0.6 +
            expected_delay_score * 0.4
        )
        self.assertAlmostEqual(result['delivery_score'], expected_delivery_score, places=2)

    def test_calculate_price_metrics(self):
        """Test price metrics calculation"""
        # Mock the returned data from order service
        self.service.order_service.get_supplier_performance_records.return_value = [
            {'price_competitiveness': 7.0},
            {'price_competitiveness': 8.0}
        ]
        
        # Mock the returned data from warehouse service
        self.service.warehouse_service.get_supplier_products.return_value = [
            {'product_id': 1, 'unit_price': 10.0},
            {'product_id': 2, 'unit_price': 20.0},
            {'product_id': 3, 'unit_price': 15.0}
        ]
        
        self.service.warehouse_service.get_product_suppliers.side_effect = [
            # Suppliers for product 1 (unit_price 10.0 is the best/lowest)
            [
                {'unit_price': 10.0},  # Our supplier
                {'unit_price': 12.0},
                {'unit_price': 15.0}
            ],
            # Suppliers for product 2 (unit_price 20.0 is the worst/highest)
            [
                {'unit_price': 15.0},
                {'unit_price': 18.0},
                {'unit_price': 20.0}  # Our supplier
            ],
            # Suppliers for product 3 (unit_price 15.0 is in the middle)
            [
                {'unit_price': 14.0},
                {'unit_price': 15.0},  # Our supplier
                {'unit_price': 16.0}
            ]
        ]
        
        # Call the method
        result = self.service.calculate_price_metrics(self.supplier_id)
        
        # Verify the services were called correctly
        self.service.order_service.get_supplier_performance_records.assert_called_once()
        self.service.warehouse_service.get_supplier_products.assert_called_once()
        self.assertEqual(self.service.warehouse_service.get_product_suppliers.call_count, 3)
        
        # Verify the calculation results
        self.assertIn('price_score', result)
        self.assertIn('price_competitiveness', result)
        self.assertIn('calculated_price_competitiveness', result)
        self.assertIn('products_analyzed', result)
        
        # Check the values
        self.assertEqual(result['products_analyzed'], 3)
        self.assertAlmostEqual(result['price_competitiveness'], 7.5, places=2)  # (7.0 + 8.0) / 2
        
        # For our products:
        # Product 1: Best price (10.0) = 10.0 score
        # Product 2: Worst price (20.0) = 0.0 score
        # Product 3: Middle price (15.0) = 5.0 score
        # Average: (10 + 0 + 5) / 3 = 5.0
        self.assertAlmostEqual(result['calculated_price_competitiveness'], 5.0, places=2)
        
        # Overall price score is weighted: 5.0 * 0.7 + 7.5 * 0.3 = 5.75
        self.assertAlmostEqual(result['price_score'], 5.75, places=2)

    def test_calculate_service_metrics(self):
        """Test service metrics calculation"""
        # Mock the returned data from order service
        self.service.order_service.get_supplier_performance_records.return_value = [
            {
                'responsiveness': 8.0, 
                'issue_resolution_time': 24.0,  # 24 hours
                'fill_rate': 95.0, 
                'order_accuracy': 98.0
            },
            {
                'responsiveness': 7.0, 
                'issue_resolution_time': 36.0,  # 36 hours
                'fill_rate': 93.0, 
                'order_accuracy': 97.0
            }
        ]
        
        # Call the method
        result = self.service.calculate_service_metrics(self.supplier_id)
        
        # Verify the order service was called correctly
        self.service.order_service.get_supplier_performance_records.assert_called_once()
        
        # Verify the calculation results
        self.assertIn('service_score', result)
        self.assertIn('responsiveness', result)
        self.assertIn('issue_resolution_time', result)
        self.assertIn('fill_rate', result)
        self.assertIn('order_accuracy', result)
        
        # Check the values
        self.assertAlmostEqual(result['responsiveness'], 7.5, places=2)  # (8.0 + 7.0) / 2
        self.assertAlmostEqual(result['issue_resolution_time'], 30.0, places=2)  # (24.0 + 36.0) / 2
        self.assertAlmostEqual(result['fill_rate'], 94.0, places=2)  # (95.0 + 93.0) / 2
        self.assertAlmostEqual(result['order_accuracy'], 97.5, places=2)  # (98.0 + 97.0) / 2
        
        # Verify the service score calculation is correct
        expected_issue_resolution_score = max(0, 10 - (30.0 / 7.2))
        expected_fill_rate_score = 94.0 / 10
        expected_order_accuracy_score = 97.5 / 10
        
        expected_service_score = (
            7.5 * 0.3 +  # responsiveness
            expected_issue_resolution_score * 0.2 +
            expected_fill_rate_score * 0.25 +
            expected_order_accuracy_score * 0.25
        )
        self.assertAlmostEqual(result['service_score'], expected_service_score, places=2)

    @patch('ranking_engine.services.metrics_service.MetricsService.get_active_configuration')
    def test_calculate_combined_metrics(self, mock_get_config):
        """Test combined metrics calculation"""
        # Set up the mock to return our configuration
        mock_get_config.return_value = self.mock_config
        
        # Create mock results for individual metric calculations
        mock_quality_metrics = {
            'quality_score': 8.5,
            'defect_rate': 2.5,
            'return_rate': 1.5,
            'raw_quality_score': 9.0,
            'transactions_analyzed': 200,
            'quantity_analyzed': 5000
        }
        
        mock_delivery_metrics = {
            'delivery_score': 7.8,
            'on_time_delivery_rate': 92.0,
            'average_delay_days': 0.5,
            'average_lead_time': 4.0,
            'fill_rate': 95.0,
            'order_accuracy': 98.0,
            'transactions_analyzed': 180
        }
        
        mock_price_metrics = {
            'price_score': 6.7,
            'price_competitiveness': 7.0,
            'calculated_price_competitiveness': 6.5,
            'products_analyzed': 15
        }
        
        mock_service_metrics = {
            'service_score': 8.2,
            'responsiveness': 7.5,
            'issue_resolution_time': 24.0,
            'fill_rate': 94.0,
            'order_accuracy': 97.5
        }
        
        # Mock the individual metric calculation methods
        self.service.calculate_quality_metrics = MagicMock(return_value=mock_quality_metrics)
        self.service.calculate_delivery_metrics = MagicMock(return_value=mock_delivery_metrics)
        self.service.calculate_price_metrics = MagicMock(return_value=mock_price_metrics)
        self.service.calculate_service_metrics = MagicMock(return_value=mock_service_metrics)
        
        # Call the method
        result = self.service.calculate_combined_metrics(self.supplier_id, days=30)
        
        # Verify the individual metric methods were called correctly
        self.service.calculate_quality_metrics.assert_called_once_with(self.supplier_id, 30)
        self.service.calculate_delivery_metrics.assert_called_once_with(self.supplier_id, 30)
        self.service.calculate_price_metrics.assert_called_once_with(self.supplier_id, 30)
        self.service.calculate_service_metrics.assert_called_once_with(self.supplier_id, 30)
        
        # Verify the combined result structure
        self.assertIn('supplier_id', result)
        self.assertIn('overall_score', result)
        self.assertIn('quality_score', result)
        self.assertIn('delivery_score', result)
        self.assertIn('price_score', result)
        self.assertIn('service_score', result)
        self.assertIn('quality_metrics', result)
        self.assertIn('delivery_metrics', result)
        self.assertIn('price_metrics', result)
        self.assertIn('service_metrics', result)
        self.assertIn('calculation_date', result)
        
        # Verify the weighted overall score calculation
        expected_overall_score = (
            8.5 * 0.3 +  # quality_score * quality_weight
            7.8 * 0.3 +  # delivery_score * delivery_weight
            6.7 * 0.2 +  # price_score * price_weight
            8.2 * 0.2    # service_score * service_weight
        )
        self.assertAlmostEqual(result['overall_score'], expected_overall_score, places=2)
        
        # Verify that the individual metric dictionaries are included
        self.assertEqual(result['quality_metrics'], mock_quality_metrics)
        self.assertEqual(result['delivery_metrics'], mock_delivery_metrics)
        self.assertEqual(result['price_metrics'], mock_price_metrics)
        self.assertEqual(result['service_metrics'], mock_service_metrics)

    def test_calculate_metrics_for_all_suppliers(self):
        """Test calculating metrics for all suppliers"""
        # Mock the user service to return supplier list
        self.service.user_service.get_active_suppliers.return_value = [
            {'id': 101, 'name': 'Supplier A', 'code': 'SUP-A'},
            {'id': 102, 'name': 'Supplier B', 'code': 'SUP-B'},
            {'id': 103, 'name': 'Supplier C', 'code': 'SUP-C'}
        ]
        
        # Create mock results for combined metrics
        def mock_combined_metrics(supplier_id, days):
            scores = {
                101: {'overall_score': 9.2, 'quality_score': 9.0, 'delivery_score': 8.5, 'price_score': 7.8, 'service_score': 8.9},
                102: {'overall_score': 7.5, 'quality_score': 7.2, 'delivery_score': 7.0, 'price_score': 8.0, 'service_score': 7.5},
                103: {'overall_score': 8.3, 'quality_score': 8.0, 'delivery_score': 7.8, 'price_score': 8.5, 'service_score': 8.0}
            }
            base_metrics = {
                'supplier_id': supplier_id,
                'quality_metrics': {},
                'delivery_metrics': {},
                'price_metrics': {},
                'service_metrics': {},
                'calculation_date': date.today()
            }
            return {**base_metrics, **scores[supplier_id]}
        
        # Mock the combined metrics calculation method
        self.service.calculate_combined_metrics = MagicMock(side_effect=mock_combined_metrics)
        
        # Call the method
        result = self.service.calculate_metrics_for_all_suppliers(days=60)
        
        # Verify the user service was called
        self.service.user_service.get_active_suppliers.assert_called_once()
        
        # Verify combined metrics was called for each supplier
        self.assertEqual(self.service.calculate_combined_metrics.call_count, 3)
        
        # Verify result structure
        self.assertEqual(len(result), 3)
        
        # Verify suppliers are sorted by overall score (highest first)
        self.assertEqual(result[0]['supplier_id'], 101)  # 9.2 score (highest)
        self.assertEqual(result[1]['supplier_id'], 103)  # 8.3 score (middle)
        self.assertEqual(result[2]['supplier_id'], 102)  # 7.5 score (lowest)
        
        # Verify ranks were assigned correctly
        self.assertEqual(result[0]['rank'], 1)
        self.assertEqual(result[1]['rank'], 2)
        self.assertEqual(result[2]['rank'], 3)
        
        # Verify supplier names and codes were added
        self.assertEqual(result[0]['supplier_name'], 'Supplier A')
        self.assertEqual(result[0]['supplier_code'], 'SUP-A')
        self.assertEqual(result[1]['supplier_name'], 'Supplier C')
        self.assertEqual(result[1]['supplier_code'], 'SUP-C')
        self.assertEqual(result[2]['supplier_name'], 'Supplier B')
        self.assertEqual(result[2]['supplier_code'], 'SUP-B')


if __name__ == '__main__':
    unittest.main()
import unittest
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta, date

from api.models import (
    Supplier, Product, SupplierProduct, SupplierPerformance,
    Transaction, QLearningState, QLearningAction, QTableEntry,
    SupplierRanking, RankingConfiguration
)
from ranking_engine.q_learning.agent import SupplierRankingAgent
from ranking_engine.q_learning.environment import SupplierEnvironment
from ranking_engine.q_learning.state_mapper import StateMapper
from ranking_engine.services.ranking_service import RankingService
from ranking_engine.services.supplier_service import SupplierService
from ranking_engine.services.metrics_service import MetricsService
from ranking_engine.utils.data_preprocessing import preprocess_supplier_data


class RankingIntegrationTests(TestCase):
    """Test the integration between different components of the ranking system"""

    def setUp(self):
        # Create test data
        # Suppliers
        self.supplier1 = Supplier.objects.create(
            name="Quality Supplier",
            code="SUP001",
            contact_email="quality@example.com",
            address="123 Quality St",
            country="Quality Land",
            supplier_size="M",
            credit_score=85.0,
            average_lead_time=5
        )
        
        self.supplier2 = Supplier.objects.create(
            name="Budget Supplier",
            code="SUP002",
            contact_email="budget@example.com",
            address="456 Budget Ave",
            country="Budget Land",
            supplier_size="S",
            credit_score=65.0,
            average_lead_time=10
        )
        
        # Products
        self.product1 = Product.objects.create(
            name="Widget A",
            sku="WID-A",
            category="Widgets",
            unit_of_measure="EA"
        )
        
        # Link products to suppliers
        self.supplier_product1 = SupplierProduct.objects.create(
            supplier=self.supplier1,
            product=self.product1,
            unit_price=100.00,
            minimum_order_quantity=10,
            lead_time_days=5,
            is_preferred=True
        )
        
        self.supplier_product2 = SupplierProduct.objects.create(
            supplier=self.supplier2,
            product=self.product1,
            unit_price=80.00,
            minimum_order_quantity=20,
            lead_time_days=12,
            is_preferred=False
        )
        
        # Performance metrics
        today = date.today()
        
        # Good supplier performance
        self.performance1 = SupplierPerformance.objects.create(
            supplier=self.supplier1,
            date=today,
            quality_score=9.5,
            defect_rate=0.5,
            return_rate=0.2,
            on_time_delivery_rate=98.0,
            average_delay_days=0.1,
            price_competitiveness=7.5,  # Not the best price
            responsiveness=9.0,
            fill_rate=99.5,
            order_accuracy=99.8,
            compliance_score=9.5
        )
        
        # Budget supplier with worse quality but better price
        self.performance2 = SupplierPerformance.objects.create(
            supplier=self.supplier2,
            date=today,
            quality_score=7.0,
            defect_rate=3.0,
            return_rate=1.5,
            on_time_delivery_rate=85.0,
            average_delay_days=1.5,
            price_competitiveness=9.0,  # Better price
            responsiveness=6.5,
            fill_rate=90.0,
            order_accuracy=95.0,
            compliance_score=8.0
        )
        
        # Transactions
        order_date = timezone.now() - timedelta(days=30)
        expected_delivery = order_date + timedelta(days=5)
        actual_delivery = expected_delivery  # On time
        
        self.transaction1 = Transaction.objects.create(
            supplier=self.supplier1,
            product=self.product1,
            order_date=order_date,
            expected_delivery_date=expected_delivery,
            actual_delivery_date=actual_delivery,
            quantity=100,
            unit_price=100.00,
            status="DELIVERED",
            defect_count=1
        )
        
        # Late delivery for supplier 2
        order_date2 = timezone.now() - timedelta(days=30)
        expected_delivery2 = order_date2 + timedelta(days=10)
        actual_delivery2 = expected_delivery2 + timedelta(days=3)  # 3 days late
        
        self.transaction2 = Transaction.objects.create(
            supplier=self.supplier2,
            product=self.product1,
            order_date=order_date2,
            expected_delivery_date=expected_delivery2,
            actual_delivery_date=actual_delivery2,
            quantity=200,
            unit_price=80.00,
            status="DELIVERED",
            defect_count=8
        )
        
        # Create states
        self.state_high_quality = QLearningState.objects.create(
            name="high_quality",
            description="High quality performance"
        )
        
        self.state_low_quality = QLearningState.objects.create(
            name="low_quality",
            description="Low quality performance"
        )
        
        self.state_medium_quality = QLearningState.objects.create(
            name="medium_quality",
            description="Medium quality performance"
        )
        
        # Create actions
        self.action_increase = QLearningAction.objects.create(
            name="increase_rank",
            description="Increase supplier rank"
        )
        
        self.action_maintain = QLearningAction.objects.create(
            name="maintain_rank",
            description="Maintain supplier rank"
        )
        
        self.action_decrease = QLearningAction.objects.create(
            name="decrease_rank",
            description="Decrease supplier rank"
        )
        
        # Create Q-values
        QTableEntry.objects.create(
            state=self.state_high_quality,
            action=self.action_increase,
            q_value=0.9
        )
        
        QTableEntry.objects.create(
            state=self.state_high_quality,
            action=self.action_maintain,
            q_value=0.7
        )
        
        QTableEntry.objects.create(
            state=self.state_high_quality,
            action=self.action_decrease,
            q_value=0.1
        )
        
        QTableEntry.objects.create(
            state=self.state_low_quality,
            action=self.action_increase,
            q_value=0.2
        )
        
        QTableEntry.objects.create(
            state=self.state_low_quality,
            action=self.action_maintain,
            q_value=0.3
        )
        
        QTableEntry.objects.create(
            state=self.state_low_quality,
            action=self.action_decrease,
            q_value=0.8
        )
        
        # Configuration
        self.config = RankingConfiguration.objects.create(
            name="test_integration_config",
            learning_rate=0.1,
            discount_factor=0.9,
            exploration_rate=0.0,  # Deterministic for testing
            quality_weight=0.4,
            delivery_weight=0.3,
            price_weight=0.2,
            service_weight=0.1
        )
        
        # Initialize components
        self.state_mapper = StateMapper()
        self.environment = SupplierEnvironment()
        self.agent = SupplierRankingAgent(self.config)
        self.metrics_service = MetricsService()
        self.supplier_service = SupplierService()
        self.ranking_service = RankingService()
        # Store the other objects as instance variables if they're needed in tests
        self.agent = self.agent
        self.environment = self.environment
        self.state_mapper = self.state_mapper
    
    def test_end_to_end_ranking_process(self):
        """Test the complete ranking process from data to final rankings"""
        # Run the ranking process
        rankings = self.ranking_service.generate_supplier_rankings()
        
        # Check that rankings were created
        self.assertEqual(len(rankings), 2)  # Two suppliers
        
        # Get rankings by supplier
        supplier1_ranking = next((r for r in rankings if r.supplier == self.supplier1), None)
        supplier2_ranking = next((r for r in rankings if r.supplier == self.supplier2), None)
        
        self.assertIsNotNone(supplier1_ranking)
        self.assertIsNotNone(supplier2_ranking)
        
        # Check that the quality supplier has a higher rank (lower number is better)
        self.assertTrue(supplier1_ranking.rank < supplier2_ranking.rank)
        
        # Check that scores reflect the input data
        self.assertTrue(supplier1_ranking.quality_score > supplier2_ranking.quality_score)
        self.assertTrue(supplier1_ranking.delivery_score > supplier2_ranking.delivery_score)
        self.assertTrue(supplier1_ranking.price_score < supplier2_ranking.price_score)
        
        # Check that overall scores were calculated correctly
        # Using the weights from config
        expected_score1 = (
            self.config.quality_weight * supplier1_ranking.quality_score +
            self.config.delivery_weight * supplier1_ranking.delivery_score +
            self.config.price_weight * supplier1_ranking.price_score +
            self.config.service_weight * supplier1_ranking.service_score
        )
        
        self.assertAlmostEqual(supplier1_ranking.overall_score, expected_score1, places=2)

    def test_q_learning_updates(self):
        """Test that Q-values are updated after processing transactions"""
        # Get initial Q-values
        q_entry_high_increase = QTableEntry.objects.get(
            state=self.state_high_quality, 
            action=self.action_increase
        )
        initial_q_value = q_entry_high_increase.q_value
        
        # Run a learning iteration that should update Q-values
        self.ranking_service.update_q_values_from_transactions([self.transaction1, self.transaction2])
        
        # Check that Q-values were updated
        q_entry_high_increase.refresh_from_db()
        self.assertNotEqual(q_entry_high_increase.q_value, initial_q_value)
        
    def test_data_preprocessing(self):
        """Test that data preprocessing works correctly"""
        # Run preprocessing on transaction data
        processed_data = preprocess_supplier_data([self.transaction1, self.transaction2])
        
        # Check that preprocessing produces expected output
        self.assertIn(self.supplier1.id, processed_data)
        self.assertIn(self.supplier2.id, processed_data)
        
        # Check that metrics were calculated correctly
        supplier1_data = processed_data[self.supplier1.id]
        self.assertIn('defect_rate', supplier1_data)
        self.assertIn('on_time_delivery_rate', supplier1_data)
        
        # Check specific metric calculation
        # For supplier1's transaction, there was 1 defect in 100 items
        expected_defect_rate = 1 / 100 * 100  # As percentage
        self.assertAlmostEqual(supplier1_data['defect_rate'], expected_defect_rate, places=2)


if __name__ == '__main__':
    unittest.main()
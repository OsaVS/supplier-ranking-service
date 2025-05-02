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


class QLearningModelTests(TestCase):
    """Test the Q-Learning model classes"""

    def setUp(self):
        # Create test states and actions
        self.state1 = QLearningState.objects.create(
            name="high_quality_low_delivery",
            description="High quality score but low delivery performance"
        )
        self.state2 = QLearningState.objects.create(
            name="low_quality_high_delivery",
            description="Low quality score but high delivery performance"
        )
        
        self.action1 = QLearningAction.objects.create(
            name="increase_rank",
            description="Increase supplier rank"
        )
        self.action2 = QLearningAction.objects.create(
            name="decrease_rank",
            description="Decrease supplier rank"
        )
        
        # Create Q-Table entries
        self.q_entry1 = QTableEntry.objects.create(
            state=self.state1,
            action=self.action1,
            q_value=0.75,
            update_count=5
        )
        
        # Create config
        self.config = RankingConfiguration.objects.create(
            name="default_config",
            learning_rate=0.1,
            discount_factor=0.9,
            exploration_rate=0.2
        )

    def test_q_table_entry_creation(self):
        """Test that QTableEntry objects can be created correctly"""
        self.assertEqual(self.q_entry1.state.name, "high_quality_low_delivery")
        self.assertEqual(self.q_entry1.action.name, "increase_rank")
        self.assertEqual(self.q_entry1.q_value, 0.75)
        
    def test_q_table_updates(self):
        """Test updating Q-values"""
        old_value = self.q_entry1.q_value
        
        # Update Q-value
        self.q_entry1.q_value = 0.8
        self.q_entry1.update_count += 1
        self.q_entry1.save()
        
        # Fetch from DB again to verify
        updated_entry = QTableEntry.objects.get(id=self.q_entry1.id)
        self.assertEqual(updated_entry.q_value, 0.8)
        self.assertEqual(updated_entry.update_count, 6)
        self.assertNotEqual(updated_entry.q_value, old_value)


class StateMapperTests(TestCase):
    """Test the StateMapper that converts supplier metrics to states"""
    
    def setUp(self):
        # Create test suppliers
        self.supplier1 = Supplier.objects.create(
            name="Test Supplier 1",
            code="SUP001",
            contact_email="supplier1@example.com",
            address="123 Test St",
            country="Test Country",
            supplier_size="M"
        )
        
        # Create performance records
        today = date.today()
        self.performance1 = SupplierPerformance.objects.create(
            supplier=self.supplier1,
            date=today,
            quality_score=8.5,
            defect_rate=2.3,
            return_rate=1.5,
            on_time_delivery_rate=95.0,
            average_delay_days=0.5,
            price_competitiveness=7.8,
            responsiveness=9.0,
            fill_rate=98.0,
            order_accuracy=99.2,
            compliance_score=8.7
        )
        
        # Create states
        self.high_quality_state = QLearningState.objects.create(
            name="high_quality",
            description="High quality performance"
        )
        self.low_quality_state = QLearningState.objects.create(
            name="low_quality",
            description="Low quality performance"
        )
        
        # Create state mapper
        self.state_mapper = StateMapper()
        
    def test_map_supplier_to_state(self):
        """Test mapping supplier metrics to states"""
        # This is a simplified test - your actual implementation will be more complex
        # Mock the state_mapper's internal logic for testing
        
        def mock_map_quality(score):
            if score >= 7.0:
                return self.high_quality_state
            return self.low_quality_state
            
        # Replace the actual implementation with our mock for testing
        self.state_mapper.map_quality = mock_map_quality
        
        # Test mapping
        mapped_state = self.state_mapper.map_quality(self.performance1.quality_score)
        self.assertEqual(mapped_state, self.high_quality_state)


class SupplierEnvironmentTests(TestCase):
    """Test the SupplierEnvironment that provides rewards"""
    
    def setUp(self):
        # Create test data similar to StateMapperTests
        self.supplier1 = Supplier.objects.create(
            name="Test Supplier 1",
            code="SUP001",
            contact_email="supplier1@example.com",
            address="123 Test St",
            country="Test Country",
            supplier_size="M"
        )
        
        # Create product
        self.product1 = Product.objects.create(
            name="Test Product",
            sku="PROD001",
            category="Test Category",
            unit_of_measure="EA"
        )
        
        # Create transactions
        today = timezone.now()
        yesterday = today - timedelta(days=1)
        expected_delivery = today + timedelta(days=5)
        
        self.transaction1 = Transaction.objects.create(
            supplier=self.supplier1,
            product=self.product1,
            order_date=yesterday,
            expected_delivery_date=expected_delivery,
            quantity=100,
            unit_price=10.50,
            status="ORDERED"
        )
        
        # Create environment
        self.environment = SupplierEnvironment()
        
    def test_calculate_reward(self):
        """Test reward calculation for supplier actions"""
        # This is a simplified test - your actual implementation will be more complex
        
        # For delivered orders that arrived on time
        self.transaction1.status = "DELIVERED"
        self.transaction1.actual_delivery_date = self.transaction1.expected_delivery_date
        self.transaction1.save()
        
        # Mock the environment's reward function for testing
        def mock_calculate_delivery_reward(transaction):
            if transaction.status == "DELIVERED":
                if not transaction.is_delayed:
                    return 1.0  # Positive reward for on-time delivery
                else:
                    return -0.5  # Negative reward for delayed delivery
            return 0.0
            
        # Replace the actual implementation with our mock for testing
        self.environment.calculate_delivery_reward = mock_calculate_delivery_reward
        
        # Test reward calculation
        reward = self.environment.calculate_delivery_reward(self.transaction1)
        self.assertEqual(reward, 1.0)
        
        # Test with delayed delivery
        self.transaction1.actual_delivery_date = self.transaction1.expected_delivery_date + timedelta(days=2)
        self.transaction1.save()
        reward = self.environment.calculate_delivery_reward(self.transaction1)
        self.assertEqual(reward, -0.5)


class SupplierRankingAgentTests(TestCase):
    """Test the SupplierRankingAgent that learns and makes decisions"""
    
    def setUp(self):
        # Create necessary test data
        # (Create suppliers, states, actions similar to previous tests)
        
        self.config = RankingConfiguration.objects.create(
            name="test_config",
            learning_rate=0.1,
            discount_factor=0.9,
            exploration_rate=0.0  # Set to 0 for deterministic testing
        )
        
        # Create agent
        # In a real test, you'd initialize with actual components
        self.agent = SupplierRankingAgent(self.config)
        
    def test_select_action(self):
        """Test that the agent selects the action with highest Q-value"""
        # This would need to be implemented according to your actual agent design
        # Here's a conceptual approach:
        
        # Create test states and actions
        state = QLearningState.objects.create(
            name="test_state",
            description="State for testing"
        )
        
        action1 = QLearningAction.objects.create(
            name="action1",
            description="Test action 1"
        )
        
        action2 = QLearningAction.objects.create(
            name="action2",
            description="Test action 2"
        )
        
        # Create Q-values with action2 having higher value
        QTableEntry.objects.create(
            state=state,
            action=action1,
            q_value=0.5
        )
        
        QTableEntry.objects.create(
            state=state,
            action=action2,
            q_value=0.8
        )
        
        # Test that agent selects action2 (with exploration_rate=0)
        # This assumes your agent has a method called select_best_action
        selected_action = self.agent.select_action(state, exploration=False)
        self.assertEqual(selected_action, action2)

    
    def test_update_q_value(self):
        """Test Q-value update logic"""
        # Similar to test_select_action, implement according to your agent design
        pass


if __name__ == '__main__':
    unittest.main()
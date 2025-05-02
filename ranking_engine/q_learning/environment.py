"""
Environment module for Q-Learning implementation.

This module simulates the supplier environment for the Q-Learning algorithm,
providing state transitions and rewards based on supplier actions.
"""

from api.models import (
    Supplier, SupplierPerformance, Transaction, QLearningAction, 
    QLearningState, RankingConfiguration, SupplierRanking
)
from django.db.models import Avg, Max, Min
from datetime import datetime, timedelta
import numpy as np
from ranking_engine.q_learning.state_mapper import StateMapper


class SupplierEnvironment:
    """
    Environment class for Q-Learning algorithm.
    
    This class simulates the supplier environment by providing state transitions
    and rewards based on supplier actions.
    """
    
    def __init__(self, config=None):
        """
        Initialize the supplier environment.
        
        Args:
            config (RankingConfiguration, optional): Configuration for the environment
        """
        # Get active configuration or default
        self.config = config or RankingConfiguration.objects.filter(is_active=True).first()
        if not self.config:
            # Create default configuration if none exists
            self.config = RankingConfiguration.objects.create(
                name="Default Configuration",
                learning_rate=0.1,
                discount_factor=0.9,
                exploration_rate=0.3,
                quality_weight=0.25,
                delivery_weight=0.25,
                price_weight=0.25,
                service_weight=0.25,
                is_active=True
            )
            
        # Initialize state mapper
        self.state_mapper = StateMapper()
        
        # Initialize available actions
        self._initialize_actions()
    
    def _initialize_actions(self):
        """Initialize the available actions for the Q-Learning algorithm."""
        # Define standard actions for supplier ranking
        standard_actions = [
            {
                'name': 'RANK_TIER_1',
                'description': 'Rank the supplier as Tier 1 (Preferred)'
            },
            {
                'name': 'RANK_TIER_2',
                'description': 'Rank the supplier as Tier 2 (Approved)'
            },
            {
                'name': 'RANK_TIER_3',
                'description': 'Rank the supplier as Tier 3 (Conditional)'
            },
            {
                'name': 'RANK_TIER_4',
                'description': 'Rank the supplier as Tier 4 (Probationary)'
            },
            {
                'name': 'RANK_TIER_5',
                'description': 'Rank the supplier as Tier 5 (Not Recommended)'
            },
            {
                'name': 'INCREASE_ORDER_VOLUME',
                'description': 'Recommend increasing order volume with this supplier'
            },
            {
                'name': 'DECREASE_ORDER_VOLUME',
                'description': 'Recommend decreasing order volume with this supplier'
            },
            {
                'name': 'FLAG_FOR_AUDIT',
                'description': 'Flag supplier for audit due to concerns'
            },
            {
                'name': 'REQUEST_QUALITY_IMPROVEMENT',
                'description': 'Request supplier to improve quality'
            },
            {
                'name': 'REQUEST_DELIVERY_IMPROVEMENT',
                'description': 'Request supplier to improve delivery performance'
            }
        ]
        
        # Create actions in database if they don't exist
        for action_data in standard_actions:
            QLearningAction.objects.get_or_create(
                name=action_data['name'],
                defaults={'description': action_data['description']}
            )
    
    def get_state(self, supplier_id):
        """
        Get the current state for a supplier.
        
        Args:
            supplier_id (int): ID of the supplier
            
        Returns:
            QLearningState: State object representing the supplier's current state
        """
        return self.state_mapper.get_supplier_state(supplier_id)
    
    def get_actions(self, state=None):
        """
        Get available actions for a state.
        
        Args:
            state (QLearningState, optional): The current state
            
        Returns:
            list: List of QLearningAction objects representing available actions
        """
        # For now, all actions are available in all states
        # This could be customized based on state if needed
        return list(QLearningAction.objects.all())
    
    def get_reward(self, supplier_id, state, action):
        """
        Calculate the reward for a supplier state-action pair.
        
        Args:
            supplier_id (int): ID of the supplier
            state (QLearningState): Current state of the supplier
            action (QLearningAction): Action taken
            
        Returns:
            float: Reward value
        """
        # Get supplier and recent performance
        try:
            supplier = Supplier.objects.get(id=supplier_id)
            cutoff_date = datetime.now().date() - timedelta(days=90)  # Last 90 days
            recent_performance = SupplierPerformance.objects.filter(
                supplier=supplier,
                date__gte=cutoff_date
            )
            
            # Parse state name to get component scores
            # State name format: Q{quality}_D{delivery}_P{price}_S{service}
            state_parts = state.name.split('_')
            quality_level = int(state_parts[0][1])
            delivery_level = int(state_parts[1][1])
            price_level = int(state_parts[2][1])
            service_level = int(state_parts[3][1])
            
            # Calculate base reward based on state components and config weights
            base_reward = (
                quality_level * self.config.quality_weight +
                delivery_level * self.config.delivery_weight +
                price_level * self.config.price_weight +
                service_level * self.config.service_weight
            )
            
            # Normalize to 0-10 scale
            base_reward = base_reward * 2  # Levels are 1-5, max weighted sum would be 5
            
            # Adjust reward based on action
            action_reward = self._calculate_action_reward(supplier, state, action)
            
            # Combine base reward with action reward
            final_reward = base_reward + action_reward
            
            return final_reward
            
        except Supplier.DoesNotExist:
            # Return neutral reward if supplier doesn't exist
            return 5.0
    
    def _calculate_action_reward(self, supplier, state, action):
        """
        Calculate the reward adjustment based on the action taken.
        
        Args:
            supplier (Supplier): Supplier object
            state (QLearningState): Current state
            action (QLearningAction): Action taken
            
        Returns:
            float: Reward adjustment value (-5 to +5)
        """
        # Parse state name to get component scores
        state_parts = state.name.split('_')
        quality_level = int(state_parts[0][1])
        delivery_level = int(state_parts[1][1])
        price_level = int(state_parts[2][1])
        service_level = int(state_parts[3][1])
        
        # Calculate average level across dimensions
        avg_level = (quality_level + delivery_level + price_level + service_level) / 4
        
        # Initialize reward adjustment
        adjustment = 0.0
        
        # Adjust reward based on action name
        if action.name.startswith('RANK_TIER'):
            # Extract tier number from action name
            tier = int(action.name[-1])
            
            # Calculate how appropriate the ranking is
            # Higher reward when the tier matches the average state level
            tier_appropriateness = 5 - abs(tier - (6 - avg_level))  # 6-avg_level to convert 1-5 to 5-1
            adjustment += tier_appropriateness
            
        elif action.name == 'INCREASE_ORDER_VOLUME':
            # Reward for increasing volume with good suppliers
            if avg_level >= 3.5:
                adjustment += 3.0
            else:
                adjustment -= 3.0
                
        elif action.name == 'DECREASE_ORDER_VOLUME':
            # Reward for decreasing volume with poor suppliers
            if avg_level <= 2.5:
                adjustment += 3.0
            else:
                adjustment -= 3.0
                
        elif action.name == 'FLAG_FOR_AUDIT':
            # Reward for flagging suppliers with inconsistent metrics
            variance = np.var([quality_level, delivery_level, price_level, service_level])
            if variance >= 1.5 or avg_level <= 2.0:
                adjustment += 2.0
            else:
                adjustment -= 1.0
                
        elif action.name == 'REQUEST_QUALITY_IMPROVEMENT':
            # Reward for requesting quality improvement from low-quality suppliers
            if quality_level <= 3:
                adjustment += 2.0
            else:
                adjustment -= 2.0
                
        elif action.name == 'REQUEST_DELIVERY_IMPROVEMENT':
            # Reward for requesting delivery improvement from suppliers with poor delivery
            if delivery_level <= 3:
                adjustment += 2.0
            else:
                adjustment -= 2.0
        
        return adjustment
    
    def next_state(self, supplier_id, action):
        """
        Determine the next state after taking an action.
        
        Note: In a real environment, the next state would depend on the
        action taken and external factors. For this simulation, we'll
        return the current state since actions don't immediately change
        supplier performance.
        
        Args:
            supplier_id (int): ID of the supplier
            action (QLearningAction): Action taken
            
        Returns:
            QLearningState: The next state
        """
        # In this implementation, we simply return the current state
        # In a production environment, this might simulate how supplier
        # performance changes based on the actions taken
        return self.state_mapper.get_supplier_state(supplier_id)
    
    def update_rankings(self, supplier_id, action):
        """
        Update supplier rankings based on the action taken.
        
        Args:
            supplier_id (int): ID of the supplier
            action (QLearningAction): Action taken
            
        Returns:
            SupplierRanking: Updated supplier ranking
        """
        supplier = Supplier.objects.get(id=supplier_id)
        current_state = self.get_state(supplier_id)
        today = datetime.now().date()
        
        # Parse state components
        state_parts = current_state.name.split('_')
        quality_level = int(state_parts[0][1])
        delivery_level = int(state_parts[1][1])
        price_level = int(state_parts[2][1])
        service_level = int(state_parts[3][1])
        
        # Calculate scores (convert from 1-5 scale to 0-10 scale)
        quality_score = (quality_level - 1) * 2.5
        delivery_score = (delivery_level - 1) * 2.5
        price_score = (price_level - 1) * 2.5
        service_score = (service_level - 1) * 2.5
        
        # Calculate overall score using configuration weights
        overall_score = (
            quality_score * self.config.quality_weight +
            delivery_score * self.config.delivery_weight +
            price_score * self.config.price_weight +
            service_score * self.config.service_weight
        ) * 4  # Scale up to 0-10
        
        # Determine rank based on action
        rank = None
        if action.name.startswith('RANK_TIER'):
            # Extract tier number from action name and convert to rank
            tier = int(action.name[-1])
            # Calculate actual rank based on tier
            # Tier 1: ranks 1-20%, Tier 2: ranks 21-40%, etc.
            supplier_count = Supplier.objects.filter(is_active=True).count()
            tier_size = max(1, supplier_count // 5)  # At least 1 supplier per tier
            rank_min = (tier - 1) * tier_size + 1
            rank_max = tier * tier_size
            
            # For now, assign the middle rank of the tier
            rank = (rank_min + rank_max) // 2
        else:
            # For non-ranking actions, calculate rank based on overall score
            # Get current rankings to determine relative position
            current_rankings = SupplierRanking.objects.filter(date=today)
            
            if current_rankings.exists():
                # Find position based on overall score
                higher_count = current_rankings.filter(overall_score__gt=overall_score).count()
                rank = higher_count + 1
            else:
                # First ranking of the day
                rank = 1
        
        # Create or update ranking
        ranking, created = SupplierRanking.objects.update_or_create(
            supplier=supplier,
            date=today,
            defaults={
                'overall_score': overall_score,
                'quality_score': quality_score,
                'delivery_score': delivery_score,
                'price_score': price_score,
                'service_score': service_score,
                'rank': rank,
                'state': current_state,
                'notes': f"Ranking updated via {action.name} action"
            }
        )
        
        return ranking
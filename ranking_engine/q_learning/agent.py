"""
Agent module for Q-Learning implementation.

This module implements the Q-Learning agent that learns to rank suppliers
based on their performance metrics.
"""

from api.models import (
    QLearningState, QLearningAction, QTableEntry,
    SupplierRanking, RankingConfiguration
)
from ranking_engine.q_learning.environment import SupplierEnvironment
from connectors.group29_connector import Group29Connector
from connectors.group30_connector import Group30Connector
from connectors.group32_connector import Group32Connector
from ranking_engine.services.supplier_service import SupplierService
from ranking_engine.services.metrics_service import MetricsService
import random
import numpy as np
import logging

logger = logging.getLogger(__name__)


class SupplierRankingAgent:
    """
    Q-Learning agent for supplier ranking.
    
    This class implements the Q-Learning algorithm to learn optimal
    supplier ranking policies based on performance metrics.
    """
    
    def __init__(self, config=None):
        """
        Initialize the Q-Learning agent.
        
        Args:
            config (RankingConfiguration, optional): Configuration for the agent
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
        
        # Initialize Q-Learning parameters
        self.learning_rate = self.config.learning_rate
        self.discount_factor = self.config.discount_factor
        self.exploration_rate = self.config.exploration_rate
        
        # Initialize environment
        self.environment = SupplierEnvironment(config=self.config)
        
        # Initialize service connectors
        self.supplier_service = SupplierService()
        self.metrics_service = MetricsService()
        self.demand_forecast_connector = Group29Connector()
        self.blockchain_connector = Group30Connector()
        self.logistics_connector = Group32Connector()
    
    def select_action(self, state, available_actions=None, exploration=True):
        """
        Select an action using epsilon-greedy policy.
        
        Args:
            state (QLearningState): Current state
            available_actions (list, optional): List of available actions
            exploration (bool): Whether to use exploration
            
        Returns:
            QLearningAction: Selected action
        """
        # Get available actions if not provided
        if available_actions is None:
            available_actions = self.environment.get_actions(state)
        
        # Exploration: random action
        if exploration and random.random() < self.exploration_rate:
            return random.choice(available_actions)
        
        # Exploitation: best action based on Q-values
        q_values = []
        
        for action in available_actions:
            # Get Q-value for state-action pair
            q_entry, created = QTableEntry.objects.get_or_create(
                state=state,
                action=action,
                defaults={'q_value': 0.0}
            )
            q_values.append((action, q_entry.q_value))
        
        # Find action with maximum Q-value
        if q_values:
            # In case of ties, randomly select among the best actions
            max_q = max(q_values, key=lambda x: x[1])[1]
            best_actions = [action for action, q_value in q_values if q_value == max_q]
            return random.choice(best_actions)
        else:
            # If no Q-values, select random action
            return random.choice(available_actions)
    
    def learn(self, state, action, reward, next_state):
        """
        Update Q-value for a state-action pair based on reward and next state.
        
        Args:
            state (QLearningState): Current state
            action (QLearningAction): Action taken
            reward (float): Reward received
            next_state (QLearningState): Next state
            
        Returns:
            float: Updated Q-value
        """
        # Get current Q-value
        q_entry, created = QTableEntry.objects.get_or_create(
            state=state,
            action=action,
            defaults={'q_value': 0.0}
        )
        current_q = q_entry.q_value
        
        # Get maximum Q-value for next state
        next_actions = self.environment.get_actions(next_state)
        next_q_values = []
        
        for next_action in next_actions:
            next_q_entry, created = QTableEntry.objects.get_or_create(
                state=next_state,
                action=next_action,
                defaults={'q_value': 0.0}
            )
            next_q_values.append(next_q_entry.q_value)
        
        max_next_q = max(next_q_values) if next_q_values else 0.0
        
        # Update Q-value using Q-learning formula
        new_q = current_q + self.learning_rate * (
            reward + self.discount_factor * max_next_q - current_q
        )
        
        # Update Q-value in database
        q_entry.q_value = new_q
        q_entry.update_count += 1
        q_entry.save()
        
        return new_q
    
    def rank_supplier(self, supplier_id, update_ranking=True, exploration=True):
        """
        Rank a supplier using the learned Q-values.
        
        Args:
            supplier_id (int): ID of the supplier
            update_ranking (bool): Whether to update the ranking in database
            exploration (bool): Whether to use exploration
            
        Returns:
            tuple: (action, reward, ranking)
        """
        try:
            # Get supplier from supplier service
            supplier = self.supplier_service.get_supplier(supplier_id)
            
            if not supplier:
                logger.error(f"Supplier with ID {supplier_id} does not exist or could not be fetched")
                return None, 0.0, None
                
            # Get current state
            current_state = self.environment.get_state(supplier_id)
            
            # Select action
            selected_action = self.select_action(current_state, exploration=exploration)
            
            # Get reward
            reward = self.environment.get_reward(supplier_id, current_state, selected_action)
            
            # Get next state
            next_state = self.environment.next_state(supplier_id, selected_action)
            
            # Update Q-value
            self.learn(current_state, selected_action, reward, next_state)
            
            # Update ranking in database if requested
            ranking = None
            if update_ranking:
                ranking = self.environment.update_rankings(supplier_id, selected_action)
            
            return selected_action, reward, ranking
            
        except Exception as e:
            logger.error(f"Error in rank_supplier for supplier ID {supplier_id}: {e}")
            return None, 0.0, None
    
    def batch_train(self, iterations=100, supplier_ids=None):
        """
        Train the agent on multiple suppliers for multiple iterations.
        
        Args:
            iterations (int): Number of training iterations
            supplier_ids (list, optional): List of supplier IDs to train on
            
        Returns:
            dict: Training statistics
        """
        # Get all active suppliers if supplier_ids not provided
        if supplier_ids is None:
            # Use supplier service to get active supplier IDs
            supplier_ids = self.supplier_service.get_active_supplier_ids()
        
        stats = {
            'iterations': iterations,
            'suppliers_trained': len(supplier_ids),
            'total_updates': 0,
            'avg_reward': 0.0,
            'max_reward': float('-inf'),
            'min_reward': float('inf'),
            'final_q_values': {}
        }
        
        total_reward = 0.0
        
        # Train for specified iterations
        for i in range(iterations):
            # Decrease exploration rate over time
            self.exploration_rate = max(0.05, self.config.exploration_rate * (1.0 - i/iterations))
            
            iteration_rewards = []
            
            # Train on each supplier
            for supplier_id in supplier_ids:
                # Rank supplier and get results
                action, reward, _ = self.rank_supplier(supplier_id, update_ranking=(i == iterations-1))
                
                if action:
                    stats['total_updates'] += 1
                    iteration_rewards.append(reward)
                    stats['max_reward'] = max(stats['max_reward'], reward)
                    stats['min_reward'] = min(stats['min_reward'], reward)
            
            # Update average reward
            if iteration_rewards:
                avg_iteration_reward = sum(iteration_rewards) / len(iteration_rewards)
                total_reward += avg_iteration_reward
                
                # Log progress every 10 iterations
                if (i + 1) % 10 == 0:
                    logger.info(f"Training iteration {i+1}/{iterations}, "
                               f"Avg reward: {avg_iteration_reward:.2f}, "
                               f"Exploration rate: {self.exploration_rate:.2f}")
        
        # Calculate overall average reward
        stats['avg_reward'] = total_reward / iterations if iterations > 0 else 0.0
        
        # Collect sample of final Q-values
        sample_states = QLearningState.objects.all()[:5]
        sample_actions = QLearningAction.objects.all()[:5]
        
        for state in sample_states:
            stats['final_q_values'][state.name] = {}
            for action in sample_actions:
                q_entry, _ = QTableEntry.objects.get_or_create(
                    state=state,
                    action=action,
                    defaults={'q_value': 0.0}
                )
                stats['final_q_values'][state.name][action.name] = q_entry.q_value
        
        return stats
    
    def get_q_table(self, supplier_id=None):
        """
        Get Q-table for a specific supplier or all suppliers.
        
        Args:
            supplier_id (int, optional): ID of the supplier
            
        Returns:
            dict: Q-table as a nested dictionary
        """
        q_table = {}
        
        # Get state for specific supplier or all states
        if supplier_id:
            states = [self.environment.get_state(supplier_id)]
        else:
            states = QLearningState.objects.all()
        
        # Get all actions
        actions = QLearningAction.objects.all()
        
        # Build Q-table
        for state in states:
            q_table[state.name] = {}
            for action in actions:
                q_entry, _ = QTableEntry.objects.get_or_create(
                    state=state,
                    action=action,
                    defaults={'q_value': 0.0}
                )
                q_table[state.name][action.name] = q_entry.q_value
        
        return q_table
    
    def get_policy(self, supplier_id=None):
        """
        Get the current policy (best action for each state).
        
        Args:
            supplier_id (int, optional): ID of the supplier
            
        Returns:
            dict: Policy as a dictionary mapping state names to action names
        """
        policy = {}
        
        # Get state for specific supplier or all states
        if supplier_id:
            states = [self.environment.get_state(supplier_id)]
        else:
            states = QLearningState.objects.all()
        
        # Find best action for each state
        for state in states:
            actions = self.environment.get_actions(state)
            best_action = self.select_action(state, available_actions=actions, exploration=False)
            policy[state.name] = best_action.name
        
        return policy
    
    def rank_all_suppliers(self, exploration=False):
        """
        Rank all active suppliers using the learned policy.
        
        Args:
            exploration (bool): Whether to use exploration
            
        Returns:
            list: List of supplier rankings
        """
        rankings = []
        
        # Use supplier service to get active supplier IDs
        supplier_ids = self.supplier_service.get_active_supplier_ids()
        
        for supplier_id in supplier_ids:
            action, reward, ranking = self.rank_supplier(
                supplier_id, update_ranking=True, exploration=exploration
            )
            if ranking:
                rankings.append(ranking)
        
        return rankings
    
    def reset_q_table(self):
        """
        Reset the Q-table by deleting all Q-value entries.
        
        Returns:
            int: Number of entries deleted
        """
        deleted, _ = QTableEntry.objects.all().delete()
        return deleted
    
    def get_best_action(self, state_name):
        """
        Adapter method to bridge between RankingService and select_action.
        Converts state_name to state object and calls select_action.
        
        Args:
            state_name (str): Name of the state
            
        Returns:
            str: Name of the best action
        """
        try:
            # Get the state object
            state = QLearningState.objects.get(name=state_name)
            
            # Get available actions
            available_actions = QLearningAction.objects.all()
            
            # Use existing select_action method
            best_action = self.select_action(state, available_actions)
            
            # Return the action name
            return best_action.name
            
        except QLearningState.DoesNotExist:
            # Handle the case where the state doesn't exist
            # Default to a safe action like 'maintain'
            try:
                maintain_action = QLearningAction.objects.get(name="maintain")
                return maintain_action.name
            except QLearningAction.DoesNotExist:
                # If maintain action doesn't exist, try to get any action
                actions = QLearningAction.objects.all()
                if actions.exists():
                    return actions.first().name
                return "maintain"  # Default fallback
            
    def update_q_table(self, state_name, action_name, reward, next_state_name=None):
        """
        Update the Q-value for a state-action pair based on the reward.
        
        Args:
            state_name: Name of the current state
            action_name: Name of the action taken
            reward: Reward received for taking the action
            next_state_name: Name of the resulting state (optional)
        """
        try:
            # Get the state and action objects
            state = QLearningState.objects.get(name=state_name)
            action = QLearningAction.objects.get(name=action_name)
            
            # Get the current Q-value
            q_entry, created = QTableEntry.objects.get_or_create(
                state=state,
                action=action,
                defaults={'q_value': 0.0}
            )
            
            current_q_value = q_entry.q_value
            
            # Simple update if no next state (terminal state)
            if next_state_name is None:
                new_q_value = current_q_value + self.learning_rate * (reward - current_q_value)
            else:
                # Get the next state
                next_state = QLearningState.objects.get(name=next_state_name)
                
                # Get the maximum Q-value for the next state
                next_q_entries = QTableEntry.objects.filter(state=next_state)
                
                if next_q_entries.exists():
                    max_next_q = max(entry.q_value for entry in next_q_entries)
                else:
                    max_next_q = 0.0
                
                # Calculate the new Q-value using the Q-learning formula
                new_q_value = current_q_value + self.learning_rate * (
                    reward + self.discount_factor * max_next_q - current_q_value
                )
            
            # Update the Q-value in the database
            q_entry.q_value = new_q_value
            q_entry.save()
            
        except (QLearningState.DoesNotExist, QLearningAction.DoesNotExist) as e:
            # Handle exceptions
            logger.error(f"Error updating Q-table: {e}")
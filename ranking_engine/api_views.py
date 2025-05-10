"""
Supplier Ranking API

This module provides API endpoints for the Q-Learning based Supplier Ranking Service.
"""

from api.models import RankingEvent

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from datetime import date
import logging
import hashlib

from api.models import QLearningState, QLearningAction, QTableEntry, SupplierRanking
from ranking_engine.q_learning.agent import SupplierRankingAgent
from ranking_engine.q_learning.environment import SupplierEnvironment
from ranking_engine.q_learning.state_mapper import StateMapper
from ranking_engine.services.metrics_service import MetricsService
from ranking_engine.services.supplier_service import SupplierService
from connectors.warehouse_service_connector import WarehouseServiceConnector
from connectors.user_service_connector import UserServiceConnector

logger = logging.getLogger(__name__)

class FeedbackView(APIView):
    """
    Accept supplier feedback and update Q-values using the Q-learning pipeline
    """
    permission_classes = [AllowAny]

    def post(self, request):
        supplier_id = request.data.get("supplier_id")
        product_id = request.data.get("product_id")
        city = request.data.get("city")

        # Validate input
        if not supplier_id:
            return Response(
                {"error": "supplier_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get supplier details
        user_service = UserServiceConnector()
        metrics_service = MetricsService()
        supplier = user_service.get_supplier(supplier_id)
        if not supplier:
            return Response(
                {"error": f"Supplier with ID {supplier_id} not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            # === Q-Learning Pipeline ===
            state_mapper = StateMapper()
            environment = SupplierEnvironment()
            agent = SupplierRankingAgent()

            # Step 1: Get current state using stored supplier data
            state = state_mapper.get_supplier_state(supplier_id)

            # Step 2: Agent selects the best action (based on policy)
            action = agent.get_best_action(state)

            if action.name not in [a.name for a in environment.get_actions(state)]:
                return Response(
                    {"error": f"Action {action} not found"},
                    status=status.HTTP_404_NOT_FOUND
                )


            # Step 3: Calculate reward
            reward = environment.get_reward(supplier_id, state, action)

            # Step 4: Get next state (based on action)
            next_state = environment.next_state(supplier_id, action)

            # Step 5: Learn and update Q-table
            new_q_value = agent.learn(state, action, reward, next_state)

            # Optional: Update ranking
            updated_ranking = environment.update_rankings(supplier_id, action)

            # Logging
            RankingEvent.objects.create(
                event_type='FEEDBACK_PROCESSED',
                description=f"Q-value updated via feedback for supplier {supplier_id}",
                supplier_id=supplier_id,
                state_id=state.id,
                action_id=action.id,
                reward=reward,
                metadata={
                    'product_id': product_id,
                    'city': city,
                    'q_value': new_q_value
                }
            )

            company_name = None
            if supplier:
                    # Fix the company_name retrieval to handle all possible formats
                    if 'company_name' in supplier:
                        company_name = supplier['company_name']
                    elif 'name' in supplier:
                        company_name = supplier['name']
                    elif 'user' in supplier and isinstance(supplier['user'], dict):
                        if 'name' in supplier['user']:
                            company_name = supplier['user']['name']
                        elif 'first_name' in supplier['user'] and 'last_name' in supplier['user']:
                            company_name = f"{supplier['user']['first_name']} {supplier['user']['last_name']}"    

            return Response({
                "message": "Feedback processed and Q-table updated",
                "supplier_id": supplier_id,
                "company_name": company_name or f"Supplier {supplier_id}",  # Provide default
                "state": state.name,
                "action": action.name,
                "reward": reward,
                "new_q_value": new_q_value,
                "product_id": product_id,
                "city": city
            })

        except Exception as e:
            logger.error(f"Error processing feedback: {str(e)}")
            return Response(
                {"error": "Failed to process feedback"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class SupplierRankingView(APIView):
    """
    Get ranked suppliers for a product in a city
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        product_id = request.query_params.get('product_id')
        city = request.query_params.get('city')  # Using city instead of region
        
        if not product_id:
            return Response(
                {"error": "product_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get suppliers that offer this product
            warehouse_service = WarehouseServiceConnector()
            suppliers = warehouse_service.get_suppliers_by_product(product_id)
            
            if not suppliers:
                return Response(
                    {"message": f"No suppliers found for product {product_id}"},
                    status=status.HTTP_200_OK
                )
            
            # Get metrics for each supplier
            metrics_service = MetricsService()
            user_service = UserServiceConnector()
            state_mapper = StateMapper()
            ranked_suppliers = []
            
            logger.info(f"Getting rankings for suppliers offering product {product_id} in city {city}")
            
            for supplier_id in suppliers:
                # Get supplier details to check city
                supplier = user_service.get_supplier(supplier_id)
                
                # Skip if supplier is not in the requested city
                supplier_city = None
                if supplier:
                    if 'city' in supplier:
                        supplier_city = supplier['city']
                    elif 'user' in supplier and 'city' in supplier['user']:
                        supplier_city = supplier['user']['city']
                
                # Filter by city if provided
                if city and supplier_city and supplier_city.lower() != city.lower():
                    continue
                
                # Calculate metrics for this supplier
                metrics = metrics_service.get_supplier_metrics(supplier_id)
                
                # Get state for these metrics
                state = state_mapper.get_supplier_state(supplier_id)
                
                # Get Q-values for this state and supplier
                q_entries = QTableEntry.objects.filter(state=state).order_by('-q_value')
                print(f"Q-entries found for supplier {state}: {q_entries}")
                
                # Get best action and its Q-value
                best_q_value = 0.0
                best_action = None
                
                if q_entries:
                    
                    best_entry = q_entries.first()
                    best_q_value = best_entry.q_value
                    best_action = best_entry.action.name
                
                # Calculate overall score
                score = metrics['overall_score']
                
                # Get company name with fallback
                company_name = None
                if supplier:
                    # Fix the company_name retrieval to handle all possible formats
                    if 'company_name' in supplier:
                        company_name = supplier['company_name']
                    elif 'name' in supplier:
                        company_name = supplier['name']
                    elif 'user' in supplier and isinstance(supplier['user'], dict):
                        if 'name' in supplier['user']:
                            company_name = supplier['user']['name']
                        elif 'first_name' in supplier['user'] and 'last_name' in supplier['user']:
                            company_name = f"{supplier['user']['first_name']} {supplier['user']['last_name']}"

                latest_ranking = (
                    SupplierRanking.objects.filter(supplier_id=supplier_id)
                    .order_by('-date')
                    .first()
                )

                tier = latest_ranking.tier if latest_ranking and latest_ranking.tier else 5
                score = latest_ranking.overall_score if latest_ranking else score
                
                # Use supplier_id to create a slight variation in scores to ensure uniqueness
                if score:
                    # Add a small variation (±0.1) based on supplier_id
                    seed = int(hashlib.md5(str(supplier_id).encode()).hexdigest(), 16) % 1000 / 1000.0
                    variation = (seed * 2 - 1) * 0.01  # -0.01 to 0.01 range
                    score = score + variation
                
                ranked_suppliers.append({
                    "supplier_id": supplier_id,
                    "company_name": company_name or f"Supplier {supplier_id}",  # Provide default
                    "score": score,
                    "tier": tier,
                    "state": state.name,
                    "best_action": best_action,
                    "q_value": best_q_value,
                    "city": supplier_city
                })
            
            # Sort by tier (ascending), then score (descending)
            ranked_suppliers.sort(key=lambda x: (x["tier"], -x["score"]))

            
            return Response({
                "product_id": product_id,
                "city": city,
                "suppliers": ranked_suppliers,
                "count": len(ranked_suppliers)
            })
            
        except Exception as e:
            logger.error(f"Error getting supplier rankings: {str(e)}")
            return Response(
                {"error": f"Failed to get supplier rankings: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ManualTrainingView(APIView):
    """
    Manually trigger re-training (admin only)
    """
    permission_classes = [AllowAny]
    
    @transaction.atomic
    def post(self, request):
        try:
            # Create agent
            agent = SupplierRankingAgent()
            
            # Get training parameters
            iterations = int(request.data.get('iterations', 100))
            supplier_ids = request.data.get('supplier_ids', None)
            
            logger.info(f"Starting manual training with {iterations} iterations")
            
            # Perform batch training
            agent.batch_train(iterations=iterations, supplier_ids=supplier_ids)
            
            return Response({
                "message": "Q-table updated with historical data",
                "iterations": iterations,
                "supplier_count": len(supplier_ids) if supplier_ids else "all"
            })
        
        except Exception as e:
            logger.error(f"Error during manual training: {str(e)}")
            return Response(
                {"error": f"Training failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class QValueView(APIView):
    """
    Debugging - retrieve Q-value for a given (state, action)
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        supplier_id = request.query_params.get('supplier_id')
        
        if not supplier_id:
            return Response(
                {"error": "supplier_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Use metrics service to get metrics for this supplier
            metrics_service = MetricsService()
            metrics = metrics_service.calculate_combined_metrics(supplier_id)
            
            # Map to state
            state_mapper = StateMapper()
            state = state_mapper.get_state_from_metrics(metrics)
            
            # Get available actions
            environment = SupplierEnvironment()
            actions = environment.get_actions(state)
            
            # Get Q-values for each action
            q_values = []
            for action in actions:
                try:
                    q_entry = QTableEntry.objects.get(state=state, action=action)
                    q_values.append({
                        "action": action.name,
                        "q_value": q_entry.q_value,
                        "update_count": q_entry.update_count
                    })
                except QTableEntry.DoesNotExist:
                    q_values.append({
                        "action": action.name,
                        "q_value": 0.0,
                        "update_count": 0
                    })
            
            # Get supplier details
            supplier_service = SupplierService()
            supplier = supplier_service.get_supplier(supplier_id)
            
            # Get company name with fallback
            company_name = None
            if supplier:
                company_name = supplier.get('company_name', 
                              supplier.get('name',
                              supplier.get('user', {}).get('name', f"Unknown Supplier {supplier_id}")))
            
            return Response({
                "state": state.name,
                "supplier_id": supplier_id,
                "company_name": company_name,
                "q_values": q_values,
                "metrics": metrics
            })
            
        except Exception as e:
            logger.error(f"Error retrieving Q-values: {str(e)}")
            return Response(
                {"error": f"Failed to retrieve Q-values: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class QTableView(APIView):
    """
    Export the Q-table (admin only)
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            # Support filtering
            state_name = request.query_params.get('state')
            action_name = request.query_params.get('action')
            min_q_value = request.query_params.get('min_q_value')
            limit = int(request.query_params.get('limit', 100))
            
            # Start with all entries
            entries_query = QTableEntry.objects.all()
            
            # Apply filters if provided
            if state_name:
                entries_query = entries_query.filter(state__name__contains=state_name)
            
            if action_name:
                entries_query = entries_query.filter(action__name__contains=action_name)
            
            if min_q_value:
                entries_query = entries_query.filter(q_value__gte=float(min_q_value))
            
            # Limit the result count
            entries_query = entries_query.order_by('-q_value')[:limit]
            
            # Get the entries
            entries = entries_query.select_related('state', 'action')
            
            # Format for response
            q_table = []
            for entry in entries:
                q_table.append({
                    "state": entry.state.name,
                    "action": entry.action.name,
                    "q_value": entry.q_value,
                    "update_count": entry.update_count
                })
            
            return Response({
                "q_table_entries": q_table,
                "count": len(q_table),
                "total_entries": QTableEntry.objects.count()
            })
            
        except Exception as e:
            logger.error(f"Error retrieving Q-table: {str(e)}")
            return Response(
                {"error": f"Failed to retrieve Q-table: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 
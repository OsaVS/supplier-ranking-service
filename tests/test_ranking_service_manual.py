import os
import sys
import django
import random
from datetime import datetime, timedelta, date
import matplotlib.pyplot as plt
import numpy as np

# Set up Django environment
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'suplier_ranking_service.settings')
django.setup()

# Import your models and services
from api.models import (
    Supplier, Product, SupplierProduct, SupplierPerformance,
    Transaction, QLearningState, QLearningAction, QTableEntry, RankingConfiguration
)
from ranking_engine.q_learning.agent import SupplierRankingAgent
from ranking_engine.q_learning.environment import SupplierEnvironment
from ranking_engine.q_learning.state_mapper import StateMapper
from ranking_engine.services.ranking_service import RankingService
from ranking_engine.services.supplier_service import SupplierService
from ranking_engine.services.metrics_service import MetricsService
from ranking_engine.utils.data_preprocessing import preprocess_supplier_data


def setup_test_data():
    """Create test data for manual testing"""
    print("Creating test data...")
    
    # Clear existing data (optional)
    # SupplierRanking.objects.all().delete()
    # Transaction.objects.all().delete()
    # SupplierPerformance.objects.all().delete()
    # SupplierProduct.objects.all().delete()
    # Product.objects.all().delete() 
    # Supplier.objects.all().delete()
    # QTableEntry.objects.all().delete()
    # QLearningAction.objects.all().delete()
    # QLearningState.objects.all().delete()
    # RankingConfiguration.objects.all().delete()
    
    # Create suppliers
    suppliers = []
    supplier_names = [
        "Quality First Suppliers", 
        "Budget Materials Inc.", 
        "FastTrack Logistics",
        "Premium Components Ltd",
        "Value Chain Solutions"
    ]
    
    for i, name in enumerate(supplier_names):
        code = f"SUP{i+1:03d}"
        supplier = Supplier.objects.get_or_create(
            name=name,
            defaults={
                'code': code,
                'contact_email': f"contact@{name.lower().replace(' ', '')}.com",
                'address': f"{i+100} Business Park",
                'country': "Test Country",
                'supplier_size': random.choice(['S', 'M', 'L', 'E']),
                'credit_score': random.uniform(60, 95),
                'average_lead_time': random.randint(3, 15)
            }
        )[0]
        suppliers.append(supplier)
    
    # Create products
    products = []
    product_data = [
        {"name": "Electronic Component A", "category": "Electronics"},
        {"name": "Metal Bracket B", "category": "Hardware"},
        {"name": "Plastic Casing C", "category": "Packaging"}
    ]
    
    for i, data in enumerate(product_data):
        product = Product.objects.get_or_create(
            name=data["name"],
            defaults={
                'sku': f"PROD{i+1:03d}",
                'category': data["category"],
                'unit_of_measure': "EA",
                'is_active': True
            }
        )[0]
        products.append(product)
    
    # Link suppliers with products
    for supplier in suppliers:
        for product in products:
            SupplierProduct.objects.get_or_create(
                supplier=supplier,
                product=product,
                defaults={
                    'unit_price': random.uniform(50, 200),
                    'minimum_order_quantity': random.randint(5, 20),
                    'lead_time_days': random.randint(2, 15),
                    'is_preferred': random.choice([True, False])
                }
            )
    
    # Create performance records
    today = date.today()
    for supplier in suppliers:
        # Create slightly different performance for each supplier
        quality_base = random.uniform(6.5, 9.5)
        delivery_base = random.uniform(6.5, 9.5)
        price_base = random.uniform(6.5, 9.5)
        
        for days_ago in range(30, 0, -5):  # Create data points every 5 days
            record_date = today - timedelta(days=days_ago)
            
            # Add some randomness to the scores over time
            quality_variation = random.uniform(-0.5, 0.5)
            delivery_variation = random.uniform(-0.5, 0.5)
            price_variation = random.uniform(-0.5, 0.5)
            
            SupplierPerformance.objects.get_or_create(
                supplier=supplier,
                date=record_date,
                defaults={
                    'quality_score': min(max(quality_base + quality_variation, 0), 10),
                    'defect_rate': random.uniform(0.5, 5.0),
                    'return_rate': random.uniform(0.2, 3.0),
                    'on_time_delivery_rate': min(max(delivery_base * 10 + random.uniform(-5, 5), 0), 100),
                    'average_delay_days': random.uniform(0, 3.0),
                    'price_competitiveness': min(max(price_base + price_variation, 0), 10),
                    'responsiveness': random.uniform(6.0, 9.5),
                    'fill_rate': random.uniform(90.0, 99.9),
                    'order_accuracy': random.uniform(92.0, 99.9),
                    'compliance_score': random.uniform(7.0, 9.5)
                }
            )
    
    # Create transactions with timezone-aware datetimes
    now = django.utils.timezone.now()
    for supplier in suppliers:
        for product in products:
            # Create multiple transactions for each supplier-product pair
            for days_ago in range(60, 0, -3):  # Every 3 days for past 60 days
                order_date = now - timedelta(days=days_ago)
                
                # Get the supplier product for lead time
                try:
                    supplier_product = SupplierProduct.objects.get(supplier=supplier, product=product)
                    lead_time = supplier_product.lead_time_days
                except SupplierProduct.DoesNotExist:
                    lead_time = 5  # Default if not found
                
                expected_delivery = order_date.date() + timedelta(days=lead_time)
                
                # Determine if delivered on time, with quality issues, etc.
                is_on_time = random.random() > 0.2  # 80% on-time rate
                has_defects = random.random() > 0.8  # 20% have defects
                
                if is_on_time:
                    actual_delivery = expected_delivery
                    delay_days = 0
                else:
                    delay_days = random.randint(1, 5)
                    actual_delivery = expected_delivery + timedelta(days=delay_days)
                
                defect_count = random.randint(1, 10) if has_defects else 0
                
                # Only create completed transactions
                if actual_delivery <= today:
                    Transaction.objects.get_or_create(
                        supplier=supplier,
                        product=product,
                        order_date=order_date,
                        expected_delivery_date=expected_delivery,
                        defaults={
                            'actual_delivery_date': actual_delivery,
                            'quantity': random.randint(10, 100),
                            'unit_price': supplier_product.unit_price,
                            'status': "DELIVERED",
                            'defect_count': defect_count,
                            'blockchain_reference': f"BLOCK{random.randint(10000, 99999)}"
                        }
                    )
    
    # Create Q-Learning states
    states = []
    state_names = [
        "high_quality_high_delivery",
        "high_quality_low_delivery",
        "low_quality_high_delivery",
        "low_quality_low_delivery",
        "medium_performance"
    ]
    
    for name in state_names:
        state = QLearningState.objects.get_or_create(
            name=name,
            defaults={'description': f"State representing {name.replace('_', ' ')}"}
        )[0]
        states.append(state)
    
    # Create Q-Learning actions
    actions = []
    action_names = [
        "increase_rank_significantly",
        "increase_rank",
        "maintain_rank",
        "decrease_rank",
        "decrease_rank_significantly"
    ]
    
    for name in action_names:
        action = QLearningAction.objects.get_or_create(
            name=name,
            defaults={'description': f"Action to {name.replace('_', ' ')}"}
        )[0]
        actions.append(action)
    
    # Create Q-Table entries with initial values
    for state in states:
        for action in actions:
            # Set initial Q-values based on intuitive actions for each state
            if "high_quality" in state.name and "increase" in action.name:
                initial_q = random.uniform(0.6, 0.9)
            elif "low_quality" in state.name and "decrease" in action.name:
                initial_q = random.uniform(0.6, 0.9)
            elif "medium" in state.name and "maintain" in action.name:
                initial_q = random.uniform(0.6, 0.9)
            else:
                initial_q = random.uniform(0.1, 0.5)
            
            QTableEntry.objects.get_or_create(
                state=state,
                action=action,
                defaults={
                    'q_value': initial_q,
                    'update_count': 0
                }
            )
    
    # Create configuration
    config = RankingConfiguration.objects.get_or_create(
        name="default",
        defaults={
            'learning_rate': 0.1,
            'discount_factor': 0.9,
            'exploration_rate': 0.2,
            'quality_weight': 0.4,
            'delivery_weight': 0.3,
            'price_weight': 0.2,
            'service_weight': 0.1,
            'is_active': True
        }
    )[0]
    
    print("Test data creation complete.")
    return suppliers, products, config


def run_ranking_process():
    """Run the ranking process and display results"""
    print("\nInitializing ranking components...")
    
    # Get the configuration
    config = RankingConfiguration.objects.filter(is_active=True).first()
    if not config:
        print("No active configuration found. Creating default.")
        config = RankingConfiguration.objects.create(
            name="default",
            learning_rate=0.1,
            discount_factor=0.9,
            exploration_rate=0.2,
            quality_weight=0.4,
            delivery_weight=0.3,
            price_weight=0.2,
            service_weight=0.1,
            is_active=True
        )
    
    # Initialize components
    state_mapper = StateMapper()
    environment = SupplierEnvironment()
    agent = SupplierRankingAgent(config)
    metrics_service = MetricsService()
    supplier_service = SupplierService()
    
    try:
        # Create ranking service WITHOUT arguments - this is the key change
        ranking_service = RankingService()
        
        # Run the ranking process for the current date
        today = date.today()
        print(f"Generating supplier rankings for {today}...")
        
        # If your RankingService implementation has these methods, use them:
        # Initialize service with needed components after creation
        if hasattr(ranking_service, 'set_agent'):
            ranking_service.set_agent(agent)
        if hasattr(ranking_service, 'set_environment'):
            ranking_service.set_environment(environment)
        if hasattr(ranking_service, 'set_state_mapper'):
            ranking_service.set_state_mapper(state_mapper)
        if hasattr(ranking_service, 'set_metrics_service'):
            ranking_service.set_metrics_service(metrics_service)
        if hasattr(ranking_service, 'set_supplier_service'):
            ranking_service.set_supplier_service(supplier_service)
        if hasattr(ranking_service, 'set_config'):
            ranking_service.set_config(config)
        
        # Use the method that works in your implementation
        # Try the instance method first - check if it exists
        if hasattr(ranking_service, 'generate_rankings'):
            rankings = ranking_service.generate_rankings(today)
        else:
            # Fall back to what works in your integration test
            rankings = ranking_service.generate_supplier_rankings()
        
        print(f"Successfully generated {len(rankings)} rankings.")
        
        # Display the rankings
        print("\nSupplier Rankings:")
        print("-" * 80)
        print(f"{'Rank':<5}{'Supplier':<30}{'Overall':<10}{'Quality':<10}{'Delivery':<10}{'Price':<10}{'Service':<10}")
        print("-" * 80)
        
        for ranking in sorted(rankings, key=lambda r: r.rank):
            print(f"{ranking.rank:<5}{ranking.supplier.name:<30}{ranking.overall_score:<10.2f}"
                  f"{ranking.quality_score:<10.2f}{ranking.delivery_score:<10.2f}"
                  f"{ranking.price_score:<10.2f}{ranking.service_score:<10.2f}")
        
        # Run a Q-learning training iteration if the method exists
        if hasattr(ranking_service, 'update_q_values_from_transactions'):
            print("\nUpdating Q-values from recent transactions...")
            recent_transactions = Transaction.objects.filter(
                actual_delivery_date__gte=today - timedelta(days=30)
            )
            ranking_service.update_q_values_from_transactions(recent_transactions)
            print(f"Updated Q-values based on {recent_transactions.count()} recent transactions.")
        
        return rankings
        
    except Exception as e:
        print(f"Error generating rankings: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def visualize_results(rankings):
    """Create visualizations of the ranking results"""
    if not rankings:
        print("No rankings to visualize.")
        return
    
    try:
        import matplotlib
        matplotlib.use('Agg')  # Use non-interactive backend if running headless
    except:
        pass
    
    # Prepare data
    suppliers = [r.supplier.name for r in rankings]
    overall_scores = [r.overall_score for r in rankings]
    quality_scores = [r.quality_score for r in rankings]
    delivery_scores = [r.delivery_score for r in rankings]
    price_scores = [r.price_score for r in rankings]
    service_scores = [r.service_score for r in rankings]
    
    # Create bar chart of overall scores
    plt.figure(figsize=(12, 6))
    plt.bar(suppliers, overall_scores, color='blue')
    plt.title('Overall Supplier Scores')
    plt.xlabel('Supplier')
    plt.ylabel('Score')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig('overall_scores.png')
    print("Saved overall scores visualization to 'overall_scores.png'")
    
    # Create a stacked bar chart showing score components
    plt.figure(figsize=(12, 6))
    width = 0.5
    
    # Create the bars
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Create the bars
    ax.bar(suppliers, quality_scores, width, label='Quality', color='#1f77b4')
    ax.bar(suppliers, delivery_scores, width, bottom=quality_scores, label='Delivery', color='#ff7f0e')
    
    # Calculate position for the next stack
    bottom = [q + d for q, d in zip(quality_scores, delivery_scores)]
    ax.bar(suppliers, price_scores, width, bottom=bottom, label='Price', color='#2ca02c')
    
    # Update bottom for the final stack
    bottom = [b + p for b, p in zip(bottom, price_scores)]
    ax.bar(suppliers, service_scores, width, bottom=bottom, label='Service', color='#d62728')
    
    ax.set_title('Supplier Score Components')
    ax.set_xlabel('Supplier')
    ax.set_ylabel('Score')
    ax.legend(loc='upper right')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig('score_components.png')
    print("Saved score components visualization to 'score_components.png'")
    
    # Create a radar chart comparing top suppliers
    if len(rankings) >= 3:
        top_suppliers = sorted(rankings, key=lambda r: r.overall_score, reverse=True)[:3]
        
        categories = ['Quality', 'Delivery', 'Price', 'Service']
        
        fig = plt.figure(figsize=(8, 8))
        ax = fig.add_subplot(111, polar=True)
        
        # Number of categories
        N = len(categories)
        
        # Create angles for each category
        angles = [n / float(N) * 2 * np.pi for n in range(N)]
        angles += angles[:1]  # Close the loop
        
        # Set the labels
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories)
        
        # Plot each supplier
        colors = ['blue', 'red', 'green']
        for i, supplier in enumerate(top_suppliers):
            values = [supplier.quality_score, supplier.delivery_score, 
                      supplier.price_score, supplier.service_score]
            values += values[:1]  # Close the loop
            
            ax.plot(angles, values, linewidth=2, linestyle='solid', label=supplier.supplier.name, color=colors[i])
            ax.fill(angles, values, alpha=0.1, color=colors[i])
        
        plt.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
        plt.title('Top 3 Suppliers Comparison')
        plt.tight_layout()
        plt.savefig('supplier_radar.png')
        print("Saved supplier comparison radar chart to 'supplier_radar.png'")


def analyze_q_learning():
    """Analyze the Q-learning data and training progress"""
    print("\nAnalyzing Q-Learning data...")
    
    # Get all Q-table entries
    q_entries = QTableEntry.objects.all().order_by('state__name', 'action__name')
    
    if not q_entries.exists():
        print("No Q-Learning data available for analysis.")
        return
    
    # Group by state
    states = {}
    for entry in q_entries:
        if entry.state.name not in states:
            states[entry.state.name] = []
        states[entry.state.name].append({
            'action': entry.action.name,
            'q_value': entry.q_value,
            'updates': entry.update_count
        })
    
    # Print Q-table
    print("\nCurrent Q-table:")
    print("-" * 100)
    print(f"{'State':<30}{'Action':<30}{'Q-Value':<10}{'Updates':<10}")
    print("-" * 100)
    
    for state_name, actions in states.items():
        for item in actions:
            print(f"{state_name:<30}{item['action']:<30}{item['q_value']:<10.4f}{item['updates']:<10}")
    
    # Find the best action for each state
    print("\nBest actions for each state:")
    print("-" * 70)
    print(f"{'State':<30}{'Best Action':<30}{'Q-Value':<10}")
    print("-" * 70)
    
    for state_name, actions in states.items():
        best_action = max(actions, key=lambda x: x['q_value'])
        print(f"{state_name:<30}{best_action['action']:<30}{best_action['q_value']:<10.4f}")


def main():
    """Main entry point for manual testing"""
    print("=" * 80)
    print("Supplier Ranking Service Manual Test")
    print("=" * 80)
    
    # Create test data
    suppliers, products, config = setup_test_data()
    
    # Run ranking process
    rankings = run_ranking_process()
    
    # Analyze rankings
    if rankings:
        visualize_results(rankings)
        analyze_q_learning()
    
    print("\nManual test completed.")


if __name__ == "__main__":
    main()
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Supplier(models.Model):
    """Model for storing supplier information"""
    
    SUPPLIER_SIZE_CHOICES = (
        ('S', 'Small'),
        ('M', 'Medium'),
        ('L', 'Large'),
        ('E', 'Enterprise'),
    )
    
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField()
    country = models.CharField(max_length=100)
    supplier_size = models.CharField(max_length=1, choices=SUPPLIER_SIZE_CHOICES)
    registration_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True, null=True)
    
    # Additional data
    credit_score = models.FloatField(null=True, blank=True, 
                                    validators=[MinValueValidator(0), MaxValueValidator(100)])
    average_lead_time = models.IntegerField(null=True, blank=True, 
                                           help_text="Average lead time in days")
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class Product(models.Model):
    """Model for products offered by suppliers"""
    
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=50, unique=True)
    category = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    unit_of_measure = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.sku})"


class SupplierProduct(models.Model):
    """Model for mapping products to suppliers with pricing"""
    
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='products')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='suppliers')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_order_quantity = models.IntegerField(default=1)
    maximum_order_quantity = models.IntegerField(null=True, blank=True)
    lead_time_days = models.IntegerField(help_text="Lead time in days")
    is_preferred = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('supplier', 'product')
    
    def __str__(self):
        return f"{self.supplier.name} - {self.product.name}"


class SupplierPerformance(models.Model):
    """Model for tracking supplier performance metrics"""
    
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='performance_records')
    date = models.DateField()
    
    # Quality metrics
    quality_score = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(10)])
    defect_rate = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    return_rate = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Delivery metrics
    on_time_delivery_rate = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    average_delay_days = models.FloatField(default=0)
    
    # Price metrics
    price_competitiveness = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(10)])
    
    # Service metrics
    responsiveness = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(10)])
    issue_resolution_time = models.FloatField(help_text="Average time to resolve issues in hours", null=True, blank=True)
    
    # Fulfillment metrics
    fill_rate = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)],
                                 help_text="Percentage of order quantities fulfilled")
    order_accuracy = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)],
                                     help_text="Percentage of orders with correct items")
    
    # Compliance metrics
    compliance_score = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(10)], 
                                        null=True, blank=True)
    
    class Meta:
        unique_together = ('supplier', 'date')
    
    def __str__(self):
        return f"{self.supplier.name} Performance on {self.date}"


class Transaction(models.Model):
    """Model for recording supplier transactions"""
    
    STATUS_CHOICES = (
        ('ORDERED', 'Ordered'),
        ('CONFIRMED', 'Confirmed'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
        ('RETURNED', 'Returned'),
    )
    
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='transactions')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='transactions')
    order_date = models.DateTimeField()
    expected_delivery_date = models.DateField()
    actual_delivery_date = models.DateField(null=True, blank=True)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    blockchain_reference = models.CharField(max_length=255, null=True, blank=True, 
                                          help_text="Reference to blockchain record from Group 30")
    
    # Quality information
    defect_count = models.IntegerField(default=0)
    rejection_reason = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return f"Order {self.id} - {self.supplier.name} - {self.product.name}"
    
    @property
    def is_delayed(self):
        if self.actual_delivery_date and self.expected_delivery_date:
            return self.actual_delivery_date > self.expected_delivery_date
        return False
    
    @property
    def delay_days(self):
        if self.is_delayed:
            return (self.actual_delivery_date - self.expected_delivery_date).days
        return 0
    
    @property
    def total_amount(self):
        return self.quantity * self.unit_price


class QLearningState(models.Model):
    """Model for storing states used in Q-Learning"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    
    def __str__(self):
        return self.name


class QLearningAction(models.Model):
    """Model for storing actions used in Q-Learning"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    
    def __str__(self):
        return self.name


class QTableEntry(models.Model):
    """Model for storing Q-values for state-action pairs"""
    
    state = models.ForeignKey(QLearningState, on_delete=models.CASCADE, related_name='q_values')
    action = models.ForeignKey(QLearningAction, on_delete=models.CASCADE, related_name='q_values')
    q_value = models.FloatField(default=0.0)
    update_count = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('state', 'action')
    
    def __str__(self):
        return f"{self.state.name} - {self.action.name}: {self.q_value}"


class SupplierRanking(models.Model):
    """Model for storing supplier rankings"""
    
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='rankings')
    date = models.DateField()
    overall_score = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(10)])
    quality_score = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(10)])
    delivery_score = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(10)])
    price_score = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(10)])
    service_score = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(10)])
    rank = models.IntegerField(help_text="Rank position among all suppliers")
    state = models.ForeignKey(QLearningState, on_delete=models.SET_NULL, null=True, related_name='supplier_rankings')
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ('supplier', 'date')
    
    def __str__(self):
        return f"{self.supplier.name} - Rank {self.rank} on {self.date}"


class RankingConfiguration(models.Model):
    """Model for storing configuration parameters for the ranking system"""
    
    name = models.CharField(max_length=100, unique=True)
    learning_rate = models.FloatField(default=0.1)
    discount_factor = models.FloatField(default=0.9)
    exploration_rate = models.FloatField(default=0.3)
    quality_weight = models.FloatField(default=0.25)
    delivery_weight = models.FloatField(default=0.25)
    price_weight = models.FloatField(default=0.25)
    service_weight = models.FloatField(default=0.25)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
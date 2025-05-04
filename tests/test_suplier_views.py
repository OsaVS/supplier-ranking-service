# from django.urls import reverse
# from django.test import TestCase
# from rest_framework import status
# from rest_framework.test import APITestCase, APIClient
# from datetime import date, timedelta

# from api.models import Supplier, SupplierPerformance, SupplierProduct, Product, SupplierRanking, QLearningState

# class SupplierViewSetTests(APITestCase):
#     """Tests for the SupplierViewSet API endpoints"""
    
#     def setUp(self):
#         # Create test suppliers
#         self.supplier1 = Supplier.objects.create(
#             name="Test Supplier 1",
#             code="TS001",
#             contact_email="contact1@test.com",
#             address="123 Test Address",
#             country="Test Country",
#             supplier_size="M",
#             is_active=True,
#             credit_score=85.5,
#             average_lead_time=7
#         )
        
#         self.supplier2 = Supplier.objects.create(
#             name="Test Supplier 2",
#             code="TS002",
#             contact_email="contact2@test.com",
#             address="456 Test Address",
#             country="Another Country",
#             supplier_size="L",
#             is_active=True,
#             credit_score=92.0,
#             average_lead_time=5
#         )
        
#         # Create a product
#         self.product = Product.objects.create(
#             name="Test Product",
#             sku="TP001",
#             category="Test Category",
#             unit_of_measure="EA",
#             is_active=True
#         )
        
#         # Create supplier product relationship
#         self.supplier_product = SupplierProduct.objects.create(
#             supplier=self.supplier1,
#             product=self.product,
#             unit_price=10.99,
#             minimum_order_quantity=10,
#             lead_time_days=7,
#             is_preferred=True
#         )
        
#         # Create performance record
#         self.performance = SupplierPerformance.objects.create(
#             supplier=self.supplier1,
#             date=date.today(),
#             quality_score=8.5,
#             defect_rate=1.2,
#             return_rate=0.5,
#             on_time_delivery_rate=95.5,
#             average_delay_days=0.3,
#             price_competitiveness=8.7,
#             responsiveness=9.0,
#             fill_rate=98.5,
#             order_accuracy=99.2
#         )
        
#         # Create state for ranking
#         self.state = QLearningState.objects.create(
#             name="Test State",
#             description="Test state description"
#         )
        
#         # Create ranking
#         self.ranking = SupplierRanking.objects.create(
#             supplier=self.supplier1,
#             date=date.today(),
#             overall_score=8.7,
#             quality_score=8.5,
#             delivery_score=9.0,
#             price_score=8.8,
#             service_score=8.6,
#             rank=1,
#             state=self.state
#         )
        
#         # Set up client
#         self.client = APIClient()
#         # Note: In a real application, you would authenticate here
#         # self.client.force_authenticate(user=user)

#     def test_list_suppliers(self):
#         """Test retrieving a list of suppliers"""
#         url = reverse('supplier-list')
#         response = self.client.get(url)
        
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(len(response.data), 2)
        
#     def test_retrieve_supplier(self):
#         """Test retrieving a single supplier"""
#         url = reverse('supplier-detail', args=[self.supplier1.id])
#         response = self.client.get(url)
        
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(response.data['name'], "Test Supplier 1")
#         self.assertEqual(response.data['code'], "TS001")
        
#     def test_create_supplier(self):
#         """Test creating a new supplier"""
#         url = reverse('supplier-list')
#         data = {
#             "name": "New Test Supplier",
#             "code": "NTS001",
#             "contact_email": "new@test.com",
#             "address": "789 New Address",
#             "country": "New Country",
#             "supplier_size": "S",
#             "is_active": True
#         }
        
#         response = self.client.post(url, data, format='json')
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#         self.assertEqual(Supplier.objects.count(), 3)
        
#     def test_update_supplier(self):
#         """Test updating a supplier"""
#         url = reverse('supplier-detail', args=[self.supplier1.id])
#         data = {
#             "name": "Updated Supplier",
#             "code": "TS001",  # Keep the same code to avoid unique constraint violation
#             "contact_email": "updated@test.com",
#             "address": "123 Test Address",
#             "country": "Test Country",
#             "supplier_size": "M",
#             "is_active": True
#         }
        
#         response = self.client.put(url, data, format='json')
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
        
#         # Refresh from database
#         self.supplier1.refresh_from_db()
#         self.assertEqual(self.supplier1.name, "Updated Supplier")
#         self.assertEqual(self.supplier1.contact_email, "updated@test.com")
        
#     def test_delete_supplier(self):
#         """Test deleting a supplier"""
#         url = reverse('supplier-detail', args=[self.supplier2.id])
#         response = self.client.delete(url)
        
#         self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
#         self.assertEqual(Supplier.objects.count(), 1)
        
#     def test_supplier_performance_action(self):
#         """Test retrieving supplier performance records"""
#         url = reverse('supplier-performance', args=[self.supplier1.id])
#         response = self.client.get(url)
        
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(len(response.data), 1)
#         self.assertEqual(response.data[0]['quality_score'], 8.5)
        
#     def test_supplier_rankings_action(self):
#         """Test retrieving supplier ranking records"""
#         url = reverse('supplier-rankings', args=[self.supplier1.id])
#         response = self.client.get(url)
        
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(len(response.data), 1)
#         self.assertEqual(response.data[0]['overall_score'], 8.7)
        
#     def test_supplier_products_action(self):
#         """Test retrieving supplier products"""
#         url = reverse('supplier-products', args=[self.supplier1.id])
#         response = self.client.get(url)
        
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(len(response.data), 1)
#         self.assertEqual(response.data[0]['unit_price'], '10.99')
        
#     def test_supplier_all_data_action(self):
#         """Test retrieving all supplier data"""
#         url = reverse('supplier-all-data', args=[self.supplier1.id])
#         response = self.client.get(url)
        
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(response.data['name'], "Test Supplier 1")
#         self.assertIn('performance_records', response.data)
#         self.assertIn('rankings', response.data)
#         self.assertIn('products', response.data)
        
#     def test_filter_suppliers_by_name(self):
#         """Test filtering suppliers by name"""
#         url = reverse('supplier-list') + '?search=Test Supplier 1'
#         response = self.client.get(url)
        
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(len(response.data), 1)
#         self.assertEqual(response.data[0]['name'], "Test Supplier 1")
        
#     def test_ordering_suppliers(self):
#         """Test ordering suppliers by credit score"""
#         url = reverse('supplier-list') + '?ordering=-credit_score'
#         response = self.client.get(url)
        
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(len(response.data), 2)
#         self.assertEqual(response.data[0]['name'], "Test Supplier 2")  # Higher credit score
#         self.assertEqual(response.data[1]['name'], "Test Supplier 1")
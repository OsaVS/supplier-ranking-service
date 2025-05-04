# from django.urls import reverse
# from rest_framework import status
# from rest_framework.test import APITestCase, APIClient

# from api.models import Product, Supplier, SupplierProduct

# class ProductViewSetTests(APITestCase):
#     """Tests for the ProductViewSet API endpoints"""
    
#     def setUp(self):
#         # Create test products
#         self.product1 = Product.objects.create(
#             name="Test Product 1",
#             sku="TP001",
#             category="Category A",
#             unit_of_measure="EA",
#             is_active=True
#         )
        
#         self.product2 = Product.objects.create(
#             name="Test Product 2",
#             sku="TP002",
#             category="Category B",
#             unit_of_measure="KG",
#             is_active=True
#         )
        
#         # Create a supplier
#         self.supplier = Supplier.objects.create(
#             name="Test Supplier",
#             code="TS001",
#             contact_email="contact@test.com",
#             address="123 Test Address",
#             country="Test Country",
#             supplier_size="M",
#             is_active=True
#         )
        
#         # Create supplier product relationships
#         self.supplier_product1 = SupplierProduct.objects.create(
#             supplier=self.supplier,
#             product=self.product1,
#             unit_price=10.99,
#             minimum_order_quantity=10,
#             lead_time_days=7,
#             is_preferred=True
#         )
        
#         self.supplier_product2 = SupplierProduct.objects.create(
#             supplier=self.supplier,
#             product=self.product2,
#             unit_price=20.50,
#             minimum_order_quantity=5,
#             lead_time_days=10,
#             is_preferred=False
#         )
        
#         # Set up client
#         self.client = APIClient()
#         # Note: In a real application, you would authenticate here
#         # self.client.force_authenticate(user=user)

#     def test_list_products(self):
#         """Test retrieving a list of products"""
#         url = reverse('product-list')
#         response = self.client.get(url)
        
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(len(response.data), 2)
        
#     def test_retrieve_product(self):
#         """Test retrieving a single product"""
#         url = reverse('product-detail', args=[self.product1.id])
#         response = self.client.get(url)
        
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(response.data['name'], "Test Product 1")
#         self.assertEqual(response.data['sku'], "TP001")
        
#     def test_create_product(self):
#         """Test creating a new product"""
#         url = reverse('product-list')
#         data = {
#             "name": "New Test Product",
#             "sku": "NTP001",
#             "category": "New Category",
#             "unit_of_measure": "PCS",
#             "is_active": True
#         }
        
#         response = self.client.post(url, data, format='json')
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#         self.assertEqual(Product.objects.count(), 3)
        
#     def test_update_product(self):
#         """Test updating a product"""
#         url = reverse('product-detail', args=[self.product1.id])
#         data = {
#             "name": "Updated Product",
#             "sku": "TP001",  # Keep the same SKU to avoid unique constraint violation
#             "category": "Updated Category",
#             "unit_of_measure": "EA",
#             "is_active": True
#         }
        
#         response = self.client.put(url, data, format='json')
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
        
#         # Refresh from database
#         self.product1.refresh_from_db()
#         self.assertEqual(self.product1.name, "Updated Product")
#         self.assertEqual(self.product1.category, "Updated Category")
        
#     def test_delete_product(self):
#         """Test deleting a product"""
#         url = reverse('product-detail', args=[self.product2.id])
#         response = self.client.delete(url)
        
#         self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
#         self.assertEqual(Product.objects.count(), 1)
        
#     def test_product_suppliers_action(self):
#         """Test retrieving product suppliers"""
#         url = reverse('product-suppliers', args=[self.product1.id])
#         response = self.client.get(url)
        
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(len(response.data), 1)
#         self.assertEqual(response.data[0]['unit_price'], '10.99')
#         self.assertEqual(response.data[0]['supplier'], self.supplier.id)
        
#     def test_filter_products_by_category(self):
#         """Test filtering products by category"""
#         url = reverse('product-list') + '?search=Category A'
#         response = self.client.get(url)
        
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(len(response.data), 1)
#         self.assertEqual(response.data[0]['name'], "Test Product 1")
        
#     def test_ordering_products(self):
#         """Test ordering products by name"""
#         url = reverse('product-list') + '?ordering=name'
#         response = self.client.get(url)
        
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(len(response.data), 2)
#         self.assertEqual(response.data[0]['name'], "Test Product 1")
#         self.assertEqual(response.data[1]['name'], "Test Product 2")
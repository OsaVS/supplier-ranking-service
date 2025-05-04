from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'q-learning-states', views.QLearningStateViewSet)
router.register(r'q-learning-actions', views.QLearningActionViewSet)
router.register(r'q-table-entries', views.QTableEntryViewSet)
router.register(r'supplier-rankings', views.SupplierRankingViewSet)
router.register(r'supplier-performance-cache', views.SupplierPerformanceCacheViewSet)
router.register(r'ranking-configurations', views.RankingConfigurationViewSet)
router.register(r'ranking-events', views.RankingEventViewSet)

# Additional non-viewset URLs
additional_urls = [
    # Q-Learning and training endpoints
    path('train-q-learning-model/', views.TrainQLearningModelView.as_view(), name='train-q-learning-model'),
    path('predict-supplier-ranking/', views.PredictSupplierRankingView.as_view(), name='predict-supplier-ranking'),
    
    # Analytics endpoints
    path('supplier-metrics/<int:supplier_id>/', views.SupplierMetricsView.as_view(), name='supplier-metrics'),
    path('ranking-history/', views.SupplierRankingHistoryView.as_view(), name='ranking-history'),
    path('performance-dashboard/', views.PerformanceDashboardView.as_view(), name='performance-dashboard'),
    
    # Recommendations and decision support
    path('supplier-recommendations/', views.SupplierRecommendationView.as_view(), name='supplier-recommendations'),
    path('optimal-order-allocation/', views.OptimalOrderAllocationView.as_view(), name='optimal-order-allocation'),
    # path('ranking-comparison/', views.RankingComparisonView.as_view(), name='ranking-comparison'),
    
    # Integration endpoints for other services
    # path('fetch-supplier-data/', views.FetchSupplierDataView.as_view(), name='fetch-supplier-data'),
    # path('fetch-product-data/', views.FetchProductDataView.as_view(), name='fetch-product-data'),
    # path('fetch-transaction-data/', views.FetchTransactionDataView.as_view(), name='fetch-transaction-data'),
    
    # Integration endpoints for other groups
    path('demand-forecast-integration/', views.DemandForecastIntegrationView.as_view(), name='demand-forecast-integration'),
    path('blockchain-data-integration/', views.BlockchainDataIntegrationView.as_view(), name='blockchain-data-integration'),
    path('logistics-integration/', views.LogisticsIntegrationView.as_view(), name='logistics-integration'),
    
    # System management endpoints
    path('reset-q-table/', views.ResetQTableView.as_view(), name='reset-q-table'),
    path('export-ranking-data/', views.ExportRankingDataView.as_view(), name='export-ranking-data'),
    path('import-performance-data/', views.ImportPerformanceDataView.as_view(), name='import-performance-data'),
    # path('sync-supplier-cache/', views.SyncSupplierCacheView.as_view(), name='sync-supplier-cache'),
    
    # Supplier performance detail
    # path('supplier-performance-detail/<int:supplier_id>/', views.SupplierPerformanceDetailView.as_view(), 
    #      name='supplier-performance-detail'),
]

# Combine router URLs and additional URLs
urlpatterns = [
    path('', include(router.urls)),
    *additional_urls,
    
    # API documentation
    path('docs/', views.APIDocumentationView.as_view(), name='api-docs'),
]
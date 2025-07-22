from django.urls import path
from .views import RegisterView, SummarizeView, HistoryView, HistoryDetailView, DownloadSummaryPDFView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('summarize/', SummarizeView.as_view(), name='summarize'),
    path('history/', HistoryView.as_view(), name='history'),
    path('history/<int:pk>/', HistoryDetailView.as_view(), name='history-detail'),
    path('history/<int:pk>/download/', DownloadSummaryPDFView.as_view(), name='history-download'),
]
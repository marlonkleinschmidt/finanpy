from django.urls import path

from ai.views import AnalysisCreateView, AnalysisDetailView, AnalysisListView

app_name = 'ai'

urlpatterns = [
    path('', AnalysisListView.as_view(), name='list'),
    path('new/', AnalysisCreateView.as_view(), name='create'),
    path('<int:pk>/', AnalysisDetailView.as_view(), name='detail'),
]

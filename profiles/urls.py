from django.urls import path

from profiles.views import ProfileUpdateView

urlpatterns = [
    path('profile/', ProfileUpdateView.as_view(), name='profile'),
]

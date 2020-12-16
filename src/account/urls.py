from django.urls import path
from account.views import (
    AccountRegistrationView,
    AccountLoginView,
    AccountProfileView,
    AccountLogoutView,
    AccountView,
    AccountSearchView,
    AccountAllView,
    AccountEditView,
)


urlpatterns = [
    path('all/', AccountAllView.as_view(), name='all'),
    path('edit/', AccountEditView.as_view(), name='edit'),
    path('login/', AccountLoginView.as_view(), name='login'),
    path('logout/', AccountLogoutView.as_view(), name='logout'),
    path('profile/', AccountProfileView.as_view(), name='profile'),
    path('register/', AccountRegistrationView.as_view(), name='register'),
    path('search/', AccountSearchView.as_view(), name='search'),
    path('<int:user_id>/', AccountView.as_view(), name='detail'),
]
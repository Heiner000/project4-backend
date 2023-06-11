from django.urls import path
# from rest_framework_simplejwt.views import (
#     TokenObtainPairView,
#     TokenRefreshView,
# )
from . import views
from rest_framework_simplejwt import views as jwt_views

urlpatterns = [
    # Authentication
    path('register/', views.register_view, name='register'),
    path('token/', jwt_views.TokenObtainPairView.as_view(), name='token_obtain_pair'),
    
    # User trades and portfolio
    path('trades/', views.trade_stock, name='trade_stock'),
    path('watchlist/', views.add_to_watchlist, name='add_to_watchlist'),
    path('get_watchlist/', views.user_watchlist, name='user_watchlist'),
    path('trade_history/', views.trade_history, name='trade_history'),
    path('user_info/', views.get_user, name='get_user'),
    path('user_shares/', views.user_shares, name='user_shares'),
    path('update_funds/', views.update_funds, name='update_funds'),
    path('user_all_shares/', views.user_all_shares, name='user_all_shares'),
    path('user_portfolio_values/', views.user_portfolio_values, name='user_portfolio_values'),
    path('users_and_stocks/', views.users_and_stocks, name='users_and_stocks'),
    path('remove_watchlist/<str:ticker>/<str:userId>/', views.remove_watchlist, name='remove_watchlist'),
    path('array_watchlist/', views.array_watchlist, name='array_watchlist'),

    # Following and unfollowing users
    path('follow/<int:user_id>/<int:followed_user_id>/', views.follow_user, name='follow_user'),
    path('followers/<int:user_id>/', views.followers, name='followers'),

    # Assets
    path('assets/search/<str:ticker>/', views.search_asset, name='search_asset'),
]

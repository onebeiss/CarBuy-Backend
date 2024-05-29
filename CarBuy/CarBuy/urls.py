from django.contrib import admin
from django.urls import path
from carbuyrest22app import endpoints

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', endpoints.users),
    path('sessions/', endpoints.sessions),
    path('password/', endpoints.password),
    path('account/', endpoints.account),
    path('search/', endpoints.search_cars),
    path('ad/<int:position_id>/', endpoints.ad_details),
    path('ad_management/', endpoints.ad_management)
]

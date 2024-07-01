from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, InterestViewSet, GoogleLogin, FacebookLogin


router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'interests', InterestViewSet)

urlpatterns = [
    path('', include(router.urls)),
    # path('rest-auth/', include('rest_auth.urls')),
    # path('rest-auth/registration/', include('rest_auth.registration.urls')),
    path('rest-auth/google/', GoogleLogin.as_view(), name='google_login'),
    path('rest-auth/facebook/', FacebookLogin.as_view(), name='facebook_login'),
]

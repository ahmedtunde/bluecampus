from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FAQView, HelpCenterView, PrivacyPolicyView, TermsOfServiceView, UserViewSet, InterestViewSet, GoogleLogin, FacebookLogin, LoginView


router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'interests', InterestViewSet)

urlpatterns = [
    path('', include(router.urls)),
    # path('rest-auth/', include('rest_auth.urls')),
    # path('rest-auth/registration/', include('rest_auth.registration.urls')),
    path('login/', LoginView.as_view(), name='login'),  # Add login URL here
    path('rest-auth/google/', GoogleLogin.as_view(), name='google_login'),
    path('rest-auth/facebook/', FacebookLogin.as_view(), name='facebook_login'),
    path('privacy-policy/', PrivacyPolicyView.as_view(), name='privacy_policy'),
    path('terms-of-service/', TermsOfServiceView.as_view(), name='terms_of_service'),
    path('help-center/', HelpCenterView.as_view(), name='help_center'),
    path('faq/', FAQView.as_view(), name='faq'),
]

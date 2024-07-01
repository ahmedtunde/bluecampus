from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model, authenticate
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from .models import Interest
from .serializers import UserSerializer, InterestSerializer
from bluecampus.util.renderers import set_otp, send_otp
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from dj_rest_auth.registration.views import SocialLoginView


User = get_user_model()

class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter

class FacebookLogin(SocialLoginView):
    adapter_class = FacebookOAuth2Adapter



class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    @action(detail=False, methods=['post'], url_path='send-otp')
    def send_otp(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        user, created = User.objects.get_or_create(email=email, defaults={'username': email.split('@')[0]})
        if created:
            # Send OTP for the first time
            set_otp(user)
            return Response({'message': 'OTP sent successfully'}, status=status.HTTP_200_OK)
        else:
            # Resend OTP if it exists
            if not user.otp:
                set_otp(user)
            else:
                send_otp(user.email, user.otp)
            return Response({'message': 'OTP sent successfully'}, status=status.HTTP_200_OK)
    # @action(detail=False, methods=['post'], url_path='send-otp')
    # def send_otp(self, request):
    #     email = request.data.get('email')
    #     if not email:
    #         return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
        
    #     user, created = User.objects.get_or_create(email=email, defaults={'username': email.split('@')[0]})
    #     if not created:
    #         return Response({'error': 'User with this email already exists'}, status=status.HTTP_400_BAD_REQUEST)
        
    #     set_otp(user)
    #     return Response({'message': 'OTP sent successfully'}, status=status.HTTP_200_OK)
    @action(detail=False, methods=['post'], url_path='verify-otp')
    def verify_otp(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')
        
        if not email or not otp:
            return Response({'error': 'Email and OTP are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'User with this email does not exist'}, status=status.HTTP_404_NOT_FOUND)

        if user.otp != otp:
            return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)
        
        if user.is_otp_expired():
            set_otp(user) # Generate a new OTP for the user
            send_otp(user.email, user.otp) 
            return Response({'error': 'OTP has expired. A new OTP has been sent. Please reverify.'}, status=status.HTTP_400_BAD_REQUEST)
        
        user.otp_verified = True
        user.save()
        return Response({'message': 'OTP verified successfully. Please set your password.'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='set-password')
    def set_password(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        username = request.data.get('username')
        bio = request.data.get('bio')
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')

        if not email or not password:
            return Response({'error': 'Email and password are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'User with this email does not exist'}, status=status.HTTP_404_NOT_FOUND)
        
        if not user.otp_verified:
            return Response({'error': 'Email not verified'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(password)
        user.username = username if username else user.username
        user.bio = bio if bio else user.bio
        user.first_name = first_name if first_name else user.first_name
        user.last_name = last_name if last_name else user.last_name

        user.save()
        return Response({'message': 'Password and user details set successfully'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='login')
    def login(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        if not email or not password:
            return Response({'error': 'Email and password are required'}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, username=email, password=password)
        if user is not None:
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'message': 'Login successful'
            }, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


    @action(detail=False, methods=['patch'], url_path='update-interests', permission_classes=[IsAuthenticated])
    def update_interests(self, request):
        user = request.user
        interests = request.data.get('interests', [])

        if not isinstance(interests, list):
            return Response({'error': 'Interests should be a list'}, status=status.HTTP_400_BAD_REQUEST)

        user.interests.clear()
        for interest_id in interests:
            try:
                interest = Interest.objects.get(id=interest_id)
                user.interests.add(interest)
            except Interest.DoesNotExist:
                return Response({'error': f'Interest with id {interest_id} does not exist'}, status=status.HTTP_400_BAD_REQUEST)

        user.save()
        return Response({'message': 'Interests updated successfully'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['patch'], url_path='update-profile-picture', permission_classes=[IsAuthenticated])
    def update_profile_picture(self, request):
        user = request.user
        profile_picture = request.FILES.get('profile_picture')

        if not profile_picture:
            return Response({'error': 'Profile picture is required'}, status=status.HTTP_400_BAD_REQUEST)

        user.profile_picture = profile_picture
        user.save()
        return Response({'message': 'Profile picture updated successfully'}, status=status.HTTP_200_OK)


class InterestViewSet(viewsets.ModelViewSet):
    queryset = Interest.objects.all()
    serializer_class = InterestSerializer

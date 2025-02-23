from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model, authenticate
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from .models import Interest
from .serializers import UserSerializer, InterestSerializer, UserProfileSerializer
from bluecampus.util.renderers import set_otp, send_otp, set_reset_otp, send_reset_otp
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from dj_rest_auth.registration.views import SocialLoginView
from rest_framework.permissions import AllowAny
from django.db import IntegrityError
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from django.views.generic import TemplateView

User = get_user_model()

class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter

class FacebookLogin(SocialLoginView):
    adapter_class = FacebookOAuth2Adapter


@method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView):
    authentication_classes = []  # This will prevent token checks
    permission_classes = [AllowAny] 

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({'error': 'Email and password are required'}, status=status.HTTP_400_BAD_REQUEST)

        # Authenticate the user
        user = authenticate(request, username=email, password=password)

        # Check if user exists and if the account is not restricted (e.g. not deleted or disabled)
        if user is not None and not user.deleted_status:
            # Generate a refresh and access token
            refresh = RefreshToken.for_user(user)
            # Serialize the user data
            user_data = UserProfileSerializer(user, context={'request': request}).data

            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'message': 'Login successful',
                'data': user_data
            }, status=status.HTTP_200_OK)
        else:
            # Return an error if the credentials are invalid or account is restricted
            return Response({'error': 'Invalid credentials or account is restricted'}, status=status.HTTP_401_UNAUTHORIZED)



class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(deleted_status=False)  # Only fetch non-deleted users
    serializer_class = UserSerializer
    permission_classes = AllowAny

    @action(detail=False, methods=['post'], url_path='send-otp', permission_classes=[AllowAny])
    def send_otp(self, request):    
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the user is already fully registered
        if User.objects.filter(email=email, is_active=True, otp_verified=True).exists():
            return Response({'error': 'User already exists. Please log in.'}, status=status.HTTP_400_BAD_REQUEST)

        # Get or create the user by email
        user, created = User.objects.get_or_create(email=email, defaults={'username': email.split('@')[0], 'is_active': False})
        
        # Generate and set a new OTP regardless of whether the user is new or existing
        response = set_otp(user)
        if isinstance(response, Response):  # If there was an error in set_otp
            return response

        # Send the newly generated OTP
        return Response({'message': 'OTP sent successfully'}, status=status.HTTP_200_OK)



    @action(detail=False, methods=['post'], url_path='send-reset-password-otp', permission_classes=[AllowAny])
    def send_reset_otp(self, request):    
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Get the user by email
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'User with this email does not exist'}, status=status.HTTP_404_NOT_FOUND)     
        # Generate and set a new OTP regardless of whether the user is new or existing
        response = set_reset_otp(user)
        if isinstance(response, Response):  # If there was an error in set_otp
            return response

        # Send the newly generated OTP
        # email_sent = send_reset_otp(user.email, user.otp)
        # if not email_sent:
        #     return Response({'error': 'Failed to send OTP email. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'message': 'OTP sent successfully'}, status=status.HTTP_200_OK)


    # Change Password
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated], url_path='change_password')
    def change_password(self, request):
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')

        if not old_password or not new_password or not confirm_password:
            return Response({'error': 'All fields are required'}, status=status.HTTP_400_BAD_REQUEST)

        if new_password != confirm_password:
            return Response({'error': 'New password and confirmation do not match'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if old password is correct
        if not user.check_password(old_password):
            return Response({'error': 'Old password is incorrect'}, status=status.HTTP_400_BAD_REQUEST)

        # Set the new password
        user.set_password(new_password)
        user.save()

        return Response({'message': 'Password changed successfully'}, status=status.HTTP_200_OK)

    # Change Username
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated], url_path='change_username')
    def change_username(self, request):
        user = request.user
        new_username = request.data.get('new_username')

        if not new_username:
            return Response({'error': 'New username is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the new username is already taken
        if User.objects.filter(username=new_username).exists():
            return Response({'error': 'This username is already taken'}, status=status.HTTP_400_BAD_REQUEST)

        # Set the new username
        user.username = new_username
        user.save()

        # Serialize the updated user object
        user_serializer = UserSerializer(user)

        return Response({
            'message': 'Username changed successfully',
            'user': user_serializer.data
        }, status=status.HTTP_200_OK)
        

    # Delete Account (Mark as Deleted)
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated],  url_path='delete_account')
    def delete_account(self, request):
        user = request.user

        # Mark the user account as deleted
        user.deleted_status = True
        user.is_active = False  # Optionally, you can also deactivate the account
        user.save()

        return Response({'message': 'Account has been deleted'}, status=status.HTTP_200_OK)
    
   
    @action(detail=False, methods=['post'], url_path='verify-otp', permission_classes=[AllowAny])
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
            response = set_otp(user)  # Generate a new OTP for the user
            if isinstance(response, Response):  # If there was an error in set_otp
                return response
            return Response({'error': 'OTP has expired. A new OTP has been sent. Please reverify.'}, status=status.HTTP_400_BAD_REQUEST)

        user.otp_verified = True
        user.save()
        return Response({'message': 'OTP verified successfully. Please proceed to signup.'}, status=status.HTTP_200_OK)


    @action(detail=False, methods=['post'], url_path='signup', permission_classes=[AllowAny])
    def signup(self, request):
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
            return Response({'error': 'User with this email does not exist. Please start with OTP verification.'}, status=status.HTTP_404_NOT_FOUND)

        if user.is_active:
            return Response({'error': 'User is already registered. Please log in.'}, status=status.HTTP_400_BAD_REQUEST)

        if not user.otp_verified:
            return Response({'error': 'Email not verified. Please verify OTP.'}, status=status.HTTP_400_BAD_REQUEST)

        # Check for existing username
        if username and User.objects.filter(username=username).exists():
            return Response({'error': 'Username already exists. Please choose a different username.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Set password and additional details
            user.set_password(password)
            user.username = username if username else user.username
            user.bio = bio if bio else user.bio
            user.first_name = first_name if first_name else user.first_name
            user.last_name = last_name if last_name else user.last_name
            user.is_active = True  # Mark the user as fully registered
            user.save()
        except IntegrityError as e:
            return Response({'error': 'A user with this username already exists.'}, status=status.HTTP_400_BAD_REQUEST)

        # Generate tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        # Serialize user data
        user_data = UserProfileSerializer(user).data

        return Response({
            'message': 'Signup completed successfully',
            'refresh': str(refresh),
            'access': access_token,
            'data': user_data
        }, status=status.HTTP_201_CREATED)
    
    
    @action(detail=False, methods=['patch'], url_path='update-recovery-email', permission_classes=[IsAuthenticated])
    def update_recovery_email(self, request):
        user = request.user
        recovery_email = request.data.get('recovery_email')

        if not recovery_email:
            return Response({'error': 'Recovery email is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate that the input is a valid email
        try:
            validate_email(recovery_email)
        except ValidationError:
            return Response({'error': 'Invalid email address'}, status=status.HTTP_400_BAD_REQUEST)

        # Update recovery email for the user
        user.recovery_email = recovery_email
        user.save()

        # Serialize and return the updated user data
        user_data = UserSerializer(user, context={'request': request}).data
        return Response({
            'message': 'Recovery email updated successfully',
            'user': user_data
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='verify_reset_otp', permission_classes=[AllowAny])    
    def verify_reset_otp(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')

        if not email or not otp:
            return Response({'error': 'Email and OTP are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'User with this email does not exist'}, status=status.HTTP_404_NOT_FOUND)

        if user.reset_otp != otp:
            return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)

        if user.is_otp_expired():
            response = set_otp(user)  # Generate a new OTP for the user
            if isinstance(response, Response):  # If there was an error in set_otp
                return response
            return Response({'error': 'OTP has expired. A new OTP has been sent. Please reverify.'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'message': 'OTP verified successfully. Please set your password.'}, status=status.HTTP_200_OK)


    
    @action(detail=False, methods=['post'], url_path='set-password', permission_classes=[AllowAny])
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
            return Response({'error': 'User with this email does not exist. Please start with OTP verification.'}, status=status.HTTP_404_NOT_FOUND)

        if user.is_active:
            return Response({'error': 'User is already registered. Please log in.'}, status=status.HTTP_400_BAD_REQUEST)

        if not user.otp_verified:
            return Response({'error': 'Email not verified. Please verify OTP.'}, status=status.HTTP_400_BAD_REQUEST)

        # Check for existing username
        if username and User.objects.filter(username=username).exists():
            return Response({'error': 'Username already exists. Please choose a different username.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Set password and additional details
            user.set_password(password)
            user.username = username if username else user.username
            user.bio = bio if bio else user.bio
            user.first_name = first_name if first_name else user.first_name
            user.last_name = last_name if last_name else user.last_name
            user.is_active = True  # Mark the user as fully registered
            user.save()
        except IntegrityError as e:
            return Response({'error': 'A user with this username already exists.'}, status=status.HTTP_400_BAD_REQUEST)

        # Generate tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        # Serialize user data
        user_data = UserProfileSerializer(user).data

        return Response({
            'message': 'Signup completed successfully',
            'refresh': str(refresh),
            'access': access_token,
            'data': user_data
        }, status=status.HTTP_201_CREATED)


    @action(detail=False, methods=['post'], url_path='reset_password', permission_classes=[AllowAny])
    def reset_password(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')
        password = request.data.get('password')

        if not email or not password:
            return Response({'error': 'Email and new password are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'User with this email does not exist'}, status=status.HTTP_404_NOT_FOUND)
        
        if user.reset_otp != otp:
            return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)

        # Set the new password
        user.set_password(password)
        user.save()
        # Serialize user data
        user_data = UserProfileSerializer(user).data

        return Response({
            'message': 'Password reset successfully',
            'data': user_data
        }, status=status.HTTP_201_CREATED)



    @action(detail=False, methods=['post'], url_path='logout', permission_classes=[IsAuthenticated])
    def logout(self, request):
        """
        Logout a user by blacklisting their refresh token.
        """
        try:
            # Token is stored in the request's authorization header (JWT)
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response({'message': 'Logout successful'}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='list-users', permission_classes=[IsAdminUser])
    def list_users(self, request):
        """
        Admin only: Get a list of all users.
        """
        users = User.objects.all()
        serializer = UserProfileSerializer(users, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['patch'], url_path='delete-user', permission_classes=[IsAuthenticated])
    def delete_user(self, request):
        """
        Mark the user account as deleted by setting `deleted_status` to True.
        """
        email = request.data.get('email')
        
        if not email:
            return Response({'error': 'Email is required to delete a user.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Retrieve the user to be marked as deleted by email
            user_to_delete = User.objects.get(email=email)

            # Check if the authenticated user is trying to delete their own account or if they are staff
            if request.user != user_to_delete and not request.user.is_staff:
                return Response({'error': 'You do not have permission to delete this user.'}, status=status.HTTP_403_FORBIDDEN)

            # Mark the user as deleted
            user_to_delete.deleted_status = True
            user_to_delete.save()

            return Response({'message': 'User account deleted successfully.'}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': f'An error occurred: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



    @action(detail=True, methods=['get'], url_path='get-user', permission_classes=[IsAuthenticated])
    def get_user_by_id(self, request, pk=None):
        """
        Get user details by user ID.
        """
        try:
            user = User.objects.get(pk=pk)
            serializer = UserProfileSerializer(user, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)



    @action(detail=False, methods=['patch'], url_path='update-interests', permission_classes=[IsAuthenticated])
    def update_interests(self, request):
        user = request.user
        interests = request.data.get('interests', [])

        # Ensure 'interests' is a list
        if not isinstance(interests, list):
            return Response({'error': 'Interests should be a list'}, status=status.HTTP_400_BAD_REQUEST)

        # Clear existing interests
        user.interests.clear()

        # Add new interests
        for interest_id in interests:
            try:
                interest = Interest.objects.get(id=interest_id)
                user.interests.add(interest)
            except Interest.DoesNotExist:
                return Response({'error': f'Interest with id {interest_id} does not exist'}, status=status.HTTP_400_BAD_REQUEST)

        user.save()

        # Serialize the updated user data
        user_data = UserSerializer(user, context={'request': request}).data

        # Return a successful response with the full user data
        return Response({
            'message': 'Interests updated successfully',
            'user': user_data
        }, status=status.HTTP_200_OK)
    
   
    @action(detail=False, methods=['patch'], url_path='update-profile-picture', permission_classes=[IsAuthenticated])
    def update_profile_picture(self, request):
        user = request.user
        profile_picture = request.FILES.get('profile_picture')

        if not profile_picture:
            return Response({'error': 'Profile picture is required'}, status=status.HTTP_400_BAD_REQUEST)

        user.profile_picture = profile_picture
        user.save()
        user_data = UserProfileSerializer(user, context={'request': request}).data
        return Response({
            'message': 'Profile picture updated successfully',
            'user': user_data
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='user-profile', permission_classes=[IsAuthenticated])
    def user_profile(self, request):
        """
        Get the profile of the currently authenticated user.
        """
        user = request.user  # Get the currently authenticated user
        user_data = UserProfileSerializer(user, context={'request': request}).data  # Serialize user data using the custom serializer

        return Response(user_data, status=status.HTTP_200_OK)
    

    @action(detail=False, methods=['patch'], url_path='user-profile', permission_classes=[IsAuthenticated])
    def update_user_profile(self, request):
        """
        Update the profile of the currently authenticated user.
        Allows partial updates of username, email, first_name, last_name, and bio.
        """
        user = request.user  # Get the currently authenticated user
        data = request.data  # Get the incoming data from the request

        # Use the serializer to validate and update the data
        serializer = UserProfileSerializer(user, data=data, partial=True, context={'request': request})

        # Validate and save the updates if the data is valid
        if serializer.is_valid():
            serializer.save()  # Save the changes
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class InterestViewSet(viewsets.ModelViewSet):
    queryset = Interest.objects.all()
    serializer_class = InterestSerializer
    permission_classes = [AllowAny]  # Allow unauthenticated access


@method_decorator(csrf_exempt, name='dispatch')
class PrivacyPolicyView(TemplateView):
    template_name = 'privacy_policy.html'

@method_decorator(csrf_exempt, name='dispatch')
class TermsOfServiceView(TemplateView):
    template_name = 'terms_of_service.html'

@method_decorator(csrf_exempt, name='dispatch')
class HelpCenterView(TemplateView):
    template_name = 'help_center.html'

@method_decorator(csrf_exempt, name='dispatch')
class FAQView(TemplateView):
    template_name = 'faq.html'
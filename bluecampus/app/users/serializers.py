from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Interest

User = get_user_model()

class InterestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interest
        fields = ['id', 'name']

class UserSerializer(serializers.ModelSerializer):
    interests = InterestSerializer(many=True, read_only=True)
    interest_ids = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True, queryset=Interest.objects.all(), source='interests'
    )
    profile_picture = serializers.ImageField(required=False)


    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'password', 'first_name', 'last_name','recovery_email',
            'bio', 'interests', 'interest_ids', 'otp_verified','profile_picture'
        ]
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        interests_data = validated_data.pop('interests', [])
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        user.interests.set(interests_data)
        return user

    def update(self, instance, validated_data):
        interests_data = validated_data.pop('interests', None)
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        if interests_data is not None:
            instance.interests.set(interests_data)
        instance.save()
        return instance

class UserProfileSerializer(serializers.ModelSerializer):
    interests = InterestSerializer(many=True, read_only=True)
    interest_ids = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True, queryset=Interest.objects.all(), source='interests'
    )
    profile_picture = serializers.SerializerMethodField()  


    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 'profile_picture',
            'bio', 'interests', 'interest_ids'
        ]
        depth = 2
    
    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', {})
        instance = super().update(instance, validated_data)
        
        # If the user has a related profile model, update the bio
        if profile_data:
            profile = instance.profile
            profile.bio = profile_data.get('bio', profile.bio)
            profile.save()

        return instance        
    
    def get_profile_picture(self, obj):
        request = self.context.get('request')
        base_url = 'https://tuns111.pythonanywhere.com'
        
        if obj.profile_picture:
            # If request context is available, use it to build the full URL
            if request:
                return request.build_absolute_uri(obj.profile_picture.url)
            # If request context is not available, prepend the base URL
            else:
                return f"{base_url}{obj.profile_picture.url}"
        return None
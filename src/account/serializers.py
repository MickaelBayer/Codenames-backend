from rest_framework import serializers
from rest_framework.renderers import JSONRenderer
from rest_framework_jwt.settings import api_settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from account.models import Account


JWT_PAYLOAD_HANDLER = api_settings.JWT_PAYLOAD_HANDLER
JWT_ENCODE_HANDLER = api_settings.JWT_ENCODE_HANDLER


class AccountSerializer(serializers.ModelSerializer):

    class Meta:
        model = Account
        fields = ('id', 'last_login', 'email', 'username', 'date_joined', 'is_admin', 'is_active', 'is_staff', 'is_superuser', 'profile_image', 'hide_email')


class AccountRegistrationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Account
        fields = ('email', 'username', 'password')
        # extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = Account.objects.create_user(**validated_data)
        return user


class AccountLoginSerializer(serializers.Serializer):

    email = serializers.CharField(max_length=100)
    password = serializers.CharField(max_length=255, write_only=True)
    token = serializers.CharField(max_length=255, read_only=True)
    user = serializers.JSONField(read_only=True)

    def validate(self, data):
        email = data.get('email', None)
        password = data.get('password', None)
        user = authenticate(email=email, password=password)
        if user is None:
            raise serializers.ValidationError('A user with this email and password is not found')
        try:
            serialized_user = AccountSerializer(user)
            payload = JWT_PAYLOAD_HANDLER(user)
            jwt_token = JWT_ENCODE_HANDLER(payload)
            update_last_login(None, user)
        except user.DoesNotExist:
            raise serializers.ValidationError('User with given email and password does not exist')
        return {
            'email': user.email,
            'user' : serialized_user.data,
            'token': jwt_token
        }

class AccountUpateSerializer(serializers.ModelSerializer):

    email = serializers.EmailField(max_length=100)
    username = serializers.CharField(max_length=100)
    profile_image = serializers.ImageField(max_length=255, required=False, allow_empty_file=True)
    hide_email = serializers.BooleanField()
    
    class Meta:
        model = Account
        fields = ('email', 'username', 'hide_email', 'profile_image')

    def validate_email(self, value):
        if value != self.instance.email:
            try:
                user = Account.objects.get(email=value)
                raise serializers.ValidationError("Email already in use.")
            except Account.DoesNotExist:
                return value
        else:
            return value
    
    def validate_username(self, value):
        if value != self.instance.username:
            try:
                user = Account.objects.get(username=value)
                raise serializers.ValidationError("Username already in use.")
            except Account.DoesNotExist:
                return value
        else:
            return value

    def update(self, instance, validated_data):
        instance.email = validated_data.get('email', instance.email)
        instance.username = validated_data.get('username', instance.username)
        instance.profile_image = validated_data.get('profile_image', instance.profile_image)
        instance.hide_email = validated_data.get('hide_email', instance.hide_email)
        instance.save()
        return instance
        

import re
from typing import Any, Dict, Optional
from django.db.models import Q
from django.contrib.auth import get_user_model
from rest_framework import exceptions
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.state import token_backend
from users.sessions import check_session
from users.models.users import Users
from users.models.friendships import Friends
from django.core.exceptions import ValidationError

class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = Users
        fields = ['id', 'display_name', 'username', 'password', 'avatar', 'otp_enabled', 'is_online', 'oauth_connected', 'password', 'self_hosted_avatar']

    def validate_display_name(self: serializers.ModelSerializer, value: str) -> str:
        if not re.match(r'^[a-zA-Z0-9]+$', value):
            raise serializers.ValidationError(
            )
        return value

    def validate_username(self: serializers.ModelSerializer, value: str) -> str:
        if not re.match(r'^[a-zA-Z0-9]+$', value):
            raise serializers.ValidationError()
        return value

    def valid_password(self: serializers.ModelSerializer, value: str) -> None:
        if not re.match(r'^(?=.*[a-zA-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?":{}|<>~+=\-_/]).+$', value):
            raise serializers.ValidationError(
            )
        if len(value) < 8:
            raise serializers.ValidationError(
            )

    def create(self, validated_data: dict) -> Users:  # noqa: ANN101
        try:
            self.valid_password(validated_data['password'])
        except ValidationError:
            raise serializers.ValidationError(
            )
        user = Users.objects.create(
            username=validated_data['username'],
            display_name=validated_data['display_name']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


    def update(self, instance: Users, validated_data: dict) -> Users:  # noqa: ANN101
        instance.display_name = validated_data.get('display_name', instance.display_name)
        instance.username = validated_data.get('username', instance.username)
        if 'password' in validated_data:
            try:
                self.valid_password(validated_data['password'])
            except ValidationError:
                raise serializers.ValidationError()
            instance.set_password(validated_data['password'])
        instance.avatar = validated_data.get('avatar', instance.avatar)
        instance.otp_enabled = validated_data.get('otp_enabled', instance.otp_enabled)
        instance.is_online = validated_data.get('is_online', instance.is_online)
        instance.save()
        return instance

class GetUserInfoSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    friendship_status = serializers.SerializerMethodField()

    class Meta:
        model = Users
        fields = ['id', 'display_name', 'username', 'avatar', 'status', 'friendship_status', 'oauth_connected']

    def get_status(self: serializers.ModelSerializer, instance: Users) -> Optional[str]:
        from game.multiplayer import MultiplayerPong
        in_progress_players = MultiplayerPong.get_players_by_status('in_progress')
        in_game = any(instance.username in d for d in in_progress_players)
        if in_game:
            return 'in_party'
        return 'online' if instance.is_online else 'offline'

    def get_friendship_status(self: serializers.ModelSerializer, instance: Users) -> Optional[str]:
        try:
            friendship = Friends.objects.select_related('user', 'friend').filter((Q(user=instance) & Q(friend=self.context['request'].user)) | (Q(user=self.context['request'].user) & Q(friend=instance))).first()
            return friendship.status
        except:
            return None

class FriendshipsSerializer(serializers.ModelSerializer):
    user_username = serializers.ReadOnlyField(source='user.username')
    friend_username = serializers.ReadOnlyField(source='friend.username')

    class Meta:
        model = Friends
        fields = ['pk', 'user', 'friend', 'status', 'user_username', 'friend_username']
        extra_kwargs = {'pk': {'read_only': True}, 'user': {'read_only': True}, 'friend': {'read_only': True}, 'status': {'read_only': True}}


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    """
    Inherit from `TokenRefreshSerializer` and touch the database
    before re-issuing a new access token and ensure that the user
    exists and is active.
    """
    error_msg = 'No active account found with the given credentials'

    def validate(self: TokenRefreshSerializer, attrs: Dict[str, Any]) -> Dict[str, str]:
        token_payload = token_backend.decode(attrs['refresh'])
        try:
            user = get_user_model().objects.get(pk=token_payload['user_id'])
            request = self.context.get('request')
            if request and request.COOKIES.get('session'):
                session_token = request.COOKIES.get('session')
                if not check_session(user, session_token):
                    raise exceptions.AuthenticationFailed('Invalid session')
        except get_user_model().DoesNotExist:
            raise exceptions.AuthenticationFailed(
                self.error_msg, 'no_active_account'
            )
        return super().validate(attrs)

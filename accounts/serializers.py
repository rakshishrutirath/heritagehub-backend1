from rest_framework import serializers
from .models import User

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'role', 'community']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User(**{k: v for k, v in validated_data.items() if k != 'password'})
        user.set_password(validated_data['password'])
        user.save()
        return user

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import SignupProof

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "referral_code", "referred_by", "is_approved"]
        read_only_fields = ["referral_code", "is_approved"]

class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    referral_code = serializers.CharField(required=False, allow_blank=True)
    name = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ["email", "password", "name", "first_name", "last_name", "referral_code"]

    def create(self, validated_data):
        ref_code = validated_data.pop("referral_code", "").strip()
        name = validated_data.pop("name", "").strip()
        first = validated_data.pop("first_name", "").strip()
        last = validated_data.pop("last_name", "").strip()
        if name and not first:
            parts = name.split(" ")
            first = parts[0]
            last = " ".join(parts[1:]) if len(parts) > 1 else ""
        email = validated_data.get("email")
        user = User.objects.create_user(username=email, email=email, password=validated_data["password"], first_name=first, last_name=last)
        if ref_code:
            user.referred_by = User.objects.filter(referral_code=ref_code).first()
        user.is_approved = False
        user.save()
        return user

class SignupProofSerializer(serializers.ModelSerializer):
    proof_image_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = SignupProof
        fields = """__all__"""
        read_only_fields = ["user", "status", "processed_at"]

    def get_proof_image_url(self, obj):
        request = self.context.get('request')
        if obj.proof_image and hasattr(obj.proof_image, 'url'):
            url = obj.proof_image.url
            if request is not None:
                return request.build_absolute_uri(url)
            return url
        return None
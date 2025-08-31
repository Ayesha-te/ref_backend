from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import authenticate, get_user_model
from django.utils import timezone
from .serializers import UserSerializer, SignupSerializer, SignupProofSerializer
from .models import SignupProof

User = get_user_model()

class MeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

class SignupView(generics.CreateAPIView):
    serializer_class = SignupSerializer
    permission_classes = [permissions.AllowAny]

class TokenObtainPairPatchedView(TokenObtainPairView):
    """Deny token issuance unless the user is approved by admin."""
    def post(self, request, *args, **kwargs):
        username = request.data.get('username') or request.data.get('email')
        password = request.data.get('password')
        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response({'detail': 'No active account found with the given credentials'}, status=401)
        if not getattr(user, 'is_approved', False):
            return Response({'detail': 'Account pending admin approval'}, status=403)
        return super().post(request, *args, **kwargs)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def request_approval(request):
    # After signup user can explicitly request admin approval; flag could be used for queue
    # For now, nothing extra; admin uses is_approved toggle in admin.
    return Response({"status": "pending"})

class MySignupProofsView(generics.ListCreateAPIView):
    serializer_class = SignupProofSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SignupProof.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # DRF will read amount_pkr, tx_id, proof_image from request.data/FILES automatically
        serializer.save(user=self.request.user)

class SignupProofPublicCreateView(generics.CreateAPIView):
    """Allow unauthenticated users to submit signup proof by email."""
    serializer_class = SignupProofSerializer
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def create(self, request, *args, **kwargs):
        email = request.data.get('email')
        if not email:
            return Response({'detail': 'Email is required'}, status=400)
        user = User.objects.filter(email=email).first()
        if not user:
            return Response({'detail': 'User not found'}, status=404)
        # Remove non-model field 'email' before serializer validation
        data = request.data.copy()
        data.pop('email', None)
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(user=user, status='PENDING')
        headers = self.get_success_headers(serializer.data)
        return Response(SignupProofSerializer(instance, context={'request': request}).data, status=201, headers=headers)

# Admin: list pending users and approve/reject
class AdminPendingUsersView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return User.objects.filter(is_approved=False).order_by('-date_joined')

@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def admin_pending_signup_proofs(request):
    qs = SignupProof.objects.filter(status='PENDING').order_by('-created_at')
    data = SignupProofSerializer(qs, many=True, context={'request': request}).data
    return Response(data)

@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def admin_signup_proof_action(request, pk):
    try:
        sp = SignupProof.objects.get(pk=pk)
    except SignupProof.DoesNotExist:
        return Response({"detail": "Not found"}, status=404)
    action = request.data.get('action')  # APPROVE/REJECT
    if action == 'APPROVE':
        sp.status = 'APPROVED'
        sp.processed_at = timezone.now()
        sp.user.is_approved = True
        sp.user.is_active = True
        sp.user.save()
        sp.save()
    elif action == 'REJECT':
        sp.status = 'REJECTED'
        sp.processed_at = timezone.now()
        sp.user.is_approved = False
        sp.user.save()
        sp.save()
    else:
        return Response({"detail": "Invalid action"}, status=400)
    return Response({"status": sp.status})

@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def admin_approve_user(request, pk):
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response({"detail": "User not found"}, status=404)
    user.is_approved = True
    user.is_active = True
    user.save()
    return Response({"status": "APPROVED"})

@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def admin_reject_user(request, pk):
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response({"detail": "User not found"}, status=404)
    # Keep account but mark inactive and not approved
    user.is_approved = False
    user.is_active = False
    user.save()
    return Response({"status": "REJECTED"})
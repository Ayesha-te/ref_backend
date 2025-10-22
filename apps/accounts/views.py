from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import authenticate, get_user_model
from django.utils import timezone
from django.db import models
from django.db.models import Sum, OuterRef, Subquery, CharField, Count, Value, DecimalField
from django.db.models.functions import Coalesce
from .serializers import UserSerializer, SignupSerializer, SignupProofSerializer
from .models import SignupProof
from apps.earnings.models import PassiveEarning
from apps.wallets.models import DepositRequest, Transaction

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
    """Customized token view.
    - Accepts username or email
    - Auto-bootstraps a specific admin (Ahmad/12345) on first login
    - Allows staff/superusers to bypass approval
    - Requires approval for regular users
    """
    def post(self, request, *args, **kwargs):
        identifier = request.data.get('username') or request.data.get('email')
        password = request.data.get('password')
        if not identifier or not password:
            return Response({'detail': 'Missing credentials'}, status=400)

        # Authenticate using identifier as username for Django's auth
        user = authenticate(request, username=identifier, password=password)
        if user is None:
            return Response({'detail': 'No active account found with the given credentials'}, status=401)

        # One-time bootstrap: promote Ahmad to admin and approve
        if user.username.lower() == 'ahmad' and password == '12345':
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            setattr(user, 'is_approved', True)
            user.save()

        # Allow staff/superusers regardless of approval
        if not (user.is_staff or user.is_superuser):
            if not getattr(user, 'is_approved', False):
                return Response({'detail': 'Account pending admin approval'}, status=403)

        # Issue tokens using resolved username (supports email-or-username input)
        data = {'username': user.username, 'password': password}
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=200)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def request_approval(request):
    # After signup user can explicitly request admin approval; flag could be used for queue
    # For now, nothing extra; admin uses is_approved toggle in admin.
    return Response({"status": "pending"})

class MySignupProofsView(generics.ListCreateAPIView):
    serializer_class = SignupProofSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        return SignupProof.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Mirror deposit flow: explicitly read file from request.FILES
        proof_image = self.request.FILES.get('proof_image')
        serializer.save(user=self.request.user, proof_image=proof_image)

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

# Admin: list pending users with latest pending signup proof info and approve/reject
class AdminPendingUsersView(generics.GenericAPIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, *args, **kwargs):
        latest_pending_proof = SignupProof.objects.filter(user=OuterRef('pk'), status='PENDING').order_by('-created_at')
        users = (
            User.objects
            .filter(is_approved=False)
            .filter(models.Exists(latest_pending_proof))  # Only users who currently have a PENDING signup proof
            .annotate(
                signup_proof_id=Subquery(latest_pending_proof.values('id')[:1]),
                signup_tx_id=Subquery(latest_pending_proof.values('tx_id')[:1], output_field=CharField()),
                signup_proof_path=Subquery(latest_pending_proof.values('proof_image')[:1], output_field=CharField()),
                submitted_at=Subquery(latest_pending_proof.values('created_at')[:1]),
            )
            .order_by('-date_joined')
        )

        def build_proof_url(path: str | None) -> str | None:
            try:
                if not path:
                    return None
                url = f"/media/{path}" if not str(path).startswith('http') else str(path)
                return request.build_absolute_uri(url)
            except Exception:
                return None

        data = [
            {
                'id': u.id,
                'username': u.username,
                'first_name': u.first_name,
                'last_name': u.last_name,
                'email': u.email,
                'signup_proof_id': getattr(u, 'signup_proof_id', None),
                'signup_tx_id': getattr(u, 'signup_tx_id', None) or '',
                'signup_proof_url': build_proof_url(getattr(u, 'signup_proof_path', None)),
                'submitted_at': getattr(u, 'submitted_at', None),
            }
            for u in users
        ]
        return Response(data)

@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def admin_pending_signup_proofs(request):
    qs = SignupProof.objects.filter(status='PENDING').order_by('-created_at')
    data = SignupProofSerializer(qs, many=True, context={'request': request}).data
    return Response(data)

@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def admin_signup_proof_action(request, pk):
    from decimal import Decimal
    from django.conf import settings
    
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
        
        # ===== NEW: Create deposit for signup fee to start passive income =====
        # Convert signup amount to USD using FX rate
        fx_rate = Decimal(str(settings.ADMIN_USD_TO_PKR))
        amount_usd = (sp.amount_pkr / fx_rate).quantize(Decimal('0.01'))
        
        # Check if signup deposit already exists for this user
        existing_signup_deposit = DepositRequest.objects.filter(
            user=sp.user,
            tx_id='SIGNUP-INIT'
        ).first()
        
        if not existing_signup_deposit:
            # Create and credit the signup fee deposit
            deposit = DepositRequest.objects.create(
                user=sp.user,
                amount_pkr=sp.amount_pkr,
                amount_usd=amount_usd,
                fx_rate=fx_rate,
                tx_id='SIGNUP-INIT',
                proof_image=sp.proof_image,  # Link to signup proof
                status='CREDITED',
                processed_at=timezone.now()
            )
            
            # Credit to wallet and record transaction
            from apps.wallets.models import Wallet, Transaction
            from apps.earnings.models_global_pool import GlobalPool
            
            wallet, _ = Wallet.objects.get_or_create(user=sp.user)
            user_share_rate = Decimal(str(settings.ECONOMICS['USER_WALLET_SHARE']))
            global_pool_rate = Decimal(str(settings.ECONOMICS['GLOBAL_POOL_CUT']))
            
            user_share = (amount_usd * user_share_rate).quantize(Decimal('0.01'))
            platform_hold = (amount_usd - user_share).quantize(Decimal('0.01'))
            global_pool = (amount_usd * global_pool_rate).quantize(Decimal('0.01'))
            
            wallet.available_usd = (Decimal(wallet.available_usd) + user_share).quantize(Decimal('0.01'))
            wallet.hold_usd = (Decimal(wallet.hold_usd) + platform_hold).quantize(Decimal('0.01'))
            wallet.save()
            
            # Track global pool balance
            gp = GlobalPool.objects.first() or GlobalPool.objects.create()
            gp.balance_usd = (Decimal(gp.balance_usd) + global_pool).quantize(Decimal('0.01'))
            gp.save()
            
            # Record full deposit in transactions with breakdown
            Transaction.objects.create(
                wallet=wallet,
                type=Transaction.CREDIT,
                amount_usd=amount_usd,
                meta={
                    'type': 'deposit',
                    'source': 'signup-initial',
                    'id': deposit.id,
                    'tx_id': 'SIGNUP-INIT',
                    'user_share_usd': str(user_share),
                    'platform_hold_usd': str(platform_hold),
                    'global_pool_usd': str(global_pool),
                }
            )
        
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
    print(f"DEBUG: admin_reject_user called with pk={pk}, user={request.user}")
    try:
        user = User.objects.get(pk=pk)
        print(f"DEBUG: Found user {user.username} (id={user.id})")
    except User.DoesNotExist:
        print(f"DEBUG: User with pk={pk} not found")
        return Response({"detail": "User not found"}, status=404)
    
    # Keep account but mark inactive and not approved
    print(f"DEBUG: Before rejection - is_approved={user.is_approved}, is_active={user.is_active}")
    user.is_approved = False
    user.is_active = False
    user.save()
    print(f"DEBUG: After rejection - is_approved={user.is_approved}, is_active={user.is_active}")
    return Response({"status": "REJECTED"})

@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def admin_activate_user(request, pk):
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response({"detail": "User not found"}, status=404)
    user.is_active = True
    user.save()
    return Response({"status": "ACTIVATED"})

@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def admin_deactivate_user(request, pk):
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response({"detail": "User not found"}, status=404)
    user.is_active = False
    user.save()
    return Response({"status": "DEACTIVATED"})

class AdminUsersListView(generics.GenericAPIView):
    """Admin endpoint returning users with rewards and bank details.
    Supports search, filters, sorting, and pagination.
    Query params: 
      - q (icontains on username/email)
      - is_approved (true/false)
      - is_active (true/false)
      - is_staff (true/false)
      - date_joined_from (YYYY-MM-DD)
      - date_joined_to (YYYY-MM-DD)
      - order_by (username,email,date_joined,-date_joined,last_login,-last_login,rewards_usd,-rewards_usd)
      - page, page_size
    """
    permission_classes = [permissions.IsAdminUser]

    def _parse_bool(self, val):
        if val is None: return None
        s = str(val).lower()
        if s in ['true','1','yes','y']: return True
        if s in ['false','0','no','n']: return False
        return None

    def get(self, request, *args, **kwargs):
        q = request.query_params.get('q')
        is_approved = self._parse_bool(request.query_params.get('is_approved'))
        is_active = self._parse_bool(request.query_params.get('is_active'))
        is_staff = self._parse_bool(request.query_params.get('is_staff'))
        dj_from = request.query_params.get('date_joined_from')
        dj_to = request.query_params.get('date_joined_to')
        order_by = request.query_params.get('order_by') or 'id'
        page = max(int(request.query_params.get('page', 1) or 1), 1)
        page_size = int(request.query_params.get('page_size', 20) or 20)
        page_size = max(1, min(page_size, 200))  # clamp

        # Latest deposit request per user for bank details
        latest_dr = DepositRequest.objects.filter(user=OuterRef('pk')).order_by('-created_at')
        users = User.objects.all()

        if q:
            users = users.filter(models.Q(username__icontains=q) | models.Q(email__icontains=q))
        if is_approved is not None:
            users = users.filter(is_approved=is_approved)
        if is_active is not None:
            users = users.filter(is_active=is_active)
        if is_staff is not None:
            users = users.filter(is_staff=is_staff)
        if dj_from:
            users = users.filter(date_joined__date__gte=dj_from)
        if dj_to:
            users = users.filter(date_joined__date__lte=dj_to)

        users = users.annotate(
            # PassiveEarning model sum (might be dummy data)
            rewards_usd=Coalesce(Sum('passive_earnings__amount_usd'), Value(0, output_field=DecimalField(max_digits=12, decimal_places=2))),
            passive_income_usd=Coalesce(Sum('passive_earnings__amount_usd'), Value(0, output_field=DecimalField(max_digits=12, decimal_places=2))),
            # Transaction-based passive income (real data)
            passive_income_from_transactions=Coalesce(
                Subquery(
                    Transaction.objects.filter(
                        wallet__user=OuterRef('pk'),
                        type=Transaction.CREDIT,
                        meta__type='passive'
                    ).values('wallet__user')
                    .annotate(total=Sum('amount_usd'))
                    .values('total')[:1],
                    output_field=DecimalField(max_digits=12, decimal_places=2)
                ), 
                Value(0, output_field=DecimalField(max_digits=12, decimal_places=2))
            ),
            bank_name=Subquery(latest_dr.values('bank_name')[:1], output_field=CharField()),
            account_name=Subquery(latest_dr.values('account_name')[:1], output_field=CharField()),
            referrals_count=Count('referrals', distinct=True),  # direct referrals
        )

        allowed_orders = {
            'id': 'id', '-id': '-id',
            'username': 'username', '-username': '-username',
            'email': 'email', '-email': '-email',
            'date_joined': 'date_joined', '-date_joined': '-date_joined',
            'last_login': 'last_login', '-last_login': '-last_login',
            'rewards_usd': 'rewards_usd', '-rewards_usd': '-rewards_usd',
            'referrals_count': 'referrals_count', '-referrals_count': '-referrals_count',
        }
        users = users.order_by(allowed_orders.get(order_by, 'id'))

        total = users.count()
        start = (page - 1) * page_size
        end = start + page_size
        page_qs = users[start:end]

        data = []
        for u in page_qs:
            # Get wallet and calculate current income (passive + referral + milestone + global pool)
            try:
                wallet = u.wallet
                current_balance_usd = str(wallet.available_usd)
                # Calculate current income from wallet method (includes all income types)
                current_income_usd = str(wallet.get_current_income_usd())
                # Also get the stored income_usd field
                stored_income_usd = str(wallet.income_usd)
            except:
                current_balance_usd = '0.00'
                current_income_usd = '0.00'
                stored_income_usd = '0.00'
            
            # Use transaction-based passive income as the primary value (real data)
            real_passive_income = str(getattr(u, 'passive_income_from_transactions', 0) or 0)
            dummy_passive_income = str(getattr(u, 'passive_income_usd', 0) or 0)
            
            data.append({
                'id': u.id,
                'username': u.username,
                'first_name': u.first_name,
                'last_name': u.last_name,
                'email': u.email,
                'is_active': u.is_active,
                'is_staff': u.is_staff,
                'is_approved': u.is_approved,
                'date_joined': u.date_joined,
                'last_login': u.last_login,
                'rewards_usd': real_passive_income,  # Use real transaction-based data
                'passive_income_usd': real_passive_income,  # Use real transaction-based data
                'passive_income_from_model': dummy_passive_income,  # For debugging/comparison
                'current_balance_usd': current_balance_usd,  # Available balance (deposits only)
                'current_income_usd': current_income_usd,  # Total income (passive + referral + milestone + global pool)
                'stored_income_usd': stored_income_usd,  # Stored income_usd field (for comparison)
                'bank_name': getattr(u, 'bank_name', '') or '',
                'account_name': getattr(u, 'account_name', '') or '',
                'referrals_count': getattr(u, 'referrals_count', 0) or 0,
            })

        return Response({
            'count': total,
            'page': page,
            'page_size': page_size,
            'results': data,
        })
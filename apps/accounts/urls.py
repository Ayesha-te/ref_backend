from django.urls import path
from .views import (
    MeView,
    SignupView,
    request_approval,
    AdminPendingUsersView,
    admin_approve_user,
    admin_reject_user,
    MySignupProofsView,
    admin_pending_signup_proofs,
    admin_signup_proof_action,
    SignupProofPublicCreateView,
)

urlpatterns = [
    path('me/', MeView.as_view()),
    path('signup/', SignupView.as_view()),
    path('request-approval/', request_approval),

    # User signup proof (authed)
    path('me/signup-proofs/', MySignupProofsView.as_view()),
    # Public signup proof by email
    path('signup-proof/', SignupProofPublicCreateView.as_view()),

    # Admin
    path('admin/pending-users/', AdminPendingUsersView.as_view()),
    path('admin/approve/<int:pk>/', admin_approve_user),
    path('admin/reject/<int:pk>/', admin_reject_user),
    path('admin/pending-signup-proofs/', admin_pending_signup_proofs),
    path('admin/signup-proof/action/<int:pk>/', admin_signup_proof_action),
]
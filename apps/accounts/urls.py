from django.urls import path
from .views import (
    MeView,
    SignupView,
    request_approval,
    AdminPendingUsersView,
    admin_approve_user,
    admin_reject_user,
    admin_activate_user,
    admin_deactivate_user,
    MySignupProofsView,
    admin_pending_signup_proofs,
    admin_signup_proof_action,
    SignupProofPublicCreateView,
    AdminUsersListView,
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
    path('admin/activate/<int:pk>/', admin_activate_user),
    path('admin/deactivate/<int:pk>/', admin_deactivate_user),
    path('admin/pending-signup-proofs/', admin_pending_signup_proofs),
    path('admin/signup-proof/action/<int:pk>/', admin_signup_proof_action),

    # Admin users list with rewards and bank info
    path('admin/users/', AdminUsersListView.as_view()),
]
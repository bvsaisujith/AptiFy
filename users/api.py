"""
Read-only API for user profile (expose existing User/Profile models).
"""
from typing import Optional, List
from ninja import Router, Schema
from django.shortcuts import get_object_or_404
from aptify.auth import django_auth

router = Router()


class ProfileSchema(Schema):
    username: str
    email: str
    full_name: str
    first_name: str
    last_name: str
    has_profile: bool
    bio: Optional[str] = None
    dob: Optional[str] = None


@router.get("/profile", auth=django_auth, response=ProfileSchema)
def get_my_profile(request):
    """Return current user and profile data (Module 1 – Profile)."""
    user = request.user
    profile = getattr(user, "profile", None)
    return {
        "username": user.username,
        "email": user.email or "",
        "full_name": getattr(profile, "full_name", None) or user.get_full_name() or user.username,
        "first_name": user.first_name or "",
        "last_name": user.last_name or "",
        "has_profile": profile is not None,
        "bio": getattr(profile, "bio", None) or "",
        "dob": str(profile.dob) if profile and profile.dob else None,
    }

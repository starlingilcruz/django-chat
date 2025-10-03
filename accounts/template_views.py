"""
Template-based views for user authentication
"""

from django.contrib.auth import authenticate, get_user_model, login, logout
from django.shortcuts import redirect, render
from django.views import View

from .serializers import SignupSerializer

User = get_user_model()


class LoginTemplateView(View):
    """Login page"""

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("conversation-list")
        return render(request, "accounts/login.html")

    def post(self, request):
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect("conversation-list")

        return render(request, "accounts/login.html", {"error": "Invalid credentials"})


class SignupTemplateView(View):
    """Signup page"""

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("conversation-list")
        return render(request, "accounts/signup.html")

    def post(self, request):
        data = {
            "email": request.POST.get("email"),
            "username": request.POST.get("username"),
            "first_name": request.POST.get("first_name"),
            "last_name": request.POST.get("last_name"),
            "password": request.POST.get("password"),
            "password_confirm": request.POST.get("password_confirm"),
        }

        serializer = SignupSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            login(request, user)
            return redirect("conversation-list")

        return render(request, "accounts/signup.html", {"errors": serializer.errors})


class LogoutTemplateView(View):
    """Logout view"""

    def get(self, request):
        logout(request)
        return redirect("login")

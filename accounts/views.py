"""
Views for user authentication
"""

import logging

from django.contrib.auth import authenticate, get_user_model
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import LoginSerializer, SignupSerializer, UserSerializer

User = get_user_model()
logger = logging.getLogger(__name__)


class SignupView(APIView):
    """
    API endpoint for user registration
    """

    permission_classes = [AllowAny]
    serializer_class = SignupSerializer

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user_serializer = UserSerializer(user)

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)

            logger.info(
                "User registered successfully",
                extra={"user_id": user.id, "email": user.email},
            )

            return Response(
                {
                    "user": user_serializer.data,
                    "tokens": {
                        "refresh": str(refresh),
                        "access": str(refresh.access_token),
                    },
                },
                status=status.HTTP_201_CREATED,
            )

        logger.warning(
            "User registration failed",
            extra={"errors": serializer.errors},
        )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """
    API endpoint for user login
    """

    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            password = serializer.validated_data["password"]

            # Authenticate user
            user = authenticate(request, username=email, password=password)

            if user is not None:
                # Generate JWT tokens
                refresh = RefreshToken.for_user(user)
                user_serializer = UserSerializer(user)

                logger.info(
                    "User logged in successfully",
                    extra={"user_id": user.id, "email": user.email},
                )

                return Response(
                    {
                        "user": user_serializer.data,
                        "tokens": {
                            "refresh": str(refresh),
                            "access": str(refresh.access_token),
                        },
                    },
                    status=status.HTTP_200_OK,
                )

            logger.warning(
                "Login failed - invalid credentials",
                extra={"email": email},
            )
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

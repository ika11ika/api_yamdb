import random

from django.core.mail import send_mail
from django.shortcuts import get_object_or_404

from rest_framework import permissions, status, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken

from api_yamdb.settings import EMAIL_HOST_USER
from api.permissions import IsAuthenticatedAdmin
from users.models import User
from .serializers import (TokenSerializer, UserAdminCreateSerializer,
                          UserFieldsSerializer, UserSignUpSerializer)


class UserRUDView(APIView):
    """Вью для операций с пользователем. (получение, обновление, удаление)"""
    permission_classes = [IsAuthenticatedAdmin]

    def get(self, request, username):
        user = get_object_or_404(User, username=username)
        serializer = UserFieldsSerializer(user)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    def patch(self, request, username):
        user = get_object_or_404(User, username=username)
        serializer = UserFieldsSerializer(
            user,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.validated_data,
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, username):
        user = get_object_or_404(User, username=username)
        if user:
            user.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class UsersViewSet(viewsets.ModelViewSet):
    """Вью для создания пользователей администратором."""
    queryset = User.objects.all()
    permission_classes = (IsAuthenticatedAdmin,)
    serializer_class = UserAdminCreateSerializer
    pagination_class = PageNumberPagination

    def perform_create(self, serializer):
        if self.request.data.get('role') is None:
            serializer.save(role="user")
        else:
            serializer.save()


class CreateUserView(APIView):
    """Вью для самостоятельной регистрации пользователя."""
    def post(self, request):
        serializer = UserSignUpSerializer(data=request.data)
        if serializer.is_valid():
            code = random.randint(1000, 9999)
            user = serializer.save(
                confirmation_code=code,
            )
            send_mail(
                'YAMDB API confirmation code',
                str(code),
                EMAIL_HOST_USER,
                [user.email],
                fail_silently=False,
            )
            return Response(
                {'email': user.email, 'username': user.username},
                status=status.HTTP_200_OK
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class GetUserInfoView(APIView):
    """Вью для самостоятельного получения и обновления инфы пользователя."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = User.objects.get(id=request.user.pk)
        serializer = UserFieldsSerializer(user)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    def patch(self, request):
        user = User.objects.get(id=request.user.pk)
        new_query_dict = self.request.data.copy()
        if not request.user.is_admin and not request.user.is_superuser:
            new_query_dict['role'] = request.user.role
        serializer = UserFieldsSerializer(
            user,
            data=new_query_dict,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.validated_data,
                status=status.HTTP_200_OK
            )
        return Response(
            serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )


class GetAPIToken(APIView):
    """Вью для получения токена."""
    def post(self, request):
        serializer = TokenSerializer(data=request.data)
        if serializer.is_valid():
            fields = serializer.validated_data
            user = get_object_or_404(User, username=fields['username'])
            if fields['confirmation_code'] == user.confirmation_code:
                token = AccessToken.for_user(user)
                return Response(
                    {'token': str(token)},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {'Неверный код'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(
            {'Неверные данные'},
            status=status.HTTP_400_BAD_REQUEST
        )

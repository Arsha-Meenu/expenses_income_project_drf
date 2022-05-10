from distutils.log import error
import imp
from os import stat
from pydoc import describe
import re
import jwt
from django.urls import reverse
from django.shortcuts import render
from rest_framework import status,views
from .models import User
from .serializers import *
from rest_framework.response import Response
from rest_framework import generics,status
from rest_framework_simplejwt.tokens import RefreshToken
from .utils import Util
from django.contrib.sites.shortcuts import get_current_site
from django.conf import settings
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi 
from .renderers import *
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import smart_bytes,smart_str,force_bytes,DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_decode,urlsafe_base64_encode
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from .utils import Util

class RegisterView(generics.GenericAPIView):

    serializer_class = RegisterSerializer
    renderer_classes = (UserRenderer,)

    def post(self, request):
        user = request.data
        serializer = self.serializer_class(data=user)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        user_data = serializer.data
        # email sending
        user = User.objects.get(email=user_data['email'])
        print('user',user)
        print(str(RefreshToken.for_user(user)))
        print('access',str(RefreshToken.for_user(user).access_token))
        token = RefreshToken.for_user(user).access_token
        current_site = get_current_site(request).domain
        relativeLink = reverse('email-verify')
        absurl = 'http://'+current_site+relativeLink+"?token="+str(token)
        email_body = 'Hi '+user.username + \
            ' Use the link below to verify your email \n' + absurl
        data = {'email_body': email_body, 'to_email': user.email,
                'email_subject': 'Verify your email'}
        Util.send_email(data)
        # \
        return Response(user_data, status=status.HTTP_201_CREATED)


class VerifyEmail(views.APIView):
    serializer_class = EmailVerificationSerializer

    token_param_config = openapi.Parameter(
        'token', in_=openapi.IN_QUERY, description='Description', type=openapi.TYPE_STRING)

    @swagger_auto_schema(manual_parameters=[token_param_config])
    def get(self, request):
        token = request.GET.get('token')
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])    
            
            user = User.objects.get(id=payload['user_id'])
            if not user.is_verified:
                user.is_verified = True
                user.save()
            return Response({'email': 'Successfully activated'}, status=status.HTTP_200_OK)
        except jwt.ExpiredSignatureError as identifier:
            return Response({'error': 'Activation Expired'}, status=status.HTTP_400_BAD_REQUEST)
        except jwt.exceptions.DecodeError as identifier:
            return Response({'error': 'Invalid token','identifier':identifier}, status=status.HTTP_400_BAD_REQUEST)


class LoginAPIView(generics.GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        print('serializer.data',serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RequestPasswordReset(generics.GenericAPIView):
    serializer_class = ResetPasswordEmailRequestSerializer

    def post(self,request):
        serializer = self.serializer_class(data=request.data)

        email = request.data.get('email','')
        if User.objects.filter(email = email).exists():
            user = User.objects.get(email = email)
            uidb64 = urlsafe_base64_encode(smart_bytes(user.id))
            token = PasswordResetTokenGenerator().make_token(user)

            current_site = get_current_site(request=request).domain
            relativeLink = reverse('password-reset-confirm',kwargs={'uidb64':uidb64,'token':token   })
            absurl = 'http://'+current_site+relativeLink
            email_body = 'Hello, \n Use the link below to reset your password \n' + absurl
            data = {'email_body': email_body, 'to_email': user.email,
                        'email_subject': 'Reset Your Password '}
            Util.send_email(data)
        return Response({'success':'We have sent a link tou you to reset the password.'},status=status.HTTP_200_OK)


class PasswordTokenCheckAPIView(generics.GenericAPIView):

    def get(self,request,uidb64,token):
        try:
            id = smart_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id = id)
            if not PasswordResetTokenGenerator().check_token(user,token):
                return Response({'error':'Token is not valid.Please request a anew one.'},status= status.HTTP_401_UNAUTHORIZED)
            return Response({'status':True,'message':'Credentials Valid','uidb64':uidb64,'token':token},status=status.HTTP_200_OK)
            

        except DjangoUnicodeDecodeError as identifier:

            if not PasswordResetTokenGenerator().check_token(user):
                return Response({'error':'Token is not valid.Please request a anew one.'},status= status.HTTP_401_UNAUTHORIZED)


class SetNewPasswordAPIView(generics.GenericAPIView):
    serializer_class = SetNewPasswordSerializer

    def patch(self,request):
        serializer = self.serializer_class(data = request.data)
        serializer.is_valid(raise_exception =True)
        return Response({'success':True,'message':'Password reset success.'},status=status.HTTP_200_OK)

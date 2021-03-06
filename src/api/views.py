from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.utils import timezone
from django.forms.models import model_to_dict

from rest_framework.decorators import api_view, permission_classes
from django.conf.urls import url, include
from django.contrib.auth.models import User
from rest_framework import routers, serializers, viewsets
from rest_framework import permissions
from rest_framework.permissions import IsAuthenticated

from api import serializers

import json

from core import models

# Create your views here.

class JSONResponse(HttpResponse):
    """
    An HttpResponse that renders its content into JSON.
    """
    def __init__(self, data, **kwargs):
        content = JSONRenderer().render(data)
        kwargs['content_type'] = 'application/json'
        super(JSONResponse, self).__init__(content, **kwargs)

@api_view(['GET'])
@permission_classes((permissions.AllowAny, ))
def index(request):
    response_dict = {
        'Message': 'Welcome to the API',
        'Version': '1.0',
        'API Endpoints':
            [],
    }
    json_content = json.dumps(response_dict)

    return HttpResponse(json_content, content_type="application/json")

class BookViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows books to be viewed or edited.
    """
    queryset = models.Book.objects.all().order_by('-submission_date')
    serializer_class = serializers.BookSerializer


class AuthorViewSet(viewsets.ModelViewSet):

    queryset = models.Author.objects.all()
    serializer_class = serializers.AuthorSerializer

class JuraBookViewSet(viewsets.ModelViewSet):

    permission_classes = (IsAuthenticated,)

    queryset = models.Book.objects.all().order_by('-submission_date')
    serializer_class = serializers.JuraBookSerializer

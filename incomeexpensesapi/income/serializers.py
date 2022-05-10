from rest_framework import serializers
from .models import *


class IncomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Income
        fields = ['id','date','description','source','amount']
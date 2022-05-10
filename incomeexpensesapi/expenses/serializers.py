from unicodedata import category
from rest_framework import serializers
from .models import *
class ExpensesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = ['id','date','description','category','amount']
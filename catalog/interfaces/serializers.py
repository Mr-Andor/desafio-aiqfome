from rest_framework import serializers


class ProductSearchResultSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    description = serializers.CharField()
    price = serializers.FloatField()
    rating = serializers.FloatField(required=False, allow_null=True)
    image = serializers.CharField(required=False, allow_null=True, allow_blank=True)

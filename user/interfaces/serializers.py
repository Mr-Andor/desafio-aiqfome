from rest_framework import serializers


class CustomerOutputSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    email = serializers.EmailField()


class CustomerInputSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    email = serializers.EmailField()


class CustomerCreateInputSerializer(CustomerInputSerializer):
    password = serializers.CharField(write_only=True, min_length=1)


class FavoriteCreateSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)


class FavoriteOutputSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    customer_id = serializers.IntegerField()
    product_id = serializers.IntegerField()
    title = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    description = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    price = serializers.FloatField(required=False, allow_null=True)
    rating = serializers.FloatField(required=False, allow_null=True)
    image = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    review = serializers.JSONField(required=False, allow_null=True)

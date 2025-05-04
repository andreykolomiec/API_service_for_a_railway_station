from rest_framework import serializers
from railway_station.models import Train, TrainType


class TrainTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = TrainType
        fields = ("id", "name")


class TrainSerializer(serializers.ModelSerializer):

    class Meta:
        model = Train
        fields = ("id", "name", "cargo_num", "place_in_cargo", "train_type")


class TrainImageSerializer(serializers.ModelSerializer):

    class Meta:
        model = Train
        fields = ("id", "image")


class TrainListSerializer(TrainSerializer):
    train_type = serializers.SlugRelatedField(
        read_only=True,
        slug_field="name"
    )


class TrainRetrieveSerializer(TrainSerializer):
    train_type = TrainTypeSerializer()
from django.db import transaction
from rest_framework import serializers

from railway_station.models import Train, TrainType, Route, Station, Crew, Journey, Ticket, Order


class TrainTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = TrainType
        fields = ("id", "name")


class TrainSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False)

    class Meta:
        model = Train
        fields = (
            "id",
            "name",
            "cargo_num",
            "place_in_cargo",
            "train_type",
            "image"
        )

    def validate(self, attrs):

        if attrs["cargo_num"] <= 0:
            raise serializers.ValidationError(
                "Cargo num must be greater than zero."
            )
        if attrs["place_in_cargo"] <= 0:
            raise serializers.ValidationError(
                "Place in cargo num must be greater than zero."
            )

        return attrs


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


class StationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Station
        fields = (
            "id",
            "name",
            "latitude",
            "longitude"
        )


class RouteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Route
        fields = (
            "id",
            "source",
            "destination",
            "distance"
        )

    def validate(self, attrs):
        if attrs["source"] == attrs["destination"]:
            raise serializers.ValidationError(
                "Source and destination stations must be different."
            )
        if attrs["distance"] <= 0:
            raise serializers.ValidationError(
                "Distance must be greater than zero."
            )

        return attrs


class RouteListSerializer(serializers.ModelSerializer):
    source = serializers.SlugRelatedField(
        read_only=True,
        slug_field="name"
    )
    destination = serializers.SlugRelatedField(
        read_only=True,
        slug_field="name"
    )
    class Meta:
        model = Route
        fields = (
            "id",
            "source",
            "destination",
            "distance"
        )


class RouteRetrieveSerializer(serializers.ModelSerializer):
    source_name = serializers.CharField(source="source.name", read_only=True)
    destination_name = serializers.CharField(source="destination.name", read_only=True)
    source_coordinates = serializers.SerializerMethodField()
    destination_coordinates = serializers.SerializerMethodField()

    class Meta:
        model = Route
        fields = (
            "id",
            "source_name",
            "source_coordinates",
            "destination_name",
            "destination_coordinates",
            "distance"
        )

    def get_source_coordinates(self, obj):
        if obj.source:
            return obj.source.coordinates
        return None

    def get_destination_coordinates(self, obj):
        if obj.destination:
            return obj.destination.coordinates
        return None


class CrewSerializer(serializers.ModelSerializer):

    class Meta:
        model = Crew
        fields = ("id", "first_name", "last_name")


class JourneySerializer(serializers.ModelSerializer):
    crew = serializers.SlugRelatedField(
        many=True,
        queryset=Crew.objects.all(),
        slug_field="full_name",
        required=False
    )

    class Meta:
        model = Journey
        fields = (
            "id",
            "route",
            "train",
            "departure_time",
            "arrival_time",
            "crew"
        )

    def create(self, validated_data):
        crew_data = validated_data.pop('crew', [])
        journey = Journey.objects.create(**validated_data)
        journey.crew.set(crew_data)
        return journey

    def update(self, instance, validated_data):
        crew_data = validated_data.pop('crew', None)
        instance = super().update(instance, validated_data)
        if crew_data is not None:
            instance.crew.set(crew_data)
        return instance



class JourneyListSerializer(JourneySerializer):
    route_source = serializers.CharField(source="route.source.name", read_only=True)
    route_destination = serializers.CharField(source="route.destination.name", read_only=True)
    train = serializers.SlugRelatedField(
        read_only=True,
        slug_field="name"
    )
    crew_count = serializers.IntegerField(source="crew.count", read_only=True)

    class Meta:
        model = Journey
        fields = (
            "id",
            "route_source",
            "route_destination",
            "train",
            "departure_time",
            "arrival_time",
            "crew_count"
        )


class JourneyRetrieveSerializer(JourneySerializer):
    train = TrainRetrieveSerializer(many=False, read_only=True)
    route = RouteRetrieveSerializer(many=False, read_only=True)
    crew = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="full_name"
    )

    class Meta:
        model = Journey
        fields = (
            "id",
            "route",
            "train",
            "departure_time",
            "arrival_time",
            "crew"
        )


class TicketSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ticket
        fields = ("id","cargo", "seat", "journey")

    def validate(self, attrs):
        Ticket.validate_seat(
            attrs["seat"],
            attrs["journey"].train.place_in_cargo,
            serializers.ValidationError
        )
        Ticket.validate_cargo(
            attrs["cargo"],
            attrs['journey'].train.cargo_num,
            serializers.ValidationError
        )


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=False, allow_empty=False)
    class Meta:
        model = Order
        fields = ("id", "created_at", "tickets")

    def create(self, validated_data):
        with transaction.atomic():
            tickets_data = validated_data.pop("tickets")
            order = Order.objects.create(**validated_data)
            for ticket_data in tickets_data:
                Ticket.objects.create(order=order, **ticket_data)
            return order

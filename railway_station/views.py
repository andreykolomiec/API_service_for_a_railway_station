from datetime import datetime

from django.utils.dateparse import parse_datetime
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from railway_station.models import (
    Crew,
    Journey,
    Order,
    Route,
    Station,
    Train,
    TrainType,
)
from railway_station.permissions import IsAdminAllORIsAuthenticatedReadOnly
from railway_station.serializers import (
    CrewSerializer,
    JourneyListSerializer,
    JourneyRetrieveSerializer,
    JourneySerializer,
    OrderSerializer,
    RouteListSerializer,
    RouteRetrieveSerializer,
    RouteSerializer,
    StationSerializer,
    TrainImageSerializer,
    TrainListSerializer,
    TrainRetrieveSerializer,
    TrainSerializer,
    TrainTypeSerializer,
)


class TrainTypeViewSet(viewsets.ModelViewSet):
    queryset = TrainType.objects.all()
    serializer_class = TrainTypeSerializer
    permission_classes = (IsAdminAllORIsAuthenticatedReadOnly,)

    @staticmethod
    def _params_to_ints(query_string):
        return [int(str_id) for str_id in query_string.split(",")]

    def get_queryset(self):
        queryset = self.queryset
        name = self.request.query_params.get("name")

        if name:
            name_id = self._params_to_ints(name)
            queryset = queryset.filter(id__in=name_id)
        return queryset

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "name",
                type={"type": "array", "items": {"type": "number"}},
                description="Filter train type by name id (ex. ?name=2,3)",
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        """Get list of train types and filter by train type name ID"""
        return super().list(request, *args, **kwargs)


class TrainViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = Train.objects.all()
    serializer_class = TrainListSerializer

    @staticmethod
    def _params_to_ints(query_string):
        return [int(str_id) for str_id in query_string.split(",")]

    def get_serializer_class(self):
        if self.action == "list":
            return TrainListSerializer

        elif self.action == "retrieve":
            return TrainRetrieveSerializer

        elif self.action == "upload_image":
            return TrainImageSerializer

        return TrainSerializer

    def get_queryset(self):
        queryset = self.queryset

        name = self.request.query_params.get("name")
        train_type = self.request.query_params.get("train_type")

        if name:
            name_id = self._params_to_ints(name)
            queryset = queryset.filter(id__in=name_id)

        if train_type:
            train_type = self._params_to_ints(train_type)
            queryset = queryset.filter(train_type__id__in=train_type)

        if self.action in ("list", "retrieve"):
            queryset = queryset.select_related("train_type")
        return queryset.distinct()

    # http://127.0.0.1:8000/api/railway/train/2/upload-image/
    @action(
        methods=["POST"],
        detail=True,
        permission_classes=[IsAdminUser],
        url_path="upload-image",
    )
    def upload_image(self, request, pk=None):
        train = self.get_object()
        serializer = self.get_serializer(train, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "train_type",
                type={"type": "array", "items": {"type": "number"}},
                description="Filter by train_type id (ex. ?train_type=2,3)",
            ),
            OpenApiParameter(
                "name",
                type={"type": "array", "items": {"type": "number"}},
                description="Filter by name id (ex. ?name=2,3)",
            ),
        ],
    )
    def list(self, request, *args, **kwargs):
        """Get list of all trains and filter the trains by train name ID and train type ID."""
        return super().list(request, *args, **kwargs)


class StationViewSet(viewsets.ModelViewSet):
    queryset = Station.objects.all()
    serializer_class = StationSerializer

    @staticmethod
    def _params_to_ints(query_string):
        return [int(str_id) for str_id in query_string.split(",")]

    def get_queryset(self):
        queryset = self.queryset
        station = self.request.query_params.get("station")
        if station:
            station_id = self._params_to_ints(station)
            queryset = queryset.filter(id__in=station_id)
        return queryset

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "station",
                type={"type": "array", "items": {"type": "number"}},
                description="Filter by station id (ex. ?station=2,3)",
            ),
        ],
    )
    def list(self, request, *args, **kwargs):
        """Get a list of all stations and filter by ID"""
        return super().list(request, *args, **kwargs)


class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.all().select_related("source", "destination")
    serializer_class = RouteSerializer

    @staticmethod
    def _params_to_ints(query_string):
        return [int(str_id) for str_id in query_string.split(",")]

    def get_serializer_class(self):
        if self.action == "list":
            return RouteListSerializer
        elif self.action == "retrieve":
            return RouteRetrieveSerializer

        return RouteSerializer

    def get_queryset(self):
        queryset = self.queryset

        source_param = self.request.query_params.get("source")
        destination_param = self.request.query_params.get("destination")
        distance_parm = self.request.query_params.get("distance")

        if source_param:
            source_param_id = self._params_to_ints(source_param)
            queryset = queryset.filter(source__id__in=source_param_id)

        if destination_param:
            destination_param_id = self._params_to_ints(destination_param)
            queryset = queryset.filter(destination__id__in=destination_param_id)

        if distance_parm:
            queryset = queryset.filter(distance=distance_parm)

        return queryset.distinct()

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "source",
                type={"type": "array", "items": {"type": "number"}},
                description="Filter by source id (ex. ?source=2,3)",
            ),
            OpenApiParameter(
                "destination",
                type={"type": "array", "items": {"type": "number"}},
                description="Filter by destination id (ex. ?destination=2,3)",
            ),
        ],
    )
    def list(self, request, *args, **kwargs):
        """Get a list of all sources and destinations and filter the route by source ID and route ID ."""
        return super().list(request, *args, **kwargs)


class CrewViewSet(viewsets.ModelViewSet):
    queryset = Crew.objects.all()
    serializer_class = CrewSerializer
    permission_classes = (IsAdminAllORIsAuthenticatedReadOnly,)

    @staticmethod
    def _params_to_ints(query_string):
        return [int(str_id) for str_id in query_string.split(",")]

    def get_queryset(self):
        queryset = self.queryset
        crew = self.request.query_params.get("crew")
        if crew:
            crew_id = self._params_to_ints(crew)
            queryset = queryset.filter(id__in=crew_id)
        return queryset

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "crew",
                type={"type": "array", "items": {"type": "number"}},
                description="Filter by crew id (ex. ?crew=2,3)",
            ),
        ],
    )
    def list(self, request, *args, **kwargs):
        """Get list of all crews."""
        return super().list(request, *args, **kwargs)


class JourneyViewSet(viewsets.ModelViewSet):
    queryset = (
        Journey.objects.all()
        .select_related("train", "route", "route__source", "route__destination")
        .prefetch_related("crew")
    )
    serializer_class = JourneySerializer

    def get_serializer_class(self):
        if self.action == "list":
            return JourneyListSerializer
        elif self.action == "retrieve":
            return JourneyRetrieveSerializer

        return JourneySerializer

    def get_queryset(self):
        queryset = self.queryset

        start_data = self.request.query_params.get("start")
        route_id_str = self.request.query_params.get("route")
        departure_time_gte = self.request.query_params.get("departure_time__gte")

        if start_data:
            start_data = datetime.strptime(start_data, "%Y-%m-%d").date()
            queryset = queryset.filter(departure_time___date=start_data)

        if route_id_str:
            queryset = queryset.filter(route_id=int(route_id_str))

        if departure_time_gte:
            parsed_dt = parse_datetime(departure_time_gte)
            if parsed_dt:
                queryset = queryset.filter(departure_time__gte=parsed_dt)

        return queryset

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="start",
                type=OpenApiTypes.DATE,
                description=(
                    "Filter journey (trips) starting from the specified date (YYYY-MM-DD)"
                    "(ex. ?start=2025-05-08)"
                ),
                location=OpenApiParameter.QUERY,
                required=False,
            ),
            OpenApiParameter(
                name="route",
                type=OpenApiTypes.INT,
                description="Filter journey (trips) by route ID (ex. ?route=101)",
                location=OpenApiParameter.QUERY,
                required=False,
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        """
        Get a list of all journey (trips) with the ability to filter by start date and route ID.
        """
        return super().list(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="id",
                type=OpenApiTypes.INT,
                description="Ідентифікатор подорожі.",
                location=OpenApiParameter.PATH,
                required=True,
            ),
        ]
    )
    def retrieve(self, request, *args, **kwargs):
        """
        Get detailed information about a specific journey (trip) by its ID.
        """
        return super().retrieve(request, *args, **kwargs)


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().select_related("user")
    serializer_class = OrderSerializer

    def get_queryset(self):
        queryset = (
            Order.objects.filter(user=self.request.user)
            .prefetch_related("tickets")
            .select_related("user")
        )
        created_at = self.request.query_params.get("created_at")
        if created_at:
            created_at = datetime.strptime(created_at, "%Y-%m-%d").date()
            queryset = queryset.filter(created_at__date=created_at)

        return queryset

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="created_at",
                type=OpenApiTypes.DATE,
                description="Filter orders by creation date (YYYY-MM-DD) (ex. ?created_at=2025-05-13)",
                location=OpenApiParameter.QUERY,
                required=False,
            ),
        ],
    )
    def list(self, request, *args, **kwargs):
        """Get a list of user's orders, optionally filtered by creation date."""
        return super().list(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

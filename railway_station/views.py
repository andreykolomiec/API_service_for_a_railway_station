from datetime import datetime

from drf_spectacular.types import OpenApiTypes
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from drf_spectacular.utils import extend_schema, OpenApiParameter

from railway_station.models import Train, TrainType, Station, Route, Crew, Journey, Order
from railway_station.serializers import TrainTypeSerializer, TrainSerializer, TrainListSerializer, \
    TrainRetrieveSerializer, TrainImageSerializer, StationSerializer, RouteSerializer, RouteListSerializer, \
    RouteRetrieveSerializer, CrewSerializer, JourneyListSerializer, JourneyRetrieveSerializer, JourneySerializer, \
    OrderSerializer


class TrainTypeViewSet(viewsets.ModelViewSet):
    queryset = TrainType.objects.all()
    serializer_class = TrainTypeSerializer


class TrainViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
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

        train_type = self.request.query_params.get("train_type")
        if train_type:
            train_type = self._params_to_ints(train_type)
            queryset = queryset.filter(
                train_type__id__in=train_type
            )

        if self.action in ("list", "retrieve"):
            queryset = queryset.select_related("train_type")
        return queryset.distinct()

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
        ],
    )
    def list(self, request, *args, **kwargs):
        """Get list of all trains."""
        return super().list(request, *args, **kwargs)


class StationViewSet(viewsets.ModelViewSet):
    queryset = Station.objects.all()
    serializer_class = StationSerializer


class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.all().select_related("source", "destination")
    serializer_class = RouteSerializer

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

        if source_param:
            queryset = queryset.filter(source=source_param)

        if destination_param:
            queryset = queryset.filter(destination=destination_param)

        return  queryset


class CrewViewSet(viewsets.ModelViewSet):
    queryset = Crew.objects.all()
    serializer_class = CrewSerializer


class JourneyViewSet(viewsets.ModelViewSet):
    queryset = Journey.objects.all().select_related(
        "train",
        "route",
        "route__source",
        "route__destination"
    ).prefetch_related(
        "crew"
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

        if start_data:
            start_data = datetime.strptime(start_data, "%Y-%m-%d").date()
            queryset = queryset.filter(departure_time___date=start_data)

        if route_id_str:
            queryset = queryset.filter(route_id=int(route_id_str))

        return queryset

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="start",
                type=OpenApiTypes.DATE,
                description=
                "Filter journey (trips) starting from the specified date (YYYY-MM-DD)"
                " (ex. ?start=2025-05-08)",
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
        return Order.objects.filter(user=self.request.user).prefetch_related("tickets").select_related("user")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


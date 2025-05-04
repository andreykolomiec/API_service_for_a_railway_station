from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from drf_spectacular.utils import extend_schema, OpenApiParameter

from railway_station.models import Train, TrainType
from railway_station.serializers import TrainTypeSerializer, TrainSerializer, TrainListSerializer, \
    TrainRetrieveSerializer, TrainImageSerializer


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
                name="train_type",
                type={"type": "array", "items": {"type": "number"}},
                description="Filter by train_type id (ex. ?train_type=2,3)",
            ),
        ],
    )
    def list(self, request, *args, **kwargs):
        """Get list of all trains."""
        return super().list(request, *args, **kwargs)

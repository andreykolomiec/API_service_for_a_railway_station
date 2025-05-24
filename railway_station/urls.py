from django.urls import include, path
from rest_framework import routers

from railway_station.views import (
    CrewViewSet,
    JourneyViewSet,
    OrderViewSet,
    RouteViewSet,
    StationViewSet,
    TrainTypeViewSet,
    TrainViewSet,
)

router = routers.DefaultRouter()
router.register("train", TrainViewSet)
router.register("train-type", TrainTypeViewSet)
router.register("stations", StationViewSet)
router.register("route", RouteViewSet)
router.register("journey", JourneyViewSet)
router.register("crew", CrewViewSet)
router.register("order", OrderViewSet)


urlpatterns = [
    path("", include(router.urls)),
]

app_name = "railway_station"

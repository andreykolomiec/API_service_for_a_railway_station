from django.urls import include, path
from railway_station.views import TrainViewSet, TrainTypeViewSet, StationViewSet, RouteViewSet, JourneyViewSet, \
    CrewViewSet, OrderViewSet
from rest_framework import routers


router = routers.DefaultRouter()
router.register("train", TrainViewSet)
router.register("train-type", TrainTypeViewSet)
router.register("stations", StationViewSet)
router.register("route", RouteViewSet)
router.register("journey", JourneyViewSet)
router.register("crew", CrewViewSet)
router.register("orders", OrderViewSet)



urlpatterns = [
    path("", include(router.urls)),
]

app_name = "railway_station"
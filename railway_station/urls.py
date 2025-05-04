from django.urls import include, path
from railway_station.views import TrainViewSet, TrainTypeViewSet
from rest_framework import routers


router = routers.DefaultRouter()
router.register("train", TrainViewSet)
router.register("train-type", TrainTypeViewSet)

urlpatterns = [
    path("", include(router.urls)),
]

app_name = "railway_station"
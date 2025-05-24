from django.test import TestCase
from django.utils.timezone import make_aware
from rest_framework import status

from rest_framework.test import APIClient
from django.urls import reverse
from railway_station.models import (
    TrainType,
    Train,
    Station,
    Route,
    Crew,
    Journey,
    Order,
    Ticket,
)
from django.contrib.auth import get_user_model
from datetime import datetime

User = get_user_model()


class BaseTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_email = "testuser@example.com"
        self.user_password = "pass1234"
        self.user = User.objects.create_user(
            email=self.user_email, password=self.user_password
        )
        self.station_a = Station.objects.create(
            name="Station A", latitude=50.0, longitude=30.0
        )
        self.station_b = Station.objects.create(
            name="Station B", latitude=51.0, longitude=31.0
        )

    def authenticate(self):
        self.client.force_authenticate(user=self.user)


class TrainTypeTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.tt1 = TrainType.objects.create(name="Type1")
        self.tt2 = TrainType.objects.create(name="Type2")

    def test_anonymous_can_get_train_types(self):
        url = reverse("railway_station:traintype-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

    def test_filter_by_ids_authenticated(self):
        self.authenticate()
        url = reverse("railway_station:traintype-list")
        response = self.client.get(url, {"name": f"{self.tt1.id},{self.tt2.id}"})
        self.assertEqual(response.status_code, 200)
        returned_ids = [item["id"] for item in response.json()]
        self.assertIn(self.tt1.id, returned_ids)
        self.assertIn(self.tt2.id, returned_ids)


class TrainTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.tt = TrainType.objects.create(name="Express")
        self.train1 = Train.objects.create(
            name="Train1", train_type=self.tt, cargo_num=1, place_in_cargo=2
        )
        self.train2 = Train.objects.create(
            name="Train2", train_type=self.tt, cargo_num=2, place_in_cargo=3
        )

    def test_anon_cannot_create_train(self):
        url = reverse("railway_station:train-list")
        data = {"name": "NewTrain", "train_type": self.tt.id}
        response = self.client.post(url, data)
        self.assertIn(response.status_code, [401, 403])

    def test_authenticated_can_filter_trains(self):
        self.authenticate()
        url = reverse("railway_station:train-list")
        response = self.client.get(
            url, {"name": str(self.train1.id), "train_type": str(self.tt.id)}
        )
        self.assertEqual(response.status_code, 200)
        ids = [train["id"] for train in response.json()]
        self.assertIn(self.train1.id, ids)


class StationTests(BaseTestCase):
    def setUp(self):
        super().setUp()

    def test_any_user_can_list_stations(self):
        url = reverse("railway_station:station-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

    def test_filter_by_name_authenticated(self):
        self.authenticate()
        url = reverse("railway_station:station-list")
        response = self.client.get(
            url, {"name": f"{self.station_a.name},{self.station_b.name}"}
        )
        self.assertEqual(response.status_code, 200)
        names = [station["name"] for station in response.json()]
        self.assertIn(self.station_a.name, names)
        self.assertIn(self.station_b.name, names)


class RouteTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.route1 = Route.objects.create(
            source=self.station_a, destination=self.station_b, distance=100
        )
        self.route2 = Route.objects.create(
            source=self.station_a, destination=self.station_b, distance=120
        )

    def _get_routes(self, params=None, authenticated=False):
        """A helper method for GET request to route-list."""
        if authenticated:
            self.authenticate()
        url = reverse("railway_station:route-list")
        return self.client.get(url, params)

    def test_anon_can_list_routes(self):
        url = reverse("railway_station:route-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

    def test_filter_routes_authenticated(self):
        self.authenticate()
        url = reverse("railway_station:route-list")
        params = {
            "source": self.station_a.id,
            "destination": self.station_b.id,
            "distance": 100,
        }
        response = self.client.get(path=url, data=params)
        self.assertEqual(response.status_code, 200)
        route_id = [route["id"] for route in response.json()]
        self.assertIn(self.route1.id, route_id)
        self.assertNotIn(self.route2.id, route_id)


class CrewTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.crew1 = Crew.objects.create(first_name="John", last_name="Doe")
        self.crew2 = Crew.objects.create(first_name="Jane", last_name="Smith")

    def _get_returned_names(self, response) -> set[tuple[str, str]]:
        self.assertEqual(response.status_code, 200)
        return {(crew["first_name"], crew["last_name"]) for crew in response.json()}

    def test_list_crews_anon(self):
        url = reverse("railway_station:crew-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

    def test_list_crews_authenticated(self):
        self.authenticate()
        url = reverse("railway_station:crew-list")
        response = self.client.get(url)
        returned_names = self._get_returned_names(response)
        expected_names = {
            (self.crew1.first_name, self.crew1.last_name),
            (self.crew2.first_name, self.crew2.last_name),
        }
        self.assertTrue(expected_names.issubset(returned_names))

    def test_filter_crews_authenticated(self):
        self.authenticate()
        url = reverse("railway_station:crew-list")
        response = self.client.get(url, {"crew": f"{self.crew1.id},{self.crew2.id}"})
        returned_names = self._get_returned_names(response)
        expected_names = {
            (self.crew1.first_name, self.crew1.last_name),
            (self.crew2.first_name, self.crew2.last_name),
        }
        self.assertTrue(expected_names.issubset(returned_names))


class JourneyTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.train = Train.objects.create(
            name="TrainA",
            train_type=TrainType.objects.create(name="TypeA"),
            cargo_num=9,
            place_in_cargo=50,
        )

        self.route = Route.objects.create(
            source=self.station_a, destination=self.station_b, distance=100
        )
        self.journey1 = Journey.objects.create(
            train=self.train,
            route=self.route,
            departure_time=make_aware(datetime(2025, 5, 20, 8, 0)),
            arrival_time=make_aware(datetime(2025, 5, 20, 10, 0)),
        )
        self.journey2 = Journey.objects.create(
            train=self.train,
            route=self.route,
            departure_time=make_aware(datetime(2025, 4, 20, 7, 0)),
            arrival_time=make_aware(datetime(2025, 4, 21, 18, 0)),
        )

    def test_journeys_list_anon(self):
        url = reverse("railway_station:journey-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

    def test_filter_journeys_authenticated(self):
        self.authenticate()
        url = reverse("railway_station:journey-list")
        params = {
            "train": str(self.train.id),
            "route": str(self.route.id),
            "departure_time__gte": "2025-05-01T12:00:00",
        }
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, 200)
        ids = [journey["id"] for journey in response.json()]
        self.assertIn(self.journey1.id, ids)
        self.assertNotIn(self.journey2.id, ids)


class OrderTests(BaseTestCase):
    def setUp(self):
        super().setUp()

        self.train_type = TrainType.objects.create(name="Express")
        self.train = Train.objects.create(
            name="T-123",
            train_type=self.train_type,
            cargo_num=9,
            place_in_cargo=50,
        )

        self.route = Route.objects.create(
            source=self.station_a, destination=self.station_b, distance=100
        )

        self.journey = Journey.objects.create(
            train=self.train,
            route=self.route,
            departure_time=make_aware(datetime(2025, 5, 20, 8, 0)),
            arrival_time=make_aware(datetime(2025, 5, 20, 10, 0)),
        )

        self.order = Order.objects.create(user=self.user)
        self.ticket = Ticket.objects.create(
            cargo=1, seat=1, journey=self.journey, order=self.order
        )

        self.admin_user = User.objects.create_user(
            email="admin@example.com", password="admin123"
        )
        self.admin_user.is_staff = True
        self.admin_user.save()

    def test_authenticated_user_can_list_orders(self):
        self.authenticate()
        url = reverse("railway_station:order-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_unauthenticated_user_cannot_list_orders(self):
        url = reverse("railway_station:order-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_can_create_valid_order(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("railway_station:order-list")
        data = {"tickets": [{"cargo": 2, "seat": 2, "journey": self.journey.id}]}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 2)
        self.assertEqual(Ticket.objects.count(), 2)

    def test_admin_create_order_with_invalid_seat(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("railway_station:order-list")
        data = {"tickets": [{"cargo": 1, "seat": 99, "journey": self.journey.id}]}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("seat", str(response.data))

    def test_admin_create_order_with_invalid_cargo(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("railway_station:order-list")
        data = {"tickets": [{"cargo": 99, "seat": 4, "journey": self.journey.id}]}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("cargo", str(response.data))

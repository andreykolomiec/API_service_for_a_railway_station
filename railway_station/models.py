import pathlib
import uuid

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify
from railway_service import settings


class TrainType(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = "train_types"

    def __str__(self):
        return self.name


def train_image_path(instance: "Train", filename: str) -> pathlib.Path:
    filename = f"{ slugify (instance.name)} - {uuid.uuid4()}" + pathlib.Path(filename).suffix
    return pathlib.Path("uploads/train/") / pathlib.Path(filename)


class Train(models.Model):
    name = models.CharField(max_length=100)
    cargo_num = models.IntegerField(validators=[MinValueValidator(1)])
    place_in_cargo = models.IntegerField(validators=[MinValueValidator(1)])
    train_type = models.ForeignKey(TrainType, related_name="trains", on_delete=models.CASCADE)
    image = models.ImageField(null=True, upload_to=train_image_path)

    class Meta:
        verbose_name_plural = "trains"

    def __str__(self):
        return f"Train: {self.name} (id = {self.id})"


class Station(models.Model):
    name = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()

    class Meta:
        verbose_name_plural = "stations"

    def __str__(self):
        return f"Station: {self.name}"

    @property
    def coordinates(self):
        return f"({self.latitude}, {self.longitude})"


class Route(models.Model):
    source = models.ForeignKey(Station, on_delete=models.CASCADE, related_name="routes_from")
    destination = models.ForeignKey(Station, on_delete=models.CASCADE, related_name="routes_to")
    distance = models.IntegerField()

    class Meta:
        indexes = [
            models.Index(fields=["source", "destination"]),
            models.Index(fields=["distance"]),
        ]

    def __str__(self):
        return f"Route: {self.source} - {self.destination} ({self.distance})"


class Journey(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name="journeys")
    train = models.ForeignKey(Train, on_delete=models.CASCADE, related_name="journeys")
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()

    class Meta:
        indexes = [
            models.Index(fields=["route", "train"]),
            models.Index(fields=["departure_time", "arrival_time"])
        ]
        ordering = ["-departure_time"]

    def __str__(self):
        return (f" rout: {self.route},"
                f" train: {self.train}"
                f" (departure: {self.departure_time},"
                f" arrival: {self.arrival_time})")


class Crew(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    full_name = models.CharField(max_length=200, blank=True, null=True)
    journey = models.ManyToManyField(Journey, related_name="crew")

    class Meta:
        verbose_name_plural = "crews"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name_property(self):

        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        self.full_name = self.full_name_property
        super().save(*args, **kwargs)


class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order: {self.created_at}"


class Ticket(models.Model):
    cargo = models.IntegerField(validators=[MinValueValidator(1)])
    seat = models.IntegerField(validators=[MinValueValidator(1)])
    journey = models.ForeignKey(Journey, on_delete=models.CASCADE, related_name="tickets")
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="tickets")

    class Meta:
        verbose_name_plural = "tickets"
        unique_together = ("seat", "journey")
        ordering = ["seat"]

    def __str__(self):
        return f"{self.journey} - seat: {self.seat}"

    @staticmethod
    def validate_seat(seat: int, places_in_cargo: int, error_to_rais):
        if not (1 <= seat <= places_in_cargo):
            raise error_to_rais(
                {
                    "seat": f"seat must be in the range [1, {places_in_cargo}], not {seat}"
                }
            )

    @staticmethod
    def validate_cargo(cargo: int, cargo_num: int, error_to_rais):
        if not (1 <= cargo <= cargo_num):
            raise error_to_rais(
                {
                    "cargo": f"cargo must be in the range [1, {cargo_num}], not {cargo}"
                }
            )

    def clean(self):
        # train = self.journey.train
        Ticket.validate_seat(self.seat, self.journey.train.place_in_cargo, ValueError)
        Ticket.validate_cargo(self.cargo, self.journey.train.cargo_num, ValueError)

    def save(self, *args, force_insert=False, force_update=False, using=None, update_fields=None):
        self.full_clean()
        return super(Ticket, self).save(force_insert, force_update, using, update_fields)

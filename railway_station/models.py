import pathlib
import uuid

from django.db import models
from django.utils.text import slugify


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
    cargo_num = models.IntegerField()
    place_in_cargo = models.IntegerField()
    train_type = models.ForeignKey(TrainType, related_name="trains", on_delete=models.CASCADE)
    image = models.ImageField(null=True, upload_to=train_image_path)

    class Meta:
        verbose_name_plural = "trains"

    def __str__(self):
        return f"Train: {self.name} (id = {self.id})"
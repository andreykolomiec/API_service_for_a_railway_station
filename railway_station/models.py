from django.db import models


class TrainType(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = "train_types"

    def __str__(self):
        return self.name


class Train(models.Model):
    name = models.CharField(max_length=100)
    cargo_num = models.IntegerField()
    place_in_cargo = models.IntegerField()
    train_type = models.ForeignKey(TrainType, related_name="trains", on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = "trains"

    def __str__(self):
        return f"Train: {self.name} (id = {self.id})"
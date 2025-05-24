from django.contrib import admin

from .models import Crew, Order, Route, Station, Ticket, Train, TrainType

admin.site.register(Train)
admin.site.register(TrainType)
admin.site.register(Station)
admin.site.register(Route)
admin.site.register(Crew)
admin.site.register(Ticket)
admin.site.register(Order)

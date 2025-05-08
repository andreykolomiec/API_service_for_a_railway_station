from django.contrib import admin

from .models import Train, TrainType, Station, Route, Crew, Ticket, Order

admin.site.register(Train)
admin.site.register(TrainType)
admin.site.register(Station)
admin.site.register(Route)
admin.site.register(Crew)
admin.site.register(Ticket)
admin.site.register(Order)


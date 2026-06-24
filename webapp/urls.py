from django.urls import path

from . import views

app_name = "webapp"

urlpatterns = [
    path("", views.index, name="index"),
    path("api/bootstrap/", views.bootstrap, name="bootstrap"),
    path("api/searches/", views.create_searches, name="create_searches"),
    path("api/searches/<int:search_id>/toggle/", views.toggle_search, name="toggle_search"),
    path("api/searches/<int:search_id>/delete/", views.delete_search, name="delete_search"),
]

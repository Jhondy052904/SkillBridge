from django.urls import path
from . import views

urlpatterns = [
    path("list/", views.list_trainings, name="list_trainings"),
    path("post/", views.post_training, name="post_training"),
    path("edit/<str:training_id>/", views.edit_training, name="edit_training"),
    path("delete/<str:training_id>/", views.delete_training, name="delete_training"),
]

from django.urls import path
from . import views

urlpatterns = [
    path("list/", views.list_trainings, name="list_trainings"),
    path("post/", views.post_training, name="post_training"),
    path("register/<str:training_id>/", views.register_training, name="register_training"),
    path("edit/<str:training_id>/", views.edit_training, name="edit_training"),
    path("delete/<str:training_id>/", views.delete_training, name="delete_training"),
    path('<str:training_id>/', views.training_detail, name='training_detail'),
    path("attendees/<str:training_id>/", views.training_attendees, name="training_attendees"),
    path("attendees/<int:attendee_id>/attended/", views.mark_attended, name="mark_attended"),
    path("attendees/<int:attendee_id>/not-attended/", views.mark_not_attended, name="mark_not_attended"),

]

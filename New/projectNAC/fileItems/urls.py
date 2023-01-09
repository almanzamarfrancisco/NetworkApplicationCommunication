from django.urls import path

from fileItems import views

urlpatterns = [
	path(
		route='',
		view=views.HomeView,
		name='home',
	),
]
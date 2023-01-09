from django.urls import path

from fileItems import views

urlpatterns = [
	path(
		route='',
		view=views.home_view,
		name='home',
	),
]
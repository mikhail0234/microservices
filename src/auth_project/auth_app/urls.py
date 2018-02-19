from django.conf.urls import url, include
from django.contrib import admin
from django.contrib.auth import views as auth_views

from src.auth_project.auth_project import views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    url(r'^accounts/login/$', auth_views.LoginView.as_view(template_name='login.html')),
    url(r'^accounts/logout/$', auth_views.LogoutView.as_view(template_name='logout.html'), name='logout'),
    url(r'^secret/$', views.secret_page, name='secret'),
    url(r'^user/$', views.get_user, name='get-user')
]
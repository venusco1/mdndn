from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path("", TemplateView.as_view(template_name="index.html"), name="home"),
    path("user-guide/", TemplateView.as_view(template_name="user-guide.html"), name="user_guide"),
    path("user-guide/detailed-manual/", TemplateView.as_view(template_name="user-manual.html"), name="user_manual"),
    path("admin/", admin.site.urls),
    path("accounts/login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", include("lifeos.urls")),
]

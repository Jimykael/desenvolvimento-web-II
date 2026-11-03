"""URLs do projeto AcadSystem.

/api/...  -> API JSON (app academico)
/admin/   -> administração do Django
/         -> frontend (arquivos estáticos da pasta ../frontend, apenas em desenvolvimento)
"""
from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import RedirectView
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('academico.urls')),
]

if settings.DEBUG:
    urlpatterns += [
        path('', RedirectView.as_view(url='/index.html')),
        re_path(r'^(?P<path>.+)$', serve, {'document_root': settings.FRONTEND_DIR}),
    ]

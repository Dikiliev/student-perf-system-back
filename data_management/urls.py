from django.urls import path
from .views import TemplateDownloadView, ExportView, ImportPreviewView, ImportCommitView

urlpatterns = [
    path('templates/<str:entity>/download/', TemplateDownloadView.as_view(), name='template-download'),
    path('export/<str:entity>/', ExportView.as_view(), name='data-export'),
    path('import/<str:entity>/preview/', ImportPreviewView.as_view(), name='import-preview'),
    path('import/<str:entity>/commit/', ImportCommitView.as_view(), name='import-commit'),
]

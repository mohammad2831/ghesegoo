from django.urls import path
from .views import ProfileUploadGatewayView, ImageSelectionGatewayView, StoryGenerationGatewayView

app_name= 'api_gateway'

urlpatterns = [
    path('audio/upload/', ProfileUploadGatewayView.as_view(), name='gateway-profile-upload'),
    path('images/select/', ImageSelectionGatewayView.as_view(), name='gateway-image-upload'),
    path('story/generate/', StoryGenerationGatewayView.as_view(), name='gateway-story-generate'),
]
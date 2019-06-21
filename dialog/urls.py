from django.conf.urls import url
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    url(r'^chat_message/', views.chat_message, name='chat_message'),
    url(r'^rate_chat/', views.rate_chat, name='rate_chat'),
    url(r'^rate_chat_response/', views.rate_chat_response, name='rate_chat_response'),
    url(r'^error/', views.error, name='error'),
    url(r'^dialogadmins/', views.bot_test_page, name='bot_test_page'),
    url(r'^(?P<study_key>\w+)/', views.index, name='index'),
    url(r'^$', views.index, name='index'),
]

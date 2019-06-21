from django.contrib import admin
from .models import ChatRecord, ChatRating, Study
from django.conf.urls import url
from django.http.response import HttpResponse
import csv, simplejson
from django import forms
from .chatbots import chatbots
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count

def register(model):
    def inner(admin_class):
        admin.site.register(model,admin_class)
        return admin_class

    return inner


def _download_records_csv(request, study_key=None):
    all_records = ChatRecord.objects.order_by('study_key', 'chat_id', 'timestamp')

    study = None
    if study_key:
        study = Study.objects.get(key=study_key)
        all_records = all_records.filter(study_key=study.key)

    all_records = all_records.all()

    chat_ids = set([record.chat_id for record in all_records])

    ratings = ChatRating.objects.filter(chat_id__in=chat_ids)
    ratings = {rating.chat_id: rating for rating in ratings}

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="chatrecords{0}.csv"'.format("_" + study.key if study else "")

    writer = csv.writer(response)
    writer.writerow(["ID", "Chat ID", "Datetime", "Chatbot ID", "Message", "Response", "Bot Input", "Study Key", "User Session Key", "Response Rating", "Chat Rating Quality", "Chat Rating Fluency", "Chat Rating Coherency", "Chat Rating Diversity", "Chat Rating Contingency", "Chat Rating Empathy", "Chat Rating Comments"])
    for record in all_records:
        rating = ratings.get(record.chat_id)
        writer.writerow([record.id,
                         record.chat_id,
                         record.timestamp.isoformat(),
                         record.chatbot_id,
                         record.message,
                         record.response,
                         record.message_history,
                         record.study_key,
                         record.user_session_id,
                         record.rating,
                         rating.quality if rating else "",
                         rating.fluency if rating else "",
                         rating.coherency if rating else "",
                         rating.diversity if rating else "",
                         rating.contingency if rating else "",
                         rating.empathy if rating else "",
                         rating.comments if rating else "",
                         ])

    return response


def _download_rating_csv(request, study_key=None):
    all_ratings = ChatRating.objects.order_by('timestamp')

    if study_key:
        all_ratings = all_ratings.filter(study_key=study_key)

    all_ratings = all_ratings.all()

    chat_lengths = ChatRecord.objects.values('chat_id').annotate(Count('chat_id'))
    chat_lengths = {chat['chat_id']:chat['chat_id__count'] for chat in chat_lengths}

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="chat_ratings{0}.csv"'.format(
        "_" + study_key if study_key else "")

    writer = csv.writer(response)
    writer.writerow(["ID",
                     "Chat ID",
                     "Datetime",
                     "Chatbot ID",
                     "User Session Key",
                     "Quality",
                     "Coherency",
                     "Fluency",
                     "Diversity",
                     "Contingency",
                     "Empathy",
                     "Comments",
                     "Chat Length",
                     "MTurk Code",
                     "MTurk User ID",
                     "Study Key"])

    for rating in all_ratings:
        writer.writerow([rating.id,
                         rating.chat_id,
                         rating.timestamp.isoformat(),
                         rating.chatbot_id,
                         rating.user_session_id,
                         rating.quality,
                         rating.coherency,
                         rating.fluency,
                         rating.diversity,
                         rating.contingency,
                         rating.empathy,
                         rating.comments,
                         chat_lengths.get(rating.chat_id),
                         rating.mturk_code,
                         rating.mturk_user_id,
                         rating.study_key,
                         ])

    return response


@register(ChatRecord)
class ChatRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'chat_id', 'chatbot_id', 'user_session_id', 'message', 'response', 'timestamp', 'rating', 'study_key')
    search_fields = ('chat_id', 'chatbot_id', 'study_key', 'user_session_id')

    change_list_template = 'chatrecordchangelist.html'

    def get_urls(self):
        urls = super(ChatRecordAdmin, self).get_urls()
        my_urls = [
            url(r'download_records_csv/$', self.admin_site.admin_view(_download_records_csv), name="download_records_csv"),
        ]
        return my_urls + urls



@register(ChatRating)
class ChatRatingAdmin(admin.ModelAdmin):
    list_display = ('id', 'chat_id', 'study_key', 'chatbot_id', 'user_session_id', 'mturk_code', 'mturk_user_id', 'timestamp', 'quality', 'coherency', 'fluency', 'diversity', 'contingency', 'empathy', 'comments')
    search_fields = ('study_key', 'chat_id', 'chatbot_id', 'user_session_id', 'mturk_user_id')
    change_list_template = 'chatratingchangelist.html'

    def get_urls(self):
        urls = super(ChatRatingAdmin, self).get_urls()
        my_urls = [
            url(r'download_rating_csv/$', self.admin_site.admin_view(_download_rating_csv), name="download_rating_csv"),
        ]
        return my_urls + urls


BOT_CHOICES = tuple((key, chatbots[key].name) for key in chatbots)


class JSONMultipleChoiceField(forms.MultipleChoiceField):
    widget = FilteredSelectMultiple("Bots", is_stacked=False, choices=BOT_CHOICES)


class StudyForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(StudyForm, self).__init__(*args, **kwargs)
        if self.instance.pk:
            self.initial["bot_list"] = simplejson.loads(self.instance.bot_list)

    def save(self, commit=True):
        m = super(StudyForm, self).save(commit=False)
        m.bot_list = simplejson.dumps(self.cleaned_data["bot_list"])
        if commit:
            m.save()
        return m

    class Meta:
        model = Study
        fields = '__all__'

    bot_list = JSONMultipleChoiceField(choices=BOT_CHOICES)


@register(Study)
class StudyAdmin(admin.ModelAdmin):
    list_display = ('key', 'name', 'link', 'is_random_bot', 'bot_list', 'is_mturk', 'is_anonymized')
    readonly_fields = ('key',)
    form = StudyForm

    change_form_template = 'studychange.html'

    def get_urls(self):
        urls = super(StudyAdmin, self).get_urls()
        my_urls = [
            url(r'download_records_csv/(?P<study_key>\w+)/', self.admin_site.admin_view(_download_records_csv), name="download_study_records_csv"),
            url(r'download_rating_csv/(?P<study_key>\w+)/', self.admin_site.admin_view(_download_rating_csv), name="download_study_ratings_csv"),
        ]
        return my_urls + urls

    def link(self, obj):
        return mark_safe(u'<a href="{0}" target="_blank">Link</a>'.format(reverse("index", kwargs=dict(study_key=obj.key))))


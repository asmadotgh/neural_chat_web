from django.shortcuts import render
from django.http.response import HttpResponse
import simplejson
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .chatbots import chatbots
from .models import ChatRecord, Study, ChatRating
import datetime
import pytz
from django.shortcuts import get_object_or_404
import random
from django.utils.timezone import make_aware
import re
import uuid
from django.conf import settings

def render_to_json(**kwargs):
    return HttpResponse(simplejson.dumps(kwargs))


def index(request, study_key=None):

    if not study_key:
        bot_list = list(chatbots.keys())

        study = Study(bot_list=simplejson.dumps(bot_list), is_random_bot=True, key="index", is_anonymized=True)

    else:
        study = get_object_or_404(Study, key=study_key)

    botlist = [key for key in simplejson.loads(study.bot_list) if key in chatbots.keys()]

    if study.is_mturk:
        # don't repeat any bots that've already been seen by this user, but only for mturk studies, and only if they haven't already seen all the bots
        botlist = [bot for bot in botlist if not getattr(chatbots[bot], "is_test_bot", None)]

        ratings = ChatRating.objects.filter(user_session_id=_get_session_id(request))
        seen_bots = [rating.chatbot_id for rating in ratings]
        unseen_bots = [bot for bot in botlist if bot not in seen_bots]

        if unseen_bots:
            botlist = unseen_bots

    if study.is_random_bot:
        botlist = [bot for bot in botlist if not getattr(chatbots[bot], "is_test_bot", None)]
        botlist = [random.choice(botlist)] if botlist else botlist

    return render(request, "index.html", context=dict(study=study, chatbots={key: chatbots[key] for key in botlist}))


def bot_test_page(request):
    study = Study(bot_list=simplejson.dumps(list(chatbots.keys())), key="bot_test_page")

    botlist = [key for key in simplejson.loads(study.bot_list) if key in chatbots.keys()]

    return render(request, "index.html", context=dict(study=study, chatbots={key: chatbots[key] for key in botlist}))


@csrf_exempt
@require_POST
def chat_message(request):

    message = request.POST.get("message")
    chatbot_id = request.POST.get("chatbotID")
    chat_id = request.POST.get("chatID")
    timestamp = request.POST.get("timestamp")
    message_history = request.POST.get("messageHistory")
    study_key = request.POST.get("studyKey")

    chatbot = chatbots[chatbot_id]
    response = chatbot.handle_messages(simplejson.loads(message_history))

    chatrecord = ChatRecord(message=message,
                            chat_id=chat_id,
                            chatbot_id=chatbot_id,
                            timestamp=datetime.datetime.fromtimestamp(int(timestamp)/1000).replace(tzinfo=pytz.UTC),
                            message_history=message_history,
                            study_key=study_key,
                            response=response,
                            user_session_id=_get_session_id(request),
                            )
    chatrecord.save()

    emoji_regex = re.compile(u"[^\U00000000-\U0000d7ff\U0000e000-\U0000ffff]", flags=re.UNICODE)
    response_stripped = emoji_regex.sub(u'', response).strip()

    return render_to_json(success=True, response=response, response_stripped=response_stripped, response_id=chatrecord.id)


@csrf_exempt
@require_POST
def rate_chat_response(request):
    chatrecord_id = request.POST.get("response_id")
    rating = int(request.POST.get("rating"))

    chatrecord = get_object_or_404(ChatRecord, pk=chatrecord_id)

    make_vote_active = chatrecord.rating != rating
    chatrecord.rating = rating if make_vote_active else 0
    chatrecord.save()

    return render_to_json(success=True, make_vote_active=make_vote_active)


@require_POST
def rate_chat(request):

    chat_id = request.POST.get("chat_id")
    chatbot_id = request.POST.get("chatbot_id")
    study_key = request.POST.get("study_key")
    quality = request.POST.get("quality")
    fluency = request.POST.get("fluency")
    diversity = request.POST.get("diversity")
    contingency = request.POST.get("contingency")
    empathy = request.POST.get("empathy")
    comments = request.POST.get("comments")
    mturk_user_id = request.POST.get("mturkUserId", "")

    chat_rating = ChatRating(
        chat_id=chat_id,
        chatbot_id=chatbot_id,
        study_key=study_key,
        quality=quality,
        fluency=fluency,
        diversity=diversity,
        contingency=contingency,
        empathy=empathy,
        comments=comments,
        timestamp=make_aware(datetime.datetime.utcnow()),
        user_session_id=_get_session_id(request),
        mturk_user_id=mturk_user_id,
    )

    if chat_rating.should_generate_mturk_code():
        chat_rating.generate_mturk_code()

    chat_rating.save()

    return render_to_json(success=True, mturk_code=chat_rating.mturk_code)


def error(request):
    return render_to_json(value=5/0)


def _get_session_id(request):
    if not request.session.get("uuid"):
        request.session["uuid"] = str(uuid.uuid4())
    return request.session["uuid"]

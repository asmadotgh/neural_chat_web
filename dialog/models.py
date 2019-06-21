from django.db import models
import string, random, simplejson


class JsonField(models.TextField):
    pass


def key_generator(size=10, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


class BaseModel(models.Model):
    '''
    Base model from which all other models should inherit. It has a unique key and other nice fields
    '''
    id = models.AutoField(primary_key=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ChatRecord(BaseModel):
    chat_id = models.CharField(max_length=128, db_index=True)
    timestamp = models.DateTimeField()
    chatbot_id = models.CharField(max_length=128)
    message = models.TextField()
    message_history = JsonField()
    response = models.TextField()
    study_key = models.CharField(max_length=128)
    rating = models.IntegerField(default=0)
    user_session_id = models.CharField(max_length=128)


class ChatRating(BaseModel):
    chat_id = models.CharField(max_length=128, db_index=True)
    timestamp = models.DateTimeField()
    chatbot_id = models.CharField(max_length=128)
    quality = models.IntegerField()
    coherency = models.IntegerField(null=True)
    fluency = models.IntegerField()
    diversity = models.IntegerField()
    contingency = models.IntegerField()
    empathy = models.IntegerField()
    comments = models.TextField(blank=True)
    study_key = models.CharField(max_length=128)
    user_session_id = models.CharField(max_length=128)
    mturk_code = models.CharField(max_length=128)
    mturk_user_id = models.CharField(max_length=128, blank=True)

    def generate_mturk_code(self):
        if not self.mturk_code:
            for _ in range(6):
                mturk_code = key_generator(6)
                mturk_code = mturk_code[:3] + "-" + mturk_code[3:]
                if not type(self).objects.filter(mturk_code=mturk_code).count():
                    self.mturk_code = mturk_code
                    break

    def should_generate_mturk_code(self):
        try:
            study = Study.objects.get(key=self.study_key)
        except:
            return False

        if study.is_mturk:
            return True
            # num_previous_ratings = ChatRating.objects.filter(user_session_id=self.user_session_id, study_key=self.study_key).count()
            # if num_previous_ratings == 2:
            #     return True
        return False


class Study(BaseModel):
    key = models.CharField(max_length=128, unique=True, db_index=True, blank=True)
    name = models.CharField(max_length=128)
    is_random_bot = models.BooleanField(blank=True, default=False)
    bot_list = models.TextField(blank=True)
    is_mturk = models.BooleanField(blank=True, default=False)
    is_anonymized = models.BooleanField(blank=True, default=False)

    class Meta:
        verbose_name_plural = "studies"

    def generate_key(self):
        if not self.key:
            for _ in range(10):
                key = key_generator(10)
                if not type(self).objects.filter(key=key).count():
                    self.key = key
                    break

    def save(self, *args, **kwargs):
        self.generate_key()
        super(BaseModel, self).save(*args, **kwargs)


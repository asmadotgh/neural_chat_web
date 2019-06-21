from collections import OrderedDict
from abc import ABC, abstractmethod
from django.conf import settings


chatbots = OrderedDict()

try:
    from web_chatbots import chatbots as aibots
    chatbots = aibots
except ImportError:
    pass


def registerbot(botclass):
    bot = botclass()
    chatbots[bot.id] = bot


class Chatbot(ABC):
    def __init__(self, id, name, is_test_bot=False):
        """
        All chatbots should extend this class and be registered with the @registerbot decorator
        :param id: An id string, must be unique!
        :param name: A user-friendly string shown to the end user to identify the chatbot. Should be unique.
        """
        self.id = id
        self.name = name
        self.is_test_bot = is_test_bot

    @abstractmethod
    def handle_messages(self, messages):
        """
        Takes a list of messages, and combines those with magic to return a response string
        :param messages: list of strings
        :return: string
        """
        pass

if not settings.IS_PRODUCTION:
    @registerbot
    class Bot1(Chatbot):
        def __init__(self):
            super().__init__("bot1", "Albert")

        def handle_messages(self, messages):
            return "HI I AM ALBERT"


    @registerbot
    class Bot2(Chatbot):
        def __init__(self):
            super().__init__("bot2", "Betty")

        def handle_messages(self, messages):
            return "HI I AM BETTY"


    @registerbot
    class Bot3(Chatbot):
        def __init__(self):
            super().__init__("bot3", "Cuthbert")

        def handle_messages(self, messages):
            return "HI I AM CUTHBERT"


    @registerbot
    class Bot4(Chatbot):
        def __init__(self):
            super().__init__("bot4", "Diane", True)

        def handle_messages(self, messages):
            return "HI I AM DIANE"


    @registerbot
    class Pretzelbot(Chatbot):
        def __init__(self):
            super().__init__("pretzel", "PretzelBot")

        def handle_messages(self, messages):
            return u'\U0001F968'

from chatbots import chatbots

if __name__ == "__main__":

    username = None
    chatbotid = None

    messages = []

    while not username:
        username = input("Please enter your name.\n> ")

    while chatbotid not in chatbots.keys():
        chatbotid = input("Please enter the chatbot ID of your choice.\nValid choices are [" + ", ".join(chatbots.keys()) + "]:\n> ")

    chatbot = chatbots[chatbotid]

    print("\nPlease enjoy your chat with {0}! Type 'exit' or 'quit' to end the chat at any point.\n".format(chatbot.name))

    while True:

        message = input("[User]: ")

        if message == "exit" or message == "quit":
            print("Goodbye!")
            quit()

        if not message:
            continue

        messages.append(message)
        messages = messages[-5:]

        response = chatbot.handle_messages(messages)

        print("[" + chatbot.name + "]: " + response)

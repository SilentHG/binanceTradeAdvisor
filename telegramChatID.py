import requests

# Replace 'your_bot_token' with the token you received from BotFather
bot_token = '7427647021:AAFytDlcix4-Y5tqkJfkiAmoUF5Uw7XY4Z8'

# Define the URL to get updates
# url = f'https://api.telegram.org/bot{bot_token}/getUpdates'
#
# # Make a request to the URL
# response = requests.get(url)
#
# # Parse the JSON response
# data = response.json()
# print(data)
#
# # Extract the chat ID from the response
# # This assumes you've sent at least one message to the bot
# if 'result' in data and len(data['result']) > 0:
#     chat_id = data['result'][0]['message']['chat']['id']
#     print(f'Your chat ID is: {chat_id}')
# else:
#     print('No messages found. Send a message to your bot and try again.')

# Define the URL to send a message
message = 'Hello from your bot!'
chat_id = '-1002217857669'
url = f'https://api.telegram.org/bot{bot_token}/sendMessage'

# Define the message data
data = {
    'chat_id': chat_id,
    'text': message
}

# Make a request to the URL
response = requests.post(url, data=data)

# Parse the JSON response
print(response.json())
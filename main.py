# the os module helps us access environment variables
# i.e., our API keys
import os

# these modules are for querying the Hugging Face model
import json
import requests

# the Discord Python API
import discord

# this should point to your Huggingface model endpoint
API_URL = 'https://***YOURENDPOINTHERE***.huggingface.cloud/'

class MyClient(discord.Client):
    def __init__(self):
        # adding intents module to prevent intents error in __init__ method in newer versions of Discord.py
        intents = discord.Intents.default() # Select all the intents in your bot settings as it's easier
        intents.message_content = True
        super().__init__(intents=intents)
        self.api_endpoint = API_URL
        # retrieve the secret API token from the system environment
        huggingface_token = os.environ['HUGGINGFACE_TOKEN']
        # format the header in our request to Hugging Face
        self.request_headers = {
            'Authorization': 'Bearer {}'.format(huggingface_token),
            'Content-Type': 'application/json'
        }

    def send_request(self, payload):
        """
        Sends a request to the Hugging Face API.
        """
        data = json.dumps(payload)
        response = requests.request('POST',
                                    self.api_endpoint,
                                    headers=self.request_headers,
                                    data=data)
        return response

    def query(self, payload):
        """
        make request to the Hugging Face model API
        """
        response = self.send_request(payload)  # Assuming this is how you send the request
        if response.status_code == 200:
            try:
                ret = json.loads(response.content.decode('utf-8'))
                return ret
            except json.JSONDecodeError:
                print("Failed to decode JSON. Response content:", response.content)
                return None
        else:
            print(f"Request failed with status code: {response.status_code} and response: {response.content}")
            return None

    async def on_ready(self):
        # print out information when the bot wakes up
        print('Logged in as')
        if self.user:
            print(self.user.name)
            print(self.user.id)
        #print(self.user.name)
        #print(self.user.id)
        print('------')
        # send a request to the model without caring about the response
        # just so that the model wakes up and starts loading
        self.query({'inputs': 'Hello!'})

    async def on_message(self, message):
        """
        this function is called whenever the bot sees a message in a channel
        """
        # ignore the message if it comes from the bot itself
        if self.user and message.author.id == self.user.id:
        #if message.author.id == self.user.id:
            return

        # form query payload with the content of the message
        payload = {'inputs': message.content}

        # while the bot is waiting on a response from the model
        # set the its status as typing for user-friendliness
        async with message.channel.typing():
          response = self.query(payload)
        if response:
            # Handle different response formats
            if isinstance(response, list) and len(response) > 0:
                # If response is a list, get the first item
                first_item = response[0]
                if isinstance(first_item, dict):
                    bot_response = first_item.get('generated_text', None)
                else:
                    bot_response = str(first_item)
            elif isinstance(response, dict):
                bot_response = response.get('generated_text', None)
            else:
                bot_response = str(response)
        else:
            bot_response = 'Hmm... something is not right. No response received.'
        # we may get ill-formed response if the model hasn't fully loaded
        # or has timed out
        if not bot_response:
            if response and isinstance(response, dict) and 'error' in response:
                bot_response = '`Error: {}`'.format(response['error'])
            else:
                bot_response = 'Hmm... something is not right.'

        # send the model's response to the Discord channel
        await message.channel.send(bot_response)

def main():
    # Using custom Hugging Face endpoint
    client = MyClient()
    client.run(os.environ['DISCORD_TOKEN'])

if __name__ == '__main__':
  main()

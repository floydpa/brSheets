import os
from telethon import TelegramClient
from telethon.tl.functions.contacts import ImportContactsRequest
from telethon.tl.types import InputPhoneContact

# Credentials from environment or hardcoded for setup
API_ID = int(os.environ.get("TG_API_ID", 1234567))
API_HASH = os.environ.get("TG_API_HASH", "your_api_hash_here")

MY_USER_ID = 'me' 

client = TelegramClient("session_name", API_ID, API_HASH)

async def main():
    await client.start()

    # Import/resolve contact by phone number
    contact = InputPhoneContact(
        client_id=0,
        phone="+447783413314",
        first_name="Oliver",
        last_name=""
    )

    result = await client(ImportContactsRequest([contact]))

    # Get the Telegram user entity
    user = result.users[0]
    print(user)

    # Send message
    # await client.send_message(user, "Hello from MTProto!")

with client:
    client.loop.run_until_complete(main())


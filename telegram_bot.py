# Integration with Telegram Bot API for bet notifications and interactions.

import os
import asyncio
from telethon import TelegramClient, events
from database import SessionLocal, TipMessage, TipDetail
from parser.tof_parser import TurnOfFootParser
from utils import generate_oddschecker_url
import racing_api
from datetime import datetime

# Credentials from environment or hardcoded for setup
API_ID = int(os.environ.get("TG_API_ID", 1234567))
API_HASH = os.environ.get("TG_API_HASH", "your_api_hash_here")

# Run mode determines channel to listen on and who to alert
RUN_MODE = os.environ.get("TG_RUN_MODE")
MY_USER_ID = 'me'
SON_USER_ID = os.environ.get("TG_USER_ID")

if "TEST" in RUN_MODE:
    print("Running in TEST mode: Listening to 'me'")
    TARGET_CHANNEL = 'me'
else:
    TARGET_CHANNEL = 'Turn Of Foot - Mainline'

tip_alert_list = [] # Who to alert when a new tip has been received and parsed.
if "Solo" in RUN_MODE:
    print("Running in SOLO mode: Alerts will only be sent to me")
    tip_alert_list.append("me")
elif "Both" in RUN_MODE:
    print("Running in NORMAL mode: Alerts will be sent to me and son")
    tip_alert_list.extend(["me", SON_USER_ID])

client = TelegramClient('br_sheets_session', API_ID, API_HASH)
parser = TurnOfFootParser()

async def init_entities():
    """Resolves the son's ID into a Telegram entity so we can message him."""
    global SON_USER_ID
    try:
        # Convert to int and save back to the global variable
        SON_USER_ID = int(SON_USER_ID)
        entity = await client.get_entity(SON_USER_ID)
        print(f"Successfully resolved entity for: {entity.first_name} (ID: {entity.id})")
    except Exception as e:
        print(f"Warning: Could not resolve son's ID automatically: {e}")

@client.on(events.NewMessage(chats=TARGET_CHANNEL))
async def handle_new_message(event):
    raw_text = event.message.message
    msg_id = event.message.id
    chat_id = event.chat_id

    # 1. Safety: Never parse our own alert messages to avoid infinite loops
    if "🚨" in raw_text:
        return

    # 1. Parse the message using your TOF logic
    # Metadata mimicking what your offline extract_messages.py provided
    msg_metadata = {
        'id': msg_id,
        'date': event.message.date.isoformat()
    }
    
    # parse_message returns list of (DraftBet object, filename)
    parsed_bets = parser.parse_message(raw_text, msg_metadata)

    if not parsed_bets:
        print(f"No bets found in message {msg_id}, skipping DB and notification.")
        return # Chatty message, no tips found

    # 2. Save to Database
    db = SessionLocal()
    try:
        # Create parent entry
        new_msg = TipMessage(
            chat_id=chat_id,
            msg_id=msg_id,
            raw_text=raw_text,
            service_name="TOF"
        )
        db.add(new_msg)
        db.flush() # Get the new_msg.id for the foreign key

        for bet_obj, _ in parsed_bets:
            # Safely push the synchronous API check to a background thread
            sent_time_str = event.message.date.strftime("%H:%M")
            
            print(f"Verifying race date via API for {bet_obj.horse}...")
            confirmed_date = await asyncio.to_thread(
                racing_api.find_confirmed_race_date,
                sent_time_str,
                bet_obj.racecourse,
                bet_obj.raceTime,
                bet_obj.horse
            )
            
            # Override parser regex guess with the API certified date value
            bet_obj.raceDate = confirmed_date
            print(f"Race date confirmed as: {bet_obj.raceDate}")

            # Create child entry
            detail = TipDetail(
                message_id=new_msg.id,
                msg_tip_summary=bet_obj.msgTipSummary, # Original line
                parsed_summary=bet_obj.tipSummary, # Adjust if you want specific custom text
                race_date=bet_obj.raceDate,
                race_time=bet_obj.raceTime,
                horse_name=bet_obj.horse,
                stake_pts=bet_obj.stakePts,
                bet_type=bet_obj.betType.lower(),
                adv_odds=bet_obj.advisedOdds,
                adv_places=int(bet_obj.advisedPlaces) if bet_obj.advisedPlaces else None
            )
            db.add(detail)

            # 3. Send Notification with Oddschecker URL
            url = generate_oddschecker_url(bet_obj.raceDate, bet_obj.racecourse, bet_obj.raceTime)
            if "TEST" in RUN_MODE:  # Different type of alert for testing
                alert_text = f"🚨 ** TEST Tip - IGNORE! **\n\n{bet_obj.tipSummary}\n\n[Click for Oddschecker]({url})"
            else:
                alert_text = f"🚨 ** New Tip from Kev! **\n\n{bet_obj.tipSummary}\n\n[Click for Oddschecker]({url})"
            
            for recipient in tip_alert_list:
                print(f"Sending alert to {recipient} for message {msg_id}:\n{alert_text}\n\n")
                await client.send_message(recipient, alert_text, link_preview=False)

        db.commit()
    except Exception as e:
        print(f"Error processing message {msg_id}: {e}")
        db.rollback()
    finally:
        db.close()

# Main execution block
if __name__ == "__main__":
    print("Listener starting...")
    client.start()
    
    # Run the entity resolution once
    client.loop.run_until_complete(init_entities())
    
    print("Listener active and monitoring...")
    client.run_until_disconnected()


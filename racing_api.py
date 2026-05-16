import os
import time
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta

# Simple in-memory cache for courses to avoid redundant API calls
region_list = []
course_list = []
race_card_list = { "today": [], "tomorrow": [] }  
race_card_dates = { "today": None, "tomorrow": None }
results_today_list = { "gb": [], "ire": [] }
results_today_dates = { "gb": None, "ire": None }

def get_auth():
    return HTTPBasicAuth(os.getenv('RACING_API_USER'), os.getenv('RACING_API_PWD'))

def get_regions():
    url = "https://api.theracingapi.com/v1/courses/regions"
    if len(region_list) == 0:
        response = requests.get(url, auth=get_auth())
        time.sleep(1.2)  # Proper synchronous execution delay
        data = response.json()
        region_list.extend(data['regions'] if 'regions' in data else [])
    return region_list

def get_courses():
    url = "https://api.theracingapi.com/v1/courses"
    params = { "region_codes": ["gb","ire"] }
    if len(course_list) == 0:
        response = requests.get(url, auth=get_auth(), params=params)
        time.sleep(1.2)  
        data = response.json()
        course_list.extend(data['courses'] if 'courses' in data else [])
    return course_list

def get_course_id(course_name):
    for course in get_courses():
        if course_name.lower() == course['course'].lower():
            return course['id']
    return None

def get_racecards(day_param="today"):
    url = "https://api.theracingapi.com/v1/racecards/free"
    params = { "region_codes": ["gb","ire"], "day": day_param }
    
    actual_dates = {
        "today": datetime.now().strftime('%Y-%m-%d'),
        "tomorrow": (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')   
    }

    print(f"get_racecards called for {day_param}. Current cache date: {race_card_dates[day_param]}, Actual date: {actual_dates[day_param]}")
    
    if race_card_dates[day_param] is None or race_card_dates[day_param] != actual_dates[day_param]:
        print(f"Fetching new racecards for {day_param} ({actual_dates[day_param]})...")
        response = requests.get(url, auth=get_auth(), params=params)
        time.sleep(1.2)  
        data = response.json()
        race_card_list[day_param] = data['racecards'] if 'racecards' in data else []
        race_card_dates[day_param] = actual_dates[day_param]

    return race_card_list[day_param]

def search_racecards(race_cards, race_course, race_time_obj, horse):
    race_time_str = race_time_obj.strftime("%I:%M").lstrip("0")  
    for card in race_cards:
        if race_course.lower() == card['course'].lower():
            if card['off_time'] == race_time_str:
                runners = [r['horse'].lower() for r in card.get('runners', [])]
                if horse.lower() in runners:
                    return card
    return None

def find_confirmed_race_date(msg_time, race_course, race_time, horse):
    print(f"Finding confirmed race date for {horse} at {race_course} {race_time} based on message time {msg_time}...")
    race_time_obj = datetime.strptime(race_time, "%H:%M").time()
    msg_time_obj  = datetime.strptime(msg_time, "%H:%M").time()

    card = None
    if msg_time_obj < race_time_obj:
        print("Checking today's racecards...")
        card = search_racecards(get_racecards("today"), race_course, race_time_obj, horse)

    if not card:
        print("Checking tomorrow's racecards...")
        card = search_racecards(get_racecards("tomorrow"), race_course, race_time_obj, horse)

    if card:
        # Convert API format (YYYY-MM-DD) to your DB standard (DD/MM/YYYY)
        return datetime.strptime(card['date'], '%Y-%m-%d').strftime('%d/%m/%Y')
    else:
        # Construct fallback strings in matching format
        fallback_date = race_card_dates["tomorrow"] if msg_time_obj >= race_time_obj else race_card_dates["today"]
        fallback_date =datetime.strptime(fallback_date, '%Y-%m-%d').strftime('%d/%m/%Y')
        print(f"⚠️ API did not confirm {horse} for {race_course} - falling back to {fallback_date}")
        return fallback_date

def get_results_today(region_param):
    url = "https://api.theracingapi.com/v1/results/today/free"
    params = { "region": region_param }

    actual_date = datetime.now().strftime('%Y-%m-%d') 
    print(f"get_results_today called for {region_param}. Current cache date: {results_today_dates[region_param]}, Actual date: {actual_date}")

    if results_today_dates[region_param] is None or results_today_dates[region_param] != actual_date:
        print(f"Fetching new results for {region_param} ({actual_date})...")
        response = requests.get(url, auth=get_auth(), params=params)
        time.sleep(1.2)  
        data = response.json()
        results_today_list[region_param] = data['results'] if 'results' in data else []
        results_today_dates[region_param] = actual_date

    return results_today_list[region_param]

if __name__ == "__main__":
    
    from dotenv import load_dotenv
    load_dotenv()  # This looks for a .env file and loads it into os.environ

    # json_response = get_courses()
    # print(json_response)

    # course_id = get_course_id("Perth")
    for course in get_courses():
        print(course['course'])

    for result in get_results_today("gb"):
        print(result['course'], result['date'], result['off_dt'], result['off'])
        for r in result.get('runners', []):
            sp = r.get('sp', 'N/A')
            print(r['position'], r['horse'], sp)
    
    # for card in get_racecards("today"):
    #     print(card['course'], card['date'], card['off_time'])
    #     for r in card.get('runners', []):
    #         print("  -", r['horse'])

    # dt = find_confirmed_race_date("08:36", "Perth", "15:43", "Aill Dubh")
    # print(f"Confirmed race date: {dt}")




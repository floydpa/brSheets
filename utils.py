# Utility functions

from datetime import datetime

def generate_oddschecker_url(race_date: str, course: str, race_time: str) -> str:
    """
    race_date: e.g. DD/MM/YYYY
    course: e.g. "Southwell" or "Newton Abbot"
    race_time: e.g. "14:00"
    """
    # Clean course: lowercase and replace spaces with hyphens
    clean_course = course.strip().lower().replace(" ", "-")
    
    # Convert date to the correct format for oddschecker
    clean_date = datetime.strptime(race_date, "%d/%m/%Y").strftime("%Y-%m-%d")
    
    return f"https://www.oddschecker.com/horse-racing/{clean_date}-{clean_course}/{race_time}/winner"

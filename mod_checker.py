import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import re

class SteamModChecker:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def get_collection_mods(self, collection_url):
        try:
            response = self.session.get(collection_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            mods = []
            
            collection_items = soup.find_all('div', class_='collectionItem')
            
            for item in collection_items:
                mod_id = item.get('id', '').replace('sharedfile_', '')
                if mod_id and mod_id.isdigit():
                    name_elem = item.find('div', class_='workshopItemTitle')
                    mod_name = name_elem.text.strip() if name_elem else f"Mod_{mod_id}"
                    
                    mods.append({
                        'id': mod_id,
                        'name': mod_name,
                        'steam_url': f"https://steamcommunity.com/sharedfiles/filedetails/?id={mod_id}"
                    })
            
            return mods
            
        except Exception as e:
            print(f"Error fetching collection: {e}")
            return []
    
    def get_steam_mod_date(self, mod_url):
        try:
            response = self.session.get(mod_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            stats_container = soup.find('div', class_='detailsStatsContainerRight')
            if stats_container:
                date_elements = stats_container.find_all('div', class_='detailsStatRight')
                
                if date_elements:
                    date_text = date_elements[-1].text.strip()
                    
                    # Remove commas and @ symbols for simpler parsing
                    date_text = date_text.replace(',', '').replace('@', '').strip()
                    
                    # Check if year is missing (no 4-digit number)
                    if not re.search(r'\b\d{4}\b', date_text):
                        # Add current year between month and time
                        parts = date_text.split()
                        if len(parts) >= 3:  # Should be like: ["27", "May", "12:05pm"]
                            # Insert year between month and time
                            date_text = f"{parts[0]} {parts[1]} {datetime.now().year} {parts[2]}"
                    
                    # Try parsing with common formats
                    date_formats = [
                        '%d %b %Y %I:%M%p',      # 16 Oct 2020 4:08pm
                        '%d %B %Y %I:%M%p',      # 16 October 2020 4:08pm
                        '%d %b %Y',              # Fallback: date only with year
                        '%d %B %Y',              # Fallback: date only with full month
                    ]
                    
                    for fmt in date_formats:
                        try:
                            return datetime.strptime(date_text, fmt)
                        except ValueError:
                            continue
        except Exception as e:
            print(f"Error getting Steam date for {mod_url}: {e}")
        
        return None
    
    def get_skymods_mod_info(self, mod_id):
        try:
            search_url = f"https://catalogue.smods.ru/?s={mod_id}"
            response = self.session.get(search_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            results = soup.find_all('article')
            if not results:
                return {'found': False, 'date': None}
            
            for result in results:
                # Check if this result matches our mod
                steam_link = result.find('a', href=lambda x: x and f'steamcommunity.com/workshop/filedetails/?id={mod_id}' in x)
                
                if steam_link:
                    date_elem = result.find('span', class_='skymods-item-date')
                    
                    if date_elem:
                        date_text = date_elem.text.strip()
                        date_text = date_text.replace(',', '').replace(' UTC', '')
                        
                        # Handle dates without year by inserting current year between month and "at"
                        if 'at' in date_text:
                            # Check if the date already has a 4-digit year
                            if not re.search(r'\b\d{4}\b', date_text):
                                # Insert current year between month and "at"
                                parts = date_text.split(' at ')
                                if len(parts) == 2:
                                    date_part = parts[0].strip()
                                    time_part = parts[1].strip()
                                    # Insert current year
                                    date_text = f"{date_part} {datetime.now().year} at {time_part}"
                        
                        date_formats = [
                            '%d %b %Y at %H:%M',
                            '%d %B %Y at %H:%M',
                        ]
                        
                        for fmt in date_formats:
                            try:
                                return {
                                    'found': True,
                                    'date': datetime.strptime(date_text, fmt)
                                }
                            except ValueError:
                                continue
                    
                    # Found mod but couldn't parse date
                    return {'found': True, 'date': None}
            
            return {'found': False, 'date': None}
        
        except Exception as e:
            print(f"Error checking SkyMods for mod {mod_id}: {e}")
            return {'found': False, 'date': None}
    
    def dates_within_tolerance(self, date1, date2, tolerance_days=1):
        if not date1 or not date2:
            return False
        
        difference = abs((date1 - date2).days)
        return difference <= tolerance_days
    
    def check_collection(self, collection_url, delay=1):
        print(f"Scanning collection: {collection_url}")
        print("=" * 60)
        
        mods = self.get_collection_mods(collection_url)
        if not mods:
            print("No mods found in collection")
            return
        
        print(f"Found {len(mods)} mods in collection")
        print("Checking each mod...\n")
        
        outdated_mods = []
        missing_mods = []
        
        for i, mod in enumerate(mods, 1):
            print(f"Checking {i}/{len(mods)}: {mod['name']} (ID: {mod['id']})")
            
            steam_date = self.get_steam_mod_date(mod['steam_url'])
            skymods_info = self.get_skymods_mod_info(mod['id'])
            
            if not skymods_info['found']:
                missing_mods.append(mod)
                print("  ❌ Not available on SkyMods")
            elif not steam_date:
                print("  ⚠️  Could not get Steam date")
                outdated_mods.append({**mod, 'reason': 'Could not verify Steam date'})
            elif not skymods_info['date']:
                print("  ⚠️  Could not get SkyMods date")
                outdated_mods.append({**mod, 'reason': 'Could not verify SkyMods date'})
            elif not self.dates_within_tolerance(steam_date, skymods_info['date']):
                outdated_mods.append({
                    **mod, 
                    'steam_date': steam_date,
                    'skymods_date': skymods_info['date'],
                    'reason': 'Outdated on SkyMods'
                })
                print(f"  ⚠️  Outdated - Steam: {steam_date.strftime('%Y-%m-%d')}, SkyMods: {skymods_info['date'].strftime('%Y-%m-%d')}")
            else:
                print(f"  ✅ Up to date - Steam: {steam_date.strftime('%Y-%m-%d')}, SkyMods: {skymods_info['date'].strftime('%Y-%m-%d')}")
            
            time.sleep(delay)
        
        self.generate_summary(outdated_mods, missing_mods)
    
    def generate_summary(self, outdated_mods, missing_mods):
        print("\n" + "=" * 60)
        print("SUMMARY REPORT")
        print("=" * 60)
        
        if not outdated_mods and not missing_mods:
            print("🎉 All mods are up to date on SkyMods!")
            return
        
        if outdated_mods:
            print(f"\n❌ OUTDATED MODS ({len(outdated_mods)}):")
            print("-" * 40)
            for mod in outdated_mods:
                print(f"Name: {mod['name']}")
                print(f"ID: {mod['id']}")
                if 'steam_date' in mod and 'skymods_date' in mod:
                    print(f"Steam Date: {mod['steam_date'].strftime('%Y-%m-%d')}")
                    print(f"SkyMods Date: {mod['skymods_date'].strftime('%Y-%m-%d')}")
                print(f"Reason: {mod['reason']}")
                print(f"URL: {mod['steam_url']}")
                print()
        
        if missing_mods:
            print(f"\n🔍 MISSING MODS ({len(missing_mods)}):")
            print("-" * 40)
            for mod in missing_mods:
                print(f"Name: {mod['name']}")
                print(f"ID: {mod['id']}")
                print(f"URL: {mod['steam_url']}")
                print()
        
        # Compressed summary for easy copying
        print("\n" + "=" * 60)
        print("COMPRESSED URL LIST")
        print("=" * 60)
        
        if outdated_mods:
            print(f"\nOUTDATED MODS ({len(outdated_mods)}):")
            for mod in outdated_mods:
                print(mod['steam_url'])
        
        if missing_mods:
            print(f"\nMISSING MODS ({len(missing_mods)}):")
            for mod in missing_mods:
                print(mod['steam_url'])

def main():
    checker = SteamModChecker()
    
    print("Steam Workshop Collection SkyMods Checker")
    print()
    
    collection_url = input("Enter Steam Workshop Collection URL: ").strip()
    
    delay = input("Delay between requests in seconds (default: 1): ").strip()
    try:
        delay = float(delay) if delay else 1.0
    except ValueError:
        delay = 1.0
    
    print()
    checker.check_collection(collection_url, delay)

if __name__ == "__main__":
    main()

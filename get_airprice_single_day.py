from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup as bs
import datetime
import argparse
import csv

def load_city_name_mapping(file_path):
    mapping = {}
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            mapping[row['Original']] = row['Updated']
    return mapping

def fetch_flight_data(url, city_name_mapping):
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode, optional
    service = Service('./chromedriver-win64/chromedriver.exe')

    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get(url)

    soup = bs(driver.page_source, 'html.parser')
    driver.quit()

    flight_info_list = soup.find_all('ul', class_='ftl-flight-info')

    if not flight_info_list:
        print("No flight results found.")
        return

    # Extract the flight date
    flight_date_element = soup.find('li', class_='ftl-date-active')
    flight_date_str = flight_date_element.find('span').get_text(strip=True) if flight_date_element else 'Unknown'
    flight_date = datetime.datetime.strptime(flight_date_str, '%d-%m-%Y') if flight_date_str != 'Unknown' else None

    # Open files for appending data
    with open('./data/flight-price.txt', 'a', encoding='utf-8') as data_storage, \
         open('./data/flight-data.csv', 'a', newline='', encoding='utf-8') as csv_file:
        
        csv_writer = csv.writer(csv_file)
        
        # Write headers if the CSV file is empty
        if csv_file.tell() == 0:
            csv_writer.writerow(['Airline', 'Flight Number', 'Departure City', 'Departure Time', 'Arrival City', 'Arrival Time', 'Price'])

        data_storage.write('-' * 30 + '\n' + datetime.date.today().strftime('%b %d %Y result:') + '\n')

        for flight_info in flight_info_list:
            try:
                airline_img = flight_info.find('img')['src']
                airline_name = flight_info.find_all('p')[0].get_text(strip=True)
                departure_city = flight_info.find_all('div', class_='ftl-flight-city')[0].get_text(strip=True)
                departure_time_str = flight_info.find_all('div', class_='ftl-flight-time')[0].get_text(strip=True)
                flight_num = flight_info.find_all('div', class_='ftl-flight-numb')[0].get_text(strip=True)
                arrival_city = flight_info.find_all('div', class_='ftl-flight-city')[1].get_text(strip=True)
                arrival_time_str = flight_info.find_all('div', class_='ftl-flight-time')[1].get_text(strip=True)
                price = flight_info.find('div', class_='ftl-flight-price').get_text(strip=True).replace('\xa0', '')

                # Map city names using the dictionary
                departure_city = city_name_mapping.get(departure_city, departure_city)
                arrival_city = city_name_mapping.get(arrival_city, arrival_city)

                # Combine flight date with departure and arrival times
                departure_datetime = datetime.datetime.combine(flight_date, datetime.datetime.strptime(departure_time_str, '%H:%M').time())
                arrival_datetime = datetime.datetime.combine(flight_date, datetime.datetime.strptime(arrival_time_str, '%H:%M').time())

                # Adjust arrival date if necessary
                if arrival_datetime < departure_datetime:
                    arrival_datetime += datetime.timedelta(days=1)

                # Format date and time strings for output
                departure_str = departure_datetime.strftime('%d-%m-%Y %H:%M')
                arrival_str = arrival_datetime.strftime('%d-%m-%Y %H:%M')

                data_storage.write(f"{airline_name}\t{flight_num}\t{departure_city} at {departure_str} to {arrival_city} at {arrival_str}\t{price}\n")
                
                csv_writer.writerow([airline_name, flight_num, departure_city, departure_str, arrival_city, arrival_str, price])
            except Exception as e:
                print(f"Error processing flight info: {e}")
                continue

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('origin', help='Origin airport code')
    parser.add_argument('destination', help='Destination airport code')
    parser.add_argument('date', help='Flight date in DDMMYYYY format')
    args = parser.parse_args()

    url = f'https://www.vemaybay.vn/flight-result?request={args.origin}{args.destination}{args.date}-1-0-0'
    
    city_name_mapping = load_city_name_mapping('./data/city_name_mapping.csv')
    fetch_flight_data(url, city_name_mapping)

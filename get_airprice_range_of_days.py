from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup as bs
import datetime
import argparse
import csv
import concurrent.futures

# Dictionary to map original city names to updated names
city_name_mapping = {
    "Hà Nội": "Ha Noi",
    "Hồ Chí Minh": "Ho Chi Minh",
    "Đà Nẵng": "Da Nang",
    "Điện Biên Phủ": "Dien Bien Phu",
    "Hải Phòng": "Hai Phong",
    "Thanh Hóa": "Thanh Hoa",
    "Vinh": "Vinh",
    "Quảng Bình": "Quang Binh",
    "Quảng Nam": "Quang Nam",
    "Huế": "Hue",
    "Pleiku": "Pleiku",
    "Phú Yên": "Phu Yen",
    "Ban Mê Thuột": "Ban Me Thuot",
    "Nha Trang": "Nha Trang",
    "Qui Nhơn": "Qui Nhon",
    "Đà Lạt": "Da Lat",
    "Cần Thơ": "Can Tho",
    "Kiên Giang": "Kien Giang",
    "Cà Mau": "Ca Mau",
    "Phú Quốc": "Phu Quoc",
    "Côn Đảo": "Con Dao",
    "Quảng Ninh": "Quang Ninh"
}

# List of airport codes
airport_codes = ["HAN", "SGN", "DAD", "DIN", "HPH", "THD", "VII", "VDH", "VCL", "HUI", "PXU", "TBB", "BMV", "CXR", "UIH", "DLI", "VCA", "VKG", "CAH", "PQC", "VCS", "VDO"]

def fetch_flight_data(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode, optional
    service = Service('./chromedriver-win64/chromedriver.exe')

    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get(url)

    soup = bs(driver.page_source, 'html.parser')
    driver.quit()

    flight_info_list = soup.find_all('ul', class_='ftl-flight-info')

    if not flight_info_list:
        print(f"No flight results found for URL: {url}")
        return []

    # Extract the flight date
    flight_date_element = soup.find('li', class_='ftl-date-active')
    flight_date_str = flight_date_element.find('span').get_text(strip=True) if flight_date_element else 'Unknown'
    flight_date = datetime.datetime.strptime(flight_date_str, '%d-%m-%Y') if flight_date_str != 'Unknown' else None

    flight_data = []
    
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

            flight_data.append([airline_name, flight_num, departure_city, departure_str, arrival_city, arrival_str, price])
        except Exception as e:
            print(f"Error processing flight info: {e}")
            continue
    
    return flight_data

def date_range(start_date, end_date):
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + datetime.timedelta(n)

def process_dates_and_airports(start_date, end_date):
    for single_date in date_range(start_date, end_date):
        date_str = single_date.strftime('%d%m%Y')
        for origin in airport_codes:
            for destination in airport_codes:
                if origin != destination:
                    url = f'https://www.vemaybay.vn/flight-result?request={origin}{destination}{date_str}-1-0-0'
                    yield url

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('start_date', help='Start date in DDMMYYYY format')
    parser.add_argument('end_date', help='End date in DDMMYYYY format')
    args = parser.parse_args()

    start_date = datetime.datetime.strptime(args.start_date, '%d%m%Y')
    end_date = datetime.datetime.strptime(args.end_date, '%d%m%Y')

    with open('./data/flight-price.txt', 'a', encoding='utf-8') as data_storage, \
         open('./data/flight-data.csv', 'a', newline='', encoding='utf-8') as csv_file:
        
        csv_writer = csv.writer(csv_file)
        
        # Write headers if the CSV file is empty
        if csv_file.tell() == 0:
            csv_writer.writerow(['Airline', 'Flight Number', 'Departure City', 'Departure Time', 'Arrival City', 'Arrival Time', 'Price'])

        data_storage.write('-' * 30 + '\n' + datetime.date.today().strftime('%b %d %Y result:') + '\n')

        with concurrent.futures.ThreadPoolExecutor(max_workers=11) as executor:
            futures = {executor.submit(fetch_flight_data, url): url for url in process_dates_and_airports(start_date, end_date)}

            for future in concurrent.futures.as_completed(futures):
                try:
                    flight_data = future.result()
                    for flight in flight_data:
                        csv_writer.writerow(flight)
                        data_storage.write(f"{flight[0]}\t{flight[1]}\t{flight[2]} at {flight[3]} to {flight[4]} at {flight[5]}\t{flight[6]}\n")
                except Exception as exc:
                    print(f'Generated an exception: {exc}')
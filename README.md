# Airline Price Scraper & Dashboard

## Overview

This project is designed to scrape one way domestic Vietnam airline prices from vemaybay.vn and build a dashboard to visualize and analyze the data. 
The primary goal is to provide users with a comprehensive tool to monitor and compare airline prices across different dates, routes, and airlines, making it easier to find the best deals.

## Features

- **Web Scraping:** 
  - Extracts real-time flight data, including prices, from multiple airlines.
  - Scrapes additional information such as flight duration and flight number.

- **Data Storage:**
  - Saves scraped data into a structured format.
  - Supports periodic updates to ensure that the data is current.

- **Dashboard:**
  - Visualizes flight prices and trends over time.
  - Allows filtering by various parameters like departure city, destination, airline, date range, and more.
  - Displays historical data for price comparison.

 ## Usage
 
 **1. Scraping Airline Prices**
  Run this line to start collecting data for a specific route on a single day:
	
		```python get_airprice_single_day.py {FROMCITYNAME} {TOCITYNAME} {DATE}```

  Run this line to start collecting data for all airport in Vietnam in a range of days:
	
		```python get_airprice_range_of_days.py {FROMDATE} {TODATE}```

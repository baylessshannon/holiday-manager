from datetime import date, datetime
import time
import datetime
import json
from bs4 import BeautifulSoup
import requests
from dataclasses import dataclass
import config

apikey = getattr(config, 'apikey', 'no_key_found')


#defining helper functions

#gets a text response from a url
def getHTML(url):
    response = requests.get(url)
    return response.text

#gets a list of years (2 before and 2 after the current year)
#used when scraping the html
def get_years(current_year):
    return [current_year-2,current_year-1,current_year,current_year+1,current_year+2]

#ensures that a date input is in proper format
def get_date():
    date = str(input('Enter a date in YYYY-MM-DD format '))
    while True:
        try:
            datetime.datetime.strptime(date, '%Y-%m-%d')
            break
        except ValueError:
            print('That is not the right format. Try again')
            date = str(input('Enter a date in YYYY-MM-DD format '))
    return date

#ensures that an input is an integer within an approporiate range
def get_int(unit, min_num, max_num):
    num = 0
    is_valid = False

    #while we do not have a valid response
    while not is_valid:
        try:
            num = int(input( f'Enter a {unit} ([#{min_num}-{max_num}]) '))

            #make sure the number is in range
            while num < min_num or num > max_num: 
                print('That number is out of range. Try again.')
                num = int(input( f'Enter a {unit} ([#{min_num}-{max_num}] '))
            is_valid = True
        #if the user puts in a value that is not an integer and gets an error
        except ValueError:
            print('Please enter a valid number')
    return num

#ensures that the user inputs y or n when prompted
def get_y_or_n(string):
    choice = str(input(string))

    #while choice is not y or n
    while (choice != 'y') and (choice != 'n'):
        print("That is not a valid choice. Please enter either 'y' or 'n'")
        choice = str(input(string))
    return choice

#prints text with underline
def print_with_underline(string):
    underline = '='* len(string)
    print(string)
    print(underline)

#prints the welcome message and how many elements are in the holiday list
def print_start(list):
    print_with_underline('Holiday Management')
    print(f'There are {len(list)} holidays in the system')

#prints the menu options
def print_menu():
    print_with_underline('Holiday Menu')
    print('1. Add a Holiday')
    print('2. Remove a Holiday')
    print('3. Save Holiday List')
    print('4. View Holidays')
    print('5. Exit')

#facilitates the exit
def exit():
    print_with_underline('Exit')

    #use global variable go to determine if the application should keep going
    global go

    #if the user saved their changes
    if saved == True:
        choice = get_y_or_n('Are you sure you want to exit [y/n]')
        if choice == 'y':
            print('Goodbye!')
            go = False

    #if the user has unsaved changes
    else:
        print('Are you sure you want to exit?')
        print('Your changes will be lost')
        choice = get_y_or_n('[y/n] ')
        if choice == 'y':
            print('Goodbye!')
            go = False

#defining data classes
@dataclass
class Holiday:
    holiday: str
    date: date

    def __str__(self):
        return f'{self.holiday} ({self.date})'


@dataclass
class HolidayList:
    holidays: list

    #adding a holiday
    def add_holiday(self):
        #global variable saved tracks if the user has saved their changes
        global saved
        name = str(input('Enter the name of the holiday: '))
        day = get_date()

        #padding date with 0s if needed
        date_parts = day.split('-')
        if len(date_parts[1]) == 1:
            date_parts[1] = '0'+date_parts[1]

        if len(date_parts[2]) == 1:
            date_parts[2] = '0'+date_parts[2]

        day = f'{date_parts[0]}-{date_parts[1]}-{date_parts[2]}'
        print(f'Date for {name}: {day}')

        #creating an instance of Holiday
        full_holiday = Holiday(name,day)

        #adding the instance to the list
        self.holidays.append(full_holiday)
        print('Success:')
        print(f'{full_holiday} has been added to the list')

        #since the user added a holiday, their work is not saved
        saved = False

    def remove_holiday(self):
        #global variable saved tracks if the user has saved their changes
        global saved
        name = str(input('What holiday would you like to remove? '))
        list_of_names = list(map(lambda x: x.holiday, self.holidays))

        while name not in list_of_names:
            print(f'{name} not found. Try again')
            name = str(input('What holiday would you like to remove? '))

        #collects all holidays with that name
        remove_holidays = list(filter(lambda x: x.holiday == name, self.holidays))
        for i in range(len(remove_holidays)):
            self.holidays.remove(remove_holidays[i])

        print('Success:')
        print(f'{name} was removed from the list')

        #since something was removed from the list, the changes are not saved
        saved = False

    def scrape_html(self):

        #defining a month dictionary so we can convert the date later
        month_dict={
            'Jan': '01',
            'Feb': '02',
            'Mar': '03',
            'Apr': '04',
            'May': '05',
            'Jun': '06',
            'Jul': '07',
            'Aug': '08',
            'Sep': '09',
            'Oct': '10',
            'Nov': '11',
            'Dec': '12'
            }

        #getting a list of years so we can scrape multiple pages
        years = get_years(2022)

        #for every year...
        for year in years:
            html = getHTML(f'https://www.timeanddate.com/holidays/us/{year}')
            soup = BeautifulSoup(html,'html.parser')

            #drilling into the html
            table = soup.find('table', attrs = {'id':'holidays-table'})
            tbody = table.find('tbody')
            tr = tbody.find_all('tr')

            #filtering out the tags we do not want (the ones that begin with 'hol')
            remove_list=[]
            for i in range(len(tr)):
                if tr[i].attrs['id'][:3] == 'hol': 
                    remove_list.append(tr[i])

            for i in remove_list:
                tr.remove(i)

            for row in tr:
                date_str = row.find('th', attrs ={'class':'nw'}).text 

                #getting the date in the right format
                if len(date_str) == 5:
                    date = f'{year}-{month_dict[date_str[:3]]}-0{date_str[4:]}'
                else:
                    date = f'{year}-{month_dict[date_str[:3]]}-{date_str[4:]}'
                name = row.find('a').text

                #olny adding a holiday if it isn't already in the list
                if Holiday(name,date) not in self.holidays:
                    holiday = Holiday(name,date)
                    self.holidays.append(holiday)

    #getting holidays from JSON 
    def read_json(self):
        with open('holidays.json', 'r') as file:
            dict = json.load(file)

        holiday_list = dict['holidays']

        for item in holiday_list:
            name = item['name']
            date = item['date']

            #only add to the list of hilidays if it isnt already there
            if Holiday(name,date) not in self.holidays:
                holiday = Holiday(name,date)
                self.holidays.append(holiday)

    def save_to_json(self,file):
        print_with_underline('Saving Holiday List')

        #global variable saved tells the user if changes are saved
        global saved

        saved = False
        choice = get_y_or_n('Are you sure you want to save your changes? ')
        if choice == 'y':
            list = []
            for holiday in self.holidays:
                dict = holiday.__dict__
                list.append(dict)

            with open(file, 'w') as final:
                json.dump(list,final)
            print('Success:')
            print('Your changes have been saved.')
            saved = True
        else:
            print('Canceled:')
            print('Holiday list file save canceled')
            saved = False

    #get each holiday in a given week
    def display_by_week(self):
        week = get_int('week',1,52)
        year = get_int('year',0,9999)
        show_weather = get_y_or_n('Would you like to show the weather for each holiday? ')

        #getting the weekday to start on for the first of the year
        first = datetime.date(year,1,1)
        weekday = first.isoweekday()

        #get list of dates in the given week

        startdate = time.asctime(time.strptime(f'{year} %d {weekday}' % (week-1), '%Y %W %w'))
        startdate = datetime.datetime.strptime(startdate, '%a %b %d %H:%M:%S %Y')
        dates=[startdate.strftime('%Y-%m-%d')]
        for i in range(1,7):
            day =startdate + datetime.timedelta(days=i)
            dates.append(day.strftime('%Y-%m-%d'))

        print(f'These are the holidays for {year} week #{week}')

        #make a list of holidays with those dates
        weekly_holidays = list(filter(lambda x: x.date in dates, self.holidays))

        #if we want to show the weather
        if show_weather == 'y':
            for day in weekly_holidays:
                try:
                    date = day.date
                    date_parts = date.split('-')
                    date_time = datetime.datetime(int(date_parts[0]),int(date_parts[1]),int(date_parts[2]))
                    unix = time.mktime(date_time.timetuple())

                    #lat and long for St Paul, MN
                    lat = '44.943722'
                    long = '-93.094276'

                    response = requests.get(f'https://api.openweathermap.org/data/3.0/onecall/timemachine?lat={lat}&lon={long}&dt={round(unix)}&appid={apikey}').text
                    weather_dict = json.loads(response)
                    weather = weather_dict['data'][0]['weather'][0]['description']
                
                #if there is no forecast available (the date is in the future)
                except:
                    weather = 'no forecast availible'

                print(f'{day} - {weather} ')
        #if we dont want to show the weather
        else:
            for day in weekly_holidays:
                print(day)

def main():
    print_start(holiday_list.holidays)
    global saved
    global go
    saved = False
    go = True

    while go == True:
        print_menu()
        choice = get_int('choice', 0, 5)
        if choice == 1:
            holiday_list.add_holiday()   
        if choice == 2:
            holiday_list.remove_holiday()
        if choice == 3:
            holiday_list.save_to_json('all-holidays.json')
        if choice == 4:
            holiday_list.display_by_week()
        if choice == 5:
            exit()
 
##making the holiday list
holiday_list = HolidayList([])
holiday_list.read_json()
holiday_list.scrape_html()

#running the program
main()
print('all done')
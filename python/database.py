#!/usr/bin/env python3

from modules import pg8000
import configparser
import json
import string
import hashlib
import random

#####################################################
##  Database Connect
#####################################################

'''
Connects to the database using the connection string
'''


def database_connect():
    # Read the config file
    config = configparser.ConfigParser()
    config.read('config.ini')

    # Create a connection to the database
    connection = None
    try:
        # Parses the config file and connects using the connect string
        connection = pg8000.connect(database=config['DATABASE']['database'],
                                    user=config['DATABASE']['user'],
                                    password=config['DATABASE']['password'],
                                    host=config['DATABASE']['host'])
    except pg8000.OperationalError as e:
        print("""Error, you haven't updated your config.ini or you have a bad
        connection, please try again. (Update your files first, then check
        internet connection)
        """)
        print(e)
    # return the connection to use
    return connection


#####################################################
##  Login
#####################################################

'''
Check that the users information exists in the database.

- True = return the user data
- False = return None
'''


def check_login(member_id, password):
    # TODO
    # Check if the user details are correct!
    # Return the relevant information (watch the order!)


    # connection = database_connect()
    # cursor = connection.cursor()
    # cursor.execute("SELECT member_id, pass_word FROM Member")
    # file = open('/Users/jamesiryao/Desktop/password.txt', 'w')
    # result = cursor.fetchall()
    # print('RESULTS GOT!')
    # for row in result:
    #     sha256 = hashlib.sha256()
    #     salt = str(int(random.random() * 8999999999) + 1000000000)
    #     row[1] = row[1] + salt
    #     sha256.update(row[1].encode('utf-8'))
    #     row[1] = sha256.hexdigest()
    #     file.write('UPDATE Member SET hash_password = \''+row[1]+'\', hash_salt = \'' + salt +'\' WHERE member_id = \'' + row[0] + '\';\n')
    # file.close()
    # cursor.close()  # IMPORTANT: close cursor
    # connection.close()  # IMPORTANT: close connection

    results = None
    connection = database_connect()
    if (connection == None):
        return None
    cursor = connection.cursor()

    try:
        cursor.execute("SELECT * FROM getsalt(%s)", (member_id,))
    except:
        return None

    salt = cursor.fetchone()[0]
    sha256 = hashlib.sha256()
    sha256.update((password+salt).encode('utf-8'))
    hash_password = sha256.hexdigest()

    try:
        cursor.execute("SELECT * FROM MemberLogin(%s, %s)", (member_id, hash_password))
    except:
        return None

        #print('3')
    logined = cursor.fetchone()
    if (logined[0] == True):
        cursor.execute("SELECT * FROM memberdetails(%s)", (member_id,))
        results = cursor.fetchone()
    else:
        return None

    cursor.close()  # IMPORTANT: close cursor
    connection.close()  # IMPORTANT: close connection

    if (results is None):
        return None

    # FORMAT = [member_id, title, firstname, familyname, countryName, residence, member_type]
    user_data = [results[0], results[1], results[2], results[3], results[4], results[5], results[6]]

    tuples = {
            'member_id': user_data[0],
            'title': user_data[1],
            'first_name': user_data[2],
            'family_name': user_data[3],
            'country_name': user_data[4],
            'residence': user_data[5],
            'member_type': user_data[6]
        }

    return tuples


#####################################################
## Member Information
#####################################################

'''
Get the details for a member, including:
    - all the accommodation details,
    - information about their events
    - medals
    - bookings.

If they are an official, then they will have no medals, just a list of their roles.
'''


def member_details(member_id, mem_type):
    # TODO
    # Return all of the user details including subclass-specific details
    #   e.g. events participated, results.

    # TODO - Dummy Data (Try to keep the same format)
    # Accommodation [name, address, gps_lat, gps_long]
    connection = database_connect()
    if (connection == None):
        return None
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT * FROM AccommodationDetails(%s)",(member_id,))
    except:
        print("Error executing function")
        return None

    results = cursor.fetchone()
    cursor.close()
    connection.close()

    if (results is None):
        results = []

    accom_rows = [results[0], results[1], results[2], results[3]]

    connection = database_connect()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT * FROM NumberBookings(%s)",(member_id,))
    except:
        print("Error executing function")
        return None

    bookings = cursor.fetchone()
    cursor.close()
    connection.close()

    if (bookings is None):
        bookings = []

    # Check what type of member we are
    if (mem_type == 'athlete'):
        # TODO get the details for athletes
        # Member details [total events, total gold, total silver, total bronze, number of bookings]
        connection = database_connect()
        if (connection == None):
            return None
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT * FROM AthleteDetails(%s)",(member_id,))
        except:
            print("Error executing function")
            return None

        member_information_db = cursor.fetchone()
        cursor.close()
        connection.close()

        if (member_information_db is None):
            member_information_db = []

        member_information = {
            'total_events': member_information_db[0],
            'gold': member_information_db[1],
            'silver': member_information_db[2],
            'bronze': member_information_db[3],
            'bookings': bookings[0]
        }

    elif (mem_type == 'official'):

        # TODO get the relevant information for an official
        # Official = [ Role with greatest count, total event count, number of bookings]
        connection = database_connect()
        if (connection == None):
            return None
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT * FROM OfficialDetails(%s)",(member_id,))
        except:
            print("Error executing function")
            return None

        member_information_db = cursor.fetchone()
        cursor.close()
        connection.close()

        if (member_information_db is None):
            member_information_db = []

        member_information = {
            'favourite_role': member_information_db[0],
            'total_events': member_information_db[1],
            'bookings': bookings[0]
        }
    else:

        # TODO get information for staff member
        # Staff = [number of bookings ]
        member_information = {
            'bookings': bookings[0]
        }

    accommodation_details = {
        'name': accom_rows[0],
        'address': accom_rows[1],
        'gps_lat': accom_rows[2],
        'gps_lon': accom_rows[3]
    }

    # Leave the return, this is being handled for marking/frontend.
    return {'accommodation': accommodation_details, 'member_details': member_information}


#####################################################
##  Booking (make, get all, get details)
#####################################################

'''
Make a booking for a member.
Only a staff type member should be able to do this ;)
Note: `my_member_id` = Staff ID (bookedby)
      `for_member` = member id that you are booking for
'''


def make_booking(my_member_id, for_member, vehicle, date, hour, start_destination, end_destination):
    # TODO - make a booking
    # Insert a new booking
    # Only a staff member should be able to do this!!
    # Make sure to check for:
    #       - If booking > capacity
    #       - Check the booking exists for that time/place from/to.
    #       - Update nbooked
    #       - Etc.
    # return False if booking was unsuccessful :)
    # We want to make sure we check this thoroughly
    # MUST BE A TRANSACTION ;)
    connection = database_connect()
    if (connection == None):
        return None
    cursor = connection.cursor()

    try:
        cursor.execute("SELECT makebooking(%s,%s,%s,%s,%s,%s,%s)", (my_member_id, for_member, vehicle, date, hour, start_destination, end_destination))
    except:
        print("Error executing function")
        return False
    result = cursor.fetchone()
    connection.commit() #Commit Booking
    cursor.close()  # IMPORTANT: close cursor
    connection.close()  # IMPORTANT: close connection

    if (result[0]<0):
        return False

    return True


'''
List all the bookings for a member
'''


def all_bookings(member_id):
    # TODO - fix up the bookings_db information
    # Get all the bookings for this member's ID
    # You might need to join a few things ;)
    # It will be a list of lists - e.g. your rows

    # Format:
    # [
    #    [ vehicle, startday, starttime, to, from ],
    #   ...
    # ]

    connection = database_connect()
    if (connection == None):
        return None
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT * FROM BookingsWIDS(%s)",(member_id,))
    except:
        print("Error executing function11")
        return None

    bookings_db = cursor.fetchall()
    cursor.close()
    connection.close()

    if (bookings_db is None):
        bookings_db = []


    bookings = [{
        'vehicle': row[0],
        'start_day': row[1],
        'start_time': row[2],
        'to': row[3],
        'from': row[4]
    } for row in bookings_db]

    return bookings


'''
List all the bookings for a member on a certain day
'''


def day_bookings(member_id, day):
    # TODO - fix up the bookings_db information
    # Get bookings for the member id for just one day
    # You might need to join a few things ;)
    # It will be a list of lists - e.g. your rows

    # Format:
    # [
    #    [ vehicle, startday, starttime, to, from ],
    #   ...
    # ]

    connection = database_connect()
    if (connection == None):
        return None
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT * FROM BookingsWIDD(%s,%s)",(member_id, day))
    except:
        print("Error executing function")
        return None

    bookings_db = cursor.fetchall()
    cursor.close()
    connection.close()

    if (bookings_db is None):
        bookings_db = []

    bookings = [{
        'vehicle': row[0],
        'start_day': row[1],
        'start_time': row[2],
        'to': row[3],
        'from': row[4]
    } for row in bookings_db]

    return bookings


'''
Get the booking information for a specific booking
'''


def get_booking(b_date, b_hour, vehicle, from_place, to_place, member_id):
    # TODO - fix up the row to get booking information
    # Get the information about a certain booking, including who booked etc.
    # It will include more detailed information

    # Format:
    #   [vehicle, startday, starttime, to, from, booked_by (name of person), when booked]
    b_time = b_date + ' ' + b_hour
    print(b_time)
    connection = database_connect()
    if (connection == None):
        return None
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT * FROM BookingsWDetails(%s,%s)",(b_time, vehicle))

    except:
        print("Error executing function")
        return None

    row = cursor.fetchone()
    cursor.close()
    connection.close()

    if (row is None):
        row = []

    booking = {
        'vehicle': row[0],
        'start_day': row[1],
        'start_time': row[2],
        'to': row[3],
        'from': row[4],
        'booked_by': row[5],
        'whenbooked': row[6]
    }

    return booking


#####################################################
## Journeys
#####################################################

'''
List all the journeys between two places.
'''


def all_journeys(from_place, to_place):
    # TODO - get a list of all journeys between two places!
    # List all the journeys between two locations.
    # Should be chronologically ordered
    # It is a list of lists

    # Format:
    # [
    #   [ vehicle, day, time, to, from, nbooked, vehicle_capacity],
    #   ...
    # ]


    connection = database_connect()
    if (connection == None):
        return None
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT * FROM getjourneys(%s, %s) ORDER BY j_id", (from_place, to_place))
    except:
        print("Error executing function")
        return None

    results = cursor.fetchall()


    cursor.close()
    connection.close()

    journeys_db = []
    for row in results:
        r = []
        for a in row:
            r = r + [str(a)]
        r[2] = r[2] + ':00:00'
        if (len(r[2]) < 4):
            r[2] = '0' + r[2]
        journeys_db = journeys_db + [r]

    journeys = []

    for row in journeys_db:
        journeys = journeys + [{
            'vehicle': row[0],
            'start_day': row[1],
            'start_time': row[2],
            'to': row[4],
            'from': row[3],
            'booked' : row[5],
            'capacity' : row[6],
            'journey_id' : row[7]
        }]

    return journeys


'''
Get all of the journeys for a given day, from and to a selected place.
'''


def get_day_journeys(from_place, to_place, journey_date):
    # TODO - update the journeys_db variable to get information from the database about this journey!
    # List all the journeys between two locations.
    # Should be chronologically ordered
    # It is a list of lists

    # Format:
    # [
    #   [ vehicle, day, time, to, from, nbooked, vehicle_capacity],
    #   ...
    # ]

    connection = database_connect()
    if (connection == None):
        return None
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT * FROM getjourneys(%s, %s) WHERE my_day = DATE(%s) ORDER BY j_id", (from_place, to_place, str(journey_date)))
    except:
        print("Error executing function")
        return None

    results = cursor.fetchall()

    cursor.close()
    connection.close()

    journeys_db = []
    for row in results:
        r = []
        for a in row:
            r = r + [str(a)]
        r[2] = r[2] + ':00:00'
        if (len(r[2]) < 4):
            r[2] = '0' + r[2]
        journeys_db = journeys_db + [r]


    journeys = []

    for row in journeys_db:
        journeys = journeys + [{
            'vehicle': row[0],
            'start_day': row[1],
            'start_time': row[2],
            'to': row[4],
            'from': row[3],
            'booked' : row[5],
            'capacity' : row[6],
            'journey_id' : row[7]
        }]

    return journeys


#####################################################
## Events
#####################################################
def count_events():

    connection = database_connect()
    if (connection == None):
        return None
    cursor = connection.cursor()

    try:
        cursor.execute("""SELECT * FROM CountEvents()""")
    except:
        return 0

    result = cursor.fetchone()

    cursor.close()
    connection.close()

    return result


def count_sport_events(sportname):

    connection = database_connect()
    if (connection == None):
        return None
    cursor = connection.cursor()

    try:
        cursor.execute("""SELECT * FROM CountSportEvents(%s)""", (sportname,))
    except:
        return 0

    result = cursor.fetchone()

    cursor.close()
    connection.close()

    return result

'''
List all the events running in the olympics
'''
def all_events(cp, lim):

    # Format:
    # [
    #   [name, start, sport, venue_name]
    # ]

    connection = database_connect()
    if (connection == None):
        return None
    cursor = connection.cursor()

    try:
        cursor.execute("""SELECT * FROM GetAllEvents(%s, %s)""", (cp, lim,))
    except:
        print("no events")
        return None

    results = cursor.fetchall()

    cursor.close()
    connection.close()

    events_db = []

    for i in range(0, len(results)):
        events_db.append(results[i])

    events = [{
        'name': ('Mens ' if row[0] == 'M' else ('Womens ' if row[0] == 'W' else '')) + string.capwords(row[1]),
        'start': row[2],
        'sport': row[3] if row[3] == row[6] else row[6],
        'venue': row[4],
        'gender': ('Mens ' if row[0] == 'M' else ('Womens ' if row[0] == 'W' else 'N/A')),
        'event_id': row[5]
    } for row in events_db]

    return events

'''
Get all the events for a certain sport - list it in order of start
'''
def all_events_sport(sportname, cp, lim):

    # Format:
    # [
    #   [name, start, sport, venue_name]
    # ]

    connection = database_connect()
    if (connection == None):
        return None
    cursor = connection.cursor()
    events_db = []
    events = []

    sportempty = False

    try:
        cursor.execute("""SELECT * FROM GetAllEventsBySport(%s, %s, %s)""", (sportname,cp, lim))
    except:
        sportempty = True


    results = cursor.fetchall()


    cursor.close()
    connection.close()

    if (results == [] or results is None or results == ()):
        sportempty = True

    if (sportempty):
        events = get_events_for_member(sportname, cp, lim)

    else:
        for i in range(0, len(results)):
            events_db.append(results[i])

        events = [{
            'name': ('Mens ' if row[0] == 'M' else ('Womens ' if row[0] == 'W' else '')) + string.capwords(row[1]),
            'start': row[2],
            'sport': row[3] if row[3] == row[6] else row[6],
            'venue': row[4],
            'gender': ('Mens ' if row[0] == 'M' else ('Womens ' if row[0] == 'W' else 'N/A')),
            'event_id': row[5]
        } for row in events_db]

    return events



def get_events_for_member(member_id, cp, lim):

    # Format:
    # [
    #   [name, start, sport, venue_name]
    # ]

    connection = database_connect()
    if (connection == None):
        return None
    cursor = connection.cursor()

    try:
        cursor.execute("""SELECT * FROM GetAllEventsByMemId(%s, %s, %s)""", (member_id, cp, lim))
    except:
        print("no events")
        return None

    results = cursor.fetchall()

    cursor.close()
    connection.close()

    events_db = []

    for i in range(0, len(results)):
        events_db.append(results[i])

    events = [{
        'name': ('Mens ' if row[0] == 'M' else ('Womens ' if row[0] == 'W' else '')) + string.capwords(row[1]),
        'start': row[2],
        'sport': row[3] if row[3] == row[6] else row[6],
        'venue': row[4],
        'gender': ('Mens ' if row[0] == 'M' else ('Womens ' if row[0] == 'W' else 'N/A')),
        'event_id': row[5]
    } for row in events_db]


    return events


'''
Get event information for a certain event
'''
def event_details(event_id):

    # Format:
    #   [name, start, sport, venue_name]

    connection = database_connect()
    if (connection == None):
        return None
    cursor = connection.cursor()
    event_db = []
    event = []

    try:
        cursor.execute("""SELECT * FROM GetEventDetails(%s)""", (event_id,))
    except:
        print("error in getting event details")
        return None

    event_db = cursor.fetchone()

    cursor.close()
    connection.close()

    row = event_db

    event = {
        'name': ('Mens ' if row[0] == 'M' else ('Womens ' if row[0] == 'W' else '')) + string.capwords(row[1]),
        'start': row[2],
        'sport': row[3] if row[3] == row[5] else (row[5] + " [" + row[3] + "]"),
        'venue': row[4],
        'gender': ('Mens ' if row[0] == 'M' else ('Womens ' if row[0] == 'W' else 'N/A'))
    }

    return event

#####################################################
## Results
#####################################################

'''
Get the results for a given event.
'''
def get_results_for_event(event_id):

    # Format:
    # [
    #   [member_id, result, medal],
    #   ...
    # ]

    connection = database_connect()
    if (connection == None):
        return None
    cursor = connection.cursor()

    try:
        cursor.execute("""SELECT * FROM GetMedalsForMembersOfEvent(%s)""", (event_id,))
    except:
        print("error in getting event details")
        return None

    members_db = cursor.fetchall()

    cursor.close()
    connection.close()

    members = [{
        'member_id': row[0],
        'medal': ("Gold" if row[1] == "G" else ("Silver" if row[1] == "S" else ("Bronze" if row[1] == "B" else "")))
    } for row in members_db]

    return members


'''
Get all the officials that participated, and their positions.
'''
def get_all_officials(event_id):

    # [
    #   [member_id, role],
    #   ...
    # ]

    connection = database_connect()
    if (connection == None):
        return None
    cursor = connection.cursor()

    try:
        cursor.execute("SELECT * FROM GetOfficials(%s)",(event_id,))
    except:
        print("Error executing function")
        return None

    officials_db = cursor.fetchall()

    cursor.close()
    connection.close()

    officials = [{
        'member_id': row[0],
        'role': row[1]
    } for row in officials_db]

    return officials

# =================================================================
# =================================================================

#  FOR MARKING PURPOSES ONLY
#  DO NOT CHANGE

def to_json(fn_name, ret_val):
    return {'function': fn_name, 'res': json.dumps(ret_val)}

# =================================================================
# =================================================================

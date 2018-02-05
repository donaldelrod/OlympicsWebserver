# Importing the frameworks

from modules import *
from flask import *
import database
import configparser

user_details = {}                   # User details kept for us
session = {}
page = {}

# Initialise the application
app = Flask(__name__)
app.secret_key = 'aab12124d346928d14710610f'

currentpage = 0
resultsize = 10
insearch = False
searchkey = ""

#####################################################
##  INDEX
#####################################################

@app.route('/')
def index():
    # Check if the user is logged in
    if('logged_in' not in session or not session['logged_in']):
        return redirect(url_for('login'))
    page['title'] = 'Olympics'
    return render_template('index.html',
        session=session,
        page=page,
        user=user_details)

#####################################################
##  LOGIN
#####################################################

@app.route('/login', methods=['POST', 'GET'])
def login():
    # Check if they are submitting details, or they are just logging in
    if(request.method == 'POST'):
        # submitting details
        login_return_data = database.check_login(request.form['id'], request.form['password'])

        # If it's null, saying they have incorrect details
        if login_return_data is None:
            page['bar'] = False
            flash("Incorrect id/password, please try again")
            return redirect(url_for('login'))

        # If there was no error, log them in
        page['bar'] = True
        flash('You have been logged in successfully')
        session['logged_in'] = True

        # Store the user details for us to use throughout
        global user_details
        user_details = login_return_data
        session['member_type'] = user_details['member_type']
        return redirect(url_for('index'))

    elif(request.method == 'GET'):
        return(render_template('login.html', page=page))

#####################################################
##  LOGOUT
#####################################################

@app.route('/logout')
def logout():
    session['logged_in'] = False
    page['bar'] = True
    flash('You have been logged out')
    return redirect(url_for('index'))

#####################################################
##  Member Details
#####################################################

@app.route('/details')
def member_details():
    if( 'logged_in' not in session or not session['logged_in']):
        return redirect(url_for('login'))

    # Go to the database to get the user information

    return_information = database.member_details(user_details['member_id'], user_details['member_type'])

    if(return_information is None):
        flash("Error, User \'{}\' does not exist".format(user_details['member_id']))
        page['bar'] = False
        return redirect(url_for('index'))

    return render_template('member_details.html', user=user_details, extra=return_information, session=session, page=page)

#####################################################
##  LIST EVENTS
#####################################################

@app.route('/events', methods=['POST', 'GET'])
def list_events():
    global currentpage
    global resultsize
    global insearch
    global searchkey
    
    if( 'logged_in' not in session or not session['logged_in']):
        return redirect(url_for('login'))
    # The user is just viewing the page
    if (request.method == 'GET'):
        # First check if specific event
        event_list = database.all_events(currentpage, resultsize)
        #currentpage=0
        if(event_list is None):
            event_list = []
            flash("Error, no events in our system.")
            page['bar'] = False
            totalpages = 1
        else:
            totalpages = round(database.count_sport_events(searchkey)[0] / resultsize + 0.5)
        return render_template('event_list.html', events=event_list, session=session, page=page, currentpage = 1, totalpages = totalpages)

    # Try to get from the database
    elif(request.method == 'POST'):

        sportmemid = False
        totalpages = round(database.count_events()[0]/resultsize + 0.5)-1  #total pages needed for all events

        if (insearch): #if a term has been searched in the search bar
            totalpages = round(database.count_sport_events(searchkey)[0]/resultsize + 0.5)-1 #resets totalpages if currently in a search
            sport_events = database.all_events_sport(searchkey, currentpage, resultsize)
            sportmemid = True
        #if previous button is pressed
        if request.values.get('prevbtn') == "previous":
            currentpage = (currentpage - 1) if currentpage > 0 else currentpage
        #if next button is pressed
        elif request.values.get('nextbtn') == "next":
            currentpage = (currentpage + 1) if currentpage < totalpages else currentpage
        #if first button is pressed
        elif request.values.get('firstbtn') == "first":
            currentpage = 0
        #if last button is pressed
        elif request.values.get('lastbtn') == "last":
            currentpage = totalpages
        #if the search reset button is pressed
        elif request.values.get('rstbtn') == "reset":
            currentpage = 0
            searchkey = ""
            insearch = False
        #otherwise its a search
        else:
            insearch = True
            currentpage = 0
            searchkey = request.form['search']
            sportmemid = True
        #if its not a search
        if (sportmemid == False):
            sport_events = database.all_events(currentpage, resultsize)
        #if it is, keep search filtered
        else:
            sport_events = database.all_events_sport(searchkey, currentpage, resultsize)
        
        if(sport_events is None):
            sport_events = []
            flash("Error, sport \'{}\' does not exist".format(request.form['search']))
            page['bar'] = False
        
        return render_template('event_list.html', events=sport_events, session=session, page=page, currentpage = currentpage+1, totalpages = totalpages+1)

#####################################################
## EVENT DETAILS
#####################################################
@app.route('/eventdetails/')
def event_details():
    if( 'logged_in' not in session or not session['logged_in']):
        return redirect(url_for('login'))
    # Check the details of the event
    event_id = request.args.get('event_id', '')

    if not event_id:
        page['bar'] = False
        flash("Error, no event was given. URL requires \'?event_id=<id>\'")
        return(redirect(url_for('index')))

    # Get the relevant data for all the event details
    event_results = database.get_results_for_event(event_id)
    event_officials = database.get_all_officials(event_id)
    event_information = database.event_details(event_id)

    if event_officials is None:
        event_officials = []
    if event_results is None:
        event_results = []
    if event_information is None:
        page['bar'] = False
        flash("Error invalid event name given")
        return(redirect(url_for('list_events')))

    return render_template('event_detail.html', session=session, results=event_results, officials=event_officials, event=event_information, page=page)

#####################################################
##  MAKE BOOKING
#####################################################

@app.route('/new-booking' , methods=['GET', 'POST'])
def new_booking():
    if( 'logged_in' not in session or not session['logged_in']):
        return redirect(url_for('login'))

    # If we're just looking at the 'new booking' page
    if(request.method == 'GET'):
        times = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
        return render_template('new_booking.html', user=user_details, times=times, session=session, page=page)
    # If we're making the booking
    success = database.make_booking(user_details['member_id'],
                                    request.form['member_id'],
                                    request.form['vehicle_regno'],
                                    request.form['book_date'],
                                    request.form['book_hour'],
                                    request.form['from_place'],
                                    request.form['to_place'])
    if(success == True):
        page['bar'] = True
        flash("Booking Successful!")
        return(redirect(url_for('index')))
    else:
        page['bar'] = False
        flash("There was an error making your booking.")
        return(redirect(url_for('new_booking')))



#####################################################
##  SHOW MY BOOKINGS
#####################################################

@app.route('/bookings', methods=['GET', 'POST'])
def user_bookings():
    if( 'logged_in' not in session or not session['logged_in']):
        return redirect(url_for('login'))


    # Check the day filter - if it is not there, then get all bookings
    day_filter = request.args.get('dayfilter', '')

    bookings_list = []
    if(day_filter != ''):
        bookings_list = database.day_bookings(user_details['member_id'], day_filter)
    else:
        bookings_list = database.all_bookings(user_details['member_id'])

    if(bookings_list is None):
        page['bar'] = False
        flash("No bookings available")
        bookings_list = []

    return render_template('bookings_list.html', page=page, session=session, bookings=bookings_list)



@app.route('/booking-detail')
def booking_detail():
    if( 'logged_in' not in session or not session['logged_in']):
        return redirect(url_for('login'))

    # Bookings information
    booking_to = request.args.get('to', '')
    booking_from = request.args.get('from', '')
    booking_vehicle = request.args.get('vehicle', '')
    booking_startday = request.args.get('startdate', '')
    booking_starttime= request.args.get('starttime', '')

    if(booking_to == '' or booking_from == '' or booking_vehicle == '' or booking_startday == '' or booking_starttime == ''):
        # Booking details
        page['bar'] = False
        flash("Error, incorrect details provided")
        return redirect(url_for('user_bookings'))

    # Get the booking based off the information
    booking_details = database.get_booking(
        booking_startday,
        booking_starttime,
        booking_vehicle,
        booking_from,
        booking_to,
        user_details['member_id']
    )

    return render_template('booking_detail.html', user=user_details, page=page, session=session, booking=booking_details)

#####################################################
## Show Journeys
#####################################################

@app.route('/journeys', methods=['GET', 'POST'])
def journeys():
    if( 'logged_in' not in session or not session['logged_in']):
        return redirect(url_for('login'))

    if(request.method == 'GET'):
        return render_template('journey_filterpage.html', session=session, user=user_details, page=page)

    # Get the filter information
    from_place = request.form['from_place']
    to_place = request.form['to_place']
    filter_date = request.form['filter_date']

    journeys = None

    if(from_place == '' or to_place == ''):
        page['bar'] = False
        flash("Error, no from_place/to_place provided!")
        return redirect(url_for('journeys'))

    # Check if the date is filtered
    if(filter_date == ''):
        journeys = database.all_journeys(from_place, to_place)
    else:
        journeys = database.get_day_journeys(from_place, to_place, filter_date)

    if(journeys is None):
        journeys = []
        page['bar'] = False
        flash("No journeys for given places")

    totalpages = int((len(journeys)-1) / resultsize) + 1
    return render_template(
        'journey_list.html',
        page=page,
        formdata = {'to': to_place, 'from': from_place},
        session=session,
        user_details=user_details,
        journeys=journeys,
        totalpages = totalpages,
        resultsize = resultsize
    )

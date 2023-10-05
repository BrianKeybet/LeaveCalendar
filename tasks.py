import urllib.parse
from sqlalchemy import create_engine, MetaData, Table, exc, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import traceback
from decouple import config

# Openning log file
log_file = open(r'C:\Users\support.user2\LeaveCalendar\dataimportlogs.txt', 'a')
log_file.write('--------------------------------------------------------------------------------\n')
log_file.write(f'{datetime.now()} - The script started running \n')

try:
    # MySQL database connection
    log_file.write('Connecting to MySQL database...\n')
    # sql_password = 'Abracadabr@1'
    sql_password = config('MYSQL_PASSWORD')
    sql_encoded_password = urllib.parse.quote(sql_password)

    # mysql_engine = create_engine(f'mysql://Admin:{sql_encoded_password}@10.10.1.102/kapaform')
    mysql_engine = create_engine(f'mysql://root:{sql_encoded_password}@10.0.0.7/kapaform')
    mysql_connection = mysql_engine.connect()
    print('Successfully connected to MySQL DB')

    # PostgreSQL database connection
    log_file.write('Connecting to PostgreSQL database...\n')
    password = config('POSTGRES_PASSWORD')
    encoded_password = urllib.parse.quote(password)

    # Connect to PostgreSQL database
    print('Connecting to PostgreSQL database...\n')
    postgres_engine = create_engine(f'postgresql://postgres:{encoded_password}@localhost:5432/test1')
    postgres_connection = postgres_engine.connect()
    print('Successfully connected to Postgres DB')

    # Define metadata for PostgreSQL tables
    metadata = MetaData()
    department_table = Table('mycalendar_department', metadata, autoload_with=postgres_engine)
    leaverequest_table = Table('mycalendar_leaverequest', metadata, autoload_with=postgres_engine)

    # Retrieve data from MySQL
    log_file.write('Retrieving data from MySQL...\n')
    query = text('''
        SELECT users.name, leave_requests.dept_id, leave_mgr.annual, leave_requests.start_date, leave_requests.end_date, leave_requests.leave_ent
        FROM leave_requests
        JOIN users ON leave_requests.id = users.id
        JOIN leave_mgr ON leave_mgr.id = leave_requests.id WHERE leave_requests.leave_status IN (1,2,3) AND users.kapaStaff = 1
    ''')
    result = mysql_connection.execute(query)
    print('Query executed')

    # Insert data into PostgreSQL tables
    log_file.write('Inserting data into PostgreSQL tables...\n')
    with postgres_connection.begin() as trans:
        # Create a session for PostgreSQL
        Session = sessionmaker(bind=postgres_connection)
        postgres_session = Session()

        for row in result:
            name, dept_id, annual, start_date, end_date, leave_ent = row

            # Check if the record already exists in PostgreSQL
            existing_query = leaverequest_table.select().where(
                leaverequest_table.c.name == name,
                leaverequest_table.c.start_date == start_date,
                leaverequest_table.c.end_date == end_date
            )
            existing_result = postgres_connection.execute(existing_query).first()

            if existing_result:
                # Handle the case when a duplicate value is encountered
                print("Duplicate value encountered. Skipping insertion.")
                continue

            # Insert data into PostgreSQL tables
            department = department_table.select().where(department_table.c.id == dept_id + 1)
            department_result = postgres_connection.execute(department).first()

            if department_result:
                department_id = department_result[0]
            else:
                # Handle the case when the department is not found
                print(f"Department not found for dept_id: {dept_id}")
                continue

            leave_request = leaverequest_table.insert().values(
                name=name,
                start_date=start_date,
                end_date=end_date,
                leave_bal=annual,
                department_id_id=department_id,
                leave_ent=leave_ent
            )

            try:
                postgres_session.execute(leave_request)
                postgres_session.commit()
            except exc.IntegrityError:
                # Handle the case when a duplicate value is encountered during insertion
                print("Duplicate value encountered2. Skipping insertion.")
                postgres_session.rollback()

        # postgres_session.commit()
        # # Close the connections
    log_file.write('Closing connections...\n')
    mysql_connection.close()
    postgres_connection.close()



except Exception as e:
    # Handle exceptions
    print(f"An error occurred: {str(e)}")
    log_file.write(f'Data Transfer failed. Error details: {e}')
    traceback.print_exc()
    # Perform additional error handling or logging as needed

# # Close the connections
# log_file.write('Closing connections...\n')
# mysql_connection.close()
# postgres_connection.close()

log_file.write(f'{datetime.now()} - The script finished running.\n')
log_file.close()
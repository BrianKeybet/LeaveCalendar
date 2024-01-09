import urllib.parse
from sqlalchemy import create_engine, MetaData, Table, exc, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import traceback
from decouple import config

def open_log_file():
    try:
        log_file = open(r'C:\Users\support.user2\LeaveCalendar\dataimportlogs.txt', 'a')
        log_file.write('--------------------------------------------------------------------------------\n')
        log_file.write(f'{datetime.now()} - The script started running \n')
        return log_file
    except Exception as e:
        print(f"Error opening log file: {str(e)}")
        raise

def close_log_file(log_file):
    try:
        log_file.write(f'{datetime.now()} - The script finished running.\n')
        log_file.close()
    except Exception as e:
        print(f"Error closing log file: {str(e)}")
        raise

def get_mysql_connection(log_file):
    try:
        log_file.write('Connecting to MySQL database...\n')
        sql_password = config('MYSQL_PASSWORD')
        sql_encoded_password = urllib.parse.quote(sql_password)
        mysql_engine = create_engine(f'mysql://root:{sql_encoded_password}@10.0.0.7/kapaform')
        mysql_connection = mysql_engine.connect()
        print('Successfully connected to MySQL DB')
        return mysql_connection
    except Exception as e:
        print(f"Error connecting to MySQL: {str(e)}")
        raise

def get_postgres_connection(log_file):
    try:
        log_file.write('Connecting to PostgreSQL database...\n')
        password = config('POSTGRES_PASSWORD')
        encoded_password = urllib.parse.quote(password)
        postgres_engine = create_engine(f'postgresql://postgres:{encoded_password}@localhost:5432/test1')
        postgres_connection = postgres_engine.connect()
        print('Successfully connected to Postgres DB')
        return postgres_connection, postgres_engine
    except Exception as e:
        print(f"Error connecting to PostgreSQL: {str(e)}")
        raise

def retrieve_data_from_mysql(log_file, mysql_connection):
    try:
        log_file.write('Retrieving data from MySQL...\n')
        query = text('''
            SELECT users.name, leave_requests.dept_id, leave_mgr.annual, leave_requests.start_date, leave_requests.end_date, leave_requests.leave_ent
            FROM leave_requests
            JOIN users ON leave_requests.id = users.id
            JOIN leave_mgr ON leave_mgr.id = leave_requests.id WHERE leave_requests.leave_status IN (1,2,3) AND users.kapaStaff = 1
        ''')
        result = mysql_connection.execute(query)
        print('SQL Data retrieved')
        return result
    except Exception as e:
        print(f"Error retrieving data from MySQL: {str(e)}")
        raise

def insert_data_into_postgres(log_file, postgres_connection, result, postgres_engine):
    try:
        log_file.write('Inserting data into PostgreSQL tables...\n')
        metadata = MetaData()
        department_table = Table('mycalendar_department', metadata, autoload_with=postgres_engine)
        leaverequest_table = Table('mycalendar_leaverequest', metadata, autoload_with=postgres_engine)

        with postgres_connection.begin() as trans:
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
                existing_result = postgres_session.execute(existing_query).first()

                if existing_result:
                    print("Duplicate value encountered. Skipping insertion.")
                    continue

                            # Check if a record's dates have been modified
                modified_query = leaverequest_table.select().where(
                    leaverequest_table.c.leave_ent == leave_ent
                )
                modified_result = postgres_session.execute(modified_query).first()

                if modified_result:
                    # An existing record with the same leave_ent exists, update the dates
                    update_query = leaverequest_table.update().where(
                        leaverequest_table.c.leave_ent == leave_ent
                    ).values(start_date=start_date, end_date=end_date)
                    postgres_session.execute(update_query)
                else:
                    #Insert into postgres
                    department = department_table.select().where(department_table.c.id == dept_id + 1)
                    department_result = postgres_connection.execute(department).first()

                    if department_result:
                        department_id = department_result[0]
                    else:
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
                    except exc.IntegrityError as e:
                        print(f"Error inserting data into PostgreSQL: {str(e)}")
                        raise

            if trans.is_active:
                trans.commit()
            else:
                print("Transaction is not active. Skipping commit")
    except Exception as e:
        print(f"Error inserting data into PostgreSQL: {str(e)}")
        traceback.print_exc()
        raise

def retrieve_leave_balance_from_mysql(log_file, mysql_connection):
    try:
        log_file.write('Retrieving leave balance data from MySQL...\n')
        query = text('''
            SELECT users.name, leave_mgr.id, leave_mgr.annual
            FROM leave_mgr
            JOIN users ON leave_mgr.id = users.id
        ''')
        leave_balance_result = mysql_connection.execute(query)
        print('Leave balance data retrieved')
        return leave_balance_result
    except Exception as e:
        print(f"Error retrieving leave balance data from MySQL: {str(e)}")
        raise

def update_leave_balance_in_postgres(log_file, postgres_connection, leave_balance_result, postgres_engine):
    try:
        log_file.write('Updating leave balance in PostgreSQL tables...\n')
        metadata = MetaData()
        leaverequest_table = Table('mycalendar_leaverequest', metadata, autoload_with=postgres_engine)

        with postgres_connection.begin() as trans:
            Session = sessionmaker(bind=postgres_connection)
            postgres_session = Session()

            for row in leave_balance_result:
                user_name, user_id, annual = row

                # Update the most recent leave request with the current leave balance
                update_query = leaverequest_table.update().where(
                    leaverequest_table.c.name == user_name
                ).values(leave_bal=annual)

                postgres_session.execute(update_query)

            if trans.is_active:
                trans.commit()
            else:
                print("Transaction is not active. Skipping commit")
    except Exception as e:
        print(f"Error updating leave balance in PostgreSQL: {str(e)}")
        traceback.print_exc()
        raise


def main():
    log_file = open_log_file()
    mysql_connection = get_mysql_connection(log_file)
    postgres_connection, postgres_engine = get_postgres_connection(log_file)
    result = retrieve_data_from_mysql(log_file, mysql_connection)
    insert_data_into_postgres(log_file, postgres_connection, result, postgres_engine)

    # Retrieve leave balance data from MySQL
    leave_balance_result = retrieve_leave_balance_from_mysql(log_file, mysql_connection)

    # Update leave balance in PostgreSQL
    update_leave_balance_in_postgres(log_file, postgres_connection, leave_balance_result, postgres_engine)

    # Close the connections
    log_file.write('Closing connections...\n')
    try:
        mysql_connection.close()
        postgres_connection.close()
    except Exception as e:
        print(f"Error closing connections: {str(e)}")
        raise
    finally:
        close_log_file(log_file)

if __name__ == "__main__":
    main()
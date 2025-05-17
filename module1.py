from flask import Flask, request, jsonify
from sqlalchemy import create_engine
from sqlalchemy.util import to_list 
from Identity_Reconciliation import app
from config import connection_url
from datetime import datetime
import numpy as np

engine = create_engine(connection_url)

def getContactIDs(e,p):
    conn = engine.connect()

    id_query = '''
    SELECT
    id
    FROM 
    Contact
    WHERE email = (?) OR phoneNumber = (?)      
    ORDER BY
    createdAt
    '''                                      # Doubt here

    result = conn.execute(id_query, e, p)    # Doubt here

    if not result:                           # Doubt here
        create_contact_query = '''
        INSERT INTO Contact
        (
            phoneNumber,
            email,
            linkPrecedence,
            createdAt,
            updatedAt,
            deletedAt
        )
        VALUES
        (
            (?),
            (?),
            "primary",
            (?),
            (?),
            null
        )
        '''                                  # Resolved

        conn.execute(create_contact_query, p, e, datetime.now(), datetime.now())        # Resolved

        result = conn.execute(id_query, e, p)

    IDs = np.array(result)
    
    primaryContactID = IDs[0]

    try:
        secondaryContactIDs = IDs[1:]        # Doubt here
    except Exception as e:
        secondaryContactIDs = []

    conn.close()

    return (primaryContactID, secondaryContactIDs, result)

def getEmails(IDs):
    conn = engine.connect()

    email_query = '''
    SELECT
    email
    FROM
    Contact
    WHERE
    id IN (?)
    '''

    email_list = to_list(conn.execute(email_query, IDs))           # Doubt here

    conn.close()

    return email_list

def getPhoneNumbers(IDs):
    conn = engine.connect()

    phoneNumber_query = '''
    SELECT
    phoneNumber
    FROM
    Contact
    WHERE
    id IN (?)
    '''

    phoneNumber_list = to_list(conn.execute(phoneNumber_query, IDs))

    conn.close()

    return phoneNumber_list

@app.route('/')
@app.route('/identify', methods = ['POST'])
def required_contacts():
    if 'Email' not in request.data or 'Phone Number' not in request.data:                  # Order of precedence
        return jsonify({'error': 'Please enter email and phone number'})

    email = request.data['Email']
    phoneNumber = request.data['Phone Number']

    primaryContactID, secondaryContactIDs, IDs = getContactIDs(email, phoneNumber)

    emails = getEmails(IDs)

    phoneNumbers = getPhoneNumbers(IDs)

    return jsonify(
    {
        "contact":{
            "primaryContatctId": primaryContactID,
            "emails": emails, 
            "phoneNumbers": phoneNumbers, 
            "secondaryContactIds": secondaryContactIDs
        }
    }), 200











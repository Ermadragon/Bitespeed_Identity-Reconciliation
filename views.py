from flask import Flask, request, jsonify
from sqlalchemy import create_engine, text 
from Identity_Reconciliation import app
from config import connection_url
from datetime import datetime
import numpy as np

engine = create_engine(connection_url)

def add_primary_contact(e, p):
    conn = engine.connect()

    create_primary_contact_query = text('''
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
            :phone,
            :email,
            "primary",
            :createdAt,
            :updatedAt,
            NULL
        );
        ''')                                  # Resolved (SQL Syntax)

    params = {
    'phone': p,
    'email': e,
    'createdAt': datetime.now(),
    'updatedAt': datetime.now()
    }

    conn.execute(create_primary_contact_query, params)        # Resolved
    
    conn.commit()

def add_secondary_contact(e, p, r):
    conn = engine.connect()

    create_secondary_contact_query = text('''
        INSERT INTO Contact
        (
            phoneNumber,
            email,
            linkedId,
            linkPrecedence,
            createdAt,
            updatedAt,
            deletedAt
        )
        VALUES
        (
            :phone,
            :email,
            :linkedId,
            "secondary",
            :createdAt,
            :updatedAt,
            NULL
        )
        ''')
    
    params = {
    'phone': p,
    'email': e,
    'linkedId': r[0],
    'createdAt': datetime.now(),
    'updatedAt': datetime.now()
    }

    conn.execute(create_secondary_contact_query, params)

    conn.commit()

def getContactIDs(e,p):
    conn = engine.connect()

    id_query = text('''
    SELECT
    id
    FROM 
    Contact
    WHERE email = :email OR phoneNumber = :phone      
    ORDER BY
    createdAt
    ''')                                      # Doubt here (Parametrize)

    result = conn.execute(id_query, {'email': e, 'phone': p})    # Doubt here

    result_list = np.array(result)
    if not result_list:                           # Doubt here (not with result set)
        add_primary_contact(e, p)
        result = conn.execute(id_query, {'email': e, 'phone': p})

    new_contact_query = text('''
    SELECT
    id
    FROM
    Contact
    WHERE email = :email and phoneNumber = :phone
    ''')

    existing_contact = conn.execute(new_contact_query, {'email': e, 'phone': p})
    
    existing_contact_list = np.array(existing_contact)
    if not existing_contact_list:
        add_secondary_contact(e, p, to_list(result))
        result = conn.execute(id_query, {'email': e, 'phone': p})

    IDs = np.array(result)
    
    primaryContactID = IDs[0]

    try:
        secondaryContactIDs = IDs[1:]        # Doubt here (List indexing)
    except Exception as e:
        secondaryContactIDs = []

    conn.close()

    return (primaryContactID, secondaryContactIDs, result)

def getEmails(IDs):
    conn = engine.connect()

    IDs = [row[0] for row in IDs]

    placeholders = ', '.join([f':id{i}' for i in range(len(IDs))])

    email_query = text(f'''
    SELECT DISTINCT
    email
    FROM
    Contact
    WHERE
    id IN ({placeholders})
    ''')

    params = {f'id{i}': val for i, val in enumerate(IDs)}

    result = conn.execute(email_query, params)           # Doubt here
    email_list = [row[0] for row in result]

    conn.close()

    return email_list

def getPhoneNumbers(IDs):
    conn = engine.connect()
    
    IDs = [row[0] for row in IDs]

    placeholders = ', '.join([f':id{i}' for i in range(len(IDs))])

    phoneNumber_query = text(f'''
    SELECT DISTINCT
    phoneNumber
    FROM
    Contact
    WHERE
    id IN ({placeholders})                                        
    ''')                                             # Doubt here

    params = {f'id{i}': val for i, val in enumerate(IDs)}

    result = conn.execute(phoneNumber_query, params)
    phoneNumber_list = [row[0] for row in result]

    conn.close()

    return phoneNumber_list

def precedence_change(p_id, s_id):
    conn = engine.connect()

    update_query = text('''
    UPDATE Contact
    SET
    linkedId = :linkedId,
    linkPrecedence = :linkPrecedence
    WHERE
    id = :id and linkPrecedence = 'primary'
    ''')

    if len(s_id) > 0:
        for _id in s_id:
            conn.execute(update_query, {'linkedId': p_id, 'linkPrecedence': 'secondary', 'id': _id})

    conn.commit()

    conn.close()

@app.route('/')
@app.route('/identify', methods = ['POST'])
def required_contacts():
    if 'Email' not in request.data and 'Phone Number' not in request.data:                  # Order of precedence
        return jsonify({'error': 'Please enter email and/or phone number'})

    email = request.data['Email']
    phoneNumber = request.data['Phone Number']

    primaryContactID, secondaryContactIDs, IDs = getContactIDs(email, phoneNumber)

    precedence_change(primaryContactID, secondaryContactIDs)

    emails = getEmails(IDs)

    phoneNumbers = getPhoneNumbers(IDs)

    return jsonify(
    {
        "contact":{
            "primaryContactId": primaryContactID,
            "emails": emails, 
            "phoneNumbers": phoneNumbers, 
            "secondaryContactIds": secondaryContactIDs
        }
    }), 200











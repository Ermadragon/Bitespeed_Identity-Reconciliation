from flask import Flask, render_template, request, jsonify
from sqlalchemy import create_engine, text
from sqlalchemy.util import to_list 
from __init__ import app
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
            'primary',
            :createdAt,
            :updatedAt,
            NULL
        );
        ''')                                  

    params = {
    'phone': p,
    'email': e,
    'createdAt': datetime.now(),
    'updatedAt': datetime.now()
    }

    conn.execute(create_primary_contact_query, params)        
    
    conn.commit()

    conn.close()

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
    ''')                                      

    result = conn.execute(id_query, {'email': e, 'phone': p})         
    
    result_list = [row[0] for row in result]
    
    if not result_list:                           
        add_primary_contact(e, p)
        result = conn.execute(id_query, {'email': e, 'phone': p})
        result_list = [row[0] for row in result]

    new_contact_query = text('''
    SELECT
    id
    FROM
    Contact
    WHERE email = :email and phoneNumber = :phone
    ''')

    existing_contact = conn.execute(new_contact_query, {'email': e, 'phone': p})
    
    existing_contact_list = [row[0] for row in existing_contact]
    
    if not existing_contact_list:
        add_secondary_contact(e, p, [row[0] for row in result])
        result = conn.execute(id_query, {'email': e, 'phone': p})
        result_list = [row[0] for row in result]

    IDs = [row[0] for row in result]
    
    primaryContactID = result_list[0]

    try:
        secondaryContactIDs = result_list[1:]        
    except Exception as e:
        secondaryContactIDs = []

    conn.close()

    return (primaryContactID, secondaryContactIDs, result_list)

def getEmails(IDs):
    conn = engine.connect()

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

    result = conn.execute(email_query, params)           
    email_list = [row[0] for row in result]

    conn.close()

    return email_list

def getPhoneNumbers(IDs):
    conn = engine.connect()
    
    placeholders = ', '.join([f':id{i}' for i in range(len(IDs))])

    phoneNumber_query = text(f'''
    SELECT DISTINCT
    phoneNumber
    FROM
    Contact
    WHERE
    id IN ({placeholders})                                        
    ''')                                             

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
def form():
    return render_template('form.html')

@app.route('/identify', methods = ['POST'])
def required_contacts():
    if 'Email' not in request.json and 'Phone Number' not in request.json:                 
        return jsonify({'error': 'Please enter email and/or phone number'})

    email = request.json['Email']
    phoneNumber = request.json['Phone Number']

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











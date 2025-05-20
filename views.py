from collections import OrderedDict
from flask import Flask, render_template, request, jsonify
import numpy as np
from sqlalchemy import create_engine, text 
from Identity_Reconciliation import app
from config import connection_url
from datetime import datetime

engine = create_engine(connection_url)

def val(e, p):
    if not e:
        return [p, 'phoneNumber']
    else:
        return [e, 'email']

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
        ''')                                  # Resolved (SQL Syntax)("primary")

    params = {
    'phone': p,
    'email': e,
    'createdAt': datetime.now(),
    'updatedAt': datetime.now()
    }

    conn.execute(create_primary_contact_query, params)        # Resolved
    
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
            'secondary',
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

    if not e or not p:
        if_null_query_1 = text(f'''
        SELECT
        id
        FROM
        Contact
        WHERE
        {val(e,p)[1]} = :val AND linkPrecedence = 'primary'
        ORDER BY
        createdAt
        ''')

        if_null_query_2 = text(f'''
        SELECT
        id,
        linkedId
        FROM 
        Contact
        WHERE 
        {val(e,p)[1]} = :val AND linkPrecedence = 'secondary'
        ORDER BY
        createdAt
        ''')

        res1 = conn.execute(if_null_query_1, {'val': val(e,p)[0]})
        res1_list = [row[0] for row in res1]
        print("r1 ",res1_list)
        res2 = conn.execute(if_null_query_2, {'val': val(e,p)[0]})
        res2_list1 = [row for row in res2]
        print('r21 ',res2_list1[0][0], 'rs2', res2_list1[0][1])
       # res2_list2 = [row[0][1] for row in res2]
        #print('r22 ',res2_list2)

        result_list = res1_list + [res2_list1[0][0]] + [res2_list1[0][1]]
        #print(result_list)

        result_list = list(OrderedDict.fromkeys(result_list))
        print(result_list)

        #if not result_list:                                          # Doubt here (value of not e for e = "")
         #   return jsonify({'error': '''No relevant contact found. Please enter both email and phone number in order to 
          #                create new contact.'''}), 404
    else:
        id_query = text('''
        SELECT
        id
        FROM 
        Contact
        WHERE email = :email OR phoneNumber = :phone      
        ORDER BY
        createdAt
        ''')                                      # Resolved (Parametrize)

        result = conn.execute(id_query, {'email': e, 'phone': p})         # Doubt here
        print("r ", result)
        result_list = [row[0] for row in result]
        print("rs ", result_list)
        # print("rs0", result_list[0])
        if not result_list:                           # Doubt here (not with result set)                                    
            add_primary_contact(e, p)
            result = conn.execute(id_query, {'email': e, 'phone': p})
            result_list = [row[0] for row in result]

        new_contact_query_1 = text('''
        SELECT
        id
        FROM
        Contact
        WHERE email = :email
        ''')

        existing_contact = conn.execute(new_contact_query_1, {'email': e})
    
        existing_contact_list = [row[0] for row in existing_contact]

        new_contact_query_2 = text('''
        SELECT
        id
        FROM
        Contact
        WHERE phoneNumber = :phone
        ''')

        existing_contact = conn.execute(new_contact_query_2, {'phone': p})

        existing_contact_list = existing_contact_list + [row[0] for row in existing_contact]
    
        print(existing_contact_list)
        if not existing_contact_list:
            add_secondary_contact(e, p, result_list)
            result = conn.execute(id_query, {'email': e, 'phone': p})
            result_list = [row[0] for row in result]

    #print("r ", result)
    # IDs = [row[0] for row in result]
    
    print(result_list)
    primaryContactID = result_list[0]

    try:
        secondaryContactIDs = result_list[1:]        # Doubt here (List indexing)
    except Exception as e:
        secondaryContactIDs = []

    conn.close()

    return (primaryContactID, secondaryContactIDs, result_list)

def getEmails(IDs):
    conn = engine.connect()

    print("i ", IDs)

    placeholders = ', '.join([f':id{i}' for i in range(len(IDs))])
    print("p", placeholders)
    email_query = text(f'''
    SELECT
    email
    FROM
    Contact
    WHERE
    id IN ({placeholders})
    ORDER BY
    createdAt
    ''')

    params = {f'id{i}': val for i, val in enumerate(IDs)}

    result = conn.execute(email_query, params)           # Doubt here
    email_list = [row[0] for row in result]

    conn.close()

    email_list = list(OrderedDict.fromkeys(email_list))

    return email_list

def getPhoneNumbers(IDs):
    conn = engine.connect()
    
    placeholders = ', '.join([f':id{i}' for i in range(len(IDs))])

    phoneNumber_query = text(f'''
    SELECT
    phoneNumber
    FROM
    Contact
    WHERE
    id IN ({placeholders})
    ORDER BY
    createdAt
    ''')                                             # Doubt here

    params = {f'id{i}': val for i, val in enumerate(IDs)}

    result = conn.execute(phoneNumber_query, params)
    phoneNumber_list = [row[0] for row in result]

    conn.close()

    phoneNumber_list = list(OrderedDict.fromkeys(phoneNumber_list))

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
    if 'Email' not in request.json and 'Phone Number' not in request.json:                  # Order of precedence
        return jsonify({'error': 'Please enter email and/or phone number.'})

    try:
        email = request.json['Email']
    except Exception as e:
        email = ""

    print(email)

    try:
        phoneNumber = request.json['Phone Number']
    except Exception as e:
        phoneNumber = ""

    print(phoneNumber)

    print(type(email))
    print(type(phoneNumber))

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











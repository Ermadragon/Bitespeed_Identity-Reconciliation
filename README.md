# Bitespeed_Identity-Reconciliation

This is a Flask web service which faciliatates identification of customers using different contact info on e-commerce platforms, created for submission for the Bitespeed backend developer application.

The application uses **Flask** framework for the API endpoint and **SQL Server** database for storing Contacts data in a ```Contact``` table. The application consists of the ```'/identify'``` endpoint with a POST method and uses an HTML template ```form.html``` for the interface. The web service is hosted at https://bitespeed-identity-reconciliation-xiv9.onrender.com.

## Required Libraries

1. Flask
2. SQLAlchemy
3. pyodbc
4. python-dotenv
5. numpy

To run locally, install the required libraries through the **requirements.txt** file
```
pip install -r requirements.txt
```

After installing the required libraries, run the application using
```
python runserver.py
```

The environment variables were stored in a **.env** file.


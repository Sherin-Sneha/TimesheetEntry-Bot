from typing import Any, Text, Dict, List, Union, Optional
from time import sleep
from dotenv import load_dotenv

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormAction, REQUESTED_SLOT
from rasa_sdk.events import AllSlotsReset, SlotSet
from rasa_sdk import ActionExecutionRejection

from telegram import Message, Chat, Update, Bot, User
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

import smtplib
import requests
import json
import csv
import os

load_dotenv()

airtable_api_key=os.getenv("AIRTABLE_API_KEY")
base_id=os.getenv("BASE_ID")
table_name=os.getenv("TABLE_NAME")

##################################################### custom slot reset

class ActionResetAllSlots(Action):
    def name(self):
        return "action_reset_all_slots"

    def run(self, dispatcher, tracker, domain):
        return [AllSlotsReset()]

##################################################### employee entry form to make airtable entry

def create_employee_log(sender_id, emp_id, name, projectname):
    request_url=f"https://api.airtable.com/v0/{base_id}/Employees"

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {airtable_api_key}",
    }  
    data = {
        "fields": {
            "Emp ID": emp_id,
            "ID": sender_id,
            "Name": name,
            "Projects": projectname,
        }
    }
    
    try:
        response = requests.post(
            request_url, headers=headers, data=json.dumps(data)
        )
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)
    
    return response
    print(response.status_code)

##################################################### employee entry form

class EmployeeEntryForm(FormAction):

    def name(self):
        return "employee_entry_form"

    @staticmethod
    def required_slots(tracker):
        return [ "emp_id", "name", "projectname"]

    def slot_mappings(self) -> Dict[Text, Union[Dict, List[Dict]]]:

        return {
            "name": [
                self.from_entity(entity="name"),
            ],
            "emp_id": [
                self.from_entity(entity="emp_id"),
            ],
            "projectname": [
                self.from_entity(entity="projectname"),
            ],
        }

    def submit(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:

        emp_id = tracker.get_slot("emp_id")
        api_response = requests.get("https://api.airtable.com/v0/appbVKubGr1I1kkEj/Auth?filterByFormula=({Emp+ID}%3D+'"+emp_id+"')&api_key=keyknJvAfz6gaSKLX").json()
        if len(api_response['records']) == 0:
            dispatcher.utter_message("Your Emp ID don't belong in here !! Sorry you are not added to the bot!")
            return[AllSlotsReset()]
            
        else:
            sender_id = tracker.sender_id
            name = tracker.get_slot("name")
            projectname = tracker.get_slot("projectname")
            # if ('k' not in projectname):
            #     dispatcher.utter_message(text="Could you please project name?")
            response = create_employee_log(
                    sender_id=sender_id,
                    name=name,
                    emp_id=emp_id,
                    projectname=projectname,
                )
            dispatcher.utter_message(text=f"You can make entries seamlessly from now on !!\n\nHere's your Personal info:\n • Name: {name}\n • Project: {projectname}\n • Emp ID: {emp_id}")       
            return[] 
       

##################################################### timesheet entry form to make airtabe entry

def create_timesheetentry_log(name, project, workhrs, sender_id):
    request_url=f"https://api.airtable.com/v0/{base_id}/{table_name}"

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {airtable_api_key}",
    }  
    data = {
        "fields": {
            "Name": name,
            "ID": sender_id,
            "Hours of work": workhrs,
            "Project": project,
        }
    }
    
    try:
        response = requests.post(
            request_url, headers=headers, data=json.dumps(data)
        )
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)
    
    return response
    print(response.status_code)

##################################################### employee entry form

class TimesheetentryForm(FormAction):

    def name(self):
        return "timesheetentry_form"
    
    @staticmethod
    def required_slots(tracker):
        return ["ready", "project", "workhrs"]
        
    def slot_mappings(self) -> Dict[Text, Union[Dict, List[Dict]]]:

        return {
            "ready": [
                self.from_entity(entity="project")
            ],
            "project": [
                self.from_entity(entity="project"),
            ],
        }

    def submit(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        
        ready = tracker.get_slot("ready")
        sender_id = tracker.sender_id
        api_response = requests.get("https://api.airtable.com/v0/appbVKubGr1I1kkEj/Employees?filterByFormula=%7BID%7D+%3D+'"+sender_id+"'&api_key=keyknJvAfz6gaSKLX").json()
        workhrs = tracker.get_slot("workhrs")
        project = tracker.get_slot("project")
        
        res = api_response['records'][0]['fields']
        name = f"{res['Name']}"

        response = create_timesheetentry_log(
                name=name,
                sender_id=sender_id,
                workhrs=workhrs,
                project=project,
            )
        
        dispatcher.utter_message("Thanks your entry has been made!!")
        return []

#####################################################  retrieve a specific date

class DateRetrieval(Action):

    def name(self) -> Text:
        return "action_date_retrieval"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        sender_id = tracker.sender_id
        date = tracker.get_slot('date')
        print("date is ",date)
        get_date(sender_id, date, dispatcher)
        return [SlotSet("date",None), SlotSet("sender_id",None)]

def get_date(sender_id, latest_message, dispatcher):
    api_response = requests.get("https://api.airtable.com/v0/appbVKubGr1I1kkEj/Table%201?filterByFormula=AND(ID%3D+'"+sender_id+"'%2C{Created+Time}%3D+'"+latest_message+"')&api_key=keyknJvAfz6gaSKLX").json()
    api_response_2 = requests.get("https://api.airtable.com/v0/appbVKubGr1I1kkEj/Table%201?filterByFormula=AND(ID%3D+'"+sender_id+"'%2C{Created+Time}%3D+'"+latest_message+"')&api_key=keyknJvAfz6gaSKLX").text

    if len(api_response['records'])>10:
        records_parsed = json.loads(api_response_2)
        rec_data = records_parsed['records']    
        record_data = open('Data.csv', 'w')
        csvwriter = csv.writer(record_data, delimiter=',')
        
        count = 0
        for rec in rec_data:
            if count == 0:
                    header = rec.keys()
                    csvwriter.writerow(header)
                    count += 1
            csvwriter.writerow(rec.values())
        record_data.close()
        dispatcher.utter_message("Enter your email id you will recieve the data there")
    else:
        i = 0
        while i < len(api_response['records']):
            res = api_response['records'][i]['fields']
            message = f"\n\nDATA: \n Created Time : {res['Created Time']}\n Name : {res['Name']}\n Project : {res['Project']}\n Hours of work : {res['Hours of work']}\n"
            dispatcher.utter_message(message)
            i += 1
        dispatcher.utter_message("That's the data on "+latest_message+"")

#####################################################  to send an email 

class SendEmail(Action):

    def name(self) -> Text:
        return "action_send_email"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        email = tracker.get_slot('emailid')
        print("email is ",email)
        print("Sending email.................")
        send_email(email, dispatcher)
        return [SlotSet("emailid",None)]

def send_email(to_addr, dispatcher):
    from_addr = "timesheetbotmail@gmail.com"
    msg = MIMEMultipart()
    msg['From'] = from_addr
    msg['To'] = to_addr
    msg['Subject'] = "Data from chatbot"
    message = f"\nYour data in attached as csv" 
    body = message
    msg.attach(MIMEText(body, 'plain')) 
    filename = "Data.csv"
    attachment = open(filename, "rb")
    p = MIMEBase('application', 'octet-stream')
    p.set_payload((attachment).read())
    encoders.encode_base64(p)
    p.add_header('Content-Disposition', "attachment; filename= %s" % filename)
    msg.attach(p)
    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.starttls()
    # Authentication
    try:
        s.login(from_addr, "testbot@123")
        text = msg.as_string()
        s.sendmail(from_addr, to_addr, text)
        dispatcher.utter_message("Thanks!! Your email has been sent")
    except:
        dispatcher.utter_message("An Error occured while sending email, please check your mail id")
    finally:
        s.quit()

#####################################################  retrieve a date range

class RangeRetrieval(Action):
    def name(self):
        return "action_range_retrieval"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        sender_id = tracker.sender_id
        fromdate = tracker.get_slot("fromdate")
        todate = tracker.get_slot("todate")
        get_range(sender_id, fromdate, todate, dispatcher)     
        return[SlotSet("fromdate", None), SlotSet("todate", None), SlotSet("sender_id", None)]
        
def get_range(sender_id, fdate, tdate, dispatcher):
    api_response = requests.get("https://api.airtable.com/v0/appbVKubGr1I1kkEj/Table%201?filterByFormula=AND({ID}=('"+sender_id+"'),IS_AFTER({Created+Time}%2C+DATESTR('"+fdate+"'))%2C+IS_BEFORE({Created+Time}%2C+DATESTR('"+tdate+"')))&view=Grid+view&api_key=keyknJvAfz6gaSKLX").json()
    api_response_2 = requests.get("https://api.airtable.com/v0/appbVKubGr1I1kkEj/Table%201?filterByFormula=AND(IS_AFTER(%7BCreated+Time%7D%2C+DATESTR('"+fdate+"'))%2C+IS_BEFORE(%7BCreated+Time%7D%2C+DATESTR('"+tdate+"')))&view=Grid+view&api_key=keyknJvAfz6gaSKLX").text

    if len(api_response['records'])>10:
        records_parsed = json.loads(api_response_2)
        rec_data = records_parsed['records']    
        record_data = open('Data.csv', 'w')
        csvwriter = csv.writer(record_data)
        count = 0
        for rec in rec_data:
            if count == 0:
                    header = rec.keys()
                    csvwriter.writerow(header)
                    count += 1
            csvwriter.writerow(rec.values())
        record_data.close()
        dispatcher.utter_message("Enter your email id your data will be mailed shortly")
    else:
        i = 0
        while i < len(api_response['records']):
            res = api_response['records'][i]['fields']
            message = f"\n\nDATA: \n Created Time : {res['Created Time']}\n Name : {res['Name']}\n Project : {res['Project']}\n Hours of work : {res['Hours of work']}\n"
            dispatcher.utter_message(message)
            i += 1
        dispatcher.utter_message("That's the data from "+fdate+" to "+tdate+"")
        

#####################################################  retrieve last filled record       

class LastrecRetrieval(Action):
    def name(self)-> Text:
        return "action_lastrec_retrieval"

    def run(self,dispatcher,tracker,domain):
        sender_id = tracker.sender_id
        daterec(sender_id, dispatcher)
        dispatcher.utter_message("This is the last record that was entered!!")
        return [SlotSet("sender_id",None)]

def daterec(sender_id, dispatcher):
    retrieval_url = f"https://api.airtable.com/v0/appbVKubGr1I1kkEj/Table%201?filterByFormula=ID%3D+'"+sender_id+"'&maxRecords=1&view=Grid+view&api_key=keyknJvAfz6gaSKLX" 
    response = requests.get(retrieval_url)
    api_response = response.json()

    res = api_response['records'][0]['fields']
    message = f"\n\nLast filled record: \n Created Time : {res['Created Time']}\n Last Modified : {res['Last Modified']}\n Name : {res['Name']}\n Project : {res['Project']}\n Hours of work : {res['Hours of work']}"
    dispatcher.utter_message(message)  


##################################################### to show projects buttons in timesheetentry form

class Project(Action):
    def name(self):
        return "action_project"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        sender_id = tracker.sender_id
        get_project(sender_id, dispatcher)
        return [SlotSet("sender_id",None)]

def get_project(sender_id, dispatcher):
    api_response = requests.get("https://api.airtable.com/v0/appbVKubGr1I1kkEj/Employees?fields%5B%5D=Project&filterByFormula=ID%3D+'"+sender_id+"'&api_key=keyknJvAfz6gaSKLX").json()
    buttons=[]

    message = "Select the project for which you are you here to put entry "
    i = 0
    while i < len(api_response['records']):
        res = api_response['records'][i]['fields']
        mes = f"{res['Project']}\n"
        payload = "/inform{\"project\":\""+mes+"\"}"
        buttons.append({"title": ""+mes+"", "payload": payload})
        i += 1
    dispatcher.utter_button_message(message, buttons, button_type="reply")
    return []

##################################################### to show projects buttons in employeeentry form

class FillAddProject(Action):
    def name(self):
        return "action_fill_add_project"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        get_fillpro(dispatcher)
        return []

def get_fillpro(dispatcher):
    api_response = requests.get("https://api.airtable.com/v0/appbVKubGr1I1kkEj/Projects?fields%5B%5D=Project&api_key=keyknJvAfz6gaSKLX").json()
    buttons=[]

    message = "Select the project you are assigned to "
    i = 0
    while i < len(api_response['records']):
        res = api_response['records'][i]['fields']
        mes = f"{res['Project']}\n"
        payload = "/projectname{\"projectname\":\""+mes+"\"}"
        buttons.append({"title": ""+mes+"", "payload": payload})
        i += 1
    dispatcher.utter_button_message(message, buttons, button_type="reply")
    return []
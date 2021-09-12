## start
* start
    - utter_info

## survey addme
* addme
    - employee_entry_form
    - form{"name": "employee_entry_form"}
    - form{"name": null}
    - action_reset_all_slots

## survey get fillpro
* get_fillpro
    - action_fill_add_project

## say goodbye
* goodbye
  - utter_goodbye

## bot challenge
* bot_challenge
  - utter_iamabot

## survey send email
* send_email
    - form{"name": "email_form"}
    - form{"name": null}
    - action_send_email

## survey entry
* greet
    - utter_greet
* entry
    - timesheetentry_form
    - form{"name": "timesheetentry_form"}
    - form{"name": null}
    - utter_slots_values
    - action_reset_all_slots
* out_of_scope
    - utter_ask_continue

## survey get project
* get_project
    - action_project

## survey lastrec
* greet
    - utter_greet
* lastrec
    - action_lastrec_retrieval

## survey get date
* greet
    - utter_greet
* dateret
    - utter_ask_date
* get_date
    - action_date_retrieval

## survey get range
* greet
    - utter_greet
* retforrange
    - utter_ask_range
* get_range
    - action_range_retrieval


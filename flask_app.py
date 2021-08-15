# -*- coding: utf-8 -*-

from fhirclient.auth import FHIROAuth2Auth
import logging
from fhirclient import client
from fhirclient.models.medication import Medication
from fhirclient.models.medicationrequest import MedicationRequest
from fhirclient import client
from fhirclient import server
from fhirclient import auth
import json

from flask import Flask, request, redirect, session

import requests

AUTH_SERVER = 'http://localhost:8081'

# app setup
settings = {
        'app_id': 'my_web_app',
        'api_base': 'http://localhost:8080/baseDstu3/',
    }

smart = client.FHIRClient(settings=settings)

# OAuth object
fhirauth = auth.FHIROAuth2Auth

app = Flask(__name__)

def _save_state(state):
    session['state'] = state

def _get_smart():
    state = session.get('state')
    if state:
        return client.FHIRClient(state=state, save_func=_save_state)
    else:
        return client.FHIRClient(settings=smart_defaults, save_func=_save_state)

def _logout():
    if 'state' in session:
        smart = _get_smart()
        smart.reset_patient()

def _reset():
    if 'state' in session:
        del session['state']

def _get_prescriptions(smart):
    bundle = MedicationRequest.where({'patient': smart.patient_id}).perform(smart.server)
    pres = [be.resource for be in bundle.entry] if bundle is not None and bundle.entry is not None else None
    if pres is not None and len(pres) > 0:
        return pres
    return None

def _get_medication_by_ref(ref, smart):
    med_id = ref.split("/")[1]
    return Medication.read(med_id, smart.server).code

def _med_name(med):
    if med.coding:
        name = next((coding.display for coding in med.coding if coding.system == 'http://www.nlm.nih.gov/research/umls/rxnorm'), None)
        if name:
            return name
    if med.text and med.text:
        return med.text
    return "Unnamed Medication(TM)"

def _get_med_name(prescription, client=None):
    if prescription.medicationCodeableConcept is not None:
        med = prescription.medicationCodeableConcept
        return _med_name(med)
    elif prescription.medicationReference is not None and client is not None:
        med = _get_medication_by_ref(prescription.medicationReference.reference, client)
        return _med_name(med)
    else:
        return 'Error: medication not found'

# views

@app.route('/')
@app.route('/index.html')
def index():
    """ The app's main page.
    """
 
    import fhirclient.models.patient as p
    import fhirclient.models.humanname as hn
    
    # patient = p.Patient()
    
    # name = hn.HumanName()
    # name.given = ['Kevin']
    # name.family = 'Lee'
    # patient.name = [name]
    
    # p.Patient.create(patient, smart.server)
    
    # body = f"<p>{p.Patient.create(patient, smart.server)}</p>"
    # return body

    search = p.Patient.where(struct={'_id': '1'})
    print("Searched: ")
    print(search)
    patients = search.perform_resources(smart.server)
    print("patients : ")
    print(patients)
    for patient in patients:
        patient.as_json()
        print(patient.as_json())
    print(patient)
    # '1963-06-12'
    print(smart.human_name(patient.name[0]))
    # 'Christy Ebert'

    body = f"<p>{smart.human_name(patient.name[0])}</p>"
    return body


@app.route('/fhir-app/')
def callback():
    """ OAuth2 callback interception.
    """
    smart = _get_smart()
    try:
        smart.handle_callback(request.url)
    except Exception as e:
        return """<h1>Authorization Error</h1><p>{0}</p><p><a href="/">Start over</a></p>""".format(e)
    return redirect('/')


@app.route('/login', methods=["POST"])
def login():
    req_data = request.get_json()
    header = {
        "Content-Type": "application/json"
    }
    body = {
        "username": req_data["username"],
        "password": req_data["password"]
    }
    url = AUTH_SERVER + '/login'
    try:
        res = json.loads(requests.post(url, data=json.dumps(body), headers=header).text)
        print("Result to /login API call : " + str(res))
    except Exception as e:
        print("Error occured during /login API call : " + str(e))
        return {
            "status": 'error',
            "message": str(e)
        }
    
    try:
        fhirauth.set_auth_tokens(fhirauth, res["access_token"], res["refresh_token"])
        smart.server.set_auth(fhirauth)
    except Exception as e:
        print("Error occured during setting auth tokens : " + str(e))
        return {
            "status": 'error',
            "message": str(e)
        }
    return json.dumps(res)

@app.route('/logout')
def logout():
    _logout()
    return redirect('/')


@app.route('/reset')
def reset():
    _reset()
    return redirect('/')


# start the app
if '__main__' == __name__:
    import flaskbeaker
    flaskbeaker.FlaskBeaker.setup_app(app)
    
    logging.basicConfig(level=logging.DEBUG)
    app.run(debug=True, port=8000)

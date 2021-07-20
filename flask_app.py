# -*- coding: utf-8 -*-

import logging
from fhirclient import client
from fhirclient.models.medication import Medication
from fhirclient.models.medicationrequest import MedicationRequest

from flask import Flask, request, redirect, session

# app setup
smart_defaults = {
    'app_id': 'my_web_app',
    'api_base': 'http://localhost:8080/fhir/',
}

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
    from fhirclient import client
    settings = {
        'app_id': 'my_web_app',
        'api_base': 'http://localhost:8080/fhir/',
    }
    smart = client.FHIRClient(settings=settings)

    import fhirclient.models.patient as p
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

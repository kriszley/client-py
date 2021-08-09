# -*- coding: utf-8 -*-

from fhirclient.auth import FHIROAuth2Auth
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
    from fhirclient import server
    from fhirclient import auth
    import json
    settings = {
        'app_id': 'my_web_app',
        'api_base': 'http://localhost:8080/baseDstu3/',
    }

    # oauth = auth.FHIROAuth2Auth()
    # oauth.


    smart = client.FHIRClient(settings=settings)

    # fhirserver = server.FHIRServer(None, 'http://localhost:8081')

    fhirauth = auth.FHIROAuth2Auth

    # fhirauth.from_state(fhirauth, {"token_uri": "http://localhost:8081/login"})
    # params = {
    #             "password": "test",
    #             "username": "test"
    #             }
    access_token = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJtcjV3QzkxNUhZU1ZnWl9GYzFOOHFZVmlKd3BiYU5TcE54Rmdoblp5dEZVIn0.eyJleHAiOjE2Mjg0ODQ3MjgsImlhdCI6MTYyODQ4NDQyOCwianRpIjoiNWZhODg1N2QtYzVhYy00MzhhLTgzYzUtM2I3Mzg0MWQ5N2E5IiwiaXNzIjoiaHR0cDovL2tleWNsb2FrOjgwODAvYXV0aC9yZWFsbXMvSEFQSUZISVIiLCJhdWQiOiJhY2NvdW50Iiwic3ViIjoiOTlmYTIyMzUtOWUwNy00NTFkLWE4MGEtODM5MjU0MmIzNzI4IiwidHlwIjoiQmVhcmVyIiwiYXpwIjoiaGFwaWZoaXItY2xpZW50Iiwic2Vzc2lvbl9zdGF0ZSI6IjE4OGE0ZWI0LTljNjAtNDE3Yy05ZmQzLTJlN2Q2ZTgwMGU2NyIsImFjciI6IjEiLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJkZWZhdWx0LXJvbGVzLWhhcGlmaGlyIiwidW1hX2F1dGhvcml6YXRpb24iXX0sInJlc291cmNlX2FjY2VzcyI6eyJhY2NvdW50Ijp7InJvbGVzIjpbIm1hbmFnZS1hY2NvdW50IiwibWFuYWdlLWFjY291bnQtbGlua3MiLCJ2aWV3LXByb2ZpbGUiXX19LCJzY29wZSI6ImVtYWlsIHByb2ZpbGUiLCJzaWQiOiIxODhhNGViNC05YzYwLTQxN2MtOWZkMy0yZTdkNmU4MDBlNjciLCJlbWFpbF92ZXJpZmllZCI6ZmFsc2UsInByZWZlcnJlZF91c2VybmFtZSI6InRlc3QifQ.BoKKk_lAKvVl9zBhVs0tfP29ux0gOk6dBItPhdXD57mnRq3DyfDiYHbFkO-BRifiQUOKZF0PDiBHQ_nis-smWvTqaApjfsNKsPyRv2Vzl9gnfeGrSPyufPydBOqCB7nWcKWwIsahrdEjvOACjvZJIYVXVhkXFQjODuXU_dJ8P_x5todtTOc6X6KwPYcAI3KLaf8j5eiUtFrK4yt2cf7XayW2pN5zhXfdUpGGXEWbrTKHHvX6CovT8CSimHrsjejpuwBfi_V6gVD2jckYlaKgVoVSsV4QHH6Q9a1xmHsZnjOMEUIsPiLZiGgsd82ijZMm2aiz0gV5a7q5vauddQlEyA"
    refresh_token = "eyJhbGciOiJIUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICIxZTcyMDZhMy03NTAzLTQ5MmEtYWVlMy02MDNiNWFhMWYzYzYifQ.eyJleHAiOjE2Mjg0ODYyMjgsImlhdCI6MTYyODQ4NDQyOCwianRpIjoiODhhZTljMDYtNjNkZS00NDRhLWE0NmYtMzI4OGIzY2IzM2Y2IiwiaXNzIjoiaHR0cDovL2tleWNsb2FrOjgwODAvYXV0aC9yZWFsbXMvSEFQSUZISVIiLCJhdWQiOiJodHRwOi8va2V5Y2xvYWs6ODA4MC9hdXRoL3JlYWxtcy9IQVBJRkhJUiIsInN1YiI6Ijk5ZmEyMjM1LTllMDctNDUxZC1hODBhLTgzOTI1NDJiMzcyOCIsInR5cCI6IlJlZnJlc2giLCJhenAiOiJoYXBpZmhpci1jbGllbnQiLCJzZXNzaW9uX3N0YXRlIjoiMTg4YTRlYjQtOWM2MC00MTdjLTlmZDMtMmU3ZDZlODAwZTY3Iiwic2NvcGUiOiJlbWFpbCBwcm9maWxlIiwic2lkIjoiMTg4YTRlYjQtOWM2MC00MTdjLTlmZDMtMmU3ZDZlODAwZTY3In0.N9-tMpWvbpk_G1ZTD1VymbxbJa2h9dDiCHUCXpr2eV8"
    fhirauth.set_auth_tokens(fhirauth, access_token, refresh_token)
    # result = fhirauth._request_access_token(fhirauth, smart.server, json.dumps(params))

    
    # result = fhirserver.post_as_form("http://localhost:8081/login", json.dumps(params), None).json()
    # print(f"AUTH URL : {str(result)}")

    smart.server.set_auth(fhirauth)

    print(f"ACCESS TOKEN: {smart.server.auth.access_token}")
 
    import fhirclient.models.patient as p
    import fhirclient.models.humanname as hn
    
    patient = p.Patient()
    
    name = hn.HumanName()
    name.given = ['Christopher']
    name.family = 'Lee'
    patient.name = [name]
    
    # p.Patient.create(patient, smart.server)
    
    body = f"<p>{p.Patient.create(patient, smart.server)}</p>"
    return body

    # import fhirclient.models.patient as p
    # search = p.Patient.where(struct={'_id': '1'})
    # print("Searched: ")
    # print(search)
    # patients = search.perform_resources(smart.server)
    # print("patients : ")
    # print(patients)
    # for patient in patients:
    #     patient.as_json()
    #     print(patient.as_json())
    # print(patient)
    # # '1963-06-12'
    # print(smart.human_name(patient.name[0]))
    # # 'Christy Ebert'


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

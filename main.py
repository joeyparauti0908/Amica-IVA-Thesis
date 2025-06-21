# change record
# version for Joey Parauti

# imported python modules
import os
import sys
import time
import datetime
import spacy
# import PySimpleGUI as sg
import azure.cognitiveservices.speech as speech
from openai import OpenAI

# modules designed for JAIN project
import equipment_config
import speechToUnity
import location_jane
import remove_shelves
import usecases.uc015_chitchat_chatgpt_en
import usecases.uc015_chitchat_chatgpt_en2
import usecases.uc015_chitchat_jp_control
import usecases.uc015_chitchat_jp_experiment
import experiment_settings
import statements
from mistralai import Mistral
import mistral_iva_config as config_mistral
import pandas as pd
import random


def get_file_path(file_name=""):
    return os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), file_name)


def debug_log(text):
    momentary_datetime = "===\n" + py_file_name + str(datetime.datetime.now()) + "\n" + text + "\n"
    logs.insert(0, momentary_datetime)


def end_program():

    statement = "end of session"
    debug_log(statement)
    list_to_str = ' '.join(map(str, logs))

    log_file_path = equipment_config.get_project_path()
    filename = log_file_path + r"\ldblogs.txt"
    file = open(filename, "a")
    file.write(list_to_str)
    file.write("\n")
    file.close()

    remove_shelves.run()
    sys.exit()


if __name__ == "__main__":
    # In case main has crashed in previous session, remove old shelve files
    remove_shelves.run()

    # prepare for logging
    py_file_name = 'ldblogs'
    logs = []

    language = experiment_settings.experiment_language()
    gender = experiment_settings.experiment_gender()
    text_strings = display_strings = {}
    if language == "nl":
        text_strings = statements.nl_text_strings
        display_strings = statements.nl_display_text_strings
    elif language == "en":
        text_strings = statements.en_text_strings
        display_strings = statements.en_display_text_strings
    elif language == "de":
        text_strings = statements.de_text_strings
        display_strings = statements.de_display_text_strings
    elif language == "tr":
        text_strings = statements.tr_text_strings
        display_strings = statements.tr_display_text_strings
    elif language == "es":
        text_strings = statements.es_text_strings
        display_strings = statements.es_display_text_strings


    # Load API key and create client
    api_key = config_mistral.get_mistral_key()
    client = Mistral(api_key=api_key)

    # Set language and initial state
    language = 'Dutch'
    conversation_history = []
    role = config_mistral.get_mistral_role()
    ending_string= "Tot ziens"
    state = "start"



    # initiate Microsoft Azure speech to text:
    key1 = equipment_config.get_ma_key1()
    key2 = equipment_config.get_ma_key2()
    location = equipment_config.get_ma_location()
    endpoint = equipment_config.get_ma_endpoint()

    speech_key, service_region = key1, location
    speech_config = speech.SpeechConfig(subscription=speech_key, region=service_region)
    speech_config.speech_recognition_language = equipment_config.get_ma_language(language)
    speech_recognizer = speech.SpeechRecognizer(speech_config=speech_config)


    # Start Unity server and wait until Unity is connected
    speechToUnity.start_unity_server()
    while speechToUnity.client == None:
        time.sleep(1)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = get_file_path("coach-1607434593693-e866839c8b17.json")

    start_location_jane = "ArmChair"
    location_jane.set(start_location_jane)

    # Start one of the usecases for Joey
    # Test use case (original version)
    language_acronym = 'nl'
    # usecases.uc015_chitchat_chatgpt_en2.dialogue_chitchat(text_strings, display_strings, language_acronym, gender)
    # Control Version
    #usecases.uc015_chitchat_jp_control.dialogue_chitchat(text_strings, display_strings, language_acronym, gender)
    # Experiment Version
    usecases.uc015_chitchat_jp_experiment.dialogue_chitchat(text_strings, display_strings, language_acronym, gender)


    end_program()

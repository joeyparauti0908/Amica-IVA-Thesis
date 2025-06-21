# Control Version IVA Joey Parauti
# openapi_schema_to_json_schema install zie https://pypi.org/project/py-openapi-schema-to-json-schema/
import spacy
import mistral_iva_config
import demo_statements
import equipment_config
import experiment_settings
import location_jane
import speechToUnity
import time
import statements
import utils
import os
import sys
from openai import BadRequestError
from mistralai import Mistral
import mistral_iva_config as config_mistral
import pandas as pd
import random

#from usecases.uc015_chitchat_jp_experiment import prompt_for_query_openai

# Load the social activity dataset into a DataFrame
df = pd.read_csv('sociale_activiteiten_pwd.csv', encoding='utf-8')


def get_location_filter():
    keuze = "Wil je een activiteit 'binnen' of 'buiten'?"
    return keuze


# Ask the user what kind of activity they prefer
def get_type_filter():
    valid_types = df['Subcategory'].unique().tolist() # List of available types
    print("\nAmica : Dit zijn de type activiteiten waar je uit kan kiezen: ")
    for t in valid_types:
        print(f"- {t}")


# Recommend one random activity based on the selected location and type
def recommend_activities(input_answer):
    # location = get_location_filter()
    location = input_answer
    type_activity = get_type_filter()

    # Filter dataset based on indoor/outdoor choice
    if location == 'buiten':
        location_dataset = df['Category'].str.contains('buitenshuis', case=False, na=False)
    else:
        location_dataset = ~df['Category'].str.contains('buitenshuis', case=False, na=False)

    # Select activities that match both filters
    suitable_activities = df[location_dataset & (df['Subcategory'] == type_activity)]

    # Convert to list and return a random one
    all_activities = suitable_activities['Activity'].tolist()
    return random.choice(all_activities)

def get_file_path(file_name=""):
    return os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), file_name)


# Support function for testing if a text string contains a word from a list, for stopping the interaction
def string_contains_any_from_list(text, search_list):
    for item in search_list:
        if item.lower() in text.lower():  # Case-insensitive check
            return True
    return False


# Support function to extract text from text file and put into an object 'text'
def extract_text_from_text_file(file_name):
    text_file_path = get_file_path(file_name)
    text = ""
    try:
        with open(text_file_path, 'r', encoding='utf-8') as file:
            text = file.read()
    except FileNotFoundError:
        print('Error: File Not Found')
    except Exception as e:
        print(f"An error occurred: {e}")
    return text


# Support function to check if the RAG document might contain the answer to a question
def document_contains_answer(document_text, user_question, lang):
    # keywords = question.split()
    # response_doc_contains_answer = any(keyword.lower() in document_text.lower() for keyword in keywords

    # load the required language module
    if lang == 'nl':
        # Dutch
        nlp = spacy.load("nl_core_news_md")
    elif lang == 'en':
        # English
        nlp = spacy.load('en_core_web_md')
    elif lang == 'de':
        # German
        nlp = spacy.load('de_core_news_md')
    else:
        nlp = spacy.load('en_core_web_md')

    # Process the question
    doc = nlp(user_question)

    # Extract nouns and entities from the question
    nouns_and_entities = [token.text for token in doc if token.pos_ == "NOUN" or token.ent_type_ != ""]

    print("Nouns and/or entities in question: " + str(nouns_and_entities))

    # Check if the document contains the same keywords (nouns, entities) as the question and therefore might contain
    # the information needed for answering the question, and respond by bool response_doc_contains_answer = True or False
    response_doc_contains_answer = any(keyword.lower() in document_text.lower() for keyword in nouns_and_entities)
    print("response_doc_contains_answer: " + str(response_doc_contains_answer))
    return response_doc_contains_answer


# Ask Mistral to answer a user question in dementia-friendly style
def prompt_for_query_mistral(input_question, role, query_client, conversation_history, language):
    prompt = (
        f"The following is the conversation history: {conversation_history}"
        f"Please try to answer the following question {input_question}"
        f"You are not giving a list of answers, and only select the first and best answer. Use only three sentences."
        f"You are answering to a person with dementia try to formulate it dementia friendly."
        f"in your answer. Answer in the {language} language."
        f"Every sentence on a new line."
    )
    generated_answer = query_mistral(prompt, query_client, role)
    conversation_history.append({"question": input_question, "answer": generated_answer})
    return generated_answer

# Ask Mistral to suggest an activity in a dementia-friendly way
def mistral_activity_prompt(role, query_client, conversation_history, language, activity):
    prompt = (
        f"Propose the following {activity} activity to me like a suggestion."
        f"Remember: You are an IVA and cannot participate in the activity yourself."
        f"Use a maximum of 3 sentences and correct grammar"
        f"in your answer. Answer in the {language} language."
        f"Every sentence on a new line."
    )
    generated_answer = query_mistral(prompt, query_client, role)
    conversation_history.append({"activity": activity, "answer": generated_answer})
    return generated_answer

# Generate a short, friendly introduction for the virtual agent "Amica"
def prompt_introduction_mistral(role, query_client, language_adjective):
    prompt = (
        "Introduce yourself as Amica."
        "You are here to assist people in their daily life."
        "Use a dementia-friendly tone. Make your introduction in 2 or 3 short sentences. Good grammar."
        f"Answer in the {language_adjective} language."
        f"Every sentence on a new line."
    )
    generated_answer = query_mistral(prompt, query_client, role)
    return generated_answer


# Query the Mistral LLM with a formatted prompt
def query_mistral(prompt, query_client, role):
    model = "mistral-large-latest"
    chat_response = query_client.chat.complete(
        messages=[
            {
                "role": "system",
                "content": role
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        model=model,
        max_tokens=300,
        temperature=0,
    )

    # Print the generated answer
    generated_answer = chat_response.choices[0].message.content
    return generated_answer


def statement_language(lang):
    text_string_statements = {}
    if lang == 'en':
        text_string_statements = statements.en_text_strings
    elif lang == 'nl':
        text_string_statements = statements.nl_text_strings
    elif lang == 'de':
        text_string_statements = statements.de_text_strings
    elif lang == 'tr':
        text_string_statements = statements.tr_text_strings
    elif lang == 'es':
        text_string_statements = statements.es_text_strings
    return text_string_statements


def display_language(lang):
    display_statements = {}
    if lang == 'en':
        display_statements = statements.en_display_text_strings
    elif lang == 'nl':
        display_statements = statements.nl_display_text_strings
    elif lang == 'de':
        display_statements = statements.de_display_text_strings
    elif lang == 'tr':
        display_statements = statements.tr_display_text_strings
    elif lang == 'es':
        display_statements = statements.es_display_text_strings
    return display_statements


def remove_truncated_sentence(text):
    # Split the text based on period followed by a space or end of sentence
    sentences = text.split('.')
    # Filter out empty strings and remove the last sentence if it's truncated (i.e., no period)
    valid_sentences = [sentence.strip() for sentence in sentences if sentence.strip()]
    # Join the sentences back together with a period
    result = '. '.join(valid_sentences) + '.'
    return result



def dialogue_chitchat(text_strings, display_strings, language, gender):

    # Set language and initial state
    df = pd.read_csv('sociale_activiteiten_pwd.csv', encoding='utf-8')
    conversation_history = []
    role = config_mistral.get_mistral_role()
    ending_string = "tot ziens"
    state = "start"

    # Initiate Microsoft Azure STT:
    speech_recognizer = utils.init_ms_azure_stt(language)

    # Load API key and create client
    api_key = config_mistral.get_mistral_key()
    client = Mistral(api_key=api_key)

    language_adjective = experiment_settings.experiment_language_name()

    # Greet user and ask what you can do
    intro = prompt_introduction_mistral(role, client, language_adjective)
    print(display_strings['Avatar'] + intro)
    language_acronym = 'nl'
    speechToUnity.say_something(intro, language_acronym, gender)

    while speechToUnity.is_speaking:
        time.sleep(0.1)

    # Start dialogue loop
    while state != "end":

        if state == "start":
            # Listen for user input
            result = speech_recognizer.recognize_once()
            transcript = result.text.lower()
            print(display_strings['You'] + transcript)
            speechToUnity.send_chat('You', transcript)

            # Check if the user is asking for an activity
            if 'activiteit' in transcript or 'activiteiten' in transcript:
                state = "recommend_activity"
            else:
                conversation_history.append({"role": "user", "content": transcript})
                try:
                    response = prompt_for_query_mistral(transcript, role, client, conversation_history, language_adjective)
                except:
                    response = "Er ging iets mis bij het ophalen van het antwoord."
                print(display_strings['Avatar'] + response)
                speechToUnity.say_something(response, language_acronym, gender)
                while speechToUnity.is_speaking:
                    time.sleep(0.1)
                state = "chat_mode"

        elif state == "recommend_activity":
            # Ask user for location preference
            ask_loc = "Wil je een activiteit binnen of buiten?"
            print(display_strings['Avatar'] + ask_loc)
            speechToUnity.say_something(ask_loc, language_acronym, gender)
            while speechToUnity.is_speaking:
                time.sleep(0.1)
            result = speech_recognizer.recognize_once()
            loc_transcript = result.text.lower()
            print(display_strings['You'] + loc_transcript)
            speechToUnity.send_chat('You', loc_transcript)

            if "buiten" in loc_transcript:
                location_filter = df['Category'].str.contains('buitenshuis', case=False, na=False)
            else:
                location_filter = ~df['Category'].str.contains('buitenshuis', case=False, na=False)

            filtered_df = df[location_filter]

            # Ask for activity type
            time.sleep(1)
            ask_type = "Je kunt kiezen uit deze soorten activiteiten:"
            print(display_strings['Avatar'] + ask_type)
            speechToUnity.say_something(ask_type, language_acronym, gender)
            while speechToUnity.is_speaking:
                time.sleep(0.1)

            valid_types = filtered_df['Subcategory'].unique().tolist()
            keyword_map = {
                'actief': 'Leuk en actief',
                'leuk': 'Leuk en actief',
                'ontspannen': 'Ontspannen en passief',
                'passief': 'Ontspannen en passief',
                'uitdagend': 'Uitdagend',
                'nuttig': 'Nuttig',
            }

            for t in valid_types:
                speechToUnity.say_something(t, language_acronym, gender)
                print(display_strings['Avatar'] + t)
                while speechToUnity.is_speaking:
                    time.sleep(0.1)

            result = speech_recognizer.recognize_once()
            type_transcript = result.text.lower()
            print(display_strings['You'] + type_transcript)
            speechToUnity.send_chat('You', type_transcript)

            # Try mapping to a known category
            for keyword, mapped_type in keyword_map.items():
                if keyword in type_transcript:
                    selected_type = mapped_type
                    break
            else:
                selected_type = type_transcript # fallback if no mapping

            # Filter based on both location and type
            final_df = filtered_df[filtered_df['Subcategory'] == selected_type]

            if final_df.empty:
                notification = "Ik kon geen geschikte activiteit vinden. Wil je iets anders proberen?"
                print(display_strings['Avatar'] + notification)
                speechToUnity.say_something(notification, language_acronym, gender)
                while speechToUnity.is_speaking:
                    time.sleep(0.1)
                state = "chat_mode"
                continue

            # Select and suggest random activity
            activity = final_df['Activity'].sample(n=1).iloc[0]
            conversation_history.append({"role": "user", "content": activity})

            try:
                response = mistral_activity_prompt(role, client, conversation_history, language_adjective, activity)
            except:
                response = "Er ging iets mis bij het ophalen van de suggestie."

            print(display_strings['Avatar'] + response)
            speechToUnity.say_something(response, language_acronym, gender)
            while speechToUnity.is_speaking:
                time.sleep(0.1)
            state = "chat_mode"

        elif state == "chat_mode":
            # Listen for user response
            result = speech_recognizer.recognize_once()
            transcript = result.text.lower()
            print(display_strings['You'] + transcript)
            speechToUnity.send_chat('You', transcript)

            if ending_string.lower() in transcript:
                state = "end"
            elif "activiteit" in transcript or "activiteiten" in transcript:
                state = "recommend_activity"
            else:
                conversation_history.append({"role": "user", "content": transcript})
                try:
                    response = prompt_for_query_mistral(transcript, role, client, conversation_history,
                                                        language_adjective)
                except:
                    response = "Er ging iets mis bij het ophalen van het antwoord."
                print(display_strings['Avatar'] + response)
                speechToUnity.say_something(response, language_acronym, gender)
                while speechToUnity.is_speaking:
                    time.sleep(0.1)
                state = "chat_mode"
    # End of conversation
    ending_sentence = "Fijn dat we even gesproken hebben. Tot de volgende keer!"
    print(display_strings['Avatar'] + ending_sentence)
    speechToUnity.say_something(ending_sentence, language_acronym, gender)
    while speechToUnity.is_speaking:
        time.sleep(0.5)


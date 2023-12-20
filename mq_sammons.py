import requests
import json
import urllib.parse
import xml.etree.ElementTree as ET
import os

# 3 fields below used for initializing Controller class
account_name_input = "sammons"    # first segment of URI for controller
api_token_input = ""    # Client Secret - API clients (admin)
client_id_input = "mq"    # Client Name field - API clients (admin)

file_path_health_rules = '/Users/aaronjacobs/Desktop/appd_scripts/q/queue_hr_payloads'
queue_names_txt_file = "/Users/aaronjacobs/Desktop/appd_scripts/q/queue_names.txt"
hr_xml_files_dir = "/Users/aaronjacobs/Desktop/appd_scripts/q/queue_hr_payloads/"


class Controller:
    def __init__(self, account_name: str, api_token: str, client_id: str):
        self.account_name = None
        self.api_token = None
        self.client_id = None

        self.controller_headers = None
        self.controller_url = None
        self.auth_token = None
        self.token_req_string = None
        self.headers = None
        self.req = None
        self.json_resp = None
        self.access_token = None
        self.bearer_token = None
        self.update(account_name=account_name, api_token=api_token, client_id=client_id)

    def update(self, account_name: str, api_token: str, client_id: str):
        self.account_name = account_name
        self.api_token = api_token
        self.client_id = client_id

        self.controller_url = "https://{}.saas.appdynamics.com".format(account_name)
        self.auth_token = "https://{}.saas.appdynamics.com/controller/api/oauth/access_token".format(account_name)
        self.token_req_string = ("grant_type=client_credentials&client_id={}@{}&client_secret={}"
                                 .format(client_id, account_name, api_token_input))
        self.headers = {'Content-type': 'application/x-www-form-urlencoded'}
        self.req = requests.post(self.auth_token, headers=self.headers, data=self.token_req_string)
        self.json_resp = json.loads(self.req.content.decode('utf-8'))
        self.access_token = 'Bearer ' + self.json_resp["access_token"]
        self.bearer_token = {"Authorization": self.access_token}


# GET /controller/rest/applications
def get_apps(token_in, url_in):
    url_in = url_in + "/controller/rest/applications"
    print(url_in)
    resp = requests.get(url_in, headers=token_in)
    # print(resp.status_code)
    print(resp.text)


# step 1 - export a single HR that you want to replicate
def export_health_rule_for_payload(app_name, health_rule_name):
    r = str(requests.get(controller_url + '/controller/healthrules/{}?name={}'.format(app_name, health_rule_name), headers=toke).text)
    xml_filename = 'health_rule.xml'
    print(r)
    print('XML file being created in directory you ran this script from...')
    with open(xml_filename, "w") as code:
        code.write(r)
    code.close()
    print('done creating file - {} in script home directory.'.format(xml_filename))


def get_queue_names(app_name_in):
    metric_path = "Application Infrastructure Performance|Root\|MQ|Individual Nodes|VSR-P-MWMQ1|Custom Metrics|WebsphereMQ|PRDMG01|Queues"
    safe_string = urllib.parse.quote_plus(metric_path)
    url_in = controller_url + "/controller/rest/applications/{}/metrics?metric-path={}".format(app_name_in, safe_string)
    print(url_in)
    resp = str(requests.get(url_in, headers=toke).text)
    print(resp)
    root = ET.fromstring(resp)
    a = 0
    with open('queue_names.txt', 'w') as f:
        for child in root:
            queue_name = root[a][1].text
            print(queue_name)
            # writes to directory where script is located names of queues on each line so next function can take the
            # file as input
            f.write(queue_name)
            f.write('\n')
            a += 1


def create_queue_hr_xml_files(input_queue_names_file, output_file_path_hr_configs):
    # file_name = "my.xml"
    with open(input_queue_names_file) as code:
        for queue_name in code:
            queue_name = queue_name.rstrip()
            print(queue_name)
            with open('health_rule.xml') as f:
                tree = ET.parse(f)
                root = tree.getroot()
                for elem in root.iter():
                    try:
                        elem.text = elem.text.replace('PLACEHOLDER', queue_name)
                    except AttributeError:
                        pass

            tree.write(output_file_path_hr_configs + '/{}-hr_config.xml'.format(queue_name))


def import_health_rules_from_dir(dir_in, url_in, app_id_in):
    # example of input_dir "/Users/aaronjacobs/PycharmProjects/dashboard_configs/dashboard_input_dir/"
    input_files = os.listdir(dir_in)
    print(input_files)
    url_in = url_in + "/controller/healthrules/{}?overwrite=true".format(app_id_in)
    print("final URL: ", url_in)

    for i in input_files:
        hr_xml_file = dir_in + i
        print("file path: ", hr_xml_file)
        with open(hr_xml_file, 'rb') as f:
            req = requests.post(url_in, headers=bearer_token_header, files={'file=@' + hr_xml_file: f})
            print(req.status_code, req.reason)
            print(req.text)
            print()


def print_menu():
    print(30 * "-", "MENU", 30 * "-")
    print("0. Exit")
    print("1. Menu Option 1 - Export Health Rule for template")
    print("2. Menu Option 2 - Get queue names - creates a file with queue names")
    print("3. Menu Option 3 - Create Health Rule Configuration Files for queues from text file")
    print("4. Menu Option 4 - Import MQ Health Rules")
    print(77 * "-")


def menu():
    loop = True
    while loop:  ## While loop which will keep going until loop = False
        print_menu()  ## Displays menu
        choice = input("Enter your choice [1-10]: ")
        if choice == "0":
            loop = False
        elif choice == "1":
            print("1 has been selected - Export Health Rule for template; file will export to working directory -")
            app_name = input("enter application name: ")
            hr_name = input("enter health rule name to export config in working directory: ")
            export_health_rule_for_payload(app_name, hr_name)
        elif choice == "2":
            print("2 has been selected - Get queue names - creates a file queue_names.txt (metric path and app name hard-coded in function) ")
            get_queue_names("3091") # app ID for servers - find by looking at URL when on Servers in UI
        elif choice == "3":
            print("3 has been selected - Create Health Rule Configuration Files for queues from text file")
            create_queue_hr_xml_files(queue_names_txt_file, hr_xml_files_dir)
        elif choice == "4":
            print("4 has been selected - Import MQ Health Rules")
            import_health_rules_from_dir(hr_xml_files_dir, controller_url, "3091")


my_connection = Controller(account_name_input, api_token_input, client_id_input)
toke = my_connection.bearer_token
controller_url = my_connection.controller_url
menu()


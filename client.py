#!/usr/bin/python

import socket
import time
import platform
import os
import pickle
import random
from _thread import *
import PySimpleGUI as sg
import subprocess
import sys

def p2p_get_request(filename, peer_host, peer_upload_port):
    print(f"\nGET REQUEST TO PEER {peer_host} {peer_upload_port}\n")
    sct = socket.socket()
    sct.connect((peer_host, int(peer_upload_port)))
    p = int(sct.getsockname()[1])
    print(f"\nCONNECTED, owner's port: {p}\n")
    message = p2p_request_message(filename, host)
    sct.send(bytes(message, 'utf-8'))
    res = []
    while True:
        packet = sct.recv(4096)
        if not packet:
            break
        res.append(packet)
    data_rec = pickle.loads(b"".join(res))
    print('res', b"".join(res))
    print(f"\nPEER RESPONSE\n {data_rec}\n")
    my_data = data_rec
    current_path = PATH
    pm = platform.system()
    if pm == "Windows":
        filename = current_path + "\\received_files\\" + filename
    else:
        filename = current_path + "/received_files/" + filename
    with open(filename, 'a+') as file:
        file.write(my_data)
    sct.close()


def p2p_response_message(file):
    filename = str(file)
    print(f"RESPONSE FILE NAME: {filename}")
    current_time = time.strftime("%a, %d %b %Y %X %Z", time.localtime())
    pm = platform.system()
    m = filename.split()
    filename = "".join(m)
    if pm == "Windows":
        filename = "\\files\\" + filename
    else:
        filename = "files/" + filename
    if os.path.exists(PATH + filename) == 0:
        message = f"404 Not Found \nDate: {current_time} \nOS: {pm}"
    else:
        txt = open(PATH + filename)
        text = txt.read()
        last_modified = time.ctime(os.path.getmtime(PATH + filename))
        content_length = os.path.getsize(PATH + filename)
        message = f"200 OK \nDate: {current_time} \nOS: {pm} \nLast-Modified: {last_modified} \nContent" \
                  f"-Length: {content_length} \nContent-Type: text/text \n{text}"
    return message


def p2p_request_message(file, host_name):
    pm = platform.platform()
    message = f"GET File {file} \nHost: {host_name} \nOS: {pm}"
    return file


def p2s_add_message(file, host_name, port_num):
    message = f"ADD file {file} \nHost: {host_name} \nPort: {port_num}"
    return ["ADD", file, host_name, port_num]


def p2s_lookup_message(host_name, port_num):
    message = f"LOOKUP File Host: {host_name} \nPort: {port_num}"
    return ["LOOKUP", host_name, port_num]


def p2s_list_request(host_name, port_num):
    message = f"LIST \nHost: {host_name} \nPort: {port_num}"
    return ["LIST", message]


def get_local_files():
    files_path = PATH + "\\files"
    files = next(os.walk(files_path), (None, None, []))[2]
    return files


def peer_information():
    keys = ["Filename"]
    files = get_local_files()
    titles = get_local_files()
    for num in files:
        entry = [num, "reviews"]
        dict_list_of_files.insert(0, dict(zip(keys, entry)))
    return [upload_port_num, dict_list_of_files]


def print_combined_list(dictionary_list, keys):
    msg = []
    for item in dictionary_list:
        msg.append(' '.join([item[key] for key in keys][1:]))
    return msg

def add_file(review, filename):
    current_path = PATH
    pm = platform.system()
    if pm == "Windows":
        filename = current_path + "\\files\\" + filename
    else:
        filename = current_path + "/files/" + filename
    with open(filename, 'a+') as file:
        file.write("\n" + review)

def get_user_input():
    user_input = input("> Enter ADD, LIST, LOOKUP, GET, or EXIT:  ")
    if user_input == "LOOKUP":
        user_input_host = input("> Enter Peer Host: ")
        user_input_port = input("> Enter Peer Port: ")
        message = pickle.dumps(p2s_lookup_message(user_input_host, user_input_port))
        s.send(message)
        server_data = pickle.loads(s.recv(1024))
        print(f"\nRESPONSE FROM SERVER:\n {server_data}")
        keys = ['Filename', 'Hostname', 'Port Number']
        print_combined_list([server_data[0]], keys)
        get_user_input()
    else:
        get_user_input()


def p2p_listen_thread():
    upload_socket = socket.socket()
    host_name = socket.gethostname()
    upload_socket.bind((host_name, upload_port_num))
    upload_socket.listen(5)
    while True:
        c, addr = upload_socket.accept()
        data_p2p_undecode = c.recv(1024)
        data_p2p = data_p2p_undecode.decode('utf-8')
        print('GOT CONNECTION FROM: ', addr)
        print(f"RECEIVED DATA:  {data_p2p}")
        c.send(pickle.dumps(p2p_response_message(data_p2p)))
        c.close()

def graph():
    event, values = window.read()
    if event in (sg.WIN_CLOSED, 'Exit', '-BUT_EXIT-'):
        gr_exit()
    if event == '-BUT_LIST-':
        get_list()
    if event == '-BUT_GET-':
        get_file()
    if event == '-BUT_ADD-':
        gr_add_file()
            
def gr_exit():
    message = pickle.dumps(["EXIT"])
    s.send(message)
    s.close()
    print("Connection is stopped")
    window.close()
    os._exit(0)

def get_list():
    message = pickle.dumps(p2s_list_request(host, port))
    s.send(message)
    new_data = pickle.loads(s.recv(1024))
    l = print_combined_list(new_data[0], new_data[1])
    window['-TEXT_LIST-'].update("Peers: {}".format(l))
    graph()

def get_file():
    peer_host, peer_port = window['-TEXT_GET_HOST-'].get(), window['-TEXT_GET_PORT-'].get()
    user_input_host = peer_host
    user_input_port = peer_port
    message = pickle.dumps(p2s_lookup_message(user_input_host, user_input_port))
    s.send(message)
    server_data = pickle.loads(s.recv(1024))
    print(f"\nRESPONSE FROM SERVER:\n {server_data}\n")
    if server_data[0]:
        p2p_get_request(str(server_data[0]["Filename"]), user_input_host, user_input_port)
        window['-TEXT_GET_ST-'].update("Got file from peer "+ peer_host + ' ' + peer_port)
        subprocess.Popen(r'explorer /select,"C:\Mara\Study\Master\m1_el\p2p_reviews-main\received_files"')
    else:
        print(f"\nRESPONSE FROM SERVER:\n {server_data[1]}\n")  # print error
        window['-TEXT_GET_ST-'].update("Error")
    graph()

def gr_add_file():
    user_input_filename = str(host) + str(upload_port_num) + ".txt"
    user_input_review = window['-TEXT_ADD-'].get()
    message = pickle.dumps(p2s_add_message(user_input_filename, host, upload_port_num))
    s.send(message)
    server_data = s.recv(1024)
    print(f"\nRESPONSE FROM SERVER:\n {server_data.decode('utf-8')}\n")
    add_file(user_input_review, user_input_filename)
    window['-TEXT_ADD-'].update('')
    graph()



PATH = 'C:\\Mara\\Study\\Master\\m1_el\\p2p_reviews-main'
upload_port_num = 65000 + random.randint(1, 500)  # generate a upload port randomly in 65000~65500
dict_list_of_files = []
s = socket.socket()
host = socket.gethostbyname(socket.gethostname())
print('host', host)
port = 7734
s.connect((host, port))
owners_port = int(s.getsockname()[1])
print(f"\nUPLOAD PORT: {upload_port_num}")
print(f"RUNNING ON PORT: {owners_port}\n")

layout = [[sg.Text('Your peer: ' + host + ' ' + str(upload_port_num) , size=(100, 1), key='-TEXT_PEER-', font='Helvetica 16')], 
          [sg.Multiline(size=(100, 5), key='-TEXT_ADD-', font='Helvetica 16')],
        [sg.Button('Add review',enable_events=True, key='-BUT_ADD-', font='Helvetica 16')],
        [sg.Button('Get list of peers:',enable_events=True, key='-BUT_LIST-', font='Helvetica 16'), 
         sg.Multiline(size=(50, 5), key='-TEXT_LIST-', font='Helvetica 16')],
        [sg.Button('Get file from peer',size= (20, 1), enable_events=True, key='-BUT_GET-', font='Helvetica 16'),
         sg.Input(enable_events=False, size=(40, 1), font='Helvetica 16', key='-TEXT_GET_HOST-'), 
         sg.Input(enable_events=False, size=(40, 1), font='Helvetica 16', key='-TEXT_GET_PORT-')],
        [sg.Text('', size=(100, 1), key='-TEXT_GET_ST-', font='Helvetica 16')],
        [sg.Button('EXIT',enable_events=True, key='-BUT_EXIT-', font='Helvetica 16')]]
window = sg.Window('Client', layout, size=(1000,500))

data = pickle.dumps(peer_information())
print(f"\nSEND LOCAL FILES INFORMATION TO SERVER:\n {peer_information()}\n")
s.send(data)
data = s.recv(1024)
print(f"\nRESPONSE FROM SERVER:\n {data.decode('utf-8')}\n")
s.close


start_new_thread(p2p_listen_thread, ())
start_new_thread(graph, ())
get_user_input()
window.close()
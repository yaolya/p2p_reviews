#!/usr/bin/python

import socket
import time
import platform
import os
import pickle
import random
from _thread import *


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
    print(f"\nPEER RESPONSE\n {data_rec}\n")
    my_data = data_rec
    current_path = os.getcwd()
    pm = platform.system()
    if pm == "Windows":
        filename = current_path + "\\files\\" + filename
    else:
        filename = current_path + "/received_files/" + filename
    with open(filename, 'w') as file:
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
        filename = "files\\" + filename
    else:
        filename = "files/" + filename
    if os.path.exists(filename) == 0:
        message = f"404 Not Found \nDate: {current_time} \nOS: {pm}"
    else:
        txt = open(filename)
        text = txt.read()
        last_modified = time.ctime(os.path.getmtime(filename))
        content_length = os.path.getsize(filename)
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
    files_path = os.getcwd() + "/files"
    files = next(os.walk(files_path), (None, None, []))[2]
    return files


def peer_information():
    keys = ["Filename"]
    files = get_local_files()
    for num in files:
        entry = [num, "reviews"]
        dict_list_of_files.insert(0, dict(zip(keys, entry)))
    return [upload_port_num, dict_list_of_files]


def print_combined_list(dictionary_list, keys):
    print(f"\nCOMBINED LIST")
    for item in dictionary_list:
        print(' '.join([item[key] for key in keys]))
    print()


def add_file(review, filename):
    current_path = os.getcwd()
    pm = platform.system()
    if pm == "Windows":
        filename = current_path + "\\files\\" + filename
    else:
        filename = current_path + "/files/" + filename
    with open(filename, 'w') as file:
        file.write(review)


def get_user_input():
    user_input = input("> Enter ADD, LIST, LOOKUP, GET, or EXIT:  ")
    if user_input == "EXIT":
        message = pickle.dumps(["EXIT"])
        s.send(message)
        s.close()
    elif user_input == "ADD":
        user_input_filename = input("> Enter Filename: ")
        user_input_review = input("> Enter Review: ")
        message = pickle.dumps(p2s_add_message(user_input_filename, host, upload_port_num))
        s.send(message)
        server_data = s.recv(1024)
        print(f"\nRESPONSE FROM SERVER:\n {server_data.decode('utf-8')}\n")
        add_file(user_input_review, user_input_filename)
        get_user_input()
    elif user_input == "LIST":
        message = pickle.dumps(p2s_list_request(host, port))
        s.send(message)
        new_data = pickle.loads(s.recv(1024))
        print_combined_list(new_data[0], new_data[1])
        get_user_input()
    elif user_input == "GET":
        user_input_host = input("> Enter Peer Host: ")
        user_input_port = input("> Enter Peer Port: ")
        message = pickle.dumps(p2s_lookup_message(user_input_host, user_input_port))
        s.send(message)
        server_data = pickle.loads(s.recv(1024))
        print(f"\nRESPONSE FROM SERVER:\n {server_data}\n")
        print(server_data[0])
        if server_data[0]:
            p2p_get_request(str(server_data[0]["Filename"]), user_input_host, user_input_port)
        else:
            print(f"\nRESPONSE FROM SERVER:\n {server_data[1]}\n")  # print error
        get_user_input()
    elif user_input == "LOOKUP":
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


upload_port_num = 65000 + random.randint(1, 500)  # generate a upload port randomly in 65000~65500
dict_list_of_files = []
s = socket.socket()
host = socket.gethostbyname(socket.gethostname())
port = 7734
s.connect((host, port))
owners_port = int(s.getsockname()[1])
print(f"\nUPLOAD PORT: {upload_port_num}")
print(f"RUNNING ON PORT: {owners_port}\n")
data = pickle.dumps(peer_information())
print(f"\nSEND LOCAL FILES INFORMATION TO SERVER:\n {peer_information()}\n")
s.send(data)
data = s.recv(1024)
print(f"\nRESPONSE FROM SERVER:\n {data.decode('utf-8')}\n")
s.close
start_new_thread(p2p_listen_thread, ())
get_user_input()

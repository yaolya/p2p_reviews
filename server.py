#!/usr/bin/python

import socket
import time
import platform
from _thread import *
import pickle


def p2s_lookup_response(hostname, port_number):
    current_time = time.strftime("%a, %d %b %Y %X %Z", time.localtime())
    pm = platform.platform()
    response = search_combined_dict(hostname, port_number)
    
    if len(response) == 0:
        message = f"404 Not Found \nDate: {current_time} \nOS: {pm}"
    else:
        message = "200 OK"
    return response, message


def p2s_add_response(conn, filename, hostname, port_number):
    response = f"200 OK \nFile: {filename} {hostname} {port_number}"
    conn.send(bytes(response, 'utf-8'))


def search_combined_dict(hostname, port_number):
    for d in combined_list:
        if d['Hostname'] == hostname and d['Port Number'] == port_number:
            return d
    return {}


# appends a peers dictionary of hostname and port number
def create_peer_list(dictionary_list, hostname, port_number):
    keys = ['Hostname', 'Port Number']
    entry = [hostname, str(port_number)]
    dictionary_list.insert(0, dict(zip(keys, entry)))
    return dictionary_list, keys


def create_files_list(dictionary_list, dict_list_of_files, hostname):
    keys = ['Filename', 'Hostname']

    for d in dict_list_of_files:
        filename = d['Filename']
        entry = [filename, hostname]
        dictionary_list.insert(0, dict(zip(keys, entry)))

    return dictionary_list, keys


def create_combined_list(dictionary_list, dict_list_of_files, hostname, port_number):
    keys = ['Filename', 'Hostname', 'Port Number']

    for d in dict_list_of_files:
        filename = d['Filename']
        entry = [filename, hostname, str(port_number)]
        dictionary_list.insert(0, dict(zip(keys, entry)))

    return dictionary_list, keys


# inserts new dictionary item to files list when client makes an ADD request
def append_to_files_list(dictionary_list, filename, hostname):
    keys = ['Filename', 'Hostname']
    entry = [filename, hostname]
    for d in dictionary_list:
        if d['Filename'] == filename:
            return dictionary_list
    dictionary_list.insert(0, dict(zip(keys, entry)))
    return dictionary_list


def append_to_combined_list(dictionary_list, filename, hostname, port_number):
    keys = ['Filename', 'Hostname', 'Port Number']
    entry = [filename, hostname, str(port_number)]
    for d in dictionary_list:
        if d['Filename'] == filename:
            return dictionary_list
    dictionary_list.insert(0, dict(zip(keys, entry)))
    return dictionary_list


def print_dictionary(dictionary_list, keys, name):
    print(f'\nDICTIONARY "{name}"')
    for item in dictionary_list:
        print(' '.join([item[key] for key in keys]))
    print()


# Deletes the entries associated with the hostname
def delete_peers_dictionary(dict_list_of_peers, hostname):
    dict_list_of_peers[:] = [d for d in dict_list_of_peers if d.get('Hostname') != hostname]
    return dict_list_of_peers


# Deletes the entries associated with the hostname
def delete_files_dictionary(dict_list_of_files, hostname):
    dict_list_of_files[:] = [d for d in dict_list_of_files if d.get('Hostname') != hostname]
    return dict_list_of_files


def delete_combined_dictionary(combined_dict, hostname):
    combined_dict[:] = [d for d in combined_dict if d.get('Hostname') != hostname]
    return combined_dict


def return_dict():
    keys = ['Filename', 'Hostname', 'Port Number']
    return combined_list, keys


def client_thread(conn, address):
    print(f"\nTHREAD FOR CLIENT {address} CREATED\n")
    global peer_list, files_list, combined_list
    conn.send(bytes('Thank you for connecting', 'utf-8'))
    data = pickle.loads(conn.recv(1024))
    print(f"\nRECEIVED DATA:\n {data}\n")
    client_port = data[0]
    # generate the peers list and files list
    peer_list, peer_keys = create_peer_list(peer_list, address[0], data[0])
    print_dictionary(peer_list, peer_keys, "peers")
    files_list, files_keys = create_files_list(files_list, data[1], address[0])
    print_dictionary(files_list, files_keys, "files")
    combined_list, combined_keys = create_combined_list(combined_list, data[1], address[0], data[0])

    while True:
        data = pickle.loads(conn.recv(1024))
        print(f"\nRECEIVED DATA:\n {data}\n")
        if data[0] == "EXIT":
            break
        elif data[0] == "LIST":
            new_data = pickle.dumps(return_dict())
            conn.send(new_data)
        elif data[0] == "ADD":
            p2s_add_response(conn, data[1], data[2], data[3])
            files_list = append_to_files_list(files_list, data[1], data[2])
            combined_list = append_to_combined_list(combined_list, data[1], data[2], client_port)
            print_dictionary(files_list, files_keys, "files")
        elif data[0] == "LOOKUP":
            new_data = pickle.dumps(p2s_lookup_response(data[1], data[2]))
            conn.send(new_data)
    peer_list = delete_peers_dictionary(peer_list, address[0])
    files_list = delete_files_dictionary(files_list, address[0])
    combined_list = delete_combined_dictionary(combined_list, address[0])
    conn.close()


    
s = socket.socket()
host = socket.gethostname()
port = 7734
s.bind((host, port))
print(f"listening on port {port}...")
s.listen(5)

peer_list = []  # global list of dictionaries for peers
files_list = []  # global list of dictionaries for files
combined_list = []

while True:
    c, addr = s.accept()
    print(f"\nESTABLISHED CONNECTION WITH CLIENT: {addr}\n")
    start_new_thread(client_thread, (c, addr))
s.close()

import socket
from threading import Thread
import sys
import os
import pickle
# from helper import *


HOST = '127.0.0.1'
PORT = 54321
MAX_LISTEN_NUM = 5
BUFFER_SIZE = 1024
SETTIMEOUT = 60


MSG_CANCEL = "Cancel"
MSG_SUCCESS = "Success"
MSG_ABORT = "Abort"
MSG_OKAY = "Okay"
MSG_READY = "Ready"
MSG_CONTINUE = "Continue"
MSG_FILE_EXIST = "File Exist"
MSG_NOT_FOUND = "NOT FOUND"
MSG_CLOSE = "Closing"
MSG_REWRITE = "Do you wish to overwrite the file contents? [y]/[n]\n"


base_work_dir = './server_file/'
cur_work_dir = ''


'''
Helpers
'''
def str2byte(sentence):
    return sentence.encode()


def byte2str(sentence):
    return sentence.decode('utf-8')


def file_exist(fname):
    return os.path.exists(cur_work_dir + fname)


def send_file(conn, fname):

    file_dir = os.path.join(cur_work_dir, fname)
    print(cur_work_dir)

    with open(file_dir, 'rb') as file_to_send:
        for data in file_to_send:
            conn.send(data)
    
    print('Send successfully!')
    return 0


def receive_file(conn, fname):
    file_dir = os.path.join(cur_work_dir, fname)
    with open(file_dir, 'wb') as file_to_receive:
        while True:
            data = conn.recv(BUFFER_SIZE)
            # print(byte2str(data))
            if not data:
                break
            file_to_receive.write(data)
            if len(data) < BUFFER_SIZE:
                break
    
    print('File received!')
    return 1


'''
GET
'''
def get_file(conn, fname):
    if file_exist(fname):
        send_msg = MSG_FILE_EXIST
        conn.send(str2byte(send_msg))

        # send_msg = MSG_READY
        # conn.send(str2byte(send_msg))

        send_file(conn, fname)
    else:
        send_msg = MSG_CANCEL
        conn.send(str2byte(send_msg))
            

'''
PUT
'''
def put_file(conn, fname):
    if file_exist(fname):
        send_msg = MSG_FILE_EXIST
        conn.send(str2byte(send_msg))

        buf = conn.recv(BUFFER_SIZE)
        resp = byte2str(buf)
        if resp == 'y': # rewrite
            send_msg = MSG_OKAY
            conn.send(str2byte(send_msg))

            receive_file(conn, fname)
        else:
            send_msg = MSG_ABORT
            conn.send(str2byte(send_msg))
    
    else:
        send_msg = MSG_OKAY
        conn.send(str2byte(send_msg))
        receive_file(conn, fname)

'''
LS
'''
def list_file(conn):
    files = os.listdir(cur_work_dir)
    data = pickle.dumps(files)
    conn.send(data)
    return


'''
MKDIR
'''
def mkdir(conn, cmd_list):
    dir_name = cmd_list[1]

    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
        send_msg = MSG_SUCCESS
    else:
        send_msg = MSG_FILE_EXIST
    
    conn.send(str2byte(send_msg))


'''
PWD
'''
def print_working_dir(conn):
    send_msg = os.path.realpath(cur_work_dir)
    conn.send(str2byte(send_msg))


'''
CD
'''
def change_dir(conn, cmd_list):
    global cur_work_dir
    target_dir = cmd_list[1]
    tmp_dir = os.path.join(cur_work_dir, target_dir)

    if os.path.exists(tmp_dir):
        send_msg = MSG_SUCCESS
        cur_work_dir = os.path.realpath(tmp_dir)
    else:
        send_msg = MSG_NOT_FOUND
    
    conn.send(str2byte(send_msg))
    return


'''
EXIT
'''
def conn_exit(conn):
    send_msg = MSG_CLOSE
    conn.send(str2byte(send_msg))

    conn.close()


def cmd_handler(conn, cmd):
    cmd_list = cmd.split()
    cmd_name = cmd_list[0].upper()
    print(cmd_name)
    # print(cur_work_dir)

    if cmd_name == 'GET':
        #TODO: no file enter handler
        fname = cmd_list[1]
        get_file(conn, fname)
    elif cmd_name == 'PUT':
        #TODO: no file enter handler
        fname = cmd_list[1]
        put_file(conn, fname)
    elif cmd_name == 'LS':
        list_file(conn)
    elif cmd_name == 'MKDIR':
        mkdir(conn, cmd_list)
    elif cmd_name == 'PWD':
        print_working_dir(conn)
    elif cmd_name == 'CD':
        change_dir(conn, cmd_list)
    elif cmd_name == 'EXIT':
        conn_exit(conn)
        return 1
    else:
        return 0


def child_connection(index, conn, addr):
    global cur_work_dir

    cur_work_dir = base_work_dir
    print(cur_work_dir)

    conn_exit = 0

    try:
        print('begin connection %d' % index)
        conn.settimeout(60)

        while True:
            buf = conn.recv(BUFFER_SIZE)
            print('BUF: ' + str(buf, 'utf-8'))
            
            cmd = byte2str(buf)
            print('Get value %s from connection %d: ' % (cmd, index))

            if not cmd:
                break
            else:
                conn_exit = cmd_handler(conn, cmd)
            
            if conn_exit:
                print('Connection %d closed' % index)
                break
    
    except socket.timeout:
        print('Time out')
        print('Closing connection %d' % index)
        conn.close()


if __name__ == "__main__":
    try:
        print('Server is starting')
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    except:
    #    print('Failed to create socket. Error code: ' + str(msg[0]) + ', Error message: ' + msg[1])
        sys.exit()

    s.bind((HOST, PORT))
    s.listen(MAX_LISTEN_NUM)

    index = 0
    while True:
        conn, addr = s.accept()
        index += 1
        threads = []
        Thread(target = child_connection, args = (index, conn, addr)).start()

        if index > 10:
            break
    s.close()

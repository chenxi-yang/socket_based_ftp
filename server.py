import socket
from threading import Thread
import sys
import os
# from helper import *

HOST = '127.0.0.1'
PORT = 54321
MAX_LISTEN_NUM = 5
BUFFER_SIZE = 1024
SETTIMEOUT = 60

FILE_DIR = './server_file/'

MSG_CANCEL = "Cancel"
MSG_ABORT = "Abort"
MSG_OKAY = "Okay"
MSG_READY = "Ready"
MSG_CONTINUE = "Continue"
MSG_FILE_EXIST = "File Exist\n"
MSG_REWRITE = "Do you wish to overwrite the file contents? [y]/[n]\n"


'''
Helpers
'''
def str2byte(sentence):
    return sentence.encode()

def byte2str(sentence):
    return sentence.decode('utf-8')


def send_file(conn, fname):
    return 0


def receive_file(conn, fname):
    file_dir = os.path.join(FILE_DIR, fname)
    with open(file_dir, 'wb') as file_to_receive:
        while True:
            data = conn.recv(BUFFER_SIZE)
            print(byte2str(data))
            if not data:
                break
            file_to_receive.write(data)
    
    return 0


def file_exist(fname):
    return os.path.exists(FILE_DIR + fname)


def get_file(conn, fname):
    if file_exist(fname):
        send_msg = MSG_READY
        conn.send(str2byte(send_msg))
        send_file(conn, fname)
    else:
        send_msg = MSG_CANCEL
        conn.send(str2byte(send_msg))
            

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
        

def cmd_handler(conn, cmd):
    cmd_list = cmd.split()
    cmd_name = cmd_list[0].upper()

    if cmd_name == 'GET':
        fname = cmd_list[1]
        get_file(conn, fname)
    elif cmd_name == 'PUT':
        fname = cmd_list[1]
        put_file(conn, fname)
    else:
        return


def child_connection(index, conn, addr):
    try:
        print('begin connection %d' % index)
        conn.settimeout(60)

        while True:
            buf = conn.recv(BUFFER_SIZE)
            # print('BUF: ' + str(buf, 'utf-8'))
            
            cmd = byte2str(buf)
            print('Get value %s from connection %d: ' % (cmd, index))

            if not cmd:
                break
            else:
                cmd_handler(conn, cmd)
    
    except socket.timeout:
        print('time out')
        print('closing connection %d' % index)
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

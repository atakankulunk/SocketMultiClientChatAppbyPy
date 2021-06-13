from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread


MESSAGE = "MESSAGE\n"
FROM="SERVER\n"
TO="BROADCAST\n"
PROTOCOL="INFO\n"

#kurallar yazılacak
def accept_incoming_connections():
    """Sets up handling for incoming clients."""
    while True:
        client, client_address = SERVER.accept()
        print("%s:%s has connected." % client_address)
        client.send(bytes("Connection Successful! Hello There", "utf8"))
        addresses[client] = client_address
        Thread(target=handle_client, args=(client,)).start()


global namesl
def handle_client(client):  # Takes client socket as argument.
    """Handles a single client connection."""
    while True:
        usernames = clients.values()
        received = client.recv(BUFSIZ).decode("utf8")
        print(received)
        message = received.split("\n")
        if message[0] == 'USERNAME':
            username = message[3]
            if username not in usernames:
                clients[client] = username
                client.send(bytes('True', "utf8"))
                print(username)
                #print(username)
                break
            else:
                client.send(bytes('False', "utf8"))
        elif message[0] == 'QUIT':
            print(clients[client],"USER QUITTED!")
            client.close()
            del addresses[client]
            break

    usernames = "-".join(list(clients.values()))
    global namesl
    namesl=usernames
    usernamelist_message = PROTOCOL+FROM+TO+str(usernames)
    broadcast(usernamelist_message)
    print("users: "+str(usernames))

    while True:
        msg = client.recv(BUFSIZ).decode("utf8")
        received = msg.split("\n")
        if "GENEL" in msg:
            generalChat(msg)
        if received[0] == "MESSAGE":
            send_to_username(msg)

        if received[0] == 'QUIT':
            print(clients[client],"USER QUITTED!")
            client.close()
            del addresses[client]
            break


def broadcast(msg):  # prefix is for name identification.
    """Broadcasts a message to all the clients."""
    #isimler donuyor
    print(msg)
    for sock in clients:
        try:
            sock.send(bytes(str(msg), "utf8"))
        except:
            print("probably connection out")

def send_to_username(message):
    received = message.split("\n")
    TO = received[2]
    key_list = list(clients.keys())
    val_list = list(clients.values())
    TO_CLİENT = key_list[val_list.index(TO)]
    TO_CLİENT.send(bytes(message, "utf8"))

def send_to_username2(message,name):
    TO = name
    key_list = list(clients.keys())
    val_list = list(clients.values())
    TO_CLİENT = key_list[val_list.index(TO)]
    TO_CLİENT.send(bytes(message, "utf8"))

def generalChat(msg):
     names = namesl.split("-")
     for i in range(len(names)):
        send_to_username2(msg,names[i])


clients = {}
addresses = {}


HOST = '127.0.0.1'
PORT = 5252
BUFSIZ = 1024
ADDR = (HOST, PORT)

SERVER = socket(AF_INET, SOCK_STREAM)
SERVER.bind(ADDR)

if __name__ == "__main__":
    try:
        SERVER.listen(5)
        print("Waiting for connection...")
        ACCEPT_THREAD = Thread(target=accept_incoming_connections)
        ACCEPT_THREAD.start()
        ACCEPT_THREAD.join()
        SERVER.close()
    except:
        SERVER.close()

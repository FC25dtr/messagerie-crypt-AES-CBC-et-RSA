import socket 
import threading
import json
dico_id = {}

def notifier_tous(message):
    for p in dico_id:
        if dico_id[p]['conn_reception'] is not None:
            try:
                dico_id[p]['conn_reception'].send(json.dumps({'type': 'notification', 'message': message}).encode())
            except:
                pass

def gerer_client(conn):
    data = conn.recv(65536).decode()
    pseudo, type_conn = data.split("|")
    
    if pseudo not in dico_id:
        dico_id[pseudo] = {'conn_envoi': None, 'conn_reception': None, 'cle_pub': None}


    if type_conn == "envoi":
        cle_pub = json.loads(conn.recv(65536).decode())  # ← seulement pour envoi
        dico_id[pseudo]['conn_envoi'] = conn
        dico_id[pseudo]['cle_pub'] = cle_pub
    else:
        dico_id[pseudo]['conn_reception'] = conn
        notifier_tous(f"{pseudo} a rejoint la messagerie")
    while True:
        try:
            raw = conn.recv(65536)
            data = json.loads(raw.decode())
            if data['type'] == 'get_cle':
                destinataire = data['destinataire']
                if destinataire in dico_id and dico_id[destinataire]['cle_pub'] is not None:
                    conn.send(json.dumps(dico_id[destinataire]['cle_pub']).encode())
                else:
                    conn.send(json.dumps("inconnu").encode())
            elif data['type'] == 'message':
                destinataire = data['destinataire']
                if destinataire in dico_id:
                    dico_id[destinataire]['conn_reception'].send(json.dumps(data).encode())
                else:
                    conn.send("destinataire inconnu".encode())
            elif data['type'] == 'get_liste':
                liste = [p for p in dico_id if dico_id[p]['cle_pub'] is not None]
                conn.send(json.dumps(liste).encode())
        except Exception as e:
            print(f"erreur {pseudo}: {e}")
            if pseudo in dico_id:
                del dico_id[pseudo]
            notifier_tous(f"{pseudo} a quitté la messagerie")
            conn.close()
            break
        
    

s = socket.socket()
s.bind(('localhost',5026))
s.listen(10)  
while(True):
    conn, addr = s.accept()  # attend une connexion
    thread = threading.Thread(target=gerer_client, args=(conn,))
    thread.start()  # lance un thread pour ce client

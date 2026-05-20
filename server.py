import socket  # module pour la communication réseau
import threading  # module pour gérer plusieurs clients en même temps
import json  # module pour sérialiser les données avant de les envoyer sur le réseau
dico_id = {}  # dictionnaire qui stocke tous les clients connectés avec leurs sockets et clé publique

def notifier_tous(message):  # envoie un message à tous les clients connectés
    for p in dico_id:  # on parcourt tous les pseudos dans le dictionnaire
        if dico_id[p]['conn_reception'] is not None:  # on vérifie que le client est bien connecté
            try:
                dico_id[p]['conn_reception'].send(json.dumps({'type': 'notification', 'message': message}).encode())  # on envoie la notification sur le socket de réception du client
            except:
                pass  # si l'envoi échoue on ignore, le client s'est probablement déconnecté

def gerer_client(conn):  # fonction lancée dans un thread pour chaque nouvelle connexion
    data = conn.recv(65536).decode()  # on reçoit le premier message qui contient pseudo et type de connexion
    pseudo, type_conn = data.split("|")  # on sépare le pseudo et le type avec le séparateur qu'on a défini côté client
    if pseudo not in dico_id:  # si c'est la première connexion de ce pseudo on crée son entrée dans le dico
        dico_id[pseudo] = {'conn_envoi': None, 'conn_reception': None, 'conn_dh': None, 'cle_pub': None}  # on initialise toutes les connexions à None
    if type_conn == "envoi":  # si c'est la connexion d'envoi on récupère aussi la clé publique RSA
        cle_pub = json.loads(conn.recv(65536).decode())  # on reçoit la clé publique RSA du client
        dico_id[pseudo]['conn_envoi'] = conn  # on stocke le socket d'envoi
        dico_id[pseudo]['cle_pub'] = cle_pub  # on stocke la clé publique pour pouvoir la donner aux autres
    elif type_conn == "dh":  # si c'est la connexion dédiée à Diffie-Hellman
        dico_id[pseudo]['conn_dh'] = conn  # on stocke le socket DH séparé pour éviter les conflits avec les autres sockets
    else:  # sinon c'est la connexion de réception
        dico_id[pseudo]['conn_reception'] = conn  # on stocke le socket de réception
        notifier_tous(f"{pseudo} a rejoint la messagerie")  # on prévient tout le monde qu'un nouveau client est là
    while True:  # boucle infinie qui écoute les messages de ce client
        try:
            raw = conn.recv(65536)  # on attend un message du client
            data = json.loads(raw.decode())  # on désérialise le JSON reçu
            if data['type'] == 'get_cle':  # le client demande la clé publique de quelqu'un
                destinataire = data['destinataire']  # on récupère le pseudo du destinataire demandé
                if destinataire in dico_id and dico_id[destinataire]['cle_pub'] is not None:  # on vérifie que le destinataire existe et a bien envoyé sa clé
                    conn.send(json.dumps(dico_id[destinataire]['cle_pub']).encode())  # on renvoie la clé publique du destinataire
                else:
                    conn.send(json.dumps("inconnu").encode())  # le destinataire n'est pas connecté ou pas encore enregistré
            elif data['type'] == 'message':  # le client envoie un message chiffré à quelqu'un
                destinataire = data['destinataire']  # on récupère le pseudo du destinataire
                if destinataire in dico_id:  # on vérifie que le destinataire est connecté
                    dico_id[destinataire]['conn_reception'].send(json.dumps(data).encode())  # on transmet le paquet chiffré au destinataire sans le lire
                else:
                    conn.send("destinataire inconnu".encode())  # le destinataire n'existe pas
            elif data['type'] == 'get_liste':  # le client veut la liste des utilisateurs connectés
                liste = [p for p in dico_id if dico_id[p]['cle_pub'] is not None]  # on ne renvoie que les pseudos dont la clé publique est disponible pour éviter les bugs d'envoi
                conn.send(json.dumps(liste).encode())  # on envoie la liste en JSON
            elif data['type'] == 'dh_init':  # Alice démarre un échange Diffie-Hellman avec Bob
                destinataire = data['destinataire']  # on récupère le pseudo de Bob
                if destinataire in dico_id and dico_id[destinataire]['conn_reception'] is not None:  # on vérifie que Bob est bien connecté
                    dico_id[destinataire]['conn_reception'].send(json.dumps(data).encode())  # on transmet le dh_init à Bob sur son socket de réception
                else:
                    conn.send(json.dumps("inconnu").encode())  # Bob n'est pas connecté
            elif data['type'] == 'dh_response':  # Bob répond à l'échange Diffie-Hellman
                destinataire = data['destinataire']  # on récupère le pseudo d'Alice
                if destinataire in dico_id and dico_id[destinataire]['conn_dh'] is not None:  # on vérifie qu'Alice a bien un socket DH
                    dico_id[destinataire]['conn_dh'].send(json.dumps(data).encode())  # on envoie la réponse DH sur le socket dédié d'Alice pour éviter les conflits
                else:
                    conn.send(json.dumps("inconnu").encode())  # Alice n'est pas connectée
        except Exception as e:
            print(f"erreur {pseudo}: {e}")  # on affiche l'erreur pour déboguer
            if pseudo in dico_id:
                del dico_id[pseudo]  # on supprime le client du dictionnaire
            notifier_tous(f"{pseudo} a quitté la messagerie")  # on prévient tout le monde de la déconnexion
            conn.close()  # on ferme la connexion proprement
            break  # on sort de la boucle et le thread se termine

s = socket.socket()  # on crée le socket du serveur
s.bind(('localhost', 5027))  # on attache le serveur à l'adresse localhost sur le port 5027
s.listen(10)  # on met le serveur en écoute, 10 connexions en attente maximum
while True:  # boucle infinie qui attend les nouvelles connexions
    conn, addr = s.accept()  # on attend qu'un client se connecte, conn est le socket de communication
    thread = threading.Thread(target=gerer_client, args=(conn,))  # on crée un thread dédié à ce client
    thread.start()  # on lance le thread, chaque client est géré indépendamment

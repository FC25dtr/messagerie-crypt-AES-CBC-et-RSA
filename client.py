import socket  # module pour la communication réseau
import threading  # pour gerer envoi et reception en meme temps
import json  # pour serialiser les données avant envoi
from messagerie import *  # toutes les fonctions crypto RSA AES HMAC signature
import time  # pour la pause au demarrage
from diffie_hellman import *  # fonctions pour l echange de clé DH

s_envoi = socket.socket()  # socket pour envoyer les messages et requetes
s_envoi.connect(('localhost', 5027))  # connexion au serveur
s_reception = socket.socket()  # socket pour recevoir les messages
s_reception.connect(('localhost', 5027))  # deuxieme connexion au serveur
historique = []  # stocke les messages de la session
s_dh = socket.socket()  # socket dédié a l echange DH pour eviter les conflits
s_dh.connect(('localhost', 5027))  # troisieme connexion au serveur
cles_dh_en_attente = {}  # dictionnaire qui stocke temporairement les clés AES dérivées de DH en attendant le message

def envoyer():  # appelée quand l utilisateur tape /msg
    destinataire = input("entrez le destinataire : ")
    a, A = generer_cle_dh()  # on genere notre clé privée DH et la valeur publique A = g^a mod p
    s_envoi.send(json.dumps({'type': 'dh_init', 'destinataire': destinataire, 'expediteur': pseudo, 'A': A}).encode())  # on envoie A au destinataire pour lancer l echange DH
    B = json.loads(s_dh.recv(65536).decode())['B']  # on attend la valeur publique B du destinataire sur le socket DH dédié
    cle_commune = calculer_cle_commune(a, B)  # on calcule g^(ab) mod p, identique des deux cotés
    cle_aes = hashlib.sha256(str(cle_commune).encode()).digest()[:16]  # on hache pour avoir exactement 16 octets
    cle_aes = ''.join(chr(octet) for octet in cle_aes)  # conversion en string pour notre AES
    iv = [[],[],[],[]]
    for i in range(4):
        for j in range(4):
            iv[i].append(random.randint(0,255))  # IV aléatoire 4x4, different a chaque message
    s_envoi.send(json.dumps({'type': 'get_cle', 'destinataire': destinataire}).encode())  # on demande la clé publique RSA du destinataire, encore nécessaire pour chiffrer la clé MAC et verifier la signature
    cle_dest_pub = json.loads(s_envoi.recv(65536).decode())  # on recoit la clé publique RSA
    if cle_dest_pub == "inconnu":
        print("Destinataire introuvable")
        return
    gen_cles(cle_aes)  # on initialise W avec la clé AES dérivée de DH
    message = input("Entrez votre message : ")
    signature = signer(ma_priv, message)  # on signe avec notre clé privée RSA pour prouver notre identité
    historique.append(f"moi -> {destinataire} : {message}")
    tab_chiffre = CBC_chiffrement_aes(message, iv)  # chiffrement AES-CBC avec la clé dérivée de DH
    cle_mac = ""
    for i in range(16):
        cle_mac += chr(random.randint(0, 255))  # clé MAC aléatoire distincte de la clé AES
    mac = hmac.new(cle_mac.encode(), str(tab_chiffre).encode(), hashlib.sha256).digest()  # empreinte HMAC pour garantir l intégrité
    cle_mac_chiffre = chiffrement_blocs(cle_dest_pub, cle_mac)  # on chiffre la clé MAC avec RSA du destinataire
    paquet = {'type': 'message', 'destinataire': destinataire, 'expediteur': pseudo, 'cle_mac': cle_mac_chiffre, 'iv': iv, 'tab': tab_chiffre, 'mac': list(mac), 'signature': signature, 'cle_pub_expediteur': ma_pub,}  # plus de cle_aes dans le paquet, elle vient de DH maintenant
    s_envoi.send(json.dumps(paquet).encode())  # envoi du paquet au serveur

def recevoir():  # tourne en permanence dans un thread séparé
    while True:
        try:
            data = s_reception.recv(65536)  # on attend un message
            if not data:  # connexion fermée
                break
            paquet = json.loads(data.decode())
            if paquet['type'] == 'notification':  # notification serveur connexion ou deconnexion
                print(f"*** {paquet['message']} ***")
            elif paquet['type'] == 'dh_init':  # quelqu un veut faire un echange DH avec nous
                b, B = generer_cle_dh()  # on genere notre clé privée b et la valeur publique B
                cle_commune_bob = calculer_cle_commune(b, paquet['A'])  # on calcule la clé commune avec le A recu
                cle_aes_bob = hashlib.sha256(str(cle_commune_bob).encode()).digest()[:16]  # on hache pour avoir 16 octets
                cle_aes_bob = ''.join(chr(octet) for octet in cle_aes_bob)  # conversion en string pour AES
                cles_dh_en_attente[paquet['expediteur']] = cle_aes_bob  # on stocke la clé en attendant que le message arrive
                s_dh.send(json.dumps({'type': 'dh_response', 'destinataire': paquet['expediteur'], 'B': B}).encode())  # on renvoie B via le socket DH dédié
            else:  # message chiffré normal
                cle_mac_chiffre = paquet['cle_mac']  # on récupere la clé MAC chiffrée par RSA
                cle_mac_recue = dechiffrement_blocs(ma_priv, cle_mac_chiffre)  # on déchiffre la clé MAC avec notre clé privée RSA
                iv = paquet['iv']
                tab_chiffre = paquet['tab']
                mac = bytes(paquet['mac'])  # on reconvertit en bytes car JSON l avait transformé en liste
                gen_cles(cles_dh_en_attente.pop(paquet['expediteur']))  # on récupere la clé AES dérivée de DH et on initialise W, pop la supprime du dico apres usage c est le principe du forward secrecy
                mac_bob = hmac.new(cle_mac_recue.encode(), str(tab_chiffre).encode(), hashlib.sha256).digest()  # on recalcule le HMAC pour verifier l intégrité
                if hmac.compare_digest(mac, mac_bob):  # si les deux HMAC sont identiques le message n a pas été modifié
                    message_dechiffre = CBC_dechiffrement_aes(tab_chiffre, iv)  # on déchiffre avec la clé DH
                    cle_pub_expediteur = paquet['cle_pub_expediteur']
                    signature = paquet['signature']
                    if verifier(cle_pub_expediteur, signature, message_dechiffre):  # on vérifie que le message vient bien de l expéditeur prétendu
                        print(f"{paquet['expediteur']} (authentifié) : {message_dechiffre}")
                        historique.append(f"{paquet['expediteur']} : {message_dechiffre}")
                    else:
                        print("signature invalide — message suspect")
                else:
                    print("message corrompu")
        except:
            print("déconnécté du server ")
            break

ma_pub, ma_priv, n = gencle_RSAA()  # generation des clés RSA 2048 bits au demarrage

pseudo = input("Ton pseudo : ")

s_envoi.send((pseudo + "|envoi").encode())  # on s identifie sur le socket d envoi
s_reception.send((pseudo + "|reception").encode())  # on s identifie sur le socket de reception
s_envoi.send(json.dumps(ma_pub).encode())  # on envoie notre clé publique RSA au serveur

s_dh.send((pseudo + "|dh").encode())  # on s identifie sur le socket DH

thread_reception = threading.Thread(target=recevoir)  # on crée le thread de reception
thread_reception.start()  # on le lance en paralele
time.sleep(2)  # on attend que tout s initialise
print("initialisation terminé bienvenue")
while True:
    try:
        commande = input("")  # on attend une commande
        if commande == "/liste":
            s_envoi.send(json.dumps({'type': 'get_liste'}).encode())  # on demande la liste au serveur
            liste = json.loads(s_envoi.recv(65536).decode())
            print("Connectés :", liste)
        elif commande == "/msg":
            envoyer()
        elif commande == "/quitter":
            s_envoi.close()  # on ferme les sockets proprement
            s_reception.close()
            break
        elif commande == "/historique":
            if historique:
                for msg in historique:
                    print(msg)
            else:
                print("Aucun message")
        elif commande == "/aide":
            print("Commandes disponibles :")
            print("/liste      voir les utilisateurs connectés")
            print("/msg        envoyer un message")
            print("/historique  voir les messages reçus")
            print("/aide       afficher cette aide")
            print("/quitter    quitter la messagerie")
        else:
            print("Commandes : /liste  /msg  /quitter")  # commande inconnue
    except:
        print("Déconnecté du serveur")
        break

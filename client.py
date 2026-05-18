import socket
import threading
import json
from messagerie import *
import time

s_envoi = socket.socket()
s_envoi.connect(('localhost', 5026))
s_reception = socket.socket()
s_reception.connect(('localhost', 5026))
historique = []

def envoyer():
    destinataire = input("entrez le destinataire : ")
    cle_aes = ""
    for i in range(16):
        cle_aes += chr(random.randint(0,255))
    iv = [[],[],[],[]]
    for i in range(4):
        for j in range(4):
            iv[i].append(random.randint(0,255))
    
    s_envoi.send(json.dumps({'type': 'get_cle', 'destinataire': destinataire}).encode())
    cle_dest_pub = json.loads(s_envoi.recv(65536).decode())
    if cle_dest_pub == "inconnu":
        print("Destinataire introuvable")
        return
    
    cle_aes_chiffre = chiffrement_blocs(cle_dest_pub,cle_aes)
    gen_cles(cle_aes)
    message = input("Entrez votre message : ")
    signature = signer(ma_priv, message)
    historique.append(f"moi -> {destinataire} : {message}")
    tab_chiffre = CBC_chiffrement_aes(message,iv)

    cle_mac = ""
    for i in range(16):
        cle_mac += chr(random.randint(0, 255))
    mac = hmac.new(cle_mac.encode(), str(tab_chiffre).encode(), hashlib.sha256).digest() #permet de verifier l'integrité du message 
    cle_mac_chiffre = chiffrement_blocs(cle_dest_pub, cle_mac)
    
    paquet = {'type': 'message','destinataire': destinataire,'expediteur': pseudo,'cle_aes': cle_aes_chiffre,'cle_mac': cle_mac_chiffre,'iv': iv,'tab': tab_chiffre,'mac': list(mac),'signature': signature,'cle_pub_expediteur': ma_pub,}
    s_envoi.send(json.dumps(paquet).encode())
    
def recevoir():
    while True:
        try: 
            data = s_reception.recv(65536)
            if not data:  # connexion fermée proprement
                break
            paquet = json.loads(data.decode())
            if paquet['type'] == 'notification':
                print(f"*** {paquet['message']} ***")
            else:
                cle_aes_chiffre = paquet['cle_aes']
                cle_mac_chiffre = paquet['cle_mac']
                cle_mac_recue = dechiffrement_blocs(ma_priv, cle_mac_chiffre)
                iv = paquet['iv']
                tab_chiffre = paquet['tab']
                mac = bytes(paquet['mac'])
    
                cle_aes_recue = dechiffrement_blocs(ma_priv, cle_aes_chiffre)
    
                gen_cles(cle_aes_recue)
                mac_bob = hmac.new(cle_mac_recue.encode(), str(tab_chiffre).encode(), hashlib.sha256).digest()
    
                if hmac.compare_digest(mac, mac_bob):
                    message_dechiffre = CBC_dechiffrement_aes(tab_chiffre, iv)
                    cle_pub_expediteur = paquet['cle_pub_expediteur']
                    signature = paquet['signature']
                    if verifier(cle_pub_expediteur, signature, message_dechiffre):
                        print(f"{paquet['expediteur']} (authentifié) : {message_dechiffre}")
                        historique.append(f"{paquet['expediteur']} : {message_dechiffre}")
                    else:
                        print("signature invalide — message suspect")
                else:
                    print("message corrompu") 
        except:
            print("déconnécté du server ")
            break
        
ma_pub, ma_priv, n = gencle_RSAA()

pseudo = input("Ton pseudo : ")

s_envoi.send((pseudo + "|envoi").encode())
s_reception.send((pseudo + "|reception").encode())
s_envoi.send(json.dumps(ma_pub).encode())



thread_reception = threading.Thread(target=recevoir)
thread_reception.start()
time.sleep(2)
print("initialisation terminé bienvenue")
while True:
    try:
        commande = input("")
        if commande == "/liste":
            s_envoi.send(json.dumps({'type': 'get_liste'}).encode())
            liste = json.loads(s_envoi.recv(65536).decode())
            print("Connectés :", liste)
        elif commande == "/msg":
            envoyer()
        elif commande == "/quitter":
            s_envoi.close()
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
            print("Commandes : /liste  /msg  /quitter")
    except:
        print("Déconnecté du serveur")
        break


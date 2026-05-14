import socket
from messagerie import *
import json

s = socket.socket()
s.connect(('localhost', 5001))
role = input("Qui es-tu ? (alice/bob) : ")

if role == "bob":
    bob_pub,bob_priv,n = gencle_RSAA()
    s.send(json.dumps(bob_pub).encode())
    
    paquet = json.loads(s.recv(65536).decode())
    cle_aes_chiffre = paquet['cle_aes']
    cle_mac_chiffre = paquet['cle_mac']
    cle_mac_recue = dechiffrement_blocs(bob_priv, cle_mac_chiffre)
    iv = paquet['iv']
    tab_chiffre = paquet['tab']
    mac = bytes(paquet['mac'])
    
    cle_aes_recue = dechiffrement_blocs(bob_priv, cle_aes_chiffre)
    
    gen_cles(cle_aes_recue)
    mac_bob = hmac.new(cle_mac_recue.encode(), str(tab_chiffre).encode(), hashlib.sha256).digest()
    
    if hmac.compare_digest(mac, mac_bob):
        message_dechiffre = CBC_dechiffrement_aes(tab_chiffre, iv)
        print(message_dechiffre)
    else:
        print("message corrompu")   
        
elif role == "alice":
    cle_bob_pub = json.loads(s.recv(65536).decode())
    cle_aes = ""
    for i in range(16):
        cle_aes += chr(random.randint(0,255))

    iv = [[],[],[],[]]
    for i in range(4):
        for j in range(4):
            iv[i].append(random.randint(0,255))
        
    cle_aes_chiffre = chiffrement_blocs(cle_bob_pub,cle_aes)
    gen_cles(cle_aes)
    message = input("Entrez votre message : ")
    tab_chiffre = CBC_chiffrement_aes(message,iv)

    cle_mac = ""
    for i in range(16):
        cle_mac += chr(random.randint(0, 255))
    mac = hmac.new(cle_mac.encode(), str(tab_chiffre).encode(), hashlib.sha256).digest() #permet de verifier l'integrité du message 
    cle_mac_chiffre = chiffrement_blocs(cle_bob_pub, cle_mac)
    
    paquet = {'cle_aes': cle_aes_chiffre,'cle_mac': cle_mac_chiffre,'iv': iv,'tab': tab_chiffre,'mac': list(mac)
    }
    s.send(json.dumps(paquet).encode())
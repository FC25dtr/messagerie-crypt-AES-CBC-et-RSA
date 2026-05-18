from Projet_RSA.gencleRSA import *
from Projet_RSA.math_utile import *
from chiffrement_AES.AES_python import *
import random
import hmac
import hashlib


bob_pub,bob_priv,n = gencle_RSAA()

def signer(cle_privee, message):
    n, d = cle_privee
    hash_message = hashlib.sha256(message.encode()).hexdigest()
    hash_entier = message_vers_entier(hash_message)
    signature = math_utile.Exponentiation(hash_entier, d, n)
    return signature

def verifier(cle_publique_alice, signature, message):
    n, e = cle_publique_alice
    hash_entier = math_utile.Exponentiation(signature, e, n)
    hash_recu = entier_vers_texte(hash_entier)
    hash_message = hashlib.sha256(message.encode()).hexdigest()
    return hash_recu == hash_message

cle_aes = ""
for i in range(16):
    cle_aes += chr(random.randint(0,255))

iv = [[],[],[],[]]
for i in range(4):
    for j in range(4):
        iv[i].append(random.randint(0,255))
        
cle_aes_chiffre = chiffrement_blocs(bob_pub,cle_aes)

gen_cles(cle_aes)
message = "Bonjour Bob !"
tab_chiffre = CBC_chiffrement_aes(message,iv)

cle_mac = ""
for i in range(16):
    cle_mac += chr(random.randint(0, 255))
mac = hmac.new(cle_mac.encode(), str(tab_chiffre).encode(), hashlib.sha256).digest() #permet de verifier l'integrité du message 

cle_aes_recue = dechiffrement_blocs(bob_priv, cle_aes_chiffre)
gen_cles(cle_aes_recue)

mac_bob = hmac.new(cle_mac.encode(), str(tab_chiffre).encode(), hashlib.sha256).digest()
if hmac.compare_digest(mac, mac_bob):
    message_dechiffre = CBC_dechiffrement_aes(tab_chiffre, iv)
    print(message_dechiffre)
else:
    print("message corrompu")
    





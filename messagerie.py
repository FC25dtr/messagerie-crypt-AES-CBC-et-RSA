from Projet_RSA.gencleRSA import *  # on importe toutes les fonctions RSA, chiffrement_blocs, dechiffrement_blocs, gencle_RSAA etc
from Projet_RSA.math_utile import *  # on importe les fonctions mathématiques, Exponentiation, pgcd, inverse modulaire
from chiffrement_AES.AES_python import *  # on importe toutes les fonctions AES et CBC
import random  # pour générer les clés et IV aléatoires
import hmac  # pour calculer le HMAC et vérifier l intégrité des messages
import hashlib  # pour SHA256, utilisé dans la signature et la dérivation de clé

def signer(cle_privee, message):  # signe un message avec la clé privée RSA pour prouver son identité
    n, d = cle_privee  # on extrait n et d de la clé privée
    hash_message = hashlib.sha256(message.encode()).hexdigest()  # on calcule l empreinte SHA256 du message en hexadecimal
    hash_entier = message_vers_entier(hash_message)  # on convertit le hash en entier pour pouvoir l exposer avec RSA
    signature = math_utile.Exponentiation(hash_entier, d, n)  # on chiffre le hash avec la clé privée, c est ca la signature
    return signature

def verifier(cle_publique_alice, signature, message):  # vérifie qu un message vient bien de celui qui pretend l avoir envoyé
    n, e = cle_publique_alice  # on extrait n et e de la clé publique
    hash_entier = math_utile.Exponentiation(signature, e, n)  # on dechiffre la signature avec la clé publique pour retrouver le hash
    hash_recu = entier_vers_texte(hash_entier)  # on reconvertit l entier en string hexadecimale
    hash_message = hashlib.sha256(message.encode()).hexdigest()  # on recalcule le hash du message recu
    return hash_recu == hash_message  # si les deux hash sont identiques la signature est valide et le message est authentique

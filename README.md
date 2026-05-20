# Messagerie Chiffrée — RSA + AES-CBC + DH

Une messagerie chiffrée de bout en bout implémentée from scratch en Python, sans bibliothèque cryptographique externe. RSA, AES-128 et l'échange de clé Diffie-Hellman sont entièrement codés à la main.

---

## Structure du projet

```
Projet/
├── Projet_RSA/
│   ├── __init__.py
│   ├── gencleRSA.py         # Génération de clés RSA, chiffrement/déchiffrement par blocs, signature
│   └── math_utile.py        # PGCD, inverse modulaire, exponentiation rapide
├── chiffrement_AES/
│   ├── __init__.py
│   └── AES_python.py        # AES-128 complet avec mode CBC
├── diffie_hellman.py         # Paramètres DH-2048 et fonctions d'échange de clé éphémère
├── messagerie.py             # Fonctions HMAC et signature, colle entre RSA et AES
├── serveur.py                # Relais réseau multi-utilisateurs, ne déchiffre rien
└── client.py                 # Interface utilisateur avec commandes
```

---

## Comment ça marche

### Le protocole

La messagerie repose sur un chiffrement hybride avec Perfect Forward Secrecy. À chaque message la clé de chiffrement est différente et éphémère — elle ne passe jamais sur le réseau et n'existe plus après le message.

À chaque message envoyé :

1. L'expéditeur initie un échange Diffie-Hellman — il génère une valeur secrète `a` et envoie `A = g^a mod p` au destinataire
2. Le destinataire génère sa propre valeur secrète `b` et renvoie `B = g^b mod p`
3. Les deux calculent indépendamment la même clé commune `g^(ab) mod p` sans jamais se l'envoyer
4. Cette clé est hachée en SHA-256 pour obtenir la clé AES de 16 octets
5. L'expéditeur signe le message avec sa clé privée RSA pour prouver son identité
6. Il chiffre le message avec AES-128 en mode CBC
7. Il calcule une empreinte HMAC-SHA256 du message chiffré avec une clé MAC chiffrée par RSA
8. Il envoie le tout au serveur qui relaie au destinataire
9. Le destinataire vérifie le HMAC — si invalide il rejette le message
10. Il déchiffre la clé MAC avec sa clé privée RSA
11. Il recalcule la clé AES depuis sa valeur DH stockée en mémoire
12. Il vérifie la signature pour authentifier l'expéditeur
13. Il déchiffre le message avec AES-CBC

```
Expéditeur                        Serveur                   Destinataire
     |                               |                            |
     |  dh_init { A = g^a mod p }    |      dh_init              |
     | ----------------------------> | -------------------------> |
     |                               |                            |
     |              dh_response { B = g^b mod p }                |
     | <--------------------------------------------------------- |
     |                               |                            |
     |  { cle_mac_chiffree_RSA,      |                            |
     |    iv,                        |        même paquet         |
     |    message_chiffre_AES,       | -------------------------> |
     |    hmac,                      |                            |
     |    signature,                 |                            |
     |    cle_pub_expediteur }       |                            |
     | ----------------------------> |                            |
```

La clé AES ne transite jamais sur le réseau. Le serveur voit passer `A` et `B` en clair mais sans `a` ou `b` il lui est mathématiquement impossible de calculer `g^(ab) mod p`.

---

## RSA — Implémenté from scratch

**Fichier :** `Projet_RSA/gencleRSA.py`

RSA est un algorithme de chiffrement asymétrique — ce qui est chiffré avec la clé publique ne peut être déchiffré qu'avec la clé privée correspondante.

### Génération des clés

- Génération de deux grands nombres premiers p et q sur 1024 bits chacun via le test de Miller-Rabin avec 7 témoins — le module n fait donc 2048 bits
- Calcul du module `n = p * q`
- Exposant public fixé à `e = 65537` — standard industriel, petit et premier
- Exposant privé d calculé via l'algorithme d'Euclide étendu

### Chiffrement par blocs

RSA ne peut chiffrer qu'un entier inférieur à n. Pour les messages longs, le texte est découpé en blocs, chaque bloc est converti en entier puis chiffré séparément. Dans ce protocole RSA sert uniquement à chiffrer la clé MAC et à signer les messages — pas à chiffrer les messages eux-mêmes.

### Signature numérique

La signature permet de vérifier qu'un message vient bien de celui qui prétend l'avoir envoyé. C'est l'inverse du chiffrement — on signe avec la clé privée, on vérifie avec la clé publique.

1. L'expéditeur calcule SHA-256 du message
2. Il chiffre ce hash avec sa clé privée — c'est la signature
3. Le destinataire déchiffre la signature avec la clé publique de l'expéditeur
4. Il compare le hash obtenu avec celui qu'il calcule lui-même
5. S'ils correspondent, le message est authentifié

---

## Diffie-Hellman — Perfect Forward Secrecy

**Fichier :** `diffie_hellman.py`

Diffie-Hellman permet à deux personnes de construire une clé secrète commune sans jamais se l'envoyer. Même si un attaquant enregistre tous les messages aujourd'hui et casse la clé RSA dans 10 ans, il ne pourra pas déchiffrer les anciens messages — les valeurs `a` et `b` n'ont jamais existé en dehors de la mémoire vive et n'existent plus.

Les paramètres utilisés sont ceux du groupe DH-2048 défini par le RFC 3526 — un nombre premier de 2048 bits reconnu et standardisé, le même générateur `g = 2`.

Chaque session génère de nouvelles valeurs `a` et `b` — c'est pour ça qu'on parle de clés éphémères.

---

## AES-128 — Implémenté from scratch

**Fichier :** `chiffrement_AES/AES_python.py`

AES est un algorithme de chiffrement symétrique — la même clé sert à chiffrer et à déchiffrer. C'est lui qui chiffre le contenu des messages.

### Ce qui est implémenté

- Corps de Galois GF(2^8) construit avec tables de logarithmes discrets
- SubBytes via l'inverse dans GF(2^8) suivi d'une transformation affine — c'est la vraie spécification AES, pas une approximation
- ShiftRows, MixColumns, AddRoundKey
- KeySchedule complet pour générer les 11 sous-clés depuis la clé principale
- Toutes les opérations inverses pour le déchiffrement

### Mode CBC (Cipher Block Chaining)

Le mode CBC XOR chaque bloc avec le bloc chiffré précédent avant de le chiffrer. Un IV aléatoire est généré à chaque message pour garantir que deux messages identiques donnent deux chiffrés différents.

```
message → padding → blocs → XOR avec IV/bloc précédent → AES → blocs chiffrés
```

---

## Intégrité — HMAC-SHA256

Sans vérification d'intégrité, un attaquant positionné entre les deux interlocuteurs pourrait modifier les octets du message chiffré sans que personne s'en rende compte.

Le HMAC fonctionne comme un sceau : l'expéditeur calcule une empreinte du message chiffré avec une clé secrète, et le destinataire recalcule cette empreinte à la réception. Si elles diffèrent, le message est rejeté immédiatement.

La clé MAC est distincte de la clé AES et transmise chiffrée par RSA.

---

## Architecture réseau

Le serveur est un relais neutre qui gère plusieurs utilisateurs simultanément via des threads. Il ne connaît pas les clés, ne déchiffre rien et ne stocke rien. Il maintient un dictionnaire des utilisateurs connectés avec leurs clés publiques RSA et leurs sockets, et route les messages vers le bon destinataire.

Chaque utilisateur ouvre trois connexions au serveur — une pour envoyer, une pour recevoir, une dédiée à l'échange Diffie-Hellman — ce qui évite les conflits entre les threads d'envoi et de réception.

Les données sont sérialisées en JSON avant d'être envoyées sur le socket TCP.

---

## Commandes disponibles

```
/liste       — afficher les utilisateurs connectés
/msg         — envoyer un message à un utilisateur
/historique  — consulter les messages envoyés et reçus
/aide        — afficher la liste des commandes
/quitter     — se déconnecter proprement
```

---

## Lancement

### Prérequis

- Python 3.10 ou supérieur
- Aucune bibliothèque externe — uniquement la bibliothèque standard Python

### Démarrage

Ouvre deux terminaux minimum dans le dossier du projet.

**Terminal 1 — Serveur :**
```bash
python serveur.py
```

**Autres terminaux — Clients :**
```bash
python client.py
# Ton pseudo : alice
```

Chaque utilisateur choisit un pseudo à la connexion. La génération des clés RSA 2048 bits se fait automatiquement au démarrage.

---

## Limites connues

- Taille des paquets limitée par le buffer réseau — les très longs messages pourraient être tronqués
- Pas de persistance — l'historique est perdu à la déconnexion
- Pas de chiffrement de la communication avec le serveur pour l'échange des pseudos et clés publiques au démarrage

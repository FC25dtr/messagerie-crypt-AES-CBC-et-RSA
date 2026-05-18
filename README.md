# Messagerie Chiffrée — RSA + AES-CBC

Une messagerie chiffrée de bout en bout implémentée from scratch en Python, sans bibliothèque cryptographique externe. RSA et AES-128 sont entièrement codés à la main.

---

## Structure du projet

```
Projet/
├── Projet_RSA/
│   ├── __init__.py
│   ├── gencleRSA.py         # Génération de clés RSA, chiffrement/déchiffrement par blocs
│   └── math_utile.py        # PGCD, inverse modulaire, exponentiation rapide
├── chiffrement_AES/
│   ├── __init__.py
│   └── AES_python.py        # AES-128 complet avec mode CBC
├── diffie_hellman.py         # Paramètres DH-2048 et fonctions d'échange de clé (en cours)
├── messagerie.py             # Protocole complet : RSA + AES + HMAC + signature
├── serveur.py                # Relais réseau multi-utilisateurs (ne déchiffre rien)
└── client.py                 # Interface utilisateur avec commandes
```

---

## Comment ça marche

### Le protocole

La messagerie repose sur un chiffrement hybride — une technique standard utilisée par TLS, Signal ou PGP. RSA est solide mais lent, AES est rapide mais nécessite un échange de clé sécurisé. On combine les deux.

À chaque message envoyé :

1. L'expéditeur génère une clé AES et une clé MAC aléatoires
2. Il chiffre ces deux clés avec la clé publique RSA du destinataire
3. Il signe le message avec sa clé privée RSA pour prouver son identité
4. Il chiffre le message avec AES-128 en mode CBC
5. Il calcule une empreinte HMAC-SHA256 du message chiffré
6. Il envoie le tout au serveur qui relaie au destinataire
7. Le destinataire vérifie le HMAC — si invalide il rejette le message
8. Il déchiffre les clés avec sa clé privée RSA
9. Il vérifie la signature pour authentifier l'expéditeur
10. Il déchiffre le message avec AES-CBC

```
Expéditeur                   Serveur                   Destinataire
     |                          |                            |
     |  { cle_aes_chiffree,     |                            |
     |    cle_mac_chiffree,     |        même paquet         |
     |    iv,                   | -------------------------> |
     |    message_chiffre_AES,  |                            |
     |    hmac,                 |                            |
     |    signature,            |                            |
     |    cle_pub_expediteur }  |                            |
     | -----------------------> |                            |
```

---

## RSA — Implémenté from scratch

**Fichier :** `Projet_RSA/gencleRSA.py`

RSA est un algorithme de chiffrement asymétrique — ce qui est chiffré avec la clé publique ne peut être déchiffré qu'avec la clé privée correspondante. C'est ce qui permet d'envoyer une clé secrète sans que personne d'autre puisse la lire.

### Génération des clés

- Génération de deux grands nombres premiers p et q sur 1024 bits chacun via le test de Miller-Rabin avec 7 témoins — le module n fait donc 2048 bits
- Calcul du module `n = p * q`
- Exposant public fixé à `e = 65537` — standard industriel, petit et premier
- Exposant privé d calculé via l'algorithme d'Euclide étendu

### Chiffrement par blocs

RSA ne peut chiffrer qu'un entier inférieur à n. Pour les messages longs, le texte est découpé en blocs, chaque bloc est converti en entier puis chiffré séparément.

```
message → découpage en blocs → conversion entier → chiffrement RSA → liste de blocs chiffrés
```

### Signature numérique

La signature permet de vérifier qu'un message vient bien de celui qui prétend l'avoir envoyé. C'est l'inverse du chiffrement — on signe avec la clé privée, on vérifie avec la clé publique.

1. L'expéditeur calcule SHA-256 du message
2. Il chiffre ce hash avec sa clé privée — c'est la signature
3. Le destinataire déchiffre la signature avec la clé publique de l'expéditeur
4. Il compare le hash obtenu avec celui qu'il calcule lui-même
5. S'ils correspondent, le message est authentifié

---

## AES-128 — Implémenté from scratch

**Fichier :** `chiffrement_AES/AES_python.py`

AES est un algorithme de chiffrement symétrique — la même clé sert à chiffrer et à déchiffrer. Il est très rapide et c'est lui qui chiffre le contenu des messages.

### Ce qui est implémenté

- Corps de Galois GF(2^8) construit avec tables de logarithmes discrets
- SubBytes via l'inverse dans GF(2^8) suivi d'une transformation affine — c'est la vraie spécification AES, pas une approximation
- ShiftRows, MixColumns, AddRoundKey
- KeySchedule complet pour générer les 11 sous-clés depuis la clé principale
- Toutes les opérations inverses pour le déchiffrement

### Mode CBC (Cipher Block Chaining)

Sans mode d'opération, AES chiffre chaque bloc indépendamment — un même bloc de texte donnera toujours le même bloc chiffré, ce qui laisse fuiter des informations. Le mode CBC résout ça en XORant chaque bloc avec le bloc chiffré précédent avant de le chiffrer. Un IV aléatoire est généré à chaque message pour garantir que deux messages identiques donnent deux chiffrés différents.

```
message → padding → blocs → XOR avec IV/bloc précédent → AES → blocs chiffrés
```

---

## Intégrité — HMAC-SHA256

Le chiffrement seul ne suffit pas. Sans vérification d'intégrité, un attaquant positionné entre les deux interlocuteurs pourrait modifier les octets du message chiffré — le destinataire déchiffrerait alors un message corrompu sans s'en rendre compte.

Le HMAC fonctionne comme un sceau : l'expéditeur calcule une empreinte du message chiffré avec une clé secrète, et le destinataire recalcule cette empreinte à la réception. Si elles diffèrent, le message a été modifié et il est rejeté immédiatement.

La clé MAC est distincte de la clé AES et transmise chiffrée par RSA comme elle.

---

## Architecture réseau

Le serveur est un relais neutre qui gère plusieurs utilisateurs simultanément via des threads. Il ne connaît pas les clés, ne déchiffre rien et ne stocke rien. Il maintient un dictionnaire des utilisateurs connectés avec leurs clés publiques et leurs sockets, et route les messages vers le bon destinataire.

Chaque utilisateur ouvre deux connexions au serveur — une pour envoyer, une pour recevoir — ce qui permet d'envoyer et de recevoir en même temps sans blocage.

Les données sont sérialisées en JSON avant d'être envoyées sur le socket TCP.

---

## Commandes disponibles

Une fois connecté, l'interface fonctionne avec des commandes :

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

Chaque utilisateur choisit un pseudo à la connexion. La génération des clés RSA se fait automatiquement au démarrage.

---

## En cours de développement

### Perfect Forward Secrecy via Diffie-Hellman

Le fichier `diffie_hellman.py` contient les bases d'un échange de clé Diffie-Hellman en cours d'apprentissage et d'implémentation.

L'idée est que même si la clé privée RSA d'un utilisateur est compromise un jour, les messages passés restent protégés — chaque session aurait eu une clé éphémère différente générée via DH, qui n'existe plus après la session.

Le protocole DH repose sur la difficulté du logarithme discret : deux parties peuvent calculer une clé commune `g^(ab) mod p` sans jamais se l'envoyer directement, en échangeant uniquement `g^a mod p` et `g^b mod p` en public.

Les paramètres utilisés sont ceux du groupe DH-2048 défini par le RFC 3526 — un nombre premier de 2048 bits reconnu et standardisé.

---

## Limites connues

- Perfect Forward Secrecy pas encore intégré dans le protocole
- Taille des paquets limitée par le buffer réseau — les très longs messages pourraient être tronqués
- Pas de persistance — l'historique est perdu à la déconnexion

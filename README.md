# Messagerie Chiffrée — RSA + AES-CBC
 
Une messagerie chiffrée de bout en bout implémentée from scratch en Python, sans bibliothèque cryptographique externe. RSA et AES-128 sont entièrement codés à la main.
 
---
 
## Structure du projet
 
```
Projet/
├── Projet_RSA/
│   ├── __init__.py
│   ├── gencleRSA.py       # Génération de clés RSA, chiffrement/déchiffrement par blocs
│   └── math_utile.py      # PGCD, inverse modulaire, exponentiation rapide
├── chiffrement_AES/
│   ├── __init__.py
│   └── AES_python.py      # AES-128 complet avec mode CBC
├── messagerie.py           # Protocole complet : RSA + AES + HMAC
├── serveur.py              # Relais réseau (ne déchiffre rien)
└── client.py               # Interface Alice / Bob
```
 
---
 
## Comment ça marche
 
### Le protocole
 
La messagerie repose sur un chiffrement hybride — une technique standard utilisée par TLS, Signal ou PGP. L'idée est simple : RSA est solide mais lent, AES est rapide mais nécessite un échange de clé sécurisé. On combine les deux.
 
1. Bob génère une paire de clés RSA (clé publique / clé privée)
2. Alice génère une clé AES et une clé MAC aléatoires
3. Alice chiffre ces deux clés avec la clé publique RSA de Bob
4. Alice chiffre le message avec AES-128 en mode CBC
5. Alice calcule une empreinte HMAC-SHA256 du message chiffré
6. Alice envoie le tout au serveur qui relaie à Bob
7. Bob déchiffre les clés avec sa clé privée RSA
8. Bob vérifie le HMAC — si invalide il rejette le message sans même essayer de déchiffrer
9. Bob déchiffre le message avec AES-CBC
```
Alice                        Serveur                        Bob
  |                             |                             |
  |    clé publique Bob         |      clé publique Bob       |
  | <-------------------------- | <-------------------------- |
  |                             |                             |
  |  { cle_aes_chiffree_RSA,   |                             |
  |    cle_mac_chiffree_RSA,   |                             |
  |    iv,                     |                             |
  |    message_chiffre_AES,    |   même paquet               |
  |    hmac }                  |  -------------------------> |
  | -------------------------> |                             |
```
 
---
 
## RSA — Implémenté from scratch
 
**Fichier :** `Projet_RSA/gencleRSA.py`
 
RSA est un algorithme de chiffrement asymétrique — ce qui est chiffré avec la clé publique ne peut être déchiffré qu'avec la clé privée correspondante. C'est ce qui permet à Alice d'envoyer une clé secrète à Bob sans qu'ils se soient jamais rencontrés.
 
### Génération des clés
 
- Génération de deux grands nombres premiers p et q sur 512 bits via le test de primalité de Miller-Rabin avec 7 témoins
- Calcul du module `n = p * q`
- Exposant public fixé à `e = 65537` — c'est le standard industriel, petit et premier, ce qui rend le chiffrement rapide
- Exposant privé d calculé via l'algorithme d'Euclide étendu
### Chiffrement par blocs
 
RSA ne peut chiffrer qu'un entier inférieur à n. Pour les messages longs, le texte est découpé en blocs, chaque bloc est converti en entier puis chiffré séparément.
 
```
message → découpage en blocs → conversion entier → chiffrement RSA → liste de blocs chiffrés
```
 
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
 
Le chiffrement seul ne suffit pas. Sans vérification d'intégrité, un attaquant positionné entre Alice et Bob pourrait modifier les octets du message chiffré — Bob déchiffrerait alors un message corrompu sans s'en rendre compte.
 
Le HMAC fonctionne comme un sceau : Alice calcule une empreinte du message chiffré avec une clé secrète, et Bob recalcule cette empreinte à la réception. Si elles diffèrent, le message a été modifié et Bob le rejette immédiatement sans tenter de le déchiffrer.
 
La clé MAC est distincte de la clé AES et transmise chiffrée par RSA comme elle.
 
---
 
## Architecture réseau
 
Le serveur est un relais neutre. Il ne connaît pas les clés, ne déchiffre rien et ne stocke rien. Son seul rôle est de recevoir la clé publique de Bob, de la transmettre à Alice, puis de relayer le paquet chiffré d'Alice vers Bob.
 
Les données sont sérialisées en JSON avant d'être envoyées sur le socket TCP, ce qui permet de transporter des structures Python sous forme de bytes.
 
---
 
## Lancement
 
### Prérequis
 
- Python 3.10 ou supérieur
- Aucune bibliothèque externe — uniquement la bibliothèque standard Python
### Démarrage
 
Ouvre trois terminaux dans le dossier du projet et lance les commandes dans cet ordre.
 
**Terminal 1 — Serveur :**
```bash
python serveur.py
```
 
**Terminal 2 — Bob (destinataire) :**
```bash
python client.py
# Qui es-tu ? (alice/bob) : bob
```
 
**Terminal 3 — Alice (expéditeur) :**
```bash
python client.py
# Qui es-tu ? (alice/bob) : alice
# Entrez votre message : Bonjour Bob !
```
 
Lance toujours Bob avant Alice — le serveur attend la connexion de Bob en premier.
 
---
 
## Limites connues
 
- Clés RSA de 512 bits — suffisant pour un projet pédagogique, mais en production le minimum est 2048 bits
- Pas d'authentification de l'expéditeur — Alice ne prouve pas son identité à Bob, n'importe qui pourrait se connecter à sa place (une signature numérique RSA résoudrait ça)
- Un seul message par session — il faudrait une boucle pour une vraie conversation
 

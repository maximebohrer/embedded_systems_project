Projet de systèmes embarqués
============================

Raspberry Pi
------------

Le fichier tracking.py tourne sur le Raspberry Pi et se charge de la détection d'objet dans l'image de la caméra et de l'envoi de sa position à l'ESP32.

### Traitement d'images

Le traitement de l'image est réalisé grâce à OpenCV et sa fonction `matchTemplate` qui sert à détecter une image donnée (template) au sein d'une image plus grande. Cet algorithme calcule un score de ressemblance pour chaque pixel. Le script garde la position ayant le score le plus élevé, et determine si le template a effectivement été trouvé en le comparant à un seuil (`sensibility` dans le code).

Au lancement du script, l'utilisateur doit sélectionner le template à suivre dans l'image. Ce template est ensuite détecté et suivi. Afin de réduire la durée du traitement, la vitesse et l'accélération de l'objet à suivre sont calculées (`v_x`, `v_y`, `a_x`, `a_y` dans le code), afin d'estimer sa position suivante, et de limiter la taille de la zone de recherche. La nouvelle zone de recherche est en effet calculée en fonction de l'estimation de la position suivante, de la taille du template, et d'une marge d'erreur (`delta` dans le code).

A chaque détection du template, celui-ci est mis à jour avec la zone de l'image qui a été trouvée, afin que les changements d'orientation, de luminosité, etc. soient pris en compte. Cela peut par exemple permettre de suivre un  visage qui ne serait pas toujours exactement face à la caméra.

Si le template n'est pas détecté (score de ressemblance trop bas) dans la zone de recherche réduite, l'image entière est à nouveau scannée (au détriment des performances).

Il est également possible pour l'utilisateur de sélectionner à nouveau manuellement un nouveau template à tout moment en appuyant sur "s".

Des informations plus précises sur le fonctionnement sont disponibles dans les commentaires du fichier `tracking.py`.

### Calcul d'azimuth et envoi à l'ESP32

Le Rasperry Pi se connecte au serveur qui tourne sur l'ESP32 au lancement du script.

L'azimuth de l'objet détecté est calculé (0 au milieu de l'image). L'angle de vue horizontale de la caméra (~62°), qui a permis de trouver la formule, a été trouvé expérimentalement. La valeur est un flottant, qui est ensuite encodé sur 4 octets par la fonction `struct.pack` de python, et envoyé à l'ESP32 par le réseau.

ESP32
------

### Reception de l'azimuth

L'ESP32 se connecte à un réseau Wifi et crée un socket pour accepter la connexion du Raspberry Pi au lancement du script.

Les valeurs reçues du Raspberry Pi sont décodées par la fonction `struct.unpack` de python pour récupérer un flottant. La valeur est stockée dans la variable `azimuth` du code.

### Commande du moteur

Périodiquement, grâce à un timer, la consigne du moteur est calculée à partir de l'azimuth. Le moteur est à courant continu, contrôlé par un pont en H. Deux sorties de l'ESP32 sont nécéssaires à son fonctionnement : une pour chaque sens de rotation. De plus, envoyer un signal [PWM](https://fr.wikipedia.org/wiki/Modulation_de_largeur_d%27impulsion) sur ces pins permet de faire varier la vitesse en changeant le rapport cyclique. On calcule donc ce rapport cyclique en fonction de l'azimuth, et on l'envoie sur le bon pin en fonction du signe de l'azimuth.

Démo
----

### Système complet

[![Alt text](https://img.youtube.com/vi/6z1_OGObuqY/0.jpg)](https://www.youtube.com/watch?v=6z1_OGObuqY)

### Caméra

[![Alt text](https://img.youtube.com/vi/IvsRmVa7WwY/0.jpg)](https://www.youtube.com/watch?v=IvsRmVa7WwY)

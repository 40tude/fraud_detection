Dans le shéma du readme du projet (https://github.com/40tude/fraud_detection) ce code se trouve entre mlflow et "real-time" data producer.

C'est une toute première implémentation en python pur qui permet de valider quelques idées
* Comment interroger l'API
* Qu'est ce qui faut pour faire une prédiction : quelles données envoyer, quel format, comment...
* Si y a une fraude, comment envoyer un mail 
* ...

### Remarques :
1. J'ai pas encore regardé la sauvegarde de la transaction simulée et de la prediction associée dans une base de données (mais c'est dans la TODO liste)

1. Pour le reste, à ce jour 05/07, il n'est pas interdit d'être malin et de faire des demandes de prédictions par batch. Typiquement, lors de la première prédiction faut rapatrier le modèle sélectionné (lent) puis faire des prédictions (rapide). Ensuite faut juste faire faire des prédictions (plus de modèle à rapatrier)

1. Il faut aussi anticiper l'arrivée de Kafka et de ses "topics". Idéalement je verrai bien une organisation avec 2 topics. À droite, on déverse dans un premier topic les transactions (simulées) avec une vitesse speed_1. Si jamais il n'y a plus de transaction, ce n'est pas très grave. Le système est résilient. Il continue à tourner, on continue à vider le topic 1 à la vitesse speed_2 et à demander des prédictions. Si une transaction frauduleuse était dans le Topic 1, elle est détéctée "au plus vite" et une alarme est déclenchée. Ce n'est pas parce qu'on a perdu la connexion avec le générateur de données que tout s'arrête. Le système fait au mieux. Ce point est très important. Quoiqu'il arrive, on doit tout faire pour consommer les transactions reçues afin de pouvoir faire des prédictions et sonner l'alarme le cas échéant.

Pour le reste, les prédictions sont déversées dans un second topic (à gauche) à la vitesse speed_2. Enfin, topic 2 est vidé à la vitess speed 3 quand on veut remplir la base de données. Là aussi, cela permet d'avoir un système plus résilient car même si on perd la connexion avec la base, tout le reste (récupération des transactions, demandes de prédictions, alrmes) continue de tourner.   

<p align="center">
<img src="./assets/flux_meter_2_topics.png" alt="drawing" width="600"/>
<p>

3. Si une alarme pour fraude doit être envoyée (un mail par exemple), je pense qu'il faut l'envoyer le plus tôt possible, dès que la prédiction est versée dans Topic 2. Cela peut faire l'objet d'un consommateur qu'on brancherait sur Topic 2. On aurait donc 2 consommateurs branchés sur Topic 2. Un qui balance les données dans la base de données à la vitesse speed_3 et un autre qui inspecte toutes les prédictions et qui envoie un mail en cas de fraude (0.38% des transactions)

Il n'est pas prévu que ce code reste en l'état jusqu'à la fin du projet. C'est une preuve de concept. Il est fort probable que tout ou partie sera remplacée par du Kafka, des topics etc.

Pour faire simple :

* Le code de "l'application" c'est : 99_tooling\01_client_predict\app\client_predict.py
* Pour le lancer, il faut se mettre dans le répertoire 99_tooling\01_client_predict\ puis commencer par lancer : build_client_predict.ps1
* Une fois que vous avez une image, toujours dans le même répertoire il faut lancer : 99_tooling\01_client_predict\run_client_predict.ps1

1. Si vous ne comprenez pas pourquoi faut faire ça ou comment ça marche, lisez 00_mlflow_tracking_server\readme.md mais ne redéployez pas un mlflow tracking server sur Heroku qui risquerait de détruire le serveur en place. 
1. A la fin du readme précédent, on vous renvoit vers le prochain readme à lire : 02_train_code\01_sklearn\01_minimal\readme.md 
1. Ce dernier vous proposera d'aller lire 02_train_code\01_sklearn\02_template\readme.md

L'idée c'est que même si vous vous en fichez de ces histoires de modèles etc... Dans l'eprit, ça explique comment utiliser le client_predict.py qui est ici : 99_tooling\01_client_predict.

En effet, lui aussi c'est un code python qui tourne dans une image Docker. Donc faut construire l'image (avec build_client_predict.ps1) puis quand c'est fait, faut lancer l'application dans l'image avec run_client_predict.ps1.

Sinon, la dernière version de client_predict.py est la plus "évoluée" : elle se connecte à l'API, elle peut envoyer des mails, elle fait des prédictions...  

La toute première version s'appelle client_predict00.py. Si besoin allez lire son code. Si c'est encore trop pénible, allez dans les autres répertoires de 99_tooling. Il y a là des codes snippets encore plus simples.
# Réponses du test

## Prérequis

- **Python ≥ 3.10, <3.13**  
- **Poetry**  
  - Gestion des dépendances & de l’environnement virtuel  
  - Installation :  
    ```bash
    pipx install poetry
    ```  
- **Docker**
  - Permet de lancer rapidement Postgres 15 sans l’installer en dur
  - Avoir `docker` ouvert
- **Make**  
  - Pour exécuter les cibles du `Makefile`
  - Installation :
  ```bash
    sudo apt-get update
    sudo apt-get -y install make
    # check the version
    make -v
    ```  
---


### Étape 1
J'ai utilisé poetry comme système de gestion des dépendances car c'est un outil complet pour les libraries python (métadonnées du projet, fichier `poetry.lock`, environnment isolé intégré, groupes de dépendances etc).
J'ai aussi utilisé `Makefile` afin de centraliser les commandes. Makefile facilite toute manipulation (installation, exécution des scripts, tests etc). La commande `make install` va créer un environnment isolé et y installer les dépendances nécessaires au projet. Il est aussi important de bien versioner les dépendances afin de s'assurer de la comptabilité entre elles ainsi qu'avec le code.

```bash
make install
```

### Étape 2
Voici la structure du projet:
````
.
├── Makefile
├── pyproject.toml
├── poetry.lock
├── .coveragerc
├── README.md
├── Changelog.md
├── workspace.yaml               # Tell dagster where to get the files
├── README.md
├── requirements.txt
├── .gitignore
├── dagster_home/                # Dagster metadata (auto-generated)
│
│── docs/
│   ├── ANSWERS.md
├── src/
│   ├── repository.py            # Dagster entrypoint (@repository)
│   ├── config/
│   │   └── dagster_config.yaml 
│   │
│   ├── moovitamix_fastapi/
│   │   ├── __init__.py
│   │   ├── main.py              
│   │   ├── generate_fake_data.py
│   │   └── classes_out.py       
│   │
│   └── pipelines/
│       ├── __init__.py
│       ├── helpers.py           
│       ├── extract.py           # extract ops
│       ├── load.py              # load op
│       ├── ingest.py            # graph and job definition
│       └── schedules.py         # schedule definition
│
├── tests/
│   ├── unit/
│   │   ├── test_extract.py
│   │   ├── test_load.py
│   │   ├── test_schedule.py
│   │   └── test_classes_out.py
│   │
│   └── integration/
│       └── test_integration.py
│
└── scripts/
    └── check_db.py             # script to check data in db

````

J'ai utilisé `dagster`pour la création du pipeline de données (extraction et chargement). C'est un orchestrateur de worfklows qui permet de manipuler les données avec plus de robustesse, bénéficier d'une interface graphique pour visualiser les graphes de dépendances, inspecter les logs en temps réel. De plus, dagster permet de programmer/scheduler des tâches facilement.
Pour l'exercice, j'ai utilisé une base de données PostgreSQL afin d'avoir facilement une base relationnelle pour les 3 tables en local via docker.

Le pipeline fonctionne ainsi:

1. Extraction des données
Le job exécute trois opérations (`fetch_tracks`, `fetch_users`, `fetch_listen_history`).
Chacune opération envoie une requête HTTP (GET) aux endpoints correspondants du serveur FastAPI.
Les réponses `JSON` sont validées et converties en objets Python (Pydantic).

2. Chargement des données
Une fois toutes les données extraites et validées, l’opération `load_to_postgres` va écrire dans les tables `tracks`, `users` et `listen_history` de la base de données PostgreSQL. J'ai sérialisé le champ `items` pour être sûr d'avoir un array dans la table et non du texte. Par simplicité pour le test, j'ai choisi `pandas.DataFrame.to_sql()` pour convertir directement un `Dataframe` en table SQL. De plus, les types de colonnes sont mappés automatiquement ou via un `dtype` pour garantir la bonne correspondance (utile pour `DateTime()` et `JSONB()`). J'ai aussi choisi de `replace` par soucis de simplicité (il existe de techniques plus optimales en production comme l'incrémental).

3. Planification
Un cron programmé chaque jour à 8 h déclenche le `dagster-daemon`, qui orchestre l’exécution du job via Dagster.

````
[Scheduled Cron]
      │
      ▼
┌───────────────┐     HTTP      ┌─────────────┐
│ fetch_* ops   │─────────────▶ │  FastAPI    │
│ (extract)     │◀─────────────-│  endpoints  │
└───────────────┘               └─────────────┘
      │
      │ validate data
      ▼
┌───────────────────┐
│ load_to_postgres  │
│   (load)          │
└───────────────────┘
      │
      │ INSERT / REPLACE
      ▼
┌───────────┐
│PostgreSQL │
└───────────┘

````


<br>

Voici les commandes pour exécuter l’opération d'ingestion de données
```bash
# Lancer le serveur FastAPI pour récupérer les donnnées
make serve

# Lancer la base de données Postgres dans un docker, en téléchargeant l'image de Postgres au préalable
make run-db

# Exécuter la tâche d'extraction et de chargement des données dans Postgres
make ingest

# Vérifier que les données ont bien été chargées
make ingest-check

# (Optionnel) Afficher UI de dagster: http://localhost:3000
make dagit

# (Optionnel) Nettoyer toute ressource
make clean
```

### Étape 3
En plus des tests unitaires pour les classes, les ops d'extraction et de chargement ainsi que le schedule, j'ai rajouté des tests d'intégration afin de tester le pipeline end-to-end. Cela requiert Postgres fonctionnel mais permet de vérifier que chaque table Postgres contient bien des données.

````bash
# Lancer les tests de formattage, unitaires et d'intégration
make test

# Avoir un rapport sur le coverage des tests
make coverage
````

## Questions (étapes 4 à 7)

### Étape 4

J'utiliserais une **data warehouse** comme BigQuery car cela permet de faire des requêtes complexes sur un immense dataset rapidement. Avec une stratégie de **Bronze-Silver-Gold** dans un cadre **ELT** (transformation avec **DBT**), cela permet une séparation claire des responsabilités, une traçabilité, une flexibilité et des coûts plus faibles (les transformations lourdes comme les jointures s'appliquent seulement sur la couche Silver/Gold). De plus, BigQuery scale automatiquement, offre des requêtes distributées très rapides et s'intègre facilement avec d'autres microservices GCP. 

Enfin, `dbt` permet d'avoir des data modèles réutilisables pour assurer la transformation et offre des features comme un dry-run, graphe de dépendances entre modèles, exécution incrémentale, des tests intégrés, documentation automatique, etc

Voici une proposition de schéma, avec une description (utile pour un éventuel use case de self-serving/recherche sémantique):
<br>`PK` pour primary key

##### 1. `tracks` table
| Column       | Type      | Description                          |
|--------------|-----------|--------------------------------------|
| `id`         | INT64     | Track identifier (PK)                |
| `name`       | STRING    | Track title                          |
| `artist`     | STRING    | Artist name                          |
| `songwriters`| STRING    | Songwriters                          |
| `duration`   | STRING    | Duration (e.g. `"03:45"`)            |
| `genres`     | STRING    | Genres                               |
| `album`      | STRING    | Album title                          |
| `created_at` | TIMESTAMP | Record creation timestamp            |
| `updated_at` | TIMESTAMP | Record last update timestamp         |

---

##### 2. `users` table
| Column           | Type      | Description                                    |
|------------------|-----------|------------------------------------------------|
| `id`             | INT64     | User identifier (PK)                           |
| `first_name`     | STRING    | User’s first name                              |
| `last_name`      | STRING    | User’s last name                               |
| `email`          | STRING    | User’s email address                           |
| `gender`         | STRING    | User’s gender (e.g. `"female"`, `"male"`, …)   |
| `favorite_genres`| STRING    | Favorite genres                                |
| `created_at`     | TIMESTAMP | Record creation timestamp                      |
| `updated_at`     | TIMESTAMP | Record last update timestamp                   |

---

##### 3. `listen_history` table
| Column           | Type        | Description                                                         |
|------------------|-------------|---------------------------------------------------------------------|
| `user_id`        | INT64       | Foreign key to `users.id`                                           |
| `items`          | ARRAY<INT64>| List of tracks ID (int)                                             |
| `created_at`     | TIMESTAMP   | Record creation timestamp                                           |
| `updated_at`     | TIMESTAMP   | Record last update timestamp                                        |



### Étape 5

Métriques clés:
- durée d'exécution par étape et pour tout le pipeline (en s)
- taux de succès/échec (en %)
- fraicheur des données (en jour) pour s'assurer d'avoir des données récentes
- volume de données ingérées (en nombre de lignes et/ou en octets)
- coûts par étape et pour le pipeline (en $) - utile pour savoir quelles étapes à optimiser
- (optionnel) ressources utilisées (en CPU et mémoire)

Pour la méthode de surveillance, je choisirais d'abord des **seuils** (par exemple si une étape prend plus de 15 min ou supérieur à 1.5*P95, si le nombre d'échecs consécutif est supérieur à 1, si la fraicheur des données dépasse 3 jours, etc).

Pour les **alertes**, on peut utiliser des outils comme Slack, Prometheus/Splunk et Grafana (en profitant des logs structurés de Dagster). Dagster permet de voir les erreurs dans le traceback en cas d'échec d'une opération (et permet aussi un retry). Un outil comme Airflow le permet aussi. 

Il faut différencier l'alerting (intégration Dagster et Slack - ou Sentry) de l'observabilité (Grafana, GCP Looker, AWS Cloudwatch).

### Étape 6

Un exemple d'architecture pour automatiser le calcul des recommendations pourrait être:
````
                ┌────────────────────┐
                │   Orchestrator     │
                │     (Dagster)      │
                └─────────┬──────────┘
                          │ Schedule / Trigger
                          ▼
       ┌────────────────────────────────────────┐
       │  Job “compute_recommendations”          │
       │                                         │
       │  1. Load Gold–layer data                │
       │     (user profiles, item metadata,      │
       │      listening history, etc.)           │
       │                                         │
       │  2. Feature engineering / Preparation   │
       │     – Normalization, etc. (simple)      │
       │                                         │
       │  3. Model inference                     │
       │     – Load a trained model (mlflow)     │
       │     – Predict top-K recommendations     │
       │                                         │
       │  4. Write out results                   │
       │     – `recommendations` table           │
       │     – Optionally Pub/Sub                │
       └────────────────────────────────────────-┘
                          │
                          ▼
                ┌────────────────────┐
                │  Data Warehouse    │
                │   (BigQuery, etc.) │
                └────────────────────┘

````

Explication:
1. **Orchestration**: schedule par cron ou alors par un évènement/Sensor (seuil de données franchi) qui déclencherait le pipeline
2. **Utilisation des données (Gold)**: on récupère les données déjà nettoyées et préparées
3. **Features Engineering**: appliquer les mêmes transformations que lors du training (d'où l'utilisation d'un feature store ou garder les artifacts ML de transformation. On peut aussi créer un `@op` `feature_data` dans Dagster pour produire un DataFrame de features prêtes pour l'inférence)
4. **Inférence**: prendre le modèle depuis un bucket (via mlflow registry), charger ce modèle dans un `@op` `score_model` et faire la prédiction, pour chaque utilisateur, des listes des top K items
5. **Ecrire ces recommendations**: dans une table `recommendations`. Optionnel: communiquer aux downstream services via un systeme Pub/Sub
6. **Observabilité**: sauvegarder des métriques pour d'éventuelles analyses (nombre de recommendations par utilisateurs, temps de calcul, etc)


### Étape 7

Exemple d'architecture pour automatiser le réentrainement du modèle

````
[Dagster Scheduler]
              │
              ▼
┌────────────────────────────────────────-------──┐
│  Job “retrain_recommendation_model”             │
│                                                 │
│  1. Extract Gold‐layer data                     │
│                                                 │
│  2. Feature Engineering                         │
│                                                 │
│  3. Model Training                              │
│     – Launch training op/scrip/node             │
│     – Models and Hyperparameter tuning          │
│                                                 │
│  4. Validation & Comparison                     │
│     – Evaluate on test set                      │
│     – Compute metrics                           │
│     – Compare to current production             │
│                                                 │
│  5. Register in Model Registry                  │
│     – Push to MLflow/SageMaker/Vertex AI        │
│       if satisfied                              │
│                                                 │
│  6. Deploy with Strategy                        │
│     – Feature Flag                              │
│     – Canary                                    │
│     – Blue/Green                                │
│                                                 │
│  7. Notify & Report                             │
│     – Send Slack on success or failure          │
│     – Dashboard metrics updated                 │
└──────────────────────────────────────────-------┘
              │ Update
              ▼
   ┌────────────────────────────┐
   │  Serving Infrastructure    │
   │  – API Gateway / Feature   │
   │    Flag Service            │
   │  – Model endpoints (v1, v2)│
   └────────────────────────────┘

````

Explication:
- **Orchestration**: schedule par cron ou détection automatique d'une baisse de performance du modèle en production (`nannyml`)
- **Réentrainement**: à l'aide d'une `@op` ou `node` (kedro), on peut automatiser un pipeline d'entraînement de modèles ML. Par exemple, on peut avoir une dictionnaire d'algorithmes avec des sets d'hyperparametres puis on va faire une optimisation bayésienne (`hyperopt`) pour trouver le meilleur set d'hyperparamètres par algorithme. On garde la meilleure combinaison.
- **Validation et Comparaison**: on évalue notre "champion" sur un test set et on compare avec un seuil minimum pour aller en production. Si la comparaison est satisfaisante, on peut envoyer le modèle dans le model registry avec un alias `challenger`. 
- **Déploiement**: une suggestion de stratégie de déploiement est d'utiliser un feature flag ou une route challenger pour déployer progressivement le nouveau modèle. Cela permet de rollback facilement en cas de problèmes observés en production. 
- **Observation**: on observe les changements en production via les outils d'observabilité mis en place (Grafana, Honeycomb par exemple)
- **Feedback**: l'étape finale serait de collecter un retour d'utilisateurs, par exemple via un système de thumb up/down ou des métriques dites online (user-centric) comme le CTR (click-through rate), conversion rate (rajouter le morceau dans une playlist, aimer), durée d'écoute des recommandations etc.

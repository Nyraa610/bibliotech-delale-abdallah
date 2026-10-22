# Synthèse du TP 1 - Clean Code & Qualité logicielle

Binôme : Dorian Delale & Abdallah
Branche : `tp1/nettoyage`

## Tableau des améliorations

| Défaut | Emplacement | Correction | Principe |
| --- | --- | --- | --- |
| Imports sauvages (`from datetime import *`) et modules inutilisés | `bibliotech.py`, entête | Remplacement par des imports explicites (`from datetime import date, datetime, timedelta`) | Clarté / PEP 8 |
| Fichiers ouverts sans fermeture sécurisée (`open()` sans `with`) | `load()`, `save()`, `export()` | Utilisation systématique de context managers `with open(...) as f:` avec encodage UTF-8 | Robustesse / RAII |
| Évaluation dangereuse d'une chaîne avec `eval()` | `_load_books()` | Remplacement de `eval(x[4])` par `float(x[4])` pour le prix | Sécurité / Robustesse |
| Nombres magiques des durées d'emprunt (21, 7, 3) | `do_stuff()` | Création des constantes `BOOK_LOAN_DAYS`, `DVD_LOAN_DAYS`, `MAGAZINE_LOAN_DAYS` et du dictionnaire `LOAN_DURATIONS` | Lisibilité |
| Nombres magiques des quotas d'emprunt (5, 8, 3) | `do_stuff()` | Création des constantes `MAX_LOANS_STUDENT`, `MAX_LOANS_PREMIUM`, `MAX_LOANS_STANDARD` et du dictionnaire `MAX_LOANS_BY_MEMBER_TYPE` | Lisibilité |
| Calcul de pénalité de retard copié 4 fois et nombres magiques (0.5, 1.0, 0.2) | `ret()`, `overdue()`, `report()`, `export()` | Extraction d'une fonction unique `late_fee()` et des constantes `DAILY_FEES` | DRY (Don't Repeat Yourself) |
| Complexité cyclomatique excessive et anti-pattern "flèche" (imbrication de 7 `if`) | `do_stuff()` (C901 : 20 > 8) | Utilisation de clauses de garde (*early return*) et extraction de helpers (`_has_overdue_loans`, `_is_already_borrowed`, `_next_loan_id`) | Lisibilité / KISS |
| Complexité cyclomatique et mélange de responsabilités dans `report()` | `report()` (C901 : 21 > 8) | Découpage en fonctions dédiées : `_report_titles_and_members()`, `_report_stats()`, `_report_top3()` | Single Responsibility (SRP) |
| Monolithe de chargement des données | `load()` (C901 : 10 > 8) | Décomposition en trois sous-fonctions : `_load_books()`, `_load_members()`, `_load_loans()` | Single Responsibility (SRP) |
| Chaîne à rallonge `if / elif` pour le routage des commandes CLI | `process()` (C901 : 16 > 8) | Pattern dictionnaire de commandes (`COMMANDS`) associant chaque commande à sa fonction de gestion | Open/Closed / Modularité |
| Comparaisons non idiomatiques (`== None`, `== True`, `== False`) | `Library`, `process()`, `get_today()` | Remplacement par `is None`, `if x:`, `if not x:` | PEP 8 / Python idiomatique |
| Argument par défaut mutable (`options={}`) | `register_plugin()` (B006) | Remplacement par `options=None` avec initialisation si `None` | Robustesse / Bonnes pratiques |
| Clauses `except:` nues capturant toutes les erreurs à l'aveugle | `_load_loans()`, `run_plugins()` | Capture ciblée `(ValueError, IndexError)` et utilisation de `contextlib.suppress(Exception)` | Robustesse / Bonnes pratiques |
| Lignes dépassant 88 caractères et formatage hétérogène | Fichier complet | Reformatage selon les règles du projet avec `ruff format` | Lisibilité / Cohérence de style |

## Vérification de conformité

- **Pytest** : 21/21 tests passés avec succès (comportement préservé à 100 %).
- **Ruff check** : 0 erreur / 0 avertissement (réduit depuis 49 erreurs initiales).
- **Formatage** : Conforme aux standards Black / Ruff (longueur max 88 caractères).

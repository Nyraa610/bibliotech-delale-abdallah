

# Bilan du projet - TP 1 & TP 2
**Binôme : Dorian Delale & Rayan Abdallah**  
**Module : Clean Code et Qualité logicielle**

##  Démarche globale
L'objectif de ces deux TP était d'assainir et de restructurer l'application BiblioTech **sans jamais altérer son comportement fonctionnel**, validé en continu par la suite de tests automatisés.



## TP 1 - Nettoyage, Style & Qualité du code
Le code initial fonctionnait mais comportait de nombreuses mauvaises pratiques, du code mort et des violations des standards Python.

### Améliorations clés apportées :
1. **Passage au linter Ruff (49 erreurs réduites à 0) :**
    - Correction des imports inutilisés (`json`, `datetime` mal importé).
    - Suppression du code mort (comme `old_calc_fee`).
    - Formatage aux standards PEP 8 (longueur de ligne, espacements, f-strings).
2. **Gestion robuste des ressources :**
    - Remplacement des `open()` non protégés par des gestionnaires de contexte `with open(...)` pour garantir la fermeture des fichiers.
3. **Suppression des anti-patterns :**
    - Élimination des `except: pass` aveugles qui cachaient les bugs. Dans `run_plugins`, les exceptions sont désormais proprement journalisées avec `logging.exception`.
4. **Élimination des nombres magiques :**
    - Introduction de constantes explicites en majuscules pour les tarifs journaliers, les durées de prêt et les limites par type d'adhérent.
5. **Livrable :** Rédaction de `SYNTHESE_TP1.md` et ouverture de la première Pull Request.

---

## TP 2 - Refactoring & Tests unitaires (TDD)
Le TP 2 s'est concentré sur la réduction de la complexité cyclomatique et l'élimination de la duplication, avec l'écriture de tests unitaires avant chaque refactoring.

### Refactorings réalisés :
1. **Niveau 1 - Extraction de `late_fee` (Extract Function & DRY) :**
    - *Défaut :* La logique de pénalité de retard était dupliquée 4 fois (`ret`, `overdue`, `report`, `export`).
    - *Solution :* Création d'une fonction pure `late_fee(...)` pilotée par des dictionnaires de règles métier (`DAILY_FEE_BY_KIND`, `DISCOUNT_BY_MEMBER_TYPE`).
    - *Tests :* 9 tests unitaires paramétrés dans `tests/test_rules.py`.

2. **Niveau 2 - Découpage de `do_stuff` (Guard Clauses & Single Responsibility) :**
    - *Défaut :* `do_stuff` comptait 7 niveaux d'imbrication de `if`/`else` et une note critique de complexité Radon (**D, score 23**).
    - *Solution :* Renommée en `borrow` et découpée en méthodes à responsabilité unique qui retournent immédiatement en cas d'erreur (clauses de garde) :
        - `refusal_reason(member, book)` : centralise les 5 règles de refus.
        - `has_overdue_loan(member_id)` : détection d'emprunts non rendus en retard.
        - `is_borrowing(member_id, book_id)` : vérifie si le livre est déjà emprunté par ce membre.
        - `create_loan(member, book)` : calcule l'échéance et enregistre l'emprunt.
    - *Tests :* Fixture isolée dans `tests/conftest.py` et 6 tests unitaires dans `tests/test_borrow.py`.

3. **Niveau 3 (Bonus) — Extraction de `parse_date` :**
    - Remplacement de 8 appels répétitifs à `datetime.strptime(..., "%Y-%m-%d").date()` par une fonction dédiée `parse_date`, testée aux cas valides et invalides.

---

## Métriques & Résultats

| Métrique | État initial (v0) | Après TP 1 | Après TP 2 (Final) |
|---|---|---|---|
| **Erreurs Ruff** | 49 problèmes | 0 problème (`All checks passed!`) | 0 problème |
| **Complexité `do_stuff`** | Note **D** (score 23) | Note B (score 8) | Note **A** (score 4) |
| **Note D globale** | Présente | Présente | **0 note D** |
| **Suite de tests** | 21 tests (caractérisation) | 21 tests | **38 tests 100% verts** |

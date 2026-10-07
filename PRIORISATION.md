# Priorisation des UC — Matrice 3 critères

| UC | Valeur métier (1-5) | Risque technique (1-5) | Impact archi (1-5) | **Score total** | Priorité |
|----|---------------------|------------------------|--------------------|-----------------|----------|
| UC-03: Réserver une place ★ | 5 | **5** | **5** | **15** | **1ère (Elaboration)** |
| UC-04: Effectuer un paiement | 5 | 3 | 4 | 12 | 2ème (Construction) |
| UC-02: Consulter les séances | 4 | 2 | 3 | 9 | 3ème (Construction) |
| UC-01: Consulter les films | 3 | 1 | 2 | 6 | 4ème (Construction) |
| UC-05: Recevoir confirmation | 4 | 3 | 3 | 10 | 5ème (Transition) |
| UC-06: Annuler réservation | 3 | 2 | 2 | 7 | 6ème (Transition) |

> **Critères** : Valeur = importance business, Risque = difficulté technique (concurrence, externes), Impact archi = couches touchées (contrôleur→service→repo→DB→externe)

## UC à traiter en **premier (Élaboration)** : **UC-03 Réserver une place**
- Seule UC qui valide l'architecture de bout en bout + gestion concurrence (optimistic lock / SELECT FOR UPDATE)
- Bloque toutes les autres (paiement, confirmation, annulation en dépendent)
# Liste des Cas d'Utilisation

| ID | Nom | Acteur principal | Description courte | Risque technique |
|----|-----|------------------|-------------------|------------------|
| UC-01 | Consulter les films | Spectateur | Voir la liste des films à l'affiche avec affiche, synopsis, durée | Faible |
| UC-02 | Consulter les séances | Spectateur | Voir les horaires d'un film pour une date donnée, avec places dispo | Faible |
| UC-03 | **Réserver une place** ★ | Spectateur | Choisir un siège libre, le bloquer, créer réservation en attente | **Élevé (concurrence)** |
| UC-04 | Effectuer un paiement | Spectateur | Payer la réservation via prestataire externe (Stripe) | Moyen (intégration) |
| UC-05 | Recevoir une confirmation | Spectateur | Recevoir email/SMS avec QR code après paiement réussi | Moyen (asynchrone) |
| UC-06 | Annuler une réservation | Spectateur | Libérer le siège, rembourser si payé, notifier | Faible |

> ★ = UC à risque technique (conflit de réservation siège simultanée)
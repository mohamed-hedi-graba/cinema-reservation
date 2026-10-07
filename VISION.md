# Vision - Cinema Ticket Reservation

## Problème
Les cinémas indépendants perdent des clients faute de système de réservation en ligne simple, fiable et sans surréservation.

## Utilisateurs
- **Spectateur** : veut réserver une place en 2 clics, payer, recevoir sa confirmation.
- **Gérant** : veut voir l'occupation en temps réel, éviter les conflits de siège.

## Valeur
Réservation fluide, paiement sécurisé, confirmation instantanée, zéro double-réservation.

## Acteurs
| Acteur | Description |
|--------|-------------|
| **Spectateur** | Utilisateur final qui réserve, paie, annule, reçoit confirmation |
| **Gérant** | Administre films, séances, salles ; consulte statistiques |
| **Système de paiement** | Externe (Stripe/Adyen) — traite la transaction |
| **Service notification** | Externe (email/SMS) — envoie la confirmation |
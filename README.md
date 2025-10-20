# BitTravel Backend API

API REST pour la plateforme BitTravel 

## Démarrage rapide

### Prérequis

- Python 3.10+
- PostgreSQL
- Un compte KKiapay (sandbox)
- Un nœud BTCPay Server configuré

### Installation

```bash
# Cloner le projet
git clone <url-du-repo>
cd bittravel-backend

# Créer l'environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou venv\Scripts\activate sur Windows

# Installer les dépendances
pip install -r requirements.txt

# Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos vraies clés

# Créer la base de données
psql -U postgres -c "CREATE DATABASE bittravel;"

# Lancer l'application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

L'API sera accessible sur : http://localhost:8000

Documentation interactive : http://localhost:8000/docs

---

## Guide d'intégration Frontend

### Architecture générale

```
Frontend (React/Next.js)
    ↓
API Backend (FastAPI)
    ↓
PostgreSQL + KKiapay + BTCPay Server
```

### CORS

Le backend accepte toutes les origines en développement. En production, configurez les origines autorisées dans `app/main.py`.

---

## Authentification

Le backend gère **2 types d'authentification** :

### 1. Utilisateurs (Voyageurs)

#### Inscription
```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123",
  "full_name": "Jean Dupont",
  "phone": "+22997123456"
}
```

**Réponse :**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "Jean Dupont",
  "role": "user",
  "created_at": "2025-01-20T10:00:00"
}
```

#### Connexion
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

**Réponse :**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

#### Utilisation du token

Pour les routes protégées, ajoutez le header :
```
Authorization: Bearer <votre_token>
```

### 2. Agences de transport

#### Inscription d'une agence
```http
POST /agencies/register
Content-Type: application/json

{
  "name": "Transport Express",
  "contact": "Directeur Général",
  "email": "agency@example.com",
  "phone": "+22997000000",
  "password": "password123"
}
```

#### Connexion d'une agence
```http
POST /agencies/login
Content-Type: application/json

{
  "email": "agency@example.com",
  "password": "password123"
}
```

---

## Recherche de trajets

### Itinéraires populaires
```http
GET /routes/popular?limit=5
```

**Réponse :**
```json
[
  {
    "id": "uuid",
    "origin": "Cotonou",
    "destination": "Porto-Novo",
    "duration": 45,
    "agency_name": "Transport Express"
  }
]
```

### Recherche avancée
```http
GET /search?origin=Cotonou&destination=Porto-Novo&date=2025-10-15&max_price=10000
```

**Paramètres disponibles :**
- `origin` : Ville de départ
- `destination` : Ville d'arrivée
- `date` : Date au format YYYY-MM-DD
- `min_price` : Prix minimum en FCFA
- `max_price` : Prix maximum en FCFA

**Réponse :**
```json
[
  {
    "schedule_id": "uuid",
    "agency_name": "Transport Express",
    "agency_rating": 4.5,
    "origin": "Cotonou",
    "destination": "Porto-Novo",
    "departure_time": "2025-10-15T14:00:00",
    "duration": 45,
    "price": 5000,
    "available_seats": 20
  }
]
```

---

## Réservations

### Créer une réservation

```http
POST /reservations
Content-Type: application/json
Authorization: Bearer <token_optionnel>

{
  "schedule_id": "uuid",
  "passenger_info": {
    "name": "Jean Dupont",
    "phone": "+22997123456",
    "email": "jean@example.com"
  }
}
```

**Important :** Si l'utilisateur est connecté (token fourni), il bénéficie de **10% de réduction** automatiquement !

**Réponse :**
```json
{
  "id": "uuid",
  "schedule_id": "uuid",
  "passenger_info": {...},
  "payment_status": "pending",
  "total_amount": "4500",  // 5000 - 10% si connecté
  "created_at": "2025-01-20T10:00:00"
}
```

### Historique des réservations (utilisateur connecté)

```http
GET /reservations/my-reservations
Authorization: Bearer <token>
```

---

## Paiements

BitTravel supporte **2 moyens de paiement** :

### 1. KKiapay (Mobile Money : MTN, Moov, Wave)

#### Étape 1 : Récupérer les infos de paiement

```http
POST /payments/kkiapay/get-info
Content-Type: application/json

{
  "reservation_id": "uuid"
}
```

**Réponse :**
```json
{
  "success": true,
  "payment_id": "uuid",
  "amount": 5000,
  "public_key": "007cddd0aad311f0b4458351fff65ea0",
  "sandbox": true,
  "reservation_id": "uuid",
  "reason": "Ticket BitTravel #abc123",
  "phone": "+22997123456",
  "name": "Jean Dupont"
}
```

#### Étape 2 : Intégrer le widget KKiapay

```javascript
// Charger le SDK
<script src="https://cdn.kkiapay.me/k.js"></script>

// Utiliser les infos reçues
openKkiapayWidget({
  amount: paymentInfo.amount,
  api_key: paymentInfo.public_key,
  sandbox: paymentInfo.sandbox,
  phone: paymentInfo.phone,
  name: paymentInfo.name,
  reason: paymentInfo.reason
});

// Écouter le succès
addSuccessListener(async (response) => {
  // Vérifier le paiement côté backend
  await fetch('/payments/kkiapay/verify', {
    method: 'POST',
    body: JSON.stringify({
      transaction_id: response.transactionId,
      reservation_id: paymentInfo.reservation_id
    })
  });
});
```

#### Étape 3 : Vérifier le paiement

```http
POST /payments/kkiapay/verify
Content-Type: application/json

{
  "transaction_id": "transaction_id_from_kkiapay",
  "reservation_id": "uuid"
}
```

**Réponse si succès :**
```json
{
  "success": true,
  "message": "Paiement confirmé avec succès",
  "status": "SUCCESS",
  "reservation_id": "uuid"
}
```

### 2. Bitcoin Lightning

#### Étape 1 : Créer une facture Lightning

```http
POST /payments/lightning/create-invoice
Content-Type: application/json

{
  "reservation_id": "uuid"
}
```

**Réponse :**
```json
{
  "success": true,
  "message": "Facture Lightning créée",
  "invoice": "lnbc150u1p3pj257pp5qqszqgpqy...",
  "invoice_id": "abc123",
  "checkout_link": "https://btcpay.../i/abc123",
  "amount_fcfa": 5000,
  "amount_usd": 8.5,
  "qr_code": "data:image/png;base64,...",
  "payment_id": "uuid"
}
```

#### Étape 2 : Afficher le QR code ou le lien

```jsx
// React exemple
<img src={data.qr_code} alt="QR Code Lightning" />
<p>Ou scannez avec votre wallet Lightning</p>
<input value={data.invoice} readOnly />
<a href={data.checkout_link}>Payer avec BTCPay</a>
```

#### Étape 3 : Vérifier le paiement

```http
POST /payments/lightning/verify
Content-Type: application/json

{
  "payment_hash": "invoice_id_from_response",
  "reservation_id": "uuid"
}
```

**Réponse si payé :**
```json
{
  "success": true,
  "message": "Paiement Lightning confirmé",
  "paid": true,
  "reservation_id": "uuid"
}
```

---

## Génération et téléchargement de tickets

### Générer un ticket (après paiement)

```http
POST /tickets/generate
Content-Type: application/json

{
  "reservation_id": "uuid"
}
```

**Note :** Le paiement doit être au statut `completed` pour générer le ticket.

**Réponse :**
```json
{
  "id": "ticket_uuid",
  "reservation_id": "uuid",
  "payload": "{...}",
  "signature": "abc123...",
  "public_key": "def456...",
  "status": "valid",
  "expires_at": "2025-10-15T14:00:00"
}
```

### Télécharger le PDF du ticket

```http
GET /tickets/{ticket_id}/pdf
```

Retourne un fichier PDF avec :
- Informations du voyage
- Informations du passager
- QR code contenant le payload + signature

---

## Vérification de tickets (Contrôleurs)

### Vérifier un ticket scanné

```http
POST /tickets/verify
Content-Type: application/json

{
  "ticket_id": "uuid",
  "payload": {...},
  "signature": "abc123...",
  "public_key": "def456..."
}
```

**Réponse :**
```json
{
  "valid": true,
  "status": "valid",
  "message": "Ticket valide"
}
```

**Statuts possibles :**
- `valid` : Ticket OK
- `used` : Déjà utilisé
- `expired` : Expiré
- `invalid_signature` : Signature incorrecte
- `not_found` : Ticket introuvable

### Marquer un ticket comme utilisé

```http
POST /tickets/{ticket_id}/mark-used
```

---

## Gestion des agences (Dashboard)

Les agences connectées peuvent gérer leurs trajets et horaires.

### Créer un itinéraire

```http
POST /routes
Authorization: Bearer <agency_token>
Content-Type: application/json

{
  "origin": "Cotonou",
  "destination": "Porto-Novo",
  "duration": 45
}
```

### Créer un horaire

```http
POST /schedules
Authorization: Bearer <agency_token>
Content-Type: application/json

{
  "route_id": "uuid",
  "departure_time": "2025-10-15T14:00:00",
  "price": 5000,
  "seats": 50
}
```

---

## Sécurité

### Signatures cryptographiques

Les tickets sont signés avec **secp256k1** (Bitcoin/Lightning compatible) :
- Chaque agence a une paire de clés (privée/publique)
- Les tickets sont signés avec la clé privée
- La vérification se fait avec la clé publique
- Impossible de falsifier un ticket

### Authentification JWT

- Tokens valides 7 jours
- Utilisez HTTPS en production
- Stockez les tokens de manière sécurisée (pas de localStorage pour les données sensibles)

---

## Structure des données principales

### Reservation
```json
{
  "id": "uuid",
  "schedule_id": "uuid",
  "user_id": "uuid | null",
  "passenger_info": {
    "name": "string",
    "phone": "string",
    "email": "string"
  },
  "payment_status": "pending | completed | failed | cancelled",
  "total_amount": "string"
}
```

### Ticket
```json
{
  "id": "uuid",
  "reservation_id": "uuid",
  "payload": "json_string",
  "signature": "string",
  "public_key": "string",
  "status": "valid | used | expired | cancelled",
  "expires_at": "datetime"
}
```

---

## Configuration

### Variables d'environnement (.env)

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/bittravel

# Application
APP_NAME=BitTravel API
DEBUG=True
API_VERSION=v1
SECRET_KEY=votre-cle-secrete-super-longue

# KKiapay
KKIAPAY_PUBLIC_KEY=votre_cle_publique
KKIAPAY_PRIVATE_KEY=votre_cle_privee
KKIAPAY_SECRET=votre_secret
KKIAPAY_SANDBOX=True

# BTCPay Server
BTCPAY_URL=https://votre-btcpay.com
BTCPAY_API_KEY=votre_api_key
BTCPAY_STORE_ID=votre_store_id
```

---

## Tests en développement

### URLs de test

- Backend : http://localhost:8000
- Documentation : http://localhost:8000/docs
- Health check : http://localhost:8000/health

### Comptes de test

**KKiapay Sandbox :**
- Numéro test (succès) : `+22997000001`
- Numéro test (échec) : `+22997000002`

**BTCPay Server :**
Utilisez le testnet ou votre propre nœud en mode test.

---

## Flux utilisateur complet (Frontend)

```
1. Utilisateur recherche un trajet
   GET /search?origin=X&destination=Y
   
2. Utilisateur sélectionne un horaire et réserve
   POST /reservations
   
3. Utilisateur choisit son moyen de paiement
   
   Option A - Mobile Money (KKiapay):
   POST /payments/kkiapay/get-info
   → Afficher widget KKiapay
   → POST /payments/kkiapay/verify
   
   Option B - Bitcoin Lightning:
   POST /payments/lightning/create-invoice
   → Afficher QR code
   → POST /payments/lightning/verify
   
4. Une fois payé, générer le ticket
   POST /tickets/generate
   
5. Télécharger le PDF
   GET /tickets/{id}/pdf
```

---

## Gestion des erreurs

L'API retourne des codes HTTP standards :

- `200` : Succès
- `201` : Créé
- `400` : Mauvaise requête
- `401` : Non authentifié
- `403` : Non autorisé
- `404` : Non trouvé
- `500` : Erreur serveur

**Format des erreurs :**
```json
{
  "detail": "Message d'erreur explicite"
}
```

---

## Support

Pour toute question sur l'intégration :
- Consultez `/docs` pour tester interactivement
- Vérifiez les logs du backend pour débugger
- Les endpoints retournent toujours des messages d'erreur clairs

---

## Checklist d'intégration

- [ ] CORS configuré pour votre domaine frontend
- [ ] Authentification implémentée (optionnelle pour achats)
- [ ] Recherche de trajets fonctionnelle
- [ ] Formulaire de réservation connecté
- [ ] Widget KKiapay intégré
- [ ] Interface Lightning (QR code) affichée
- [ ] Vérification des paiements implémentée
- [ ] Téléchargement PDF fonctionnel
- [ ] Gestion des erreurs en place
- [ ] Tests sur les 2 moyens de paiement

---

**Bon développement !**
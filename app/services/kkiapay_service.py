# Service pour l'intégration KKiapay
# Utilise la vraie structure de l'API KKiapay

import requests
from app.core.config import settings

class KkiapayService:
    def __init__(self):
        self.base_url = "https://api-sandbox.kkiapay.me" if settings.KKIAPAY_SANDBOX else "https://api.kkiapay.me"
        self.public_key = settings.KKIAPAY_PUBLIC_KEY
        self.private_key = settings.KKIAPAY_PRIVATE_KEY
        self.secret = settings.KKIAPAY_SECRET
        
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-API-KEY": self.public_key,
            "X-PRIVATE-KEY": self.private_key,
            "X-SECRET-KEY": self.secret
        }

    def verify_transaction(self, transaction_id: str):
        url = f"{self.base_url}/api/v1/transactions/status"
        
        payload = {"transactionId": transaction_id}
        
        try:
            print(f"[KKIAPAY] Verifying transaction: {transaction_id}")
            response = requests.post(url, json=payload, headers=self.headers, timeout=10)
            print(f"[KKIAPAY] Status: {response.status_code}, Response: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "status": data.get("status"),
                    "amount": data.get("amount"),
                    "data": data
                }
            else:
                return {
                    "success": False,
                    "message": f"Erreur {response.status_code}: {response.text}"
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Erreur: {str(e)}"
            }

kkiapay_service = KkiapayService()
# Service pour l'intégration Lightning via BTCPay Server
# Gère la création et vérification des invoices Lightning

import requests
import qrcode
from io import BytesIO
import base64
from app.core.config import settings

class LightningService:
    
    def __init__(self):
        self.base_url = settings.BTCPAY_URL
        self.api_key = settings.BTCPAY_API_KEY
        self.store_id = settings.BTCPAY_STORE_ID
        self.headers = {
            "Authorization": f"token {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def fcfa_to_satoshis(self, amount_fcfa: float):
        try:
            response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=10)
            data = response.json()
            btc_usd = data["bitcoin"]["usd"]
            
            usd_per_fcfa = 0.0017
            amount_usd = amount_fcfa * usd_per_fcfa
            
            print(f"[LIGHTNING] {amount_fcfa} FCFA = ${amount_usd:.2f} USD (BTC: ${btc_usd})")
            return amount_usd
        except Exception as e:
            print(f"[LIGHTNING] Erreur conversion: {str(e)}")
            return amount_fcfa * 0.0017
    
    def create_invoice(self, amount_fcfa: float, memo: str):
        amount_usd = self.fcfa_to_satoshis(amount_fcfa)
        
        url = f"{self.base_url}/api/v1/stores/{self.store_id}/invoices"
        payload = {
            "amount": str(amount_usd),
            "currency": "USD",
            "metadata": {
                "orderId": memo
            }
        }
        
        try:
            print(f"[BTCPAY] Creating invoice: ${amount_usd}")
            response = requests.post(url, json=payload, headers=self.headers, timeout=15)
            print(f"[BTCPAY] Status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                data = response.json()
                
                lightning_invoice = data.get("BOLT11")
                checkout_link = data.get("checkoutLink")
                
                qr_img = qrcode.make(lightning_invoice if lightning_invoice else checkout_link)
                buffer = BytesIO()
                qr_img.save(buffer, format='PNG')
                qr_base64 = base64.b64encode(buffer.getvalue()).decode()
                
                return {
                    "success": True,
                    "invoice": lightning_invoice,
                    "invoice_id": data.get("id"),
                    "checkout_link": checkout_link,
                    "amount_usd": amount_usd,
                    "qr_code": f"data:image/png;base64,{qr_base64}"
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
    
    def check_invoice(self, invoice_id: str):
        url = f"{self.base_url}/api/v1/stores/{self.store_id}/invoices/{invoice_id}"
        
        try:
            print(f"[BTCPAY] Checking invoice: {invoice_id}")
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                status = data.get("status")
                
                paid = status in ["Settled", "Processing"]
                
                return {
                    "success": True,
                    "paid": paid,
                    "status": status,
                    "data": data
                }
            else:
                return {
                    "success": False,
                    "message": f"Erreur {response.status_code}"
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Erreur: {str(e)}"
            }

lightning_service = LightningService()
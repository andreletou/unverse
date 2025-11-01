import requests
import json
from django.conf import settings
from django.urls import reverse
from .models import Payment, Order
from django.utils import timezone

class PayGatePayment:
    @staticmethod
    def initiate_payment(order, phone_number, network):
        """
        Initie un paiement via PayGateGlobal avec gestion améliorée des erreurs
        """
        payload = {
            "auth_token": settings.PAYGATE_API_KEY,
            "phone_number": phone_number,
            "amount": str(order.total),
            "identifier": order.order_number,
            "network": network.upper(),  # FLOOZ ou TMONEY
            "description": f"Paiement pour la commande #{order.order_number}",
            "callback_url": settings.PAYGATE_CALLBACK_URL
        }
        
        try:
            response = requests.post(
                settings.PAYGATE_PAY_URL,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            # Enregistrer la requête et la réponse pour le débogage
            order.payment_attempts.create(
                request_data=payload,
                response_data=response.json(),
                timestamp=timezone.now()
            )
            
            data = response.json()
            
            if data.get('status') == 0:  # Succès
                # Créez l'enregistrement de paiement
                payment = Payment.objects.create(
                    order=order,
                    amount=order.total,
                    method='mobile_money',
                    status='pending',
                    transaction_id=data.get('tx_reference'),
                    payment_details={
                        'tx_reference': data['tx_reference'],
                        'network': network,
                        'phone_number': phone_number,
                        'paygate_response': data
                    }
                )
                
                # Mettre à jour l'ordre avec le paiement
                order.payment = payment
                order.save()
                
                return True, payment
            else:
                error_msg = data.get('message', 'Erreur inconnue de PayGate')
                return False, f"Erreur PayGate: {error_msg} (Code: {data.get('status')})"
                
        except requests.exceptions.Timeout:
            return False, "Délai d'attente dépassé lors de la connexion à PayGate"
        except requests.exceptions.RequestException as e:
            return False, f"Erreur de connexion à PayGate: {str(e)}"
        except Exception as e:
            return False, f"Erreur inattendue: {str(e)}"

    @staticmethod
    def check_payment_status(tx_reference):
        """
        Vérifie le statut d'un paiement avec gestion améliorée des erreurs
        """
        payload = {
            "auth_token": settings.PAYGATE_API_KEY,
            "tx_reference": tx_reference
        }
        
        try:
            response = requests.post(
                settings.PAYGATE_STATUS_URL,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            data = response.json()
            
            # Format standardisé de réponse
            result = {
                'status': data.get('status'),
                'message': data.get('message', 'Statut inconnu'),
                'raw_response': data,
                'success': data.get('status') == 0,
                'transaction_reference': tx_reference,
                'timestamp': timezone.now().isoformat()
            }
            
            return result
            
        except requests.exceptions.Timeout:
            return {
                'status': 'error',
                'message': 'Délai dépassé lors de la vérification',
                'success': False
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'success': False
            }

    @staticmethod
    def verify_transaction(order):
        """
        Vérifie une transaction et met à jour le statut de l'ordre
        """
        if not order.payment or not order.payment.transaction_id:
            return False, "Aucune information de paiement trouvée"
            
        result = PayGatePayment.check_payment_status(order.payment.transaction_id)
        
        if result['success']:
            # Paiement réussi
            order.payment.status = 'completed'
            order.payment.payment_details['verification_response'] = result
            order.payment.save()
            
            order.payment_status = True
            order.save()
            
            return True, "Paiement confirmé avec succès"
        else:
            return False, result['message']
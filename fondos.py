import sys
from algosdk import account, mnemonic, transaction
from algosdk.v2client import algod

# ----------------------------------------------------------------------
# Configuración de la red (TestNet)
# ----------------------------------------------------------------------
ALGOD_ADDRESS = "https://testnet-api.algonode.cloud"
ALGOD_TOKEN   = ""  # Algonode no necesita token
HEADERS       = {"User-Agent": "algod-python"}

algod_client = algod.AlgodClient(ALGOD_TOKEN, ALGOD_ADDRESS, HEADERS)

# ----------------------------------------------------------------------
# Función para consultar saldo 
# ----------------------------------------------------------------------
def obtener_saldo(address):
    """Consulta y muestra el saldo de una dirección en ALGOs."""
    try:
        acct_info = algod_client.account_info(address)
        micro_algo = acct_info.get('amount', 0)
        algo = micro_algo / 1_000_000
        print(f"Saldo de la cuenta: {algo} ALGO")
        return micro_algo
    except Exception as e:
        print(f" Error al obtener el saldo: {e}")
        return 0

# ----------------------------------------------------------------------
# Función para enviar ALGO 
# ----------------------------------------------------------------------
def enviar_algo(sender_sk, sender_addr, receiver_addr, amount_micro):
    """Construye, firma, envía y confirma una transacción de pago."""
    print("\nPreparando la transacción...")
    try:
        params = algod_client.suggested_params()
        unsigned_txn = transaction.PaymentTxn(
            sender=sender_addr,
            sp=params,
            receiver=receiver_addr,
            amt=amount_micro,
            note="Envío desde script interactivo".encode()
        )
        
        signed_txn = unsigned_txn.sign(sender_sk)
        txid = algod_client.send_transaction(signed_txn)
        print(f"Transacción enviada con éxito. ID: {txid}")

        # Esperar a que se confirme
        print("Esperando confirmación de la red...")
        confirmed_txn = transaction.wait_for_confirmation(algod_client, txid, 5)
        
        print(" ¡Transacción confirmada!")
        print(f"  - Confirmada en el bloque: {confirmed_txn.get('confirmed-round')}")
        print(f"  - Puedes verla en el explorador: https://testnet.algoexplorer.io/tx/{txid}")

    except Exception as e:
        print(f" Error durante el envío: {e}")

# ----------------------------------------------------------------------
# Flujo principal interactivo para enviar fondos
# ----------------------------------------------------------------------
if _name_ == "_main_":
    
    print("---  Script para Enviar ALGOs en la TestNet ---")

    # 1. Cargar la wallet del emisor usando la frase mnemónica
    try:
        passphrase = input("Introduce tu frase mnemónica de 25 palabras:\n> ")
        
        private_key = mnemonic.to_private_key(passphrase)
        address = account.address_from_private_key(private_key)
        print(f"\n Wallet cargada correctamente.")
        print(f"   Dirección: {address}")
    except Exception as e:
        print(f" Error: La frase mnemónica no es válida. {e}")
        sys.exit() # Termina el script si la frase es incorrecta

    # 2. Mostrar el saldo actual
    obtener_saldo(address)
    
    # 3. Pedir los datos para la transacción
    print("\n--- Detalles de la Transacción ---")
    receiver_addr = input("Introduce la dirección de la wallet de DESTINO:\n> ")
    
    if not receiver_addr or len(receiver_addr) != 58:
        print(" Error: La dirección de destino parece inválida.")
        sys.exit()

    try:
        amount_algo_str = input("Introduce la cantidad de ALGOs a enviar (ej: 0.5):\n> ")
        amount_micro = int(float(amount_algo_str) * 1_000_000)
    except ValueError:
        print(" Error: La cantidad introducida no es un número válido.")
        sys.exit()

    # 4. Confirmar y enviar
    print(f"\nVas a enviar {amount_algo_str} ALGO a la dirección {receiver_addr[:10]}...")
    confirmacion = input("¿Estás seguro? (s/n): ").lower()

    if confirmacion == 's':
        enviar_algo(private_key, address, receiver_addr, amount_micro)
        
        print("\n--- Saldos actualizados ---")
        obtener_saldo(address)
    else:
        print("Operación cancelada.") 
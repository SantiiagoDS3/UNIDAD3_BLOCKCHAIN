from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect, get_object_or_404
from .models import Wallet
from django.shortcuts import render
from django.http import JsonResponse
from algosdk.v2client import algod, indexer
from algosdk import account, mnemonic
from .models import Contacto


def envio(request):
    return render(request, 'wallet/envio.html')

def login_view(request):
    """Vista de login (index principal)"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('mi_wallet')
        else:
            return render(request, 'wallet/login.html', {'error': 'Credenciales incorrectas'})
    return render(request, 'wallet/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

def get_balance(request):
    adress = request.GET.get('adress', '')
    if not adress:
        return JsonResponse({"error": "Missing address"}, status=400)

    algod_client = algod.AlgodClient("", "https://testnet-api.algonode.cloud")
    try:
        account_info = algod_client.account_info(adress)
        balance = account_info.get('amount', 0) / 1_000_000  # convertir microAlgos a Algos
        return JsonResponse({"address": adress, "balance": balance})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    

@login_required
def mi_wallet(request):
    """Muestra los datos del dueño de la wallet (usuario autenticado)"""
    try:
        wallet = Wallet.objects.get(user=request.user)
        adress = wallet.adress
        algod_client = algod.AlgodClient("", "https://testnet-api.algonode.cloud")
        try:
            account_info = algod_client.account_info(adress)
            balance = account_info.get('amount', 0) / 1_000_000  # convertir microAlgos a Algos
        except Exception:
            balance = None
        txs = []
    except Wallet.DoesNotExist:
        return render(request, "wallet/no_wallet.html")
    
    return render(request, "wallet/mi_wallet.html", {
        "address": adress,
        "balance": balance,
        "txs": txs,
        "wallet": wallet
        })

@login_required
def transacciones(request):
    """Consulta transacciones reales de la wallet del usuario (en testnet)"""
    try:
        wallet = Wallet.objects.get(user=request.user)
    except Wallet.DoesNotExist:
        return render(request, "wallet/no_wallet.html")

    # Cliente del indexer público (para leer transacciones)
    client = indexer.IndexerClient("", "https://testnet-idx.algonode.cloud")

    try:
        # Consultar las últimas transacciones enviadas o recibidas por la dirección
        response = client.search_transactions_by_address(wallet.adress, limit=10)
        txs = response.get("transactions", [])
    except Exception as e:
        txs = []
        error = f"Error al obtener transacciones: {e}"
        return render(request, "wallet/transacciones.html", {"txs": txs, "error": error})

    # Convertir datos para mostrar en la plantilla
    transacciones = []
    for tx in txs:
        tipo = tx.get("tx-type", "desconocido")
        monto = tx.get("payment-transaction", {}).get("amount", 0) / 1_000_000
        receptor = tx.get("payment-transaction", {}).get("receiver", "")
        remitente = tx.get("sender", "")
        fecha = tx.get("round-time", 0)
        transacciones.append({
            "tipo": tipo,
            "monto": monto,
            "receptor": receptor,
            "remitente": remitente,
            "fecha": fecha,
        })

    return render(request, "wallet/transacciones.html", {
        "transacciones": transacciones,
        "address": wallet.adress,
    })

@login_required
def configuracion(request):
    return render(request, "wallet/configuracion.html")

@login_required
def registrar_wallet(request):
    """Genera una nueva wallet Algorand y la asocia al usuario, luego redirige a mi_wallet"""
    error = None
    if request.method == 'POST':
        # generar cuenta Algorand
        try:
            priv_key, adress = account.generate_account()
            mnemonic_phrase = mnemonic.from_private_key(priv_key)
            # Crear o actualizar wallet del usuario
            Wallet.objects.update_or_create(
                user=request.user,
                defaults={
                    'address': adress,
                    'private_key': mnemonic_phrase,
                }
            )
            return redirect('mi_wallet')
        except Exception as e:
            error = str(e)

    return render(request, 'wallet/registrar_wallet.html', {'error': error})

@login_required
def contactos_list(request):
    error = None
    if request.method == "POST":
        action = request.POST.get("action", "create")
        if action == "create":
            nombre = request.POST.get("nombre", "").strip()
            email = request.POST.get("email", "").strip()
            direccion = request.POST.get("direccion", "").strip()
            if not nombre or not email:
                error = "Nombre y email son obligatorios."
            else:
                Contacto.objects.create(user=request.user, nombre=nombre, email=email, direccion=direccion)
                return redirect('contactos')
        elif action == "edit":
            pk = request.POST.get("pk")
            contacto = get_object_or_404(Contacto, pk=pk, user=request.user)
            nombre = request.POST.get("nombre", "").strip()
            email = request.POST.get("email", "").strip()
            direccion = request.POST.get("direccion", "").strip()
            if not nombre or not email:
                error = "Nombre y email son obligatorios."
            else:
                contacto.nombre = nombre
                contacto.email = email
                contacto.direccion = direccion
                contacto.save()
                return redirect('contactos')
        elif action == "delete":
            pk = request.POST.get("pk")
            contacto = get_object_or_404(Contacto, pk=pk, user=request.user)
            contacto.delete()
            return redirect('contactos')

    contactos = Contacto.objects.filter(user=request.user).order_by('-id')
    return render(request, 'wallet/contactos_list.html', {'contactos': contactos, 'error': error})

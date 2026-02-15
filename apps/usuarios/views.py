from datetime import date

from django.db.models import Q
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.template.smartif import Literal

from apps.financeiro.models import Categoria
from django.urls import reverse
from datetime import date

from apps.financeiro.models import HistoricoSaldo

from apps.usuarios.models import CustomUser

#Função para cadastrar novos usuarios
def cadastrar(request):
    #Caso o usuario já esteja logado vai ser redirecionado para a página principal
    if request.user.is_authenticated:
        return redirect(reverse('core:index'))
    
    if request.method == "GET":
        return render(request, 'cadastro.html')
    else:
        # Armazenando as informações fornecidas para a criação do usuario
        usuario = request.POST.get('usuario', '').strip()
        email = request.POST.get('email', '').strip()
        senha = request.POST.get('senha', '').strip()
        repetir_senha = request.POST.get('repetir_senha', '').strip()
        
        # Confirmação de senha
        if senha != repetir_senha:
            messages.error(request, 'As senhas não coincidem. Tente novamente.')
            return redirect(reverse('usuario:cadastro'))
        
        # Filtra se já existe um e-mail ou usuario parecidos no banco de dados, para evitar cadastros repetidos.
        user = CustomUser.objects.filter(Q(username=usuario) | Q(email=email)).first()
        if user:
            messages.error(request, 'Já existe um usuário com esse nome de usuário ou email')
            return redirect(reverse('usuario:cadastro'))
        
        # Chamando a função de criar usuário do Django
        user = CustomUser.objects.create_user(username=usuario, email=email, password=senha)

        #Logando o usuario automaticamente e redicionando para a aplicação
        login(request, user)
        HistoricoSaldo.inicializarPrimeiroValor(user)
        return redirect(reverse('core:dashboard'))

#Função de Login
def logar(request):
    if request.user.is_authenticated:
        return redirect(reverse('core:dashboard'))
        
    if request.method == "GET":
        return render(request, 'login.html')

    # Váriaveis que vão receber os dados do frontend
    usuario = request.POST.get('usuario', '').strip()
    senha = request.POST.get('senha','').strip()

    # Autentica se o email e a senha são compativeís
    user = authenticate(request, username=usuario, password=senha)

    # Caso as informações estejam certezas ele loga
    if user:
        login(request, user)
        return redirect(reverse('core:dashboard'))
    else:  # Se não informa erro devido que retornou nenhum objeto
        messages.error(request, 'Usuário ou senha errada')
        return redirect(reverse('usuario:login'))

def deslogar(request):
    logout(request)
    return redirect(reverse('core:index'))

def configuraçoes(request):
    user = request.user

    if not user.is_authenticated:
        return redirect(reverse('core:index'))

    categorias = Categoria.objects.all()
    context = {
        'mes': date.today().month
        , 'ano': date.today().year
        , 'usuario': user
        , 'categorias': categorias
        , 'todas_categorias_receita': categorias.filter(tipo='R')
        , 'todas_categorias_despesa': categorias.filter(tipo='D')
        , 'hoje': date.today()
    }

    if not request.method == "POST":
        return render(request, 'configuraçoes.html', context)

    if "atualizar_perfil" in request.POST:
        novo_usuario = request.POST.get('nome_usuario', '').strip()
        novo_email = request.POST.get('email', '').strip()

        if not novo_usuario or not novo_email:
            messages.error(request, "Nome de usuário e e-mail são obrigatórios")
            return redirect(reverse('usuario:configuracoes'))

        pode_salvar = True

        if user.username != novo_usuario:
            if CustomUser.objects.filter(username__exact=novo_usuario).exists():
                messages.error(request, f"O nome de usuário '{novo_usuario}' já está em uso")
                pode_salvar = False

        if user.email != novo_email:
            if CustomUser.objects.filter(email__exact=novo_email).exists():
                messages.error(request, f"O e-mail '{novo_email}' já está em uso")
                pode_salvar = False

        if pode_salvar:
            user.username = novo_usuario
            user.email = novo_email
            user.save()
            messages.success(request, "Suas informações foram atualizadas com sucesso")
            return render(request, 'configuraçoes.html', context)

        return redirect(reverse('usuario:configuracoes'))

    elif "confirmar_senha" in request.POST:
        senha_atual = request.POST.get('senha_atual', '').strip()
        nova_senha = request.POST.get('nova_senha', '').strip()
        confirmar_senha = request.POST.get('confirmar_senha', '').strip()

        if not user.check_password(senha_atual):
            messages.error(request, "A senha atual está incorreta.")
            return redirect(reverse('usuario:configuracoes'))

        if not nova_senha or not confirmar_senha:
            messages.error(request, "Todos os campos de senha são obrigatórios.")
            return redirect(reverse('usuario:configuracoes'))

        if nova_senha != confirmar_senha:
            messages.error(request, "As novas senhas não coincidem.")
            return redirect(reverse('usuario:configuracoes'))

        else:
            user.set_password(nova_senha)
            user.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Senha alterada com sucesso")
            return redirect(reverse('usuario:configuracoes'))

    elif "deletar_conta" in request.POST:
        deslogar(request)
        user.delete()
        # Mensagem que a conta foi deletada com sucesso
        return redirect(reverse('core:index'))






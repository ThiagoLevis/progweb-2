from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required, permission_required
from donation.decorators import group_required
from project.models import Usuario, Campanha, Doacao
from project.forms import  EditGerenciaUsuarioForm, CriarCampanhaForm
from django.db.models import Q, Sum


def home(request):
    context = {}
    return render(request, 'home.html', context=context)

def faq(request):
    context = {}
    return render(request, 'faq.html', context=context)

@login_required
@group_required('Administrador')
def gerenciar_usuarios(request):
    
    usuarios = Usuario.objects.all()

    for usuario in usuarios:
        usuario.grupos = list(usuario.groups.all().values_list('name', flat=True))
        print(usuario)

    context = {
        'usuarios': usuarios,
    }
    return render(request, 'gerenciar_usuarios/gerenciar_usuarios.html', context=context)

@login_required
@group_required('Administrador')
def editar_usuario(request, user_id):
    usuario = get_object_or_404(Usuario, id=user_id)
    
    status = {'is_active': usuario.is_active}
    
    form = EditGerenciaUsuarioForm(request.POST or None, initial=status)
    
    if request.method == 'POST':

        if form.is_valid():

            usuario.is_active = form.cleaned_data['is_active']
            usuario.save()

            return redirect('gerenciar_usuarios')

    context = {"usuario": usuario, "form": form }

    return render(request, 'gerenciar_usuarios/editar_usuario.html', context=context)

@login_required
def campanhas_ativas(request):
    # campanhas = Campanha.objects.exclude(finalizado=True, campanha_finalizada=True)
    campanhas =  Campanha.objects.exclude(Q(finalizado=True) | Q(campanha_finalizada=True))
    context = {}
    return render(request, 'campanha/campanhas.html', context=context)

@login_required
@group_required('Administrador')
def gerenciar_campanhas(request):
    campanhas = Campanha.objects.all()
    for campanha in campanhas:
        valor_arrecadado = Doacao.objects.filter(id_campanha=campanha.id).aggregate(Sum('valor'))['valor__sum']
        if valor_arrecadado == None:
            valor_arrecadado = 0
        campanha.valor_arrecadado = valor_arrecadado
        print(valor_arrecadado)
    context = {'campanhas': campanhas}
    return render(request, 'campanha/gerenciar_campanhas.html', context=context)

@login_required
@group_required('Administrador')
def criar_campanha(request):
    
    form = CriarCampanhaForm(request.POST, request.FILES)
    
    if request.method == 'POST':

        if form.is_valid():
            form.save()

            return redirect('home')

    context = {"form": form }
    return render(request, 'campanha/criar_campanha.html', context=context)

@login_required
@group_required('Administrador')
def editar_campanha(request, id):
    context = {}
    return render(request, 'campanha/editar_campanha.html', context=context)

@login_required
def doar_campanha(request, id_campanha):
    context = {}
    return render(request, 'doar_campanha.html', context=context)

def handler_403(request):
    return render(request, 'errors/403.html', status=403)

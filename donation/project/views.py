from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required, permission_required
from donation.decorators import group_required
from project.models import Usuario, Campanha, Doacao, MensagemFAQ
from project.forms import  EditGerenciaUsuarioForm, CriarCampanhaForm, EditCampanhaForm, DoacaoForm, FAQform
from django.db.models import Q, Sum
import datetime
from django.contrib import messages
from datetime import date

def filter_campanhas():
    data_atual = date.today()
    campanhas = Campanha.objects.all().order_by('data_fim')
    campanhas_filtered =[]
    for item in campanhas:
        item.data = item.data_fim-data_atual
        valor_arrecadado = Doacao.objects.filter(id_campanha=item.id).aggregate(Sum('valor'))['valor__sum']
        if valor_arrecadado == None:
            valor_arrecadado = 0
        item.valor_arrecadado = valor_arrecadado
        item.valor_arrecadado_perc = int((valor_arrecadado / item.valor_necessario) * 100)
        if item.valor_arrecadado_perc > 100:
            item.valor_arrecadado_perc = 100
        if(item.data.days > 0 and item.data.days < 10 and item.valor_necessario != item.valor_arrecadado):
            campanhas_filtered.append(item)

    for campanhas in campanhas_filtered:
        print(campanhas.data)
        
    return campanhas_filtered

def home(request):
    filter_campanhas()
    campanhas_destaque = filter_campanhas()[:3]
    context = {'campanhas_destaque': campanhas_destaque}
    return render(request, 'home.html', context=context)

def faq(request):
    form = FAQform(request.POST or None)
    
    if request.method == 'POST':

        if form.is_valid():
            form.save()
            messages.success(request, f"{form.cleaned_data['nome']}, sua mensagem foi enviada com sucesso! ", extra_tags='alert-success')
            return redirect('home')

    context = {"form" : form}
    return render(request, 'faq/faq.html', context=context)

@login_required
@group_required('Administrador')
def mensagensFAQ(request):
    mensagens = MensagemFAQ.objects.all().order_by('-id')

    context = {
        'mensagens': mensagens,
    }
    return render(request, 'faq/mensagens_faq.html', context=context)

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
    today = datetime.datetime.today()
    campanhas =  Campanha.objects.exclude(Q(finalizado=True) | Q(data_fim__lte=today))
    for campanha in campanhas:
        valor_arrecadado = Doacao.objects.filter(id_campanha=campanha.id).aggregate(Sum('valor'))['valor__sum']
        if valor_arrecadado == None:
            valor_arrecadado = 0
        campanha.valor_arrecadado = round(valor_arrecadado, 2)
        campanha.valor_arrecadado_perc = int((valor_arrecadado / campanha.valor_necessario) * 100)
        if campanha.valor_arrecadado_perc > 100:
            campanha.valor_arrecadado_perc = 100
    context = {'campanhas': campanhas}
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
    context = {'campanhas': campanhas}
    return render(request, 'campanha/gerenciar_campanhas.html', context=context)

@login_required
@group_required('Administrador')
def criar_campanha(request):
    
    form = CriarCampanhaForm(request.POST or None, request.FILES or None)
    
    if request.method == 'POST':

        if form.is_valid():
            form.save()
            messages.success(request, f" Você criou a campanha {form.cleaned_data['nome']} com sucesso! ", extra_tags='alert-success')
            return redirect('home')

    context = {"form": form }
    return render(request, 'campanha/criar_campanha.html', context=context)

@login_required
@group_required('Administrador')
def editar_campanha(request, id_campanha):
    
    campanha = get_object_or_404(Campanha, id=id_campanha)
    
    form = EditCampanhaForm(request.POST or None, request.FILES or None, instance=campanha)
    
    if form.is_valid():
        if form.has_changed():
            form.save()
            return redirect('home')
    
    context = {'form': form}
    return render(request, 'campanha/editar_campanha.html', context=context)

def excluir_campanha(request, id_campanha):
    campanha = get_object_or_404(Campanha, id=id_campanha)
    campanha.delete()
    return redirect('gerenciar_campanhas')

@login_required
def doar_campanha(request, id_campanha):

    form = DoacaoForm(request.POST or None)
    campanha = get_object_or_404(Campanha, id=id_campanha)
    
    valor_arrecadado = Doacao.objects.filter(id_campanha=campanha.id).aggregate(Sum('valor'))['valor__sum']
    if valor_arrecadado == None:
        valor_arrecadado = 0
    falta = campanha.valor_necessario - valor_arrecadado
    if falta < 0:
        falta = 0
    campanha.falta = round(falta, 2)
    
    if request.method == 'POST':
        if form.is_valid():
            doacao = Doacao(
                id_campanha=campanha,
                id_usuario=request.user,
                data=datetime.datetime.today(),
                valor=form.cleaned_data['valor'],
                cc_number=form.cleaned_data['cc_number'],
                cc_expiry=form.cleaned_data['cc_expiry'],
                cc_code=form.cleaned_data['cc_code'],
                nome_cartao=form.cleaned_data['nome_titular'],
                cpf_titular=form.cleaned_data['cpf_titular'],
                email=form.cleaned_data['email'],
            )
            doacao.save()
            messages.success(request, f" Você doou R${form.cleaned_data['valor']} para a campanha {campanha.nome} com sucesso! ", extra_tags='alert-success')
            return redirect('home')

    context = {'campanha': campanha, 'form': form}
    return render(request, 'campanha/doar_campanha.html', context=context)

def handler_403(request):
    return render(request, 'errors/403.html', status=403)

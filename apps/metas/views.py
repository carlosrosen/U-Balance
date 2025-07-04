from django.shortcuts import render, reverse, redirect, get_object_or_404
from decimal import Decimal
from datetime import date
from unicodedata import category

from apps.metas.operacoes.metas import GetMetas, OperacoesMeta, Metas
from apps.financeiro.models import Categoria
from common.dominio.data import Data


def menuMetas(request):
    if not request.user.is_authenticated:
        return redirect(reverse('usuario:login'))

    # Atualiza as metas ativas
    metas = Metas.objects.filter(user_fk__id=request.user.id)
    operacoes = OperacoesMeta(request.user.id)
    for meta in metas:
        operacoes.atualizarStatusMeta(meta)

    gettermetas = GetMetas(request.user.id)
    metas = gettermetas.todosEmOrdem()
    categorias = Categoria.GetTodasCategorias()
    context = {'metas': metas
        , 'categorias': categorias
        , 'todas_categorias_receita': categorias.filter(tipo='R')
        , 'todas_categorias_despesa': categorias.filter(tipo='D')
        , 'hoje': date.today()
        , 'mes': date.today().month
        , 'ano': date.today().year
    }
    return render(request, 'metas.html', context)


def criarMeta(request):
    if not request.user.is_authenticated:
        return redirect(reverse('usuario:login'))
    if not request.method == "POST":
        return redirect(reverse('core:dashboard'))
    operacoes_meta = OperacoesMeta(request.user.id)
    valor = request.POST.get('valorMeta')
    tipo = request.POST.get('tipoMeta')
    data_inicio = request.POST.get('dataInicio')
    data_fim = request.POST.get('dataFinal')
    descricao = request.POST.get('descricao')
    categoria = request.POST.get('categoria')
    Categoria.verificacaoNomesCategoria(categoria)
    categoria = Categoria.objects.get(nome=categoria)

    operacoes_meta.criarMeta(categoria=categoria
                             , valor=Decimal(valor)
                             , tipo=tipo
                             , data_inicio=Data(data_inicio)
                             , data_fim=Data(data_fim)
                             , descricao=descricao
    )
    url = request.POST.get('next') or reverse('core:dashboard')
    return redirect(url)


def editarMeta(request, meta_id):
    if request.method == 'POST':
        print('\n\n',request.POST,'\n\n')
        categoria = request.POST.get('categoria')
        tipo = request.POST.get('tipoMeta')
        valor = Decimal(request.POST.get('valor'))
        data_inicio = Data(request.POST.get('data_inicio'))
        data_fim = Data(request.POST.get('data_fim'))
        descricao = request.POST.get('descricao')

        categoria = Categoria.objects.get(nome=categoria)

        operacao = OperacoesMeta(request.user.id)
        operacao.editarMeta(meta_id, categoria, tipo, valor, data_inicio, data_fim, descricao)

    return redirect("core:metas:meta")


def deletarMeta(request, meta_id):
    if request.method == 'POST':
        meta = get_object_or_404(Metas, id=meta_id)
        operacao = OperacoesMeta(request.user.id)
        operacao.deletarMeta(meta)
        return redirect("core:metas:meta")

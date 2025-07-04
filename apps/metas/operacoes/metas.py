from dateutil.utils import today

from apps.metas.models import Metas
from apps.financeiro.models import ParcelasTransacao, Categoria

from django.contrib.auth.models import AbstractBaseUser
from apps.usuarios.models import CustomUser
from typing import cast

from django.db.models import Sum

from common.dominio.data import Data
from decimal import Decimal
from datetime import date
from itertools import chain

class OperacoesMeta:
    def __init__(self, user_id):
        self.user = CustomUser.objects.get(id=user_id)

    def criarMeta(
            self,
            categoria: Categoria,
            tipo: str,
            valor: Decimal,
            data_inicio: Data,
            data_fim: Data,
            descricao: str
    ):
        # Tem que formatar os valores certinhos aqui no parametro

        if tipo not in ['MAX', 'MIN']:
            return "Tipo de meta inválido. Use 'MAX' para limite máximo ou 'MIN' para mínimo desejado."
        if data_fim.valor < data_inicio.valor:
            return "A data final não pode ser anterior à data inicial."
        if valor <= 0:
            return "Valor inserido menor ou igual a zero"

        Metas.objects.create(
            user_fk=self.user,
            tipo=tipo,
            categoria_fk=categoria,
            valor=valor,
            data_inicio=data_inicio.valor,
            data_fim=data_fim.valor,
            descricao=descricao
        )

    def editarMeta(
            self,
            meta_id: Metas,
            categoria: Categoria,
            tipo: str,
            valor: Decimal,
            data_inicio: Data,
            data_fim: Data,
            descricao: str,
    ):
        meta = Metas.objects.get(user_fk=self.user, id=meta_id)
        if not meta.status == 'A':
            return

        if data_fim.valor < data_inicio.valor:
            return "A data final não pode ser anterior à data inicial."
        elif data_fim.valor < meta.data_inicio:
            return "A data final não pode ser anterior à data inicial."

        print(f"Data de início: {data_inicio.valor}")
        print(f"Data de fim: {data_fim.valor}")
        print(f"Categoria: {categoria}")
        print(f"Tipo: {tipo}")
        print(f"Valor: {valor}")
        print(f"Descrição: {descricao}")

        print(f"Meta - Data de início: {meta.data_inicio}")
        print(f"Meta - Data de fim: {meta.data_fim}")
        print(f"Meta - Categoria: {meta.categoria_fk}")
        print(f"Meta - Tipo: {meta.tipo}")
        print(f"Meta - Valor: {meta.valor}")
        print(f"Meta - Descrição: {meta.descricao}")

        meta.data_fim = data_fim.valor
        meta.categoria_fk = categoria
        meta.tipo = tipo
        meta.valor = valor
        meta.data_inicio = data_inicio.valor
        meta.descricao = descricao

        try:
            meta.save()
        except Exception as e:
            raise Exception('Não foi possivel editar a meta')

    def deletarMeta(self, meta: Metas):
        meta.delete()

    def atualizarStatusMeta(self, meta: Metas):

        # Retorna um QuerySet [Uma lista de objetos do banco de dados que seguem algumas condições]
        parcelas = ParcelasTransacao.objects.filter(
            # O underline duplo é uma forma de navegar pelas chaves estrangeiras no Django
            transacao_fk__user_fk=self.user,
            transacao_fk__categoria_fk=meta.categoria_fk,
            data__gte=meta.data_inicio,             # __gte maior ou igual
            data__lte=meta.data_fim,                # __lte menor ou igual
            pago=True,
        )

        total = parcelas.aggregate(soma=Sum('valor'))['soma'] or Decimal('0.00')

        hoje = date.today()

        if meta.status in ['C', 'U'] and meta.data_inicio <= hoje <= meta.data_fim:
            if meta.tipo == 'MAX' and total < meta.valor:
                meta.status = 'A'
                meta.data_conclusao = None
            elif meta.tipo == 'MIN' and total < meta.valor:
                meta.status = 'A'
                meta.data_conclusao = None

        if meta.tipo == 'MAX':
            if total > meta.valor and hoje <= meta.data_fim:
                meta.status = 'U'
                meta.data_conclusao = hoje
            elif hoje > meta.data_fim and total <= meta.valor:
                meta.status = 'C'
                meta.data_conclusao = hoje
        elif meta.tipo == 'MIN':
            if total >= meta.valor and hoje <= meta.data_fim:
                meta.status = 'C'
                meta.data_conclusao = hoje
            elif hoje > meta.data_fim and total < meta.valor:
                meta.status = 'N'
                meta.data_conclusao = hoje
        try:
            meta.save()
        except Exception:
            raise Exception('Erro inesperado ao atualizar metas')

    def metasEmDict(self, meta: Metas):
        return {
            "categoria": meta.categoria_fk.nome,
            "tipo": meta.tipo,
            "valor": Decimal(meta.valor),
            "data_inicio": meta.data_inicio,
            "data_fim": meta.data_fim,
            "descricao": meta.descricao,
            "status": meta.status
        }


class GetMetas:
    def __init__(self, user):
        self.user = CustomUser.objects.get(id=user)

    def todosEmOrdem(self) -> list:
        metas = Metas.objects.filter(user_fk=self.user)
        ativos = metas.filter(status='A').order_by('data_inicio')
        ultrapassados = metas.filter(status='U').order_by('data_inicio')
        nao_atingidos = metas.filter(status='N').order_by('data_inicio')
        concluidos = metas.filter(status='C').order_by('data_inicio')
        return list(chain(ativos, ultrapassados, nao_atingidos, concluidos))

    def taxaConclusao(self) -> str:
        metas = Metas.objects.filter(user_fk=self.user)
        if metas.count() <= 0:
            return '0'
        return str(metas.filter(status="C").count()/metas.count() * 100)
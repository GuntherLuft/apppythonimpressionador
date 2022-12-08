from kivy.app import App
from kivy.lang import Builder
from telas import *
from botoes import *
import requests
import os
import certifi
from bannervenda import BannerVenda
import os
from functools import partial
from myfirebase import MyFirebase
from bannervendedor import BannerVendedor
from datetime import date

os.environ["SSL_CERT_FILE"] = certifi.where()

GUI = Builder.load_file("main.kv")
class MainApp(App):

    cliente = None
    produto = None
    unidade = None

    def build(self):
        self.firebase = MyFirebase()
        return GUI

    def on_start(self):
        #Carregar fotos de perfil
        arquivos = os.listdir("icones/fotos_perfil")
        pagina_fotoperfil = self.root.ids["fotoperfilpage"]
        lista_fotos = pagina_fotoperfil.ids['lista_fotosperfil']
        for foto in arquivos:
            imagem = ImageButton(source=f"icones/fotos_perfil/{foto}", on_release=partial(self.mudar_foto_perfil, foto))
            lista_fotos.add_widget(imagem)

        #Carregar as fotos dos clientes
        arquivos = os.listdir("icones/fotos_clientes")
        pagina_adicionarvendas = self.root.ids["adicionarvendaspage"]
        lista_clientes = pagina_adicionarvendas.ids["lista_clientes"]
        for foto_cliente in arquivos:
            imagem = ImageButton(source=f"icones/fotos_clientes/{foto_cliente}",
                                 on_release=partial(self.selecionar_cliente, foto_cliente))
            label = LabelButton(text=foto_cliente.replace(".png", "").capitalize(),
                                 on_release=partial(self.selecionar_cliente, foto_cliente))
            lista_clientes.add_widget(imagem)
            lista_clientes.add_widget(label)

        #Carregar as fotos dos produtos
        arquivos = os.listdir("icones/fotos_produtos")
        pagina_adicionarvendas = self.root.ids["adicionarvendaspage"]
        lista_produtos = pagina_adicionarvendas.ids["lista_produtos"]
        for foto_produto in arquivos:
            imagem = ImageButton(source=f"icones/fotos_produtos/{foto_produto}",
                                 on_release=partial(self.selecionar_produto, foto_produto))
            label = LabelButton(text=foto_produto.replace(".png", "").capitalize(),
                                on_release=partial(self.selecionar_produto, foto_produto))
            lista_produtos.add_widget(imagem)
            lista_produtos.add_widget(label)

        pagina_adicionarvendas = self.root.ids["adicionarvendaspage"]
        label_data = pagina_adicionarvendas.ids['label_data']
        label_data.text = f"Data: {date.today().strftime('%d/%m/%Y')}"

        self.carregar_infos_usuario()

    def carregar_infos_usuario(self):
        try:
            with open("refreshtoken.txt", "r") as arquivo:
                refresh_token = arquivo.read()
                local_id, id_token = self.firebase.trocar_token(refresh_token)
                self.local_id = local_id
                self.id_token = id_token
            # Pegando informações de vendas
            requisicao = requests.get(f"https://aplicativovendashash-1a58b-default-rtdb.firebaseio.com/{self.local_id}.json?auth={self.id_token}")
            requisicao_dict = requisicao.json()

            # Colocando foto de perfil
            avatar = requisicao_dict['avatar']
            foto_perfil = self.root.ids['foto_perfil']
            foto_perfil.source = f"icones/fotos_perfil/{avatar}"
            self.avatar = avatar

            # Criando lista com vendas
            try:
                vendas = requisicao_dict['vendas']
                self.vendas = vendas
                for id_venda in vendas:
                    venda = vendas[id_venda]
                    banner = BannerVenda(cliente=venda['cliente'], data=venda['data'], foto_cliente=venda['foto_cliente'],
                                         produto=venda['produto'], foto_produto=venda['foto_produto'],
                                         quantidade=venda['quantidade'], unidade=venda['unidade'], preco=venda['preco'])
                    pagina_homepage = self.root.ids["homepage"]
                    lista_vendas = pagina_homepage.ids["lista_vendas"]
                    lista_vendas.add_widget(banner)
            except Exception as excecao:
                print(excecao)
                pass

            #Preencher vendedores
            pagina_listavendedores = self.root.ids["listarvendedorespage"]
            lista_vendedores = pagina_listavendedores.ids["lista_vendedores"]

            equipe = requisicao_dict["equipe"]
            lista_equipe = equipe.split(',')
            for id_vendedor_equipe in lista_equipe:
                if id_vendedor_equipe != "":
                    banner_vendedor = BannerVendedor(id_vendedor=id_vendedor_equipe)
                    lista_vendedores.add_widget(banner_vendedor)


            #Preencher Total de Vendas
            total_vendas = requisicao_dict["total_vendas"]
            self.total_vendas = total_vendas
            pagina_homepage = self.root.ids["homepage"]
            pagina_homepage.ids["label_total_vendas"].text = f"[color=#000000]Total de Vendas:[/color] [b]R${total_vendas}[/b]"

            self.equipe = requisicao_dict['equipe']


            #Preencher ID único
            id_unico = requisicao_dict['id_vendedor']
            self.id_unico = id_unico
            pagina_ajustes = self.root.ids['ajustespage']
            pagina_ajustes.ids['id_vendedor'].text = f"Seu ID único: {id_unico}"


            self.mudar_tela("homepage")

        except:
            pass


    def mudar_tela(self, id_tela):
        gerenciador_telas = self.root.ids["screen_manager"]
        gerenciador_telas.current = id_tela

    def mudar_foto_perfil(self, foto, *args):
        foto_perfil = self.root.ids["foto_perfil"]
        foto_perfil.source= f"icones/fotos_perfil/{foto}"

        info = f'{{"avatar": "{foto}"}}'
        requisicao = requests.patch(f"https://aplicativovendashash-1a58b-default-rtdb.firebaseio.com/{self.local_id}.json?auth={self.id_token}",
                                    data=str(info))

        self.mudar_tela("ajustespage")

    def adicionar_vendedor(self, id_vendedor_adicionado):
        link = f'https://aplicativovendashash-1a58b-default-rtdb.firebaseio.com/.json?orderBy="id_vendedor"&equalTo="{id_vendedor_adicionado}"'
        requisicao = requests.get(link)
        requisicao_dict = requisicao.json()

        pagina_adicionarvendedor = self.root.ids['adicionarvendedorpage']
        mensagem_texto = pagina_adicionarvendedor.ids['mensagem_outrovendedor']
        if requisicao_dict == {}:
            mensagem_texto.text = "Usuário não encontrado"
        else:
            equipe = self.equipe.split(',')
            if id_vendedor_adicionado in equipe:
                mensagem_texto.text = "Vendedor já faz parte da equipe"
            else:
                self.equipe = self.equipe + f",{id_vendedor_adicionado}"
                info = f'{{"equipe": "{self.equipe}"}}'
                requests.patch(f"https://aplicativovendashash-1a58b-default-rtdb.firebaseio.com/{self.local_id}.json?auth={self.id_token}",
                               data=info)

                pagina_listavendedores = self.root.ids["listarvendedorespage"]
                lista_vendedores = pagina_listavendedores.ids["lista_vendedores"]
                banner_vendedor = BannerVendedor(id_vendedor=id_vendedor_adicionado)
                lista_vendedores.add_widget(banner_vendedor)
                mensagem_texto.text = "Vendedor adicionado"

    def selecionar_cliente(self, foto, *args):
        pagina_adicionarvendas = self.root.ids["adicionarvendaspage"]
        lista_clientes = pagina_adicionarvendas.ids["lista_clientes"]
        self.cliente = foto.replace(".png", "")

        for item in list(lista_clientes.children):
            item.color = (1, 1, 1, 1)
            try:
               texto = item.text
               texto = texto.lower() + ".png"
               if foto == texto:
                   item.color = (0, 207/255, 219/255, 1)
            except:
                pass

    def selecionar_produto(self, foto, *args):
        pagina_adicionarvendas = self.root.ids["adicionarvendaspage"]
        lista_produtos = pagina_adicionarvendas.ids["lista_produtos"]
        self.produto = foto.replace(".png", "")

        for item in list(lista_produtos.children):
            item.color = (1, 1, 1, 1)
            try:
                texto = item.text
                texto = texto.lower() + ".png"
                if texto == foto:
                    item.color = (0, 207/255, 219/255, 1)
            except:
                pass

    def selecionar_unidade(self, id_unidades, id_unidade, *args):
        pagina_adicionarvendas = self.root.ids['adicionarvendaspage']
        lista_unidades = pagina_adicionarvendas.ids[id_unidades]
        self.unidade = id_unidade.replace("unidades_", "")
        for item in list(lista_unidades.children):
            if item.text == id_unidade.replace("unidades_", ""):
                item.color = (0, 207/255, 219/255, 1)
            else:
                item.color = (1, 1, 1, 1)

    def adicionar_venda(self, *args):
        cliente = self.cliente
        produto = self.produto
        unidade = self.unidade

        pagina_adicionarvendas = self.root.ids["adicionarvendaspage"]
        data = pagina_adicionarvendas.ids['label_data'].text.replace("Data: ", "")
        preco = pagina_adicionarvendas.ids['preco_total'].text
        quantidade = pagina_adicionarvendas.ids['quantidade_total'].text

        if not cliente:
            pagina_adicionarvendas.ids['label_selecionecliente'].color = (1, 0, 0, 1)
        if not produto:
            pagina_adicionarvendas.ids['label_selecioneproduto'].color = (1, 0, 0, 1)
        if not unidade:
            pagina_adicionarvendas.ids['unidades_kg'].color = (1, 0, 0, 1)
            pagina_adicionarvendas.ids['unidades_unidades'].color = (1, 0, 0, 1)
            pagina_adicionarvendas.ids['unidades_litros'].color = (1, 0, 0, 1)
        if not preco:
            pagina_adicionarvendas.ids['label_preco'].color = (1, 0, 0, 1)
        else:
            try:
                preco = float(preco)
            except:
                pagina_adicionarvendas.ids['label_preco'].color = (1, 0, 0, 1)

        if not quantidade:
            pagina_adicionarvendas.ids['label_quantidade'].color = (1, 0, 0, 1)
        else:
            try:
                quantidade = float(quantidade)
            except:
                pagina_adicionarvendas.ids['label_quantidade'].color = (1, 0, 0, 1)

        if cliente and produto and unidade and preco and quantidade and (type(preco) == float) and (type(quantidade) == float):
            foto_produto = produto + '.png'
            foto_cliente = cliente + '.png'

            info = f'{{"cliente": "{cliente}", "produto": "{produto}", "foto_cliente": "{foto_cliente}", "foto_produto": "{foto_produto}", "data": "{data}", "unidade": "{unidade}", "preco": "{preco}", "quantidade": "{quantidade}"}}'

            requests.post(f"https://aplicativovendashash-1a58b-default-rtdb.firebaseio.com/{self.local_id}/vendas.json?auth={self.id_token}", data=info)

            banner = BannerVenda(cliente=cliente, produto=produto, foto_cliente=foto_cliente, foto_produto=foto_produto,
                                 data=data, preco=preco, quantidade=quantidade, unidade=unidade)

            pagina_homepage = self.root.ids["homepage"]
            lista_vendas = pagina_homepage.ids["lista_vendas"]
            lista_vendas.add_widget(banner)

            link = f'https://aplicativovendashash-1a58b-default-rtdb.firebaseio.com/{self.local_id}/total_vendas.json?auth={self.id_token}'
            requisicao = requests.get(link)
            valor_vendas = float(requisicao.json())

            valor_vendas += preco

            link = f'https://aplicativovendashash-1a58b-default-rtdb.firebaseio.com/{self.local_id}.json?auth={self.id_token}'
            info = f'{{"total_vendas": "{valor_vendas}"}}'
            requests.patch(link, data=info)

            pagina_homepge = self.root.ids["homepage"]
            venda_total = pagina_homepage.ids['label_total_vendas']
            venda_total.text = f"[color=#000000]Total de Vendas:[/color] [b]R${valor_vendas}[/b]"
            venda_total.markup = True



            self.mudar_tela("homepage")


        self.cliente = None
        self.produto = None
        self.unidade = None

    def carregar_todas_vendas(self):
        pagina_todasvendas = self.root.ids["todasvendaspage"]
        lista_vendas = pagina_todasvendas.ids["lista_vendas"]

        for item in list(lista_vendas.children):
            lista_vendas.remove_widget(item)


        requisicao = requests.get(f'https://aplicativovendashash-1a58b-default-rtdb.firebaseio.com/.json?orderBy="id_vendedor"')
        requisicao_dict = requisicao.json()

        total_vendas = 0

        try:
            for local_id_usuario in requisicao_dict:
                vendas = requisicao_dict[local_id_usuario]["vendas"]
                for id_venda in vendas:
                    venda = vendas[id_venda]
                    total_vendas += float(venda['preco'])
                    banner = BannerVenda(cliente=venda['cliente'], data=venda['data'],
                                         foto_cliente=venda['foto_cliente'],
                                         produto=venda['produto'], foto_produto=venda['foto_produto'],
                                         quantidade=venda['quantidade'], unidade=venda['unidade'], preco=venda['preco'])
                    lista_vendas.add_widget(banner)
        except:
            pass



        # Colocando foto de perfil

        foto_perfil = self.root.ids["foto_perfil"]
        foto_perfil.source = "icones/fotos_perfil/hash.png"

        pagina_todasvendas.ids["label_total_vendas"].text = f"[color=#000000]Total de Vendas:[/color] [b]R${total_vendas}[/b]"



        self.mudar_tela("todasvendaspage")

    def sair_todas_vendas(self, id_tela):
        foto_perfil = self.root.ids["foto_perfil"]
        foto_perfil.source = f"icones/fotos_perfil/{self.avatar}"

        self.mudar_tela(id_tela)

    def carregar_vendas_vendedor(self, dic_info_vendedor, *args):

        try:
            pagina_vendas_outrovendedor = self.root.ids["vendasoutrovendedorpage"]
            lista_vendas = pagina_vendas_outrovendedor.ids['lista_vendas']
            vendas = dic_info_vendedor['vendas']

            for item in list(lista_vendas.children):
                lista_vendas.remove_widget(item)

            for id_venda in vendas:
                venda = vendas[id_venda]
                banner = BannerVenda(cliente=venda['cliente'], data=venda['data'], foto_cliente=venda['foto_cliente'],
                                     produto=venda['produto'], foto_produto=venda['foto_produto'],
                                     quantidade=venda['quantidade'], unidade=venda['unidade'], preco=venda['preco'])
                lista_vendas.add_widget(banner)
        except Exception as excecao:
            print(excecao)

        total_vendas = dic_info_vendedor['total_vendas']
        pagina_vendas_outrovendedor.ids["label_total_vendas"].text = f"[color=#000000]Total de Vendas:[/color] [b]R${total_vendas}[/b]"

        foto_perfil = self.root.ids["foto_perfil"]
        avatar = dic_info_vendedor['avatar']
        foto_perfil.source = f"icones/fotos_perfil/{avatar}"

        self.mudar_tela("vendasoutrovendedorpage")



MainApp().run()
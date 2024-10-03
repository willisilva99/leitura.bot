import os
import discord
from discord.ext import commands, tasks
import random
from flask import Flask, jsonify
import threading
from flask_cors import CORS

# Pega o token da variável de ambiente
TOKEN = os.getenv('TOKEN')

# Configurações dos "intents" para o bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True
intents.messages = True  # Permite que o bot detecte eventos de mensagens apagadas

bot = commands.Bot(command_prefix='!', intents=intents)

# Lista de atividades para o bot
atividades = [
    "sobrevivendo ao apocalipse",
    "jogando 7 Days to Die",
    "enfrentando zumbis",
]

# Palavras-chave para interação do bot
palavras_chave = ["minha base", "lua", "morri", "servidor caiu"]

# Lista de mensagens apocalípticas para avisos
mensagens_apocalipticas = [
    'As hordas de zumbis estão à espreita, e {user} compartilhou algo importante no canal {channel}!',
    '{user} encontrou algo no apocalipse no canal {channel}! Fiquem atentos!',
    'O caos se aproxima... e {user} acabou de enviar algo no canal {channel}!',
    'Um aviso do apocalipse! {user} compartilhou uma mensagem crucial no canal {channel}.',
    'A sobrevivência depende da informação. {user} acabou de compartilhar algo no canal {channel}!',
    '{user} está enfrentando o caos e compartilhou algo no canal {channel}!',
    'A resistência se fortalece! {user} compartilhou algo no canal {channel}!',
    'Prepare-se para o inesperado... {user} postou algo no canal {channel}!',
    'Cada mensagem é vital para a sobrevivência... {user} enviou algo no canal {channel}!',
    '{user} desvendou algo importante no apocalipse e postou no canal {channel}!',
]

# Lista de novas mensagens para respostas mencionando o usuário
mensagens_resposta_apocaliptica = [
    'O apocalipse nunca descansa... {user}, esteja preparado!',
    'As trevas avançam, e {user} se destaca na luta pela sobrevivência!',
    'Todos os olhos estão em você, {user}. O destino do apocalipse depende de suas próximas ações!',
    'A resistência nunca foi tão forte... {user}, continue firme no caos!',
    'O silêncio do apocalipse foi quebrado... e {user} está no centro disso tudo!',
    'A noite se aproxima, {user}. Não deixe que os zumbis te alcancem!',
    'Mesmo nas trevas mais profundas, {user} traz esperança para todos nós.',
    'O destino do apocalipse está nas mãos de sobreviventes como você, {user}!'
]

# ---- API Flask ----
app = Flask(__name__)  
CORS(app)

@app.route('/')
def home():
    return jsonify({'status': 'Bot está online e rodando!'})

@app.route('/destaques')
def get_destaques():
    guild = bot.get_guild(1186390028990025820)  # Substitua pelo ID do seu servidor
    if guild is None:
        return jsonify({'error': 'Servidor não encontrado'}), 404

    role = discord.utils.get(guild.roles, name="Destaque")
    if not role:
        return jsonify({'error': 'Cargo não encontrado'}), 404

    members = [{
        'id': member.id,
        'display_name': member.display_name,
        'avatar': member.avatar.url if member.avatar else None
    } for member in role.members]
    return jsonify(members)

@app.route('/jogadores_online')
def jogadores_online():
    guild = bot.get_guild(1186390028990025820)  # Substitua pelo ID do seu servidor
    if guild is None:
        return jsonify({'error': 'Servidor não encontrado'}), 404

    membros_online = [{
        'id': member.id,
        'display_name': member.display_name,
        'avatar': member.avatar.url if member.avatar else None,
        'status': str(member.status).capitalize(),
    } for member in guild.members if member.status != discord.Status.offline and not member.bot]

    return jsonify(membros_online)

# ---- Bot Discord ----

# Evento que indica quando o bot está pronto
@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}')
    mudar_atividade.start()

# Tarefa que muda a atividade do bot periodicamente
@tasks.loop(minutes=5)
async def mudar_atividade():
    atividade = random.choice(atividades)
    await bot.change_presence(activity=discord.Game(name=atividade))

# ---- Comando !site ----
@bot.command()
async def site(ctx):
    await ctx.send('Acesse o nosso site: http://novaera7d.com.br/')

# ---- Comando !vote ----
@bot.command()
async def vote(ctx):
    await ctx.send('Vote em nosso servidor: https://novaera7d.netlify.app/botao')

# ---- Comando !missao ----
@bot.command()
async def missao(ctx):
    await ctx.send('Aqui está o link da missão: https://youtu.be/2tNePGLm53s')

# Evento para boas-vindas a novos membros
@bot.event
async def on_member_join(member):
    # ID do canal de boas-vindas (substitua pelo ID do seu canal)
    channel = bot.get_channel(1186636197934661632)

    # Lista de mensagens apocalípticas
    mensagens_boas_vindas = [
        f'Bem-vindo(a) ao apocalipse, {member.mention}! As hordas de zumbis estão à espreita, mas juntos sobreviveremos.',
        f'{member.mention}, você chegou na hora certa... as defesas estão baixas e precisamos de toda ajuda possível. Bem-vindo(a) à Nova Era!',
        f'Os céus estão escuros e os zumbis rondam as ruas. Seja bem-vindo(a) ao caos, {member.mention}!',
        f'Você sobreviveu ao mundo lá fora, mas agora a verdadeira luta começa aqui. Bem-vindo(a), {member.mention}, à Nova Era!',
        f'{member.mention}, o silêncio antes da tempestade nunca durou tanto tempo... Prepare-se para o que está por vir. Bem-vindo(a) ao refúgio!',
        f'Você encontrou o último refúgio da humanidade, {member.mention}. Agora, é matar ou morrer. Bem-vindo(a) à Nova Era!',
        f'Os portões se fecharam atrás de você, {member.mention}. Não há mais volta. Bem-vindo(a) ao nosso pesadelo.',
        f'{member.mention}, seja bem-vindo(a) à resistência! Os zumbis estão lá fora, mas aqui... aqui, nós lutamos até o fim!'
    ]

    # Escolhe uma mensagem aleatória
    mensagem_escolhida = random.choice(mensagens_boas_vindas)

    # Envia a mensagem no canal de boas-vindas
    if channel:
        await channel.send(mensagem_escolhida)

# Evento para reagir a imagens enviadas no chat de fotos e avisar no canal de avisos
@bot.event
async def on_message(message):
    # Certifica-se de que o bot não vai reagir às próprias mensagens
    if message.author == bot.user:
        return

    # Verifica se a mensagem foi enviada no canal de fotos (1262571048898138252)
    if message.channel.id == 1262571048898138252:
        if message.attachments:
            for attachment in message.attachments:
                # Verifica se o arquivo é uma imagem
                if attachment.content_type.startswith('image/'):
                    # Reage com um emoji customizado
                    emoji = bot.get_emoji(1262842500125556866)
                    if emoji:
                        await message.add_reaction(emoji)

                    # Enviar uma mensagem de aviso no canal de avisos (1186636197934661632)
                    aviso_channel = bot.get_channel(1186636197934661632)
                    if aviso_channel:
                        mensagem_aviso = random.choice(mensagens_apocalipticas).format(user=message.author.mention, channel=f'<#{message.channel.id}>')
                        await aviso_channel.send(mensagem_aviso)

    # Verifica se a mensagem foi enviada no canal de interação (1186636197934661632)
    if message.channel.id == 1186636197934661632:
        # Interação com palavras-chave
        for palavra in palavras_chave:
            if palavra in message.content.lower():
                # Reage com um emoji aleatório
                emoji = random.choice(['😱', '💀', '⚠️', '🧟‍♂️'])
                await message.add_reaction(emoji)

                # Enviar uma resposta apocalíptica mencionando o usuário
                resposta_apocaliptica = random.choice(mensagens_resposta_apocaliptica).format(user=message.author.mention)
                await message.channel.send(resposta_apocaliptica)
                break  # Para garantir que só reaja uma vez por mensagem

    # Processa os comandos caso a mensagem seja um comando
    await bot.process_commands(message)

# Evento para detectar quando uma mensagem é deletada
@bot.event
async def on_message_delete(message):
    # Verifica se a mensagem deletada é do canal de fotos
    if message.channel.id == 1262571048898138252:
        print(f"A mensagem com ID {message.id} foi deletada.")

# Função para rodar a API Flask em uma thread separada
def run_api():
    port = int(os.environ.get('PORT', 5000))  # Railway usa a variável de ambiente PORT
    app.run(host='0.0.0.0', port=port)

# Função para rodar o bot e a API ao mesmo tempo
def run_bot():
    bot.run(TOKEN)

# Iniciar as threads
if __name__ == '__main__':
    threading.Thread(target=run_api).start()
    run_bot()

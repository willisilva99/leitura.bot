import os
import discord
from discord.ext import commands, tasks
import random
from flask import Flask, jsonify
import threading
from flask_cors import CORS
from threading import Lock
import json

# Pega o token da variável de ambiente
TOKEN = os.getenv('TOKEN')

# Configurações dos "intents" para o bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True
intents.messages = True  # Habilitar para capturar eventos de mensagens deletadas

bot = commands.Bot(command_prefix='!', intents=intents)

# Lista global para armazenar as fotos e informações dos jogadores, protegida por um lock
fotos = []
fotos_lock = Lock()  # Lock para proteger a lista de acessos simultâneos

# Carregar as fotos do arquivo JSON (persistência)
def carregar_fotos():
    global fotos
    try:
        with open('fotos.json', 'r') as file:
            fotos = json.load(file)
    except FileNotFoundError:
        fotos = []

# Salvar as fotos no arquivo JSON (persistência)
def salvar_fotos():
    with fotos_lock:
        with open('fotos.json', 'w') as file:
            json.dump(fotos, file, indent=4)

# Carregar fotos ao iniciar
carregar_fotos()

# ---- API Flask ----
app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return jsonify({'status': 'Bot está online e rodando!'})

@app.route('/fotos', methods=['GET'])
def get_fotos():
    with fotos_lock:
        return jsonify(fotos)

# Adiciona rota para "Membros Online"
@app.route('/jogadores_online', methods=['GET'])
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

# Adiciona rota para "Destaques"
@app.route('/destaques', methods=['GET'])
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

# ---- Bot Discord ----

# Evento que indica quando o bot está pronto
@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}')
    mudar_atividade.start()

# Tarefa que muda a atividade do bot periodicamente
@tasks.loop(minutes=5)
async def mudar_atividade():
    atividade = random.choice([
        "sobrevivendo ao apocalipse",
        "jogando 7 Days to Die",
        "enfrentando zumbis"
    ])
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
    channel = bot.get_channel(1186636197934661632)  # Canal de boas-vindas

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
    
    mensagem_escolhida = random.choice(mensagens_boas_vindas)
    if channel:
        await channel.send(mensagem_escolhida)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Verifica se a mensagem foi enviada no canal correto e contém anexos
    if message.channel.id == 1262571048898138252:
        if message.attachments:
            for attachment in message.attachments:
                # Verifica se o anexo é uma imagem
                if attachment.content_type.startswith('image/'):
                    # Reage à mensagem com o emoji personalizado
                    emoji = bot.get_emoji(1262842500125556866)
                    if emoji:
                        await message.add_reaction(emoji)

                    # Armazena a foto e o apelido do jogador
                    with fotos_lock:
                        fotos.append({
                            "message_id": message.id,
                            "url": attachment.url,
                            "player": message.author.display_name,  # Apelido do jogador
                            "avatar": str(message.author.avatar.url if message.author.avatar else "")
                        })

                    # Salva as fotos no arquivo JSON para persistência
                    salvar_fotos()

    # Processa comandos normalmente
    await bot.process_commands(message)

# Evento para remover a foto quando a mensagem for deletada (opcional)
@bot.event
async def on_message_delete(message):
    if message.channel.id == 1262571048898138252:  # Verifica se é o canal correto
        with fotos_lock:
            # Filtrar as fotos e remover aquelas com o ID da mensagem deletada
            fotos[:] = [foto for foto in fotos if foto["message_id"] != message.id]
            salvar_fotos()  # Salva a lista atualizada no JSON

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

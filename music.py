# discord bot
# Criado Por Mário
#libs

#libs padrão
import time
import random
import threading

#youtube content
import pafy
from youtube_dl import YoutubeDL
from requests import get

#discord api
import discord
from discord import FFmpegPCMAudio
from discord.ext import commands

discord.opus.load_opus()

#bot settings

code = {}

intents = discord.Intents.all()

#bot prefix command
bot = commands.Bot(command_prefix="!",intents=intents)

#json responsavel por salva alguns dados dos canais

# th -> json de verificação de faixa
th = {}
# musics -> responsavel pelo player e pela playlist
musics = {}



#API's settings

#API Settings
YTDL_OPTIONS = {'format':'bestaudio','noplaylist':'False'}#youtube-dl configs
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn'}#ffmpeg-discord config

#busca conteudos do youtube
def search(arg): #busca um conteudo string
    with YoutubeDL(YTDL_OPTIONS) as ydl:#usando youtube-dl como ydl

        try: #tente

            v = pafy.new(arg)#youtube-link

            best = v.getbestaudio() #pegar o melhor audio

            video = best #return var

        except: #exceção

            video = ydl.extract_info(f"ytsearch:{arg}",download=False)['entries'][0]#buscar argumento

        else:

            video = ydl.extract_info(arg,download=False)#buscar argumento

    return video

def g(x):
    return ((x**2)+28092001)-x


def generate():
    code = random.randint(000,999)
    return code
#embed messagem
def messagem(action,content,color):
    return discord.Embed(title=action,description=content,color=color)

#função thread que verifica se a musica ainda está tocando
def verify(guild):
    #enquanto verdadeiro
    while True:
        
        if len(musics.keys()) > 0:#verificar se um numero players é maior que zero
        
            for i in musics.keys(): #percorre todos os players
        
                if not musics[i]["play"].is_playing(): #se o player não estiver mais tocando
                
                    if len(musics[i]["list"]) > 0: #verifica se existe musica na playlist
        
                        #print(f"{i} play {musics} on the playlist")
        
                        musics[i]["last"] = musics[i]["list"][0] #define a primeira musica da lista com a ultima
        
                        video = search(musics[i]["list"][0]) #busca o titulo
        
                        musics[i]["list"].remove(musics[i]["list"][0]) #remove da playlist
                        
                        source = FFmpegPCMAudio(video['url'],**FFMPEG_OPTIONS) #pega o bytecode
        
                        #musics[i]["ctx"].send(embed=messagem("Play list automatica",video["title"],0x00ff00))
        
                        musics[i]["play"].play(source) #play
    
        time.sleep(1) #timeout de 1s


#-----events-----


#quando entrar no servidor
@bot.event
async def on_ready():#quando pronto
    channels = "" #string com canais
    
    print("BOT HAS BEEN STARTED")

    for g in bot.guilds:
        channels += f"{g}\n"

    print("SERVERS:")
    print(channels)



#-----commands-----

#-----play command-----
#!play
@bot.command(aliases=['p'])
async def play(ctx,*,title):
    #buscar o video
    video = search(title) #função de busca
    
    #checar os canais de voz
    if not (ctx.voice_client):#se não estiver em um canal de voz

        if ctx.author.voice: #se o autor estiver em uma sala
            voice = await ctx.author.voice.channel.connect() #conecta
        
        else: # se não
            await ctx.send(embed=messagem("Informativo","Você não está em um sala!",0xffff00)) #menssagem informativa
            return None #interrompe o comando

        if ctx.guild.name in musics.keys(): # se a o canal tiver uma playlist

            musics.pop(ctx.guild.name) #remove a playlist
    
    else: #caso o bot esteja em um canal de voz
       
        if ctx.author.voice:
            
            if (ctx.voice_client.channel != ctx.author.voice.channel): #se o canal de voz não for o mesmo que o seu
                print("debug:",ctx.voice_client.channel)
                await ctx.send(embed=messagem("Informativo","O bot já está em uma sala",0xffff00)) #menssagem informativa
    
    #player
    if "general" not in th.keys(): #se não existir um gerenciador de playlist ativo
        
        #cria um gerenciador de playlist
        th["general"] = {
            "async":threading.Thread(target=verify,args=[musics])
        }
        
        if not th["general"]["async"].is_alive():#caso o gerenciador esteja inativo
        
            th["general"]["async"].start()#inicia o gerenciado
    
    else: #caso o gerenciador exista
    
        if not th["general"]["async"].is_alive(): #se estiver inativo

            #redefine o player para o estado atual
            th["general"] = {
                "async":threading.Thread(target=verify,args=[musics])
                }
    
            th["general"]["async"].start()#incia o gerenciador

        
    #playlist

    if ctx.guild.name not in musics.keys(): # se o servidor não possuir playlist
    
        #cria perfil de playlist
        musics[ctx.guild.name] = {
            "play":voice,
            "last":"",
            "list":[],
            "ctx":ctx}
    
    #play musica

    if musics[ctx.guild.name]["play"].is_playing():# se existe uma musica tocando

        musics[ctx.guild.name]["list"].append(title) # adiciona a lista
    
        await ctx.send(embed=messagem("Adicionado a fila",video["title"],0x0000ff))#adicionado a fila

    else: # caso o player estja vazio
        musics[ctx.guild.name]["last"] = title # define a musica como a ultima
        try: #tenta tocar a musica

            await ctx.send(embed=messagem("Tocando",video["title"],0x00ff00))
            
            source = FFmpegPCMAudio(video['url'],**FFMPEG_OPTIONS)
            
            musics[ctx.guild.name]["play"].play(source)

        except: #caso haja erro reconecta ao canal e toca a musica

            if (ctx.voice_client.channel == ctx.author.voice.channel):

                await ctx.guild.voice_client.disconnect()
                
                time.sleep(2)
                
                await ctx.author.voice.channel.connect()
                
                musics[ctx.guild.name]["play"].play(source)



#-----sair command-----

#!sair
@bot.command()
async def sair(ctx):
    if ctx.guild.name in musics.keys():# se existir uma playlist
       
        if musics[ctx.guild.name]["play"].is_playing() or musics[ctx.guild.name]["play"].is_paused():# se estiver tocando ou pausado
       
            musics[ctx.guild.name]["play"].stop()#para a musica

    if (ctx.voice_client.channel == ctx.author.voice.channel): # se estiver conectado ao canal do autor

        await ctx.guild.voice_client.disconnect() # sai do canal

    else: #se não estiver no canal do autor
        await ctx.send(embed=messagem("Informativo","O bot não está em sua sala",0xffff00))# messagem informative

#-----pause command-----

#!pause
@bot.command()
async def pause(ctx): 
    if ctx.guild.name in musics.keys(): #se existir playlist

        if (ctx.voice_client.channel == ctx.author.voice.channel): # se estiver conectado ao canal do autor

            if musics[ctx.guild.name]["play"].is_playing(): #se estiver tocando musica
            
                musics[ctx.guild.name]["play"].pause() # pausa a musica

#-----resume command-----

@bot.command()
async def resume(ctx):
    if ctx.guild.name in musics.keys(): # se exitir play list

        if (ctx.voice_client.channel == ctx.author.voice.channel): # se estiver conectado ao canal do autor
        
            if musics[ctx.guild.name]["play"].is_paused(): # se estiver pausado
            
                musics[ctx.guild.name]["play"].resume() #retoma a musica

#-----stop command-----

@bot.command()
async def stop(ctx):
    if ctx.guild.name in musics.keys(): # se existir playlist
    
        if (ctx.voice_client.channel == ctx.author.voice.channel): # se estiver conectado ao canal do autor

            if musics[ctx.guild.name]["play"].is_playing() or musics[ctx.guild.name]["play"].is_paused():# se estiver tocando ou pausado
        
                musics[ctx.guild.name]["play"].stop() #para a musica


#-----skip command-----

#playlist method


@bot.command(aliases=["s"])
async def skip(ctx):
    if ctx.guild.name in musics.keys():# se existir playlist

        if (ctx.voice_client.channel == ctx.author.voice.channel): # se estiver conectado ao canal do autor

            musics[ctx.guild.name]["play"].stop() #para a musica atual
        
            if len(musics[ctx.guild.name]["list"]) >0: #verifica se exite musica na playlist

                video = search(musics[ctx.guild.name]["list"][0]) # busca a primeira opção
                
                musics[ctx.guild.name]["list"].remove(musics[ctx.guild.name]["list"][0])#remove o titulo da playlist
                
                source = FFmpegPCMAudio(video['url'],**FFMPEG_OPTIONS)#pega o bytecode do audio
                
                await ctx.send(embed=messagem("Tocando",video["title"],0x00ff00)) #tocando

                musics[ctx.guild.name]["play"].play(source)#play



#-----recall-----
@bot.command()
async def recall(ctx):
    if ctx.guild.name in musics.keys():
        if (ctx.voice_client.channel == ctx.author.voice.channel): # se estiver conectado ao canal do autor

            m = musics[ctx.guild.name]["last"]

            video = search(m)

            source = FFmpegPCMAudio(video['url'],**FFMPEG_OPTIONS)

            await ctx.send(embed=messagem("Recall",video['title'],0x0000ff))

            musics[ctx.guild.name]["play"].play(source)

#-----show play list-----

#playlist method

@bot.command(aliases=['playlist','lista'])
async def Show(ctx):
    if ctx.guild.name in musics.keys():

        if (ctx.voice_client.channel == ctx.author.voice.channel): # se estiver conectado ao canal do autor

            lista = musics[ctx.guild.name]["list"]
            
            if len(lista) >0:
            
                content_string = ""
            
                for i,m in enumerate(lista):
            
                    content_string += f"{i}.{m}\n"

                await ctx.send(embed=messagem("Playlist",content_string,0xffffff))
            
            else:
            
                await ctx.send(embed=messagem("Playlist","vazia",0xffffff))



@bot.command(aliases=['rm','rmv'])
async def remove(ctx,content):
    if ctx.guild.name in musics.keys():
        
        if (ctx.voice_client.channel == ctx.author.voice.channel): # se estiver conectado ao canal do autor

            if len(musics[ctx.guild.name]["list"]) > 0:
            
                musics[ctx.guild.name]["list"].remove(content)
            
                await ctx.send(embed=messagem("Playlist - removido",content,0xffaa00))

@bot.command()
async def add(ctx,order,*,title):
    if ctx.guild.name in musics.keys():

        if (ctx.voice_client.channel == ctx.author.voice.channel): # se estiver conectado ao canal do autor

            
            musics[ctx.guild.name]["list"].insert(int(order),title)
            
            await ctx.send(embed=messagem("Playlist - adicionado",f"{title} adicionado a posição {order}",0x00ff00))


#-----DEV command-----
"""
@bot.command()
async def DevTest(ctx):#função de testes
    
    print(ctx.author.id)
    
    await ctx.send(embed=messagem("teste","https://google.com",0xb85911))

"""
#-----help command-----

@bot.command(aliases=['h','hlp'])
async def ajuda(ctx): #help
    menu = """
    - !h ou !ajuda - exibe o menu de ajuda do bot
    - !sair - sai do canal caso o usuario caso alguem da sala solicite
    - !p ou !play [name] ou [link] - reproduz a musica pelo nome ou link(youtube)
    - !stop - para a musica
    - !s ou !skip - pula para a proxima musica da fila
    - !pause - pausa a musica
    - !resume - continua a musica
    - !lista - exibe a playlist
    - !remove [name] - remove a musica da playlist
    - !add [posição] [name] - adiciona musica em uma posição especifica

    obs: o restart sera gravado pelas infos: server,channel,user,time
    Em caso de abuso do comando o bot sera removido do servidor!
    
    
    -- Este Bot é exclusivo do Mário, qualquer problema manda uma mensagem que vejo depois!
    """
    await ctx.send(embed=messagem("Menu",menu,0xffffff))


#bot.run(TOKEN)
# bot.py
import os
import random
import openai
import discord
from dotenv import load_dotenv
from discord.ext import commands
import youtube_dl
import asyncio
import requests


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)
 
openai.api_key = os.getenv('OPEN_AI')

model_engine = 'text-davinci-002'


ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'before_options': '-nostdin',
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

    # Placeholder
    @classmethod
    async def search(cls, search, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(search, download=not stream))
        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Streaming(name="Bot Things", url='https://www.twitch.tv/washedgamerbro'))
    print(f'{bot.user.name} has connected to Discord! (BOT)')
     
@bot.event
async def on_member_join(member):
    await member.create_dm()
    await member.dm_channel.send(
        f'Hi {member.name}, welcome to the Discord server! Don\'t plan on staying long if Nicole invited you though.'
    )
    
        
@bot.command(name='insult', help='Responds with an AI generated insult towards you!')
async def insult(ctx):
    prompt = [
            f"Insult {ctx.message.author.name}. Insult options can include their height, weight, balding status, smell, and social status. Be as vulgar and innapropriate as possible, include profanity. Not all options for the insult need to be used.", 
            f"Insult {ctx.message.author.name} by making up a horrible story about them. Have them be the loser in their story and have everyone dislike them.", 
            f"Sarcasticly thank {ctx.message.author.name} for their wonderfully horrible contributions to not only this server, but society as a whole. And list things that would be better off without them. Make sure it shows how useless they are.",
            f"Childishly insult {ctx.message.author.name} in the most stereotypical way possible."
    ]
    completions = openai.Completion.create(
        engine=model_engine,
        prompt=prompt[random.randint(0,len(prompt)-1)],
        max_tokens=2048,
        n=1,
        stop=None,
        temperature=0.9,
    )
    await ctx.reply(completions.choices[0].text)
    
        
@bot.command(name='ask', help='Ask a simple question to AI and generates a response!')
async def ask(ctx, *arg):
    prompt = ' '.join(arg)
    completions = openai.Completion.create(
        engine=model_engine,
        prompt=prompt,
        max_tokens=2048,
        n=1,
        stop=None,
        temperature=0.7,
    )
    await ctx.reply(completions.choices[0].text)
        
        
@bot.command(name='play', help='Type !play followed by the link of the youtube video you want to listen to.')
async def play(ctx, arg):
    video_link = arg
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    voice_channel = ctx.author.voice.channel
    
    if voice_client:
        print('Bot is already connected to a voice channel!')
    else:
        voice_client = await voice_channel.connect()
        
    player = await YTDLSource.from_url(video_link, stream=True)
    ctx.voice_client.play(player)
    

@bot.command(name='stop', help='Will stop and disconect the WGB Bot from its current Voice Channel.')
async def stop(ctx):
    if ctx.guild.voice_client is not None:
        await ctx.voice_client.disconnect()
        print('Bot successfully disconnected from the Voice Channel!')
    else:
        print("The bot is not currently in a Voice Channel!")

        
@bot.command(name='meme', help='A meme to hopefully make you laugh.')
async def meme(ctx):
    response = requests.get('https://meme-api.com/gimme').json()
    meme = response['preview']
    image_url = meme[-1]
    await ctx.reply(image_url)
        

@bot.command(name='roulette', help='Take a chance. 1 in 10.')
async def roulette(ctx):
    result = random.randint(1,10)
    await ctx.reply('Determining your fate...')
    await asyncio.sleep(3)
    if result == 7:
        await ctx.reply('It appears you are the winner of our game!')
        await asyncio.sleep(2)
        await ctx.author.kick()
    else:
        await ctx.reply('It appears you did not win the grand prize.. Better luck next time!')
    
        
@bot.event
async def on_message(ctx):
    if ctx.author.name == 'jophrey' and ctx.author.discriminator == '7305':
        prompt = 'Come up with a single short, funny, and unique nickname for a short person.'
        completions = openai.Completion.create(
            engine=model_engine,
            prompt=prompt,
            max_tokens=30,
            n=1,
            stop=None,
            temperature=0.85,
        )
        await ctx.author.edit(nick=completions.choices[0].text)
        await bot.process_commands(ctx)
    elif ctx.author.name == 'Jake Tucker' and ctx.author.discriminator == '1044':
        prompt = 'Come up with a single funny, and unique nickname for someone that simps for a female twitch streamer'
        completions = openai.Completion.create(
            engine=model_engine,
            prompt=prompt,
            max_tokens=30,
            n=1,
            stop=None,
            temperature=0.85,
        )
        await ctx.author.edit(nick=completions.choices[0].text)
        await bot.process_commands(ctx)
    else:
        await bot.process_commands(ctx)
        
        
@bot.event
async def on_voice_state_update(member, before, after):
    # Check if the user has joined a voice channel
    if before.channel is None and after.channel is not None:
        # Check if the user has joined the specific voice channel
        if after.channel.name == "Abandoned Friends Klub":
            # Send a message to the default channel
            if member.name == 'avidityyo' and member.discriminator == "4864":
                await member.guild.system_channel.send(f"{member.mention} joined the voice chat because her other friends are busy!!")
            elif member.name == 'Ryalexz' and member.discriminator == '8776':
                await member.guild.system_channel.send(f"Who the fuck is {member.mention}???")
            elif member.name == 'teej' and member.discriminator == '0741':
                await member.move_to(None)
            elif member.name == 'Faiyte' and member.discriminator == '4829':
                await member.guild.system_channel.send(f"Where the fuck are the cookies {member.mention}???")
            elif member.name == 'Jake Tucker' and member.discriminator == '1044':
                await member.guild.system_channel.send(f"Grand Master Simp, {member.mention}, has arrived to defend his Queen.")
            #else:
            #    await member.guild.system_channel.send(f"Welcome to the voice channel, {member.mention}!")

            
bot.run(TOKEN)



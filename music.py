import discord
from discord.ext import commands
import youtube_dl
import asyncio

youtube_dl.utils.bug_reports_message = lambda: ''

# stores the player objects and the track titles inside the guild id key
queues = {}

class music(commands.Cog):
  def __init__(self, client):
    self.client = client
    self.tracks = {}
    self.isPaused = False
    self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -nostdin', 'options': '-vn'}
    self.YDL_OPTIONS = {'format': 'bestaudio/best',
    'outtmpl': 'downloads/%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',  # ipv6 addresses cause issues sometimes
    'force-ipv4': True,
    'cachedir': False}

  async def queue(self, ctx, id, vc, url, state='add'):
    if queues[id] == [] and state == 'add':
      stream = await self.playSong(ctx, url)
      queues[id] = [stream]
    elif state == 'add':
      stream = await self.playSong(ctx, url)
      queues[id].append(stream)
      await ctx.send('Added track ' + '**' + str(self.tracks[id][len(self.tracks[id]) - 1]) + '**')

    def afterQueue(error):
      if len(queues[id]) > 0:
        queues[id].pop(0)
        self.tracks[id].pop(0)
        asyncio.run_coroutine_threadsafe(self.queue(ctx,id,vc,url,state='queue'), self.client.loop)
      else:
        asyncio.run_coroutine_threadsafe(ctx.send("Queue has finished! Bye!"), self.client.loop)
        asyncio.run_coroutine_threadsafe(vc.disconnect(), self.client.loop)

    if not vc.is_playing():
      vc.play(queues[id][0], after=afterQueue)
      await ctx.send('Playing ' + '**' + str(self.tracks[id][0]) + '**')
    
      
  @commands.command(name='join', help="Tells the bot to join the voice channel")
  async def join(self, ctx):
    if ctx.author.voice is None:
      return await ctx.send('You are not in a voice channel!')
    voiceChannel = ctx.author.voice.channel
    if ctx.voice_client is None:
      return await voiceChannel.connect()
    else:
      return await ctx.voice_client.move_to(voiceChannel)
  
  @commands.command(name='disconnect', help="Tells the bot to get lost", aliases=['disc', 'bye', 'leave'])
  async def disconnect(self, ctx):
    if ctx.author.voice is None:
      return await ctx.send('You are not in a voice channel!')
    await ctx.voice_client.disconnect()
    self.tracks[ctx.message.guild.id].clear()
    queues[ctx.message.guild.id].clear()
    await ctx.send("Leaving voice chat :wave:")

  async def playSong(self, ctx, url):
    with youtube_dl.YoutubeDL(self.YDL_OPTIONS) as ydl:
      info = ydl.extract_info(url, download=False)
      if 'entries' in info:        # if no url is input
        url2 = info['entries'][0]['formats'][0]['url']
        if ctx.message.guild.id not in self.tracks.keys():
          self.tracks[ctx.message.guild.id] = [info['entries'][0]['title']]
        else:
          self.tracks[ctx.message.guild.id].append(info['entries'][0]['title'])
      elif 'formats' in info:      # if url is passed
        url2 = info['formats'][0]['url']
        if ctx.message.guild.id not in self.tracks.keys():
          self.tracks[ctx.message.guild.id] = [info['title']]
        else:
          self.tracks[ctx.message.guild.id].append(info['title'])
      #print(*(x for x in self.tracks[ctx.message.guild.id]), sep='\n')
      stream = await discord.FFmpegOpusAudio.from_probe(url2, **self.FFMPEG_OPTIONS)
    return stream
  
  @commands.command(name='play', help="Plays any song", aliases=['pl'])
  async def play(self, ctx, *, url):
    if ctx.author.voice is None:
      return await ctx.send('You are not in a voice channel!')
    if ctx.voice_client is None:
      await ctx.author.voice.channel.connect()
    vc = ctx.guild.voice_client
    guild = ctx.message.guild
    if guild.id not in queues.keys():
      queues[guild.id] = []
    await self.queue(ctx, guild.id, vc, url)


  @commands.command(name='queue', help="Shows the current queue", aliases=['q','Q'])
  async def showQueue(self, ctx):
    if ctx.voice_client is None:
      return await ctx.send('I am not connected to a voice channel!')
    print(len(self.tracks[ctx.message.guild.id]))

    if len(self.tracks[ctx.message.guild.id]) == 1:
      queueEmbed = discord.Embed(title="Queue", description = "Your queue seems to be a tad bit empty :(", color=discord.Colour.random())
      queueEmbed.add_field(name=':drum: Currently playing \n' + self.tracks[ctx.message.guild.id][0], value='\u200b', inline=False)
      queueEmbed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
      await ctx.send(embed=queueEmbed)
    
    elif len(self.tracks[ctx.message.guild.id]) > 0:
      queueEmbed = discord.Embed(title="Queue", color=discord.Colour.random())
      queuee = ""
      if len(self.tracks[ctx.message.guild.id]) > 10:
        n = 10
      else:
        n = len(self.tracks[ctx.message.guild.id])
        
      if len(self.tracks[ctx.message.guild.id]) != 0:
        for i in range(1, n):
          queuee += ":white_small_square:" + str(i) + ". " + self.tracks[ctx.message.guild.id][i] + "\n"
      else:
        queuee = "No songs here"
      
      queueEmbed.add_field(name='Coming up next', value='**' + queuee + '**', inline=False)
      queueEmbed.add_field(name=':drum: Currently playing \n' + self.tracks[ctx.message.guild.id][0], value='\u200b', inline=False)
      queueEmbed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
      await ctx.send(embed=queueEmbed)
      
    else:
      await ctx.send('No music in queue')

  @commands.command(name='pause', help="Pauses the song", aliases=['p'])
  async def pause(self, ctx):
    self.isPaused = True
    ctx.voice_client.pause()
    await ctx.send("Paused :pause_button: !")

  @commands.command(name='resume', help="Resumes the song", aliases=['re'])
  async def resume(self, ctx):
    self.isPaused = False
    ctx.voice_client.resume()
    await ctx.send("Resumed :play_pause: !")

  
  @commands.command(name='skip', help="Skips the current song")
  async def skip(self, ctx):
    if ctx.author.voice is None:
      return await ctx.send('You are not in a voice channel!')
    ctx.voice_client.stop()
    await ctx.send("Playing next track")

async def setup(client):
    await client.add_cog(music(client))

